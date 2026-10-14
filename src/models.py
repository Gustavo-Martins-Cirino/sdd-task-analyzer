"""Estruturas de dados do TaskAnalyzer (contrato 1.3.1 a 1.3.3 da especificação).

As três estruturas são imutáveis, ``@dataclass(frozen=True)`` (CONTEXT_RULES 3.1.11). Os nomes
e os valores de ``Status`` e ``Prioridade`` são os da tabela ``tasks`` do NeuroTask (1.2).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, get_args

Prioridade = Literal["low", "medium", "high", "urgent"]
Status = Literal["pending", "in_progress", "completed", "cancelled"]

# Lidos dos próprios literais, e não reescritos: o contrato é a fonte única dos valores.
PRIORIDADES: tuple[Prioridade, ...] = get_args(Prioridade)
STATUS_VALIDOS: tuple[Status, ...] = get_args(Status)


@dataclass(frozen=True)
class Tarefa:
    """Uma tarefa recebida para análise (contrato 1.3.2).

    Attributes:
        id: Identificador único da tarefa. Não vazio.
        titulo: Rótulo legível. Não participa de cálculo; identifica a tarefa nas mensagens.
        status: Um dos quatro valores de ``Status``.
        prioridade: Um dos quatro valores de ``Prioridade``.
        criada_em: Momento de criação, timezone-aware em UTC.
        prazo: Prazo acordado. ``None`` é tarefa sem prazo, que nunca conta como atrasada.
        concluida_em: Momento da conclusão. Obrigatório quando ``status == "completed"`` e
            ``None`` nos demais status.
        iniciada_em: Início da execução. Ausente, o tempo de conclusão conta de ``criada_em``.
    """

    id: str
    titulo: str
    status: Status
    prioridade: Prioridade
    criada_em: datetime
    prazo: datetime | None = None
    concluida_em: datetime | None = None
    iniciada_em: datetime | None = None


@dataclass(frozen=True)
class IndicadorPrioridade:
    """Métricas de uma prioridade (contrato 1.3.3).

    Attributes:
        prioridade: A prioridade a que o indicador se refere.
        total_tarefas: Tarefas dessa prioridade, de qualquer status.
        total_concluidas: Tarefas dessa prioridade com ``status == "completed"``.
        tempo_medio_conclusao_min: Média em minutos; ``None`` sem nenhuma concluída.
        taxa_atraso_pct: Percentual de concluídas em atraso; ``None`` sem nenhuma concluída.
    """

    prioridade: Prioridade
    total_tarefas: int
    total_concluidas: int
    tempo_medio_conclusao_min: float | None
    taxa_atraso_pct: float | None


@dataclass(frozen=True)
class RelatorioProdutividade:
    """Relatório global e por prioridade (contrato 1.3.3).

    Attributes:
        total_tarefas: Quantidade de tarefas recebidas, de qualquer status.
        total_concluidas: Quantidade com ``status == "completed"``.
        tempo_medio_conclusao_min: Média do tempo de conclusão, em minutos, a 2 casas.
        taxa_atraso_pct: Percentual de concluídas em atraso, de 0.0 a 100.0, a 2 casas.
        indicadores_por_prioridade: Sempre com as quatro chaves de ``Prioridade``.
    """

    total_tarefas: int
    total_concluidas: int
    tempo_medio_conclusao_min: float
    taxa_atraso_pct: float
    indicadores_por_prioridade: dict[Prioridade, IndicadorPrioridade]
