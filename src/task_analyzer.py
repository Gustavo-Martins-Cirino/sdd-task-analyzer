"""Cálculo das métricas de produtividade do TaskAnalyzer (contrato 1.3.4 e 1.3.5).

O relatório é função exclusiva da lista recebida (RN-07): nada aqui lê o relógio do sistema,
gera número aleatório, persiste dado ou depende da ordem dos elementos.
"""

import logging
import math
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import NoReturn

from .exceptions import SemTarefasConcluidasError, TarefaInvalidaError
from .models import (
    PRIORIDADES,
    STATUS_VALIDOS,
    IndicadorPrioridade,
    Prioridade,
    RelatorioProdutividade,
    Tarefa,
)

logger = logging.getLogger(__name__)

STATUS_CONCLUIDA = "completed"
SEGUNDOS_POR_MINUTO = 60
CASAS_DECIMAIS = 2


def calcular_metricas(tarefas: Sequence[Tarefa]) -> RelatorioProdutividade:
    """Valida a coleção inteira e agrega as métricas de produtividade.

    Args:
        tarefas: As tarefas a analisar, em qualquer ordem.

    Returns:
        O relatório global e por prioridade, com os valores arredondados a 2 casas (RN-05).

    Raises:
        TarefaInvalidaError: Se qualquer tarefa viola o contrato. A validação de TODAS vem
            antes de qualquer cálculo (RN-10).
        SemTarefasConcluidasError: Se nenhuma tarefa está concluída, inclusive com a lista
            vazia. Levantada antes de qualquer divisão.
    """
    logger.debug("Entrada: %d tarefa(s), ids %s", len(tarefas), [t.id for t in tarefas])
    for tarefa in tarefas:
        validar_tarefa(tarefa)
    concluidas = _concluidas(tarefas)
    if not concluidas:
        raise SemTarefasConcluidasError(
            f"Nenhuma tarefa concluída: {len(tarefas)} tarefa(s) recebida(s), nenhuma com "
            f"status '{STATUS_CONCLUIDA}'."
        )
    tempo_medio, taxa_atraso = _media_e_taxa(concluidas)
    return RelatorioProdutividade(
        total_tarefas=len(tarefas),
        total_concluidas=len(concluidas),
        tempo_medio_conclusao_min=tempo_medio,
        taxa_atraso_pct=taxa_atraso,
        indicadores_por_prioridade={p: _indicador(p, tarefas) for p in PRIORIDADES},
    )


def tempo_de_conclusao_min(tarefa: Tarefa) -> float:
    """Tempo de conclusão de uma tarefa concluída, em minutos (RN-02).

    Conta a partir de ``iniciada_em`` quando existe; senão, de ``criada_em``. O valor não é
    arredondado: o arredondamento é único, sobre o resultado final da agregação (RN-05).

    Args:
        tarefa: Uma tarefa concluída.

    Returns:
        Os minutos entre o início (ou a criação) e a conclusão.

    Raises:
        TarefaInvalidaError: Se a tarefa é inválida ou não está concluída.
    """
    concluida_em = _instante_de_conclusao(tarefa)
    inicio = tarefa.iniciada_em if tarefa.iniciada_em is not None else tarefa.criada_em
    return (concluida_em - inicio).total_seconds() / SEGUNDOS_POR_MINUTO


def esta_atrasada(tarefa: Tarefa) -> bool:
    """Se a tarefa concluída estourou o prazo (RN-03).

    Atraso é concluir estritamente depois do prazo: no instante exato não é atraso, e
    tarefa sem prazo nunca é.

    Args:
        tarefa: Uma tarefa concluída.

    Returns:
        ``True`` quando ``prazo`` existe e ``concluida_em > prazo``.

    Raises:
        TarefaInvalidaError: Se a tarefa é inválida ou não está concluída.
    """
    concluida_em = _instante_de_conclusao(tarefa)
    return tarefa.prazo is not None and concluida_em > tarefa.prazo


