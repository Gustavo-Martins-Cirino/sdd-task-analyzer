"""Exceções do TaskAnalyzer (contrato 1.3.6 da especificação).

Toda falha do módulo herda de ``TaskAnalyzerError``: o consumidor captura qualquer uma delas
com uma cláusula só, sem recorrer a ``Exception`` genérica.
"""


class TaskAnalyzerError(Exception):
    """Base de toda exceção levantada pelo TaskAnalyzer."""


class TarefaInvalidaError(TaskAnalyzerError):
    """Tarefa que viola 1.3.2, RN-08 ou RN-09.

    A mensagem traz o ``id`` e o ``titulo`` da tarefa e a regra violada.
    """


class SemTarefasConcluidasError(TaskAnalyzerError):
    """Coleção sem nenhuma tarefa concluída, inclusive a lista vazia.

    É o tratamento explícito da divisão por zero: sem concluídas, o denominador das duas
    métricas globais é zero. A mensagem diz quantas tarefas chegaram e que nenhuma está
    concluída.
    """
