# Security model and limits

This is a single-operator local demonstrator with synthetic inputs. Bind only to 127.0.0.1. Do not expose the HTTP server, database or MCP process to untrusted users.

Implemented: strict input types, SQL parameters, local-origin/Host checks, JSON-only POST, request-size limit, no arbitrary file routes, browser rendering via textContent, fixed Sheets destination, RAW cells, transaction-bound decisions and no agent approval tool.

The human approval boundary assumes the local operator and host are trusted. There is no RBAC, real identity proof, CSRF token-based login, TLS deployment, secrets vault, tenant isolation, consent-revocation workflow or audit signing. Hash chaining detects selected modifications, not privileged rewrites or suffix truncation.

Untrusted text cannot alter deterministic rules. The optional LLM may still echo injection content; it has no execution authority. Test cases demonstrate bounded behavior, not general prompt-injection immunity.

Never submit real contact lists or secrets to a public issue. Report suspected bugs privately to the repository owner through an available private contact channel; do not assume a security response SLA.