def validar_tarefa(tarefa: Tarefa) -> None:
    """Confere uma tarefa contra as restrições de 1.3.2, RN-08 e RN-09.

    Os fusos são conferidos antes da ordem temporal: comparar um instante com fuso e outro
    sem fuso levantaria ``TypeError`` longe do problema real (1.3.2).

    Args:
        tarefa: A tarefa a validar.

    Raises:
        TarefaInvalidaError: Na primeira restrição violada, com id, título e regra.
    """
    violacao = (
        _violacao_de_campos(tarefa)
        or _violacao_de_fuso(tarefa)
        or _violacao_de_status(tarefa)
        or _violacao_temporal(tarefa)
    )
    if violacao is not None:
        _rejeitar(tarefa, violacao)


def _concluidas(tarefas: Sequence[Tarefa]) -> list[Tarefa]:
    """Só as tarefas concluídas, o universo de cálculo das médias (RN-01).

    Args:
        tarefas: Tarefas já validadas.

    Returns:
        As tarefas com ``status == "completed"``.
    """
    return [tarefa for tarefa in tarefas if tarefa.status == STATUS_CONCLUIDA]


def _media_e_taxa(concluidas: Sequence[Tarefa]) -> tuple[float, float]:
    """Tempo médio e taxa de atraso de tarefas concluídas (RN-02 a RN-05).

    ``math.fsum`` soma sem depender da ordem das parcelas, o que mantém o resultado idêntico
    para qualquer ordenação da lista (RN-07). O arredondamento é aplicado uma vez, no fim.

    Args:
        concluidas: Tarefas válidas e concluídas. O chamador garante que não está vazia.

    Returns:
        O tempo médio em minutos e a taxa de atraso em pontos percentuais.
    """
    tempos = [tempo_de_conclusao_min(tarefa) for tarefa in concluidas]
    atrasadas = sum(1 for tarefa in concluidas if esta_atrasada(tarefa))
    tempo_medio = math.fsum(tempos) / len(tempos)
    taxa_atraso = (atrasadas / len(concluidas)) * 100
    return round(tempo_medio, CASAS_DECIMAIS), round(taxa_atraso, CASAS_DECIMAIS)


def _indicador(prioridade: Prioridade, tarefas: Sequence[Tarefa]) -> IndicadorPrioridade:
    """O indicador de uma prioridade: RN-01 a RN-05 sobre o subconjunto dela (RN-06).

    Args:
        prioridade: A prioridade do indicador.
        tarefas: Todas as tarefas, já validadas.

    Returns:
        O indicador, com as duas métricas em ``None`` quando não há concluída para medir.
    """
    da_prioridade = [tarefa for tarefa in tarefas if tarefa.prioridade == prioridade]
    concluidas = _concluidas(da_prioridade)
    if not concluidas:
        return IndicadorPrioridade(prioridade, len(da_prioridade), 0, None, None)
    tempo_medio, taxa_atraso = _media_e_taxa(concluidas)
    return IndicadorPrioridade(
        prioridade, len(da_prioridade), len(concluidas), tempo_medio, taxa_atraso
    )


def _instante_de_conclusao(tarefa: Tarefa) -> datetime:
    """A conclusão de uma tarefa válida e concluída.

    Valida a tarefa antes de usá-la: chamadas diretas a ``tempo_de_conclusao_min`` e a
    ``esta_atrasada`` não passam por ``calcular_metricas``, e uma tarefa fora do contrato
    terminaria em ``TypeError`` em vez de numa exceção do módulo.

    Args:
        tarefa: A tarefa cuja conclusão se quer.

    Returns:
        O instante ``concluida_em``.

    Raises:
        TarefaInvalidaError: Se a tarefa é inválida ou não está concluída (RN-01).
    """
    validar_tarefa(tarefa)
    if tarefa.concluida_em is None:
        _rejeitar(tarefa, "RN-01: só tarefa concluída tem tempo de conclusão e atraso")
    return tarefa.concluida_em


