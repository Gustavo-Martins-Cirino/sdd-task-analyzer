# sdd-task-analyzer

Implementação do módulo **TaskAnalyzer** guiada por especificação (SDD — *Specification-Driven
Development*): o código foi gerado por assistente de IA a partir de um contrato técnico
executável, validado por um *Test Harness* em pytest e versionado com branches e Pull Requests.

| | |
|---|---|
| Autor | Gustavo Martins Cirino |
| Disciplina | Bootcamp III — Desafio Entrega Intermediária (Fase 2) |
| Especificação | [`specs/task_analyzer_spec.md`](specs/task_analyzer_spec.md) (Fase 1) |
| Regras para a IA | [`CONTEXT_RULES.md`](CONTEXT_RULES.md) |

## Status

| Verificação | Resultado |
|---|---|
| Testes (`pytest -v`) | **43 passed** — 100%, nenhum `skip` ou `xfail` |
| Cobertura de `src/` (`pytest --cov=src`) | **100%** (o critério da especificação é ≥ 90%) |
| Python | 3.11+ (executado em 3.12.4) |
| Dependências de produção | nenhuma — só a biblioteca padrão |

A automação (CI com GitHub Actions) é escopo da Fase 3; até lá, o status acima é o da execução
local registrada no Pull Request #3.

## O que o módulo faz

Recebe tarefas já executadas e devolve um `RelatorioProdutividade` com o tempo médio de
conclusão (minutos) e a taxa de atraso (%), no total e por prioridade. Entrada inconsistente é
sinalizada por exceção específica, antes de qualquer cálculo.

```python
from datetime import datetime, timezone

from src.models import Tarefa
from src.task_analyzer import calcular_metricas


def utc(dia: int, hora: int) -> datetime:
    return datetime(2026, 3, dia, hora, tzinfo=timezone.utc)


tarefas = [
    Tarefa("T1", "Revisar proposta", "completed", "high", utc(2, 9),
           prazo=utc(2, 12), concluida_em=utc(2, 10)),
    Tarefa("T2", "Enviar relatório", "completed", "high", utc(3, 9),
           prazo=utc(3, 10), concluida_em=utc(3, 11)),
]
relatorio = calcular_metricas(tarefas)
relatorio.tempo_medio_conclusao_min   # 90.0  — (60 + 120) / 2
relatorio.taxa_atraso_pct             # 50.0  — T2 concluiu depois do prazo
```

## Estrutura

```
sdd-task-analyzer/
├── README.md                  # Este arquivo
├── CONTEXT_RULES.md           # Regras de governança da IA (seção 3 da especificação)
├── requirements.txt           # pytest e pytest-cov, só para os testes
├── .gitignore
├── specs/
│   └── task_analyzer_spec.md  # Contrato SDD da Fase 1
├── src/
│   ├── __init__.py
│   ├── models.py              # Tarefa, IndicadorPrioridade, RelatorioProdutividade
│   ├── exceptions.py          # TaskAnalyzerError e as duas exceções filhas
│   └── task_analyzer.py       # calcular_metricas e funções de apoio
└── tests/
    ├── __init__.py
    ├── conftest.py            # Fixtures com os dados dos cenários de aceite
    └── test_harness.py        # Test Harness (pytest)
```

É a árvore planejada na seção 4.1 da especificação, sem acréscimos (CONTEXT_RULES 3.2.3).

## Como executar os testes

Requer Python 3.11 ou superior.

```bash
python -m venv .venv
# Windows:      .venv\Scripts\activate
# Linux/macOS:  source .venv/bin/activate
pip install -r requirements.txt
pytest -v --cov=src --cov-report=term-missing
```

> Se o `pip` falhar com `CERTIFICATE_VERIFY_FAILED` (comum quando um antivírus ou proxy
> inspeciona HTTPS), use o repositório de certificados do sistema em vez de desligar a
> verificação: `pip install --use-feature=truststore -r requirements.txt`.

## Fluxo de trabalho no GitHub

O contrato vem primeiro, o teste depois, o código por último — cada etapa numa branch própria,
integrada à `main` por Pull Request:

