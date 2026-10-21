# Handoff e operação

## Kickoff com o responsável comercial

- Qual problema será reduzido? Tempo de triagem e inconsistência no encaminhamento.
- Quais campos existem e qual sistema é a fonte de verdade?
- O que significa autorização de contato nessa operação?
- Quais critérios são regras e quais dependem de julgamento humano?
- Quem revisa rascunhos e em quanto tempo?
- Qual indicador provará utilidade: tempo ativo por lead, taxa de correções ou cobertura de atendimento?

Neste demonstrador, o CRM é SQLite e a entrada é JSON sintético. Não representa uma implantação em sistema de cliente.

## Treinamento de 15 minutos

1. Rodar demo e identificar os estados.
2. Abrir uma aprovação, conferir destinatário e texto, aprovar ou rejeitar.
3. Reexecutar demo e verificar ausência de duplicações.
4. Inspecionar `report` e explicar o input_hash.
5. Identificar diferença entre outbox local e envio real.

## Falhas e recuperação

- ID repetido com novo conteúdo: não altere silenciosamente. Investigue e gere ID versionado se for uma atualização legítima.
- Falha de exportação: estado local permanece; confira destino antes de repetir.
- Token expirado: renovar no provedor, fora do chat; executar de novo somente após conferência.
- Auditoria inválida: interrompa operação, preserve cópia do banco e investigue; não tente "consertar" hashes.
- Para ensaio independente: usar outro caminho `--db`, preservando o histórico anterior.

## Adoção nos primeiros 30 dias

Semanas 1–2: revisão humana integral dos resultados; medir correções, exceções e duração real das tarefas. Semanas 3–4: ajustar critérios com o dono do processo e comparar amostras equivalentes. Não alegar economia com base na latência de uma função Python.

Antes de produção: validar LGPD/retenção com a organização, RBAC, identidade dos aprovadores, consentimento revogável, recuperação de desastre, testes de ponta a ponta e rollback por conector.
