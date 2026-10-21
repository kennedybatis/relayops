# RelayOps — evidence before autonomy

A local implementation reference for a commercial agent workflow: validate synthetic leads, apply explicit campaign rules, deduplicate contacts, stage fixed-payload human approvals and retain verifiable execution evidence.

```bash
python3 -m unittest discover -s tests -v
python3 -m relayops demo
python3 -m relayops serve
```

Visit http://127.0.0.1:8765. Core requires Python 3.9+ and no third-party packages. MCP requires Python 3.10+ plus the optional SDK.

The default demonstration is deterministic. The optional Ollama advisor generates summaries without tool access; Google Sheets export uses explicit operator authorization and read-back. Approvals only release a local outbox, never real email. SQLite persists identity, decisions and hash-linked events.

Built as a portfolio demonstrator by Kennedy Batis with coding-agent assistance. This is not a claimed customer deployment or a UPX product. Live Google and model execution require a separately configured environment. Authentication, tenant isolation, immutable logs and production credential lifecycle are outside the current scope.

See [architecture](architecture.md), [operational handoff](handoff.md), [decisions](decisions.md), [evidence](evidence.md) and [security](../SECURITY.md).

## Goal-driven review

A second mode uses a real local Ollama model to choose bounded review tools against a Google Sheets sandbox. It interprets messages, flags conflicts, writes assessments and verifies each row. Direct OAuth and an explicitly documented connected-host bridge are supported. See [goal-driven agent](goal-agent.md) for setup, contracts and limitations.
