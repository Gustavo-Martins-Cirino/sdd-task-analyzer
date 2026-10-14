# CONTEXT_RULES — Governança de contexto para agentes de IA

> Seção 3 da especificação SDD TaskAnalyzer (Fase 1), transposta sem alteração. Este arquivo é
> fornecido ao assistente de IA em **toda** solicitação de geração de código, junto com a seção
> pertinente de [`specs/task_analyzer_spec.md`](specs/task_analyzer_spec.md). As referências a
> seções (1.3.4, 2, 4.1, 4.2…) apontam para esse arquivo.

O conteúdo desta seção é o que será gravado no arquivo `CONTEXT_RULES.md`, na raiz do
repositório, e fornecido ao assistente de IA em toda solicitação de geração de código.

## 3.1 Diretrizes arquiteturais (obrigatórias)

1. **Python 3.11 ou superior.** É a versão mínima; recursos mais novos não podem ser
   usados sem que a versão mínima seja atualizada nesta especificação.
2. **Apenas biblioteca padrão** no código de produção. `pytest` e `pytest-cov` são
   permitidos exclusivamente em `tests/`.
3. **`type hints` em todas as funções, métodos e atributos**, incluindo parâmetros e
   retorno. `Any` só é aceito com justificativa escrita no próprio código.
4. **PEP 8** e código limpo. Linhas de até 100 colunas.
5. **Responsabilidade única (SRP).** Uma função faz uma coisa. A separação em
   `models.py`, `exceptions.py` e `task_analyzer.py` é parte do contrato, não sugestão.
6. **Docstrings no padrão Google** para módulo, classe, função e parâmetros.
7. **Funções pequenas e coesas.** Acima de 20 linhas de corpo, justificar ou dividir.
8. **Tratamento de exceções específico.** Nada de `except Exception` genérico no código de
   produção. Toda exceção levantada pelo módulo herda de `TaskAnalyzerError` e traz
   mensagem que identifica o dado que a causou.
9. **Logs estruturados com o módulo padrão `logging`.** Nunca `print`. O módulo registra
   em `DEBUG` a entrada recebida e em `WARNING` cada tarefa rejeitada na validação.
10. **Nomes descritivos** para variáveis e funções, em português, coerentes com os nomes
    do contrato da seção 1.3. O contrato é a fonte da verdade dos nomes.
11. **Imutabilidade das estruturas de dados.** `Tarefa`, `IndicadorPrioridade` e
    `RelatorioProdutividade` são `@dataclass(frozen=True)`.
12. **Determinismo (RN-07).** Nenhuma função do módulo lê o relógio do sistema ou gera
    valores aleatórios.

## 3.2 Proibições explícitas (regras restritivas)

1. **Não utilizar bibliotecas externas não autorizadas** — inclusive `pandas`, `numpy`,
   `arrow` e `pendulum`, por mais convenientes que sejam para datas e agregações.
2. **Não alterar, remover ou adaptar os cenários de teste** da seção 2. O teste é o
   contrato; ajustar o teste para o código passar inverte a relação e invalida a entrega.
3. **Não modificar a estrutura de pastas** definida na seção 4.1.
4. **Não persistir dados** em arquivo, banco de dados, cache ou variável global.
5. **Não alterar a assinatura** (nome, parâmetros, tipos, retorno) das funções públicas de
   1.3.4 sem autorização registrada nesta especificação.
6. **Não gerar código de produção sem o teste correspondente** na mesma entrega.
7. **Não inserir código duplicado nem código não solicitado** — sem funções "para o
   futuro", sem parâmetros não usados, sem camadas de abstração que nenhum requisito pede.
8. **Não assumir comportamento não especificado.** Diante de ambiguidade, o agente
   pergunta; não escolhe por conta própria e não inventa regra de negócio.
9. **Não capturar exceção para silenciá-la.** `except: pass` e equivalentes são proibidos.
10. **Não usar `print` para diagnóstico** nem deixar código comentado no repositório.
11. **Não commitar código gerado sem homologação humana**, conforme o plano da seção 4.2.

## 3.3 Regras de interação com o agente de IA

1. Fornecer sempre o contexto completo: `CONTEXT_RULES.md` mais a seção da especificação
   pertinente à solicitação.
2. Validar a compreensão do agente antes de aceitar código: pedir que ele reformule o que
   entendeu do contrato.
3. Solicitar explicação sempre que houver dúvida sobre a solução gerada.
4. Revisar criticamente **todo** código gerado. Código que passa nos testes ainda pode
   violar as regras desta seção.
5. Rejeitar e regerar respostas que violem qualquer proibição de 3.2, registrando o motivo.