def _violacao_de_campos(tarefa: Tarefa) -> str | None:
    """Restrições de 1.3.2 sobre id, título, status e prioridade.

    Args:
        tarefa: A tarefa a conferir.

    Returns:
        A descrição da violação, com a regra, ou ``None`` se não há violação.
    """
    if not isinstance(tarefa.id, str) or not tarefa.id:
        return "1.3.2: id deve ser texto não vazio"
    if not isinstance(tarefa.titulo, str):
        return "1.3.2: título deve ser texto"
    if tarefa.status not in STATUS_VALIDOS:
        return f"1.3.2: status {tarefa.status!r} fora de {STATUS_VALIDOS}"
    if tarefa.prioridade not in PRIORIDADES:
        return f"1.3.2: prioridade {tarefa.prioridade!r} fora de {PRIORIDADES}"
    return None


def _violacao_de_fuso(tarefa: Tarefa) -> str | None:
    """Restrição de 1.3.2: todo instante é ``datetime`` timezone-aware em UTC.

    Args:
        tarefa: A tarefa a conferir.

    Returns:
        A descrição da violação, com o campo, ou ``None`` se não há violação.
    """
    opcionais = {
        "prazo": tarefa.prazo,
        "concluida_em": tarefa.concluida_em,
        "iniciada_em": tarefa.iniciada_em,
    }
    if not _em_utc(tarefa.criada_em):
        return "1.3.2: criada_em deve ser datetime timezone-aware em UTC"
    for campo, instante in opcionais.items():
        if instante is not None and not _em_utc(instante):
            return f"1.3.2: {campo} deve ser datetime timezone-aware em UTC"
    return None


def _em_utc(instante: object) -> bool:
    """Se o valor é um ``datetime`` com fuso e deslocamento zero em relação a UTC.

    Args:
        instante: O valor a conferir.

    Returns:
        ``True`` para ``datetime`` timezone-aware em UTC; ``False`` para ingênuo ou outro fuso.
    """
    return isinstance(instante, datetime) and instante.utcoffset() == timedelta(0)


def _violacao_de_status(tarefa: Tarefa) -> str | None:
    """RN-09: ``completed`` exige ``concluida_em``; os demais status exigem que falte.

    Args:
        tarefa: A tarefa a conferir.

    Returns:
        A descrição da violação, com a regra, ou ``None`` se não há violação.
    """
    concluida = tarefa.status == STATUS_CONCLUIDA
    if concluida and tarefa.concluida_em is None:
        return f"RN-09: status '{STATUS_CONCLUIDA}' exige concluida_em"
    if not concluida and tarefa.concluida_em is not None:
        return f"RN-09: status {tarefa.status!r} exige concluida_em vazio"
    return None


def _violacao_temporal(tarefa: Tarefa) -> str | None:
    """RN-08: criação <= início <= conclusão, para os instantes que existem.

    Args:
        tarefa: A tarefa a conferir, com os fusos já validados.

    Returns:
        A descrição da violação, com os instantes envolvidos, ou ``None``.
    """
    criada, iniciada, concluida = tarefa.criada_em, tarefa.iniciada_em, tarefa.concluida_em
    if iniciada is not None and iniciada < criada:
        return (
            f"RN-08: início ({iniciada.isoformat()}) anterior à criação "
            f"({criada.isoformat()})"
        )
    if concluida is not None and concluida < criada:
        return (
            f"RN-08: conclusão ({concluida.isoformat()}) anterior à criação "
            f"({criada.isoformat()})"
        )
    if iniciada is not None and concluida is not None and concluida < iniciada:
        return (
            f"RN-08: conclusão ({concluida.isoformat()}) anterior ao início "
            f"({iniciada.isoformat()})"
        )
    return None


def _rejeitar(tarefa: Tarefa, violacao: str) -> NoReturn:
    """Registra a rejeição em WARNING e levanta ``TarefaInvalidaError``.

    Args:
        tarefa: A tarefa rejeitada.
        violacao: A regra violada e o dado que a violou.

    Raises:
        TarefaInvalidaError: Sempre, com id, título e violação na mensagem (1.3.6).
    """
    mensagem = f"Tarefa {tarefa.id!r} ({tarefa.titulo!r}) inválida — {violacao}"
    logger.warning("Tarefa rejeitada na validação: %s", mensagem)
    raise TarefaInvalidaError(mensagem)