| PR | Branch | Conteúdo |
|---|---|---|
| [#1](https://github.com/Gustavo-Martins-Cirino/sdd-task-analyzer/pull/1) | `feature/sdd-specification` | Especificação SDD e CONTEXT_RULES transpostas da Fase 1 |
| [#2](https://github.com/Gustavo-Martins-Cirino/sdd-task-analyzer/pull/2) | `feature/test-harness` | Test Harness pytest dos cenários de aceite (fase vermelha: falha sem `src/`) |
| [#3](https://github.com/Gustavo-Martins-Cirino/sdd-task-analyzer/pull/3) | `feature/task-analyzer-impl` | Código gerado por IA e o registro dos cinco pontos de homologação |

Commits pequenos, no padrão `tipo: descrição`. Os commits de código gerado por IA dizem isso no
corpo da mensagem (ponto 5 da seção 4.2).

## Rastreabilidade: enunciado da Fase 2 × contrato da especificação

O enunciado da Fase 2 usa nomes genéricos. A especificação da Fase 1, que é o contrato deste
repositório, definiu os seus, e as CONTEXT_RULES proíbem alterar assinatura ou cenário sem
autorização registrada (3.2.2 e 3.2.5). Por isso o código segue a especificação, e esta tabela
mostra onde está cada item do enunciado:

| Enunciado da Fase 2 | Neste repositório (contrato da Fase 1) |
|---|---|
| função `analyze_tasks` | `calcular_metricas` (1.3.4) |
| exceção `TaskValidationError` | `TarefaInvalidaError`, filha de `TaskAnalyzerError` (1.3.6) |
| `total_tarefas`, `total_concluidas` | `total_tarefas`, `total_concluidas` |
| `total_pendentes` | não é campo do contrato; as não concluídas são `total_tarefas - total_concluidas` |
| `tempo_medio_conclusao_horas` (geral e por prioridade) | `tempo_medio_conclusao_min`, em **minutos** (1.3.3), no relatório e em cada `IndicadorPrioridade` |
| `taxa_atraso_percentual` | `taxa_atraso_pct` |
| Cenário 2: `data_conclusao < data_criacao` | Cenário 2.a: `concluida_em < criada_em` → `TarefaInvalidaError` (RN-08) |
| Casos de borda: lista vazia ou só pendentes | Cenários 2.c e 2.d: `SemTarefasConcluidasError`, exceção **específica e tratada**, levantada antes de qualquer divisão; nas prioridades sem concluída, as médias são `None` |

**Por que exceção, e não 0.0, na lista vazia:** a especificação (1.3.6) escolhe exceção porque
`RelatorioProdutividade` declara as métricas globais como `float`, e `0.0` afirmaria "nenhuma
tarefa atrasou" quando o correto é "não há o que medir". Nenhuma exceção não tratada escapa do
módulo: toda falha é uma `TaskAnalyzerError`, e o harness prova isso
(`test_falhas_do_modulo_herdam_de_task_analyzer_error` e
`test_sem_concluidas_nao_nasce_de_divisao_por_zero`).

## Desenvolvimento assistido por IA

**Ferramenta:** Claude Code (modelo Claude Opus 5.5). **Contexto fornecido** (CONTEXT_RULES
3.3.1): o `CONTEXT_RULES.md` inteiro e as seções 1.3 e 2 de `specs/task_analyzer_spec.md`.

**Prompt de geração do código:**

> Você é o agente de geração de código do projeto sdd-task-analyzer. O contexto obrigatório é o
> CONTEXT_RULES.md e as seções 1.3 e 2 da especificação, anexados. Antes de escrever código:
> (1) reformule com suas palavras o contrato de 1.3.4 a 1.3.6; (2) liste toda ambiguidade ou
> conflito que encontrar, sem resolvê-los por conta própria (CONTEXT_RULES 3.2.8). Depois, gere
> `src/__init__.py`, `src/models.py`, `src/exceptions.py` e `src/task_analyzer.py` com as
> assinaturas exatas de 1.3.4: Python 3.11+, type hints em tudo, docstrings no padrão Google,
> só biblioteca padrão, `logging` em vez de `print`, funções de até 20 linhas, e fazendo passar
> `tests/test_harness.py` sem alterar nenhum teste.

**Como as CONTEXT_RULES evitaram "alucinações"** — casos que aconteceram neste repositório:

1. **Conflito de nomes levado ao humano, não resolvido pela IA.** O enunciado da Fase 2 cita
   `analyze_tasks`, `TaskValidationError`, horas e "0.0 na lista vazia"; a especificação define
   outros nomes, minutos e exceção. A regra 3.2.8 ("diante de ambiguidade, o agente pergunta")
   fez o agente parar e perguntar em vez de renomear tudo por conta própria. A decisão humana
   foi manter o contrato da Fase 1, documentada na tabela acima.
2. **Nada inventado onde o contrato é omisso.** Título vazio não tem restrição na especificação:
   o código o aceita e um teste registra isso como comportamento não especificado, em vez de o
   agente criar uma regra "não vazio" que ninguém pediu (3.2.7 e 3.2.8).
3. **Bibliotecas convenientes recusadas.** Datas e médias ficariam mais curtas com `pandas` ou
   `pendulum`; as regras 3.1.2 e 3.2.1 limitaram o código à biblioteca padrão.
4. **Determinismo garantido, não presumido.** A RN-07 (resultado independente da ordem) levou ao
   uso de `math.fsum`, cuja soma não depende da ordem das parcelas — uma soma comum pode variar
   no último dígito conforme a ordem.
5. **Divisão por zero tratada antes, não capturada depois.** A regra 3.2.9 (não silenciar
   exceção) e o Cenário 2.c levaram a uma checagem explícita antes da divisão; o harness confere
   que a exceção não carrega uma `ZeroDivisionError` encadeada.
6. **Revisão que o teste não pega.** Com todos os testes passando, a conferência contra as
   CONTEXT_RULES ainda achou linhas acima de 100 colunas (3.1.4) e um parâmetro `id` que
   escondia a função nativa do Python — corrigidos antes do commit.

O registro completo dos cinco pontos de homologação (seção 4.2) está no
[Pull Request #3](https://github.com/Gustavo-Martins-Cirino/sdd-task-analyzer/pull/3).
