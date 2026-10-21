# Decisões e alternativas

## 01 — Processo pequeno e completo

Escolha: qualificação comercial, por ser um processo que pode ser explicado por regras, exceções e evidências. Evitamos montar seis agentes superficiais para áreas diferentes. Expandir exige kickoff e validação por domínio.

## 02 — Modelo consultivo e execução determinística

Escolha: o LLM ajuda a interpretar e comunicar; regras verificáveis decidem status e efeitos. A demonstração offline continua funcional sem um modelo. Limite: não demonstra planejamento autônomo complexo ou qualidade semântica de um modelo real.

## 03 — Dependências mínimas

Python padrão no núcleo reduz esforço de avaliação. MCP é opcional e exige Python 3.10+. O projeto é executado a partir do checkout, pois perfis, skills e arquivos web são recursos da raiz; não se apresenta como pacote portátil instalado isoladamente por pip.

## 04 — Nenhum disparo externo

Aprovação gera somente outbox local. Isso permite testar o fluxo sem expor destinatários ou causar envios. Um conector real de mensagem precisaria de idempotência no provedor, identidade do aprovador, expiração de aprovação e política de revogação de consentimento.

## 05 — Evidência sem promessas

Testes unitários e de contrato não são execução real com Google/Ollama. A trilha de hashes auxilia detecção de alterações, mas não é auditoria inviolável. O painel identifica o modo determinístico; custo zero de API nesse modo não equivale a custo operacional zero.
