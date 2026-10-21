# Evidências de validação

Validação local em 21/10/2026. Dados exclusivamente sintéticos.

| Componente | Resultado | Alcance |
|---|---|---|
| Núcleo e adaptadores | 17 testes passaram | Regras, limites, identidade, persistência, aprovação e contratos |
| HTTP local | 5 testes passaram | Fluxo completo, Host, Origin, JSON inválido e rotas |
| MCP | Sessão stdio real passou | initialize, list_tools, chamada de qualificação e inspeção |
| Skills | Duas skills validadas | Frontmatter, nomes e referências |
| JavaScript | `node --check web/app.js` passou | Sintaxe |
| Painel | Verificado no navegador | Seis entradas, quatro aprovações iniciais; aprovação humana resultou em três pendentes, sete eventos e uma outbox |
| Sheets em conta real | Não executado | Contrato HTTP com transporte simulado e verificação de read-back |
| Ollama com modelo real | Não executado | Contrato e validação de saída testados com resposta simulada |

## Reproduzir

```bash
python3 -m unittest discover -s tests -v
python3 -m relayops demo
python3 -m relayops serve
```

Para MCP, em Python 3.12, instalar o conjunto validado:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-mcp.lock
.venv/bin/python scripts/check_mcp.py
```

O lock registra o ambiente MCP exercitado; o núcleo permanece sem dependências. O SDK produziu um aviso de forward reference do pydantic-settings durante a inicialização; as chamadas MCP foram concluídas. O arquivo de lock não é uma certificação de segurança de dependências.

Logs reproduzíveis: [execução dos testes](test-results.txt) e [sessão MCP](mcp-results.txt). Nenhuma economia de tempo de cliente, taxa de conversão ou ROI foi medido. A prova de limite contra a entrada adversarial vale para o caminho determinístico testado, não para um benchmark geral de LLM.
