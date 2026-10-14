"""Test Harness do TaskAnalyzer: os cenários de aceite da seção 2 em verificação executável.

Mapeamento da seção 2.2 da especificação (``specs/task_analyzer_spec.md``):

- Cenário 1 → ``test_metricas_globais_do_conjunto_valido`` e ``test_indicadores_por_prioridade``.
- Cenários 2.a e 2.b → ``test_tarefa_invalida_levanta_excecao``.
- Cenários 2.c e 2.d → ``test_sem_tarefas_concluidas_levanta_excecao``.
- Cenário 3 → ``test_prazo_exato_e_sem_prazo_nao_sao_atraso``.
- Cenário 4 → ``test_resultado_independe_da_ordem``.
- RN-02 e RN-03 → ``test_tempo_de_conclusao_min`` e ``test_esta_atrasada``.
"""

from datetime import datetime

import pytest

from src.exceptions import SemTarefasConcluidasError, TarefaInvalidaError
from src.models import IndicadorPrioridade, Prioridade, Tarefa
from src.task_analyzer import (
    calcular_metricas,
    esta_atrasada,
    tempo_de_conclusao_min,
)
from tests.conftest import nova_tarefa, utc


# --- Cenário 1: sucesso -------------------------------------------------------------------


def test_metricas_globais_do_conjunto_valido(tarefas_cenario_1: list[Tarefa]) -> None:
    """Cenário 1: 5 tarefas, 4 concluídas, média (60+120+30+40)/4 e 1 atraso em 4."""
    relatorio = calcular_metricas(tarefas_cenario_1)

    assert relatorio.total_tarefas == 5
    assert relatorio.total_concluidas == 4
    assert relatorio.tempo_medio_conclusao_min == 62.5
    assert relatorio.taxa_atraso_pct == 25.0


@pytest.mark.parametrize(
    ("prioridade", "esperado"),
    [
        pytest.param("low", IndicadorPrioridade("low", 2, 2, 35.0, 0.0), id="low"),
        pytest.param("medium", IndicadorPrioridade("medium", 1, 0, None, None), id="medium"),
        pytest.param("high", IndicadorPrioridade("high", 2, 2, 90.0, 50.0), id="high"),
        pytest.param("urgent", IndicadorPrioridade("urgent", 0, 0, None, None), id="urgent"),
    ],
)
def test_indicadores_por_prioridade(
    tarefas_cenario_1: list[Tarefa], prioridade: Prioridade, esperado: IndicadorPrioridade
) -> None:
    """Cenário 1 (RN-06): o indicador de cada prioridade, campo a campo.

    A ordem dos campos de ``IndicadorPrioridade`` é a do contrato (1.3.3): prioridade,
    total_tarefas, total_concluidas, tempo_medio_conclusao_min, taxa_atraso_pct.
    """
    relatorio = calcular_metricas(tarefas_cenario_1)

    assert relatorio.indicadores_por_prioridade[prioridade] == esperado


def test_indicadores_tem_sempre_as_quatro_prioridades(tarefas_cenario_1: list[Tarefa]) -> None:
    """1.3.3 e RN-06: as quatro chaves existem mesmo sem tarefa nenhuma (``urgent``)."""
    relatorio = calcular_metricas(tarefas_cenario_1)

    assert set(relatorio.indicadores_por_prioridade) == {"low", "medium", "high", "urgent"}


# --- Cenário 2: exceções ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("fixture", "id_tarefa", "regra"),
    [
        pytest.param("tarefa_t6", "T6", "RN-08", id="2a-conclusao-antes-da-criacao"),
        pytest.param("tarefa_t7", "T7", "RN-09", id="2b-concluida-sem-data-de-conclusao"),
    ],
)
def test_tarefa_invalida_levanta_excecao(
    request: pytest.FixtureRequest, fixture: str, id_tarefa: str, regra: str
) -> None:
    """Cenários 2.a e 2.b: a mensagem cita o id, o título e a regra violada (1.3.6)."""
    tarefa: Tarefa = request.getfixturevalue(fixture)

    with pytest.raises(TarefaInvalidaError, match=id_tarefa) as erro:
        calcular_metricas([tarefa])

    mensagem = str(erro.value)
    assert tarefa.titulo in mensagem
    assert regra in mensagem


