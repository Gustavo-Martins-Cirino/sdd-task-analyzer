"""Fixtures com os dados dos cenários de aceite da seção 2.1 da especificação.

Os dados de teste ficam em um lugar só: um cenário que mude na especificação muda aqui, em
um ponto do código. Nenhum instante vem do relógio do sistema (RN-07): todos são fixos e em
UTC. Campos que a especificação não fixa para um cenário (título, e a prioridade das tarefas
dos cenários 2 e 3) recebem valores neutros, que não participam de nenhum cálculo testado. O
título padrão não contém o id de propósito: assim, um teste que procura o id na mensagem de
erro não passa só por causa do título.
"""

from datetime import datetime, timezone

import pytest

from src.models import Prioridade, Status, Tarefa


def utc(ano: int, mes: int, dia: int, hora: int, minuto: int = 0, segundo: int = 0) -> datetime:
    """Monta um instante fixo, timezone-aware, em UTC.

    Args:
        ano: Ano do instante.
        mes: Mês do instante.
        dia: Dia do instante.
        hora: Hora do instante.
        minuto: Minuto do instante.
        segundo: Segundo do instante.

    Returns:
        O instante em UTC.
    """
    return datetime(ano, mes, dia, hora, minuto, segundo, tzinfo=timezone.utc)


def nova_tarefa(
    id_tarefa: str,
    status: Status,
    prioridade: Prioridade,
    criada_em: datetime,
    prazo: datetime | None = None,
    concluida_em: datetime | None = None,
    iniciada_em: datetime | None = None,
    titulo: str = "Tarefa de exemplo",
) -> Tarefa:
    """Constrói uma `Tarefa` para os cenários.

    Args:
        id_tarefa: Identificador da tarefa.
        status: Status da tarefa.
        prioridade: Prioridade da tarefa.
        criada_em: Momento de criação.
        prazo: Prazo acordado, se houver.
        concluida_em: Momento da conclusão, se houver.
        iniciada_em: Momento do início, se houver.
        titulo: Rótulo da tarefa.

    Returns:
        A tarefa montada.
    """
    return Tarefa(
        id=id_tarefa,
        titulo=titulo,
        status=status,
        prioridade=prioridade,
        criada_em=criada_em,
        prazo=prazo,
        concluida_em=concluida_em,
        iniciada_em=iniciada_em,
    )


@pytest.fixture
def tarefa_t5() -> Tarefa:
    """T5 — a tarefa pendente que aparece no Cenário 1 e no Cenário 2.c."""
    return nova_tarefa("T5", "pending", "medium", utc(2026, 3, 6, 8), prazo=utc(2026, 3, 7, 8))


@pytest.fixture
def tarefas_cenario_1(tarefa_t5: Tarefa) -> list[Tarefa]:
    """Cenário 1 — as cinco tarefas T1 a T5, exatamente como na tabela da seção 2.1."""
    return [
        nova_tarefa(
            "T1", "completed", "high", utc(2026, 3, 2, 9),
            prazo=utc(2026, 3, 2, 12), concluida_em=utc(2026, 3, 2, 10),
        ),
        nova_tarefa(
            "T2", "completed", "high", utc(2026, 3, 3, 9),
            prazo=utc(2026, 3, 3, 10), concluida_em=utc(2026, 3, 3, 11),
        ),
        nova_tarefa(
            "T3", "completed", "low", utc(2026, 3, 4, 8),
            prazo=utc(2026, 3, 5, 8), concluida_em=utc(2026, 3, 4, 8, 30),
        ),
        nova_tarefa(
            "T4", "completed", "low", utc(2026, 3, 5, 8),
            prazo=utc(2026, 3, 5, 9), concluida_em=utc(2026, 3, 5, 8, 40),
        ),
        tarefa_t5,
    ]


@pytest.fixture
def tarefa_t6() -> Tarefa:
    """Cenário 2.a — concluída às 08:00 de uma tarefa criada às 09:00 (viola RN-08)."""
    return nova_tarefa(
        "T6", "completed", "medium", utc(2026, 3, 2, 9), concluida_em=utc(2026, 3, 2, 8)
    )


@pytest.fixture
def tarefa_t7() -> Tarefa:
    """Cenário 2.b — status concluído sem data de conclusão (viola RN-09)."""
    return nova_tarefa("T7", "completed", "medium", utc(2026, 3, 2, 9))


@pytest.fixture
def tarefas_sem_concluidas(tarefa_t5: Tarefa) -> list[Tarefa]:
    """Cenário 2.c — T5 e T8, ambas pendentes."""
    return [
        tarefa_t5,
        nova_tarefa("T8", "pending", "low", utc(2026, 3, 7, 8)),
    ]


@pytest.fixture
def tarefas_cenario_3() -> list[Tarefa]:
    """Cenário 3 — T9 concluída no instante exato do prazo e T10 concluída sem prazo."""
    return [
        nova_tarefa(
            "T9", "completed", "medium", utc(2026, 3, 2, 9),
            prazo=utc(2026, 3, 2, 10), concluida_em=utc(2026, 3, 2, 10),
        ),
        nova_tarefa(
            "T10", "completed", "medium", utc(2026, 3, 3, 9),
            prazo=None, concluida_em=utc(2026, 3, 3, 9, 30),
        ),
    ]


@pytest.fixture
def lista_vazia() -> list[Tarefa]:
    """Cenário 2.d — a lista vazia."""
    return []
