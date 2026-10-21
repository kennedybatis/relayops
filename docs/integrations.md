# Integrações e contratos

## Sheets

Usa a API v4 `spreadsheets.values.update`, `valueInputOption=RAW` e leitura de conferência. Endpoint fixo em sheets.googleapis.com e aba fixa RelayOps. Uma linha exportada contém ID, status, motivo e hash, sem nome ou e-mail. Identificadores ainda podem ser dados pessoais em uma operação real.

Configure um OAuth access token de uma conta autorizada, com escopo adequado ao arquivo. Este projeto não implementa consent screen nem refresh token. Não coloque credenciais no perfil, nas skills ou no repositório. Um erro HTTP não dispara retry automático.

## MCP

`inspect_operation`: leitura de execução e aprovações locais.
`qualify_commercial_lead`: valida e persiste lead; efeito de escrita local, nenhum envio.

O cliente anfitrião precisa controlar quem chama ferramentas de escrita. Acesso ao filesystem/CLI permite operar como o usuário local; a ausência da ferramenta approve não é sandbox de sistema operacional.

## Ollama

`POST http://127.0.0.1:11434/api/chat` com `stream=false`, formato JSON e limite de saída. Sem tools ou endpoints definidos por conteúdo de lead. Falhas de rede ou JSON interrompem a operação consultiva. Não há execução de comandos gerados pelo modelo.

## Referências oficiais

- [Sheets values.update](https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values/update)
- [Ollama chat](https://docs.ollama.com/api/chat)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Agent Skills specification](https://agentskills.io/specification)