@pytest.mark.parametrize(
    ("fixture", "quantidade"),
    [
        pytest.param("tarefas_sem_concluidas", 2, id="2c-so-pendentes"),
        pytest.param("lista_vazia", 0, id="2d-lista-vazia"),
    ],
)
def test_sem_tarefas_concluidas_levanta_excecao(
    request: pytest.FixtureRequest, fixture: str, quantidade: int
) -> None:
    """Cenários 2.c e 2.d: a mensagem diz quantas chegaram e que nenhuma está concluída."""
    tarefas: list[Tarefa] = request.getfixturevalue(fixture)

    with pytest.raises(SemTarefasConcluidasError, match=rf"\b{quantidade} tarefa") as erro:
        calcular_metricas(tarefas)

    assert "nenhuma" in str(erro.value).lower()


def test_sem_concluidas_nao_nasce_de_divisao_por_zero(tarefas_sem_concluidas: list[Tarefa]) -> None:
    """Cenário 2.c: a exceção vem antes de qualquer divisão, não de uma ZeroDivisionError.

    Uma exceção levantada dentro de um ``except ZeroDivisionError`` carregaria a divisão em
    ``__context__``; a ausência dos dois encadeamentos prova que não houve divisão.
    """
    with pytest.raises(SemTarefasConcluidasError) as erro:
        calcular_metricas(tarefas_sem_concluidas)

    assert erro.value.__context__ is None
    assert erro.value.__cause__ is None


# --- Cenários 3 e 4 -----------------------------------------------------------------------


def test_prazo_exato_e_sem_prazo_nao_sao_atraso(tarefas_cenario_3: list[Tarefa]) -> None:
    """Cenário 3 (RN-03 e RN-04): no instante do prazo e sem prazo não são atraso."""
    relatorio = calcular_metricas(tarefas_cenario_3)

    assert relatorio.taxa_atraso_pct == 0.0


def test_resultado_independe_da_ordem(tarefas_cenario_1: list[Tarefa]) -> None:
    """Cenário 4 (RN-07): a lista invertida produz o mesmo relatório, campo a campo."""
    invertida = list(reversed(tarefas_cenario_1))

    assert calcular_metricas(invertida) == calcular_metricas(tarefas_cenario_1)


# --- RN-02 e RN-03: funções de apoio ------------------------------------------------------


@pytest.mark.parametrize(
    ("iniciada_em", "concluida_em", "esperado"),
    [
        pytest.param(None, utc(2026, 3, 2, 10), 60.0, id="sem-inicio-mede-da-criacao"),
        pytest.param(
            utc(2026, 3, 2, 9, 30), utc(2026, 3, 2, 10), 30.0, id="com-inicio-mede-do-inicio"
        ),
        pytest.param(None, utc(2026, 3, 2, 9, 1, 30), 1.5, id="fracao-de-minuto"),
    ],
)
def test_tempo_de_conclusao_min(
    iniciada_em: datetime | None, concluida_em: datetime, esperado: float
) -> None:
    """RN-02: do início (ou da criação, sem início) até a conclusão, em minutos."""
    tarefa = nova_tarefa(
        "RN02",
        "completed",
        "low",
        utc(2026, 3, 2, 9),
        concluida_em=concluida_em,
        iniciada_em=iniciada_em,
    )

    assert tempo_de_conclusao_min(tarefa) == esperado


@pytest.mark.parametrize(
    ("prazo", "concluida_em", "esperado"),
    [
        pytest.param(utc(2026, 3, 2, 12), utc(2026, 3, 2, 10), False, id="antes-do-prazo"),
        pytest.param(utc(2026, 3, 2, 10), utc(2026, 3, 2, 11), True, id="depois-do-prazo"),
        pytest.param(utc(2026, 3, 2, 10), utc(2026, 3, 2, 10), False, id="no-instante-do-prazo"),
        pytest.param(None, utc(2026, 3, 2, 11), False, id="sem-prazo"),
    ],
)
def test_esta_atrasada(prazo: datetime | None, concluida_em: datetime, esperado: bool) -> None:
    """RN-03: atraso é concluir estritamente depois do prazo; sem prazo, nunca."""
    tarefa = nova_tarefa(
        "RN03", "completed", "low", utc(2026, 3, 2, 9), prazo=prazo, concluida_em=concluida_em
    )

    assert esta_atrasada(tarefa) is esperado
