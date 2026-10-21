# Arquitetura e fronteiras de confiança

| Componente | Responsabilidade | Não pode fazer |
|---|---|---|
| Lead.parse | Validar contrato de entrada | Converter strings em consentimento |
| qualify | Aplicar regras da campanha | Decidir crédito ou acesso à moradia |
| Engine.process | Persistir resultado, identidade e aprovação | Enviar mensagens |
| Engine.decide | Decidir payload fixo uma vez | Substituir texto após decisão |
| Advisor | Resumir contexto não confiável | Chamar ferramentas, conceder aprovação |
| GoogleSheets | Gravar e conferir um relatório | Escolher destinos a partir de texto do lead |
| MCP | Expor inspeção e processamento ao anfitrião | Aprovar rascunhos |
| HTTP local | Dar visibilidade e decisão ao operador | Autenticar múltiplos usuários |

## Persistência e concorrência

SQLite com WAL e BEGIN IMMEDIATE serializa alterações. Um ID de entrada corresponde a um hash de payload; reenvio idêntico recupera o resultado, reenvio alterado com o mesmo ID falha. E-mails são comparados em minúsculas. IDs de aprovação derivam do payload e a outbox usa chave única. Uma transação reúne decisão, liberação e evento.

## Evidência

O evento guarda hash do resultado, evitando replicar conteúdo do contato na trilha. O banco de execução e a fila ainda contêm nome e e-mail. A cadeia detecta modificações locais no encadeamento; não impede um administrador de reescrever todo o banco, truncar o final ou recalcular hashes. Não é armazenamento imutável ou assinatura digital.

## Autonomia

O modelo local é consultivo. A classificação e as ações têm regras determinísticas. Há validação de JSON para resumo e perguntas, não uma garantia de que um LLM nunca reproduzirá conteúdo malicioso. Como não recebe ferramentas, esse conteúdo não executa ações. A CLI de decisão é uma interface confiável do operador, não uma API autorizada para o agente.

## Goal-driven connected mode

`OllamaPlanner` selects one schema-constrained action. `WorkspaceTools` exposes only stage-valid capabilities, validates source freshness, limits writes to AgentReview rows and requires read-back before finish. The operator may use direct Google OAuth or a trusted connected-tool host via explicit file IPC. The core demo and connected review share campaign rules but have distinct persistence: SQLite for the offline workflow, Sheets plus JSONL for the connected review.

The optional advisor remains tool-free; the connected operator can write reviews, not send messages or approve actions. A conflict is a model assessment requiring human clarification, not permission to overwrite source data.
