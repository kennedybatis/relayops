# RelayOps — evidence before autonomy

I developed RelayOps as a local reference for a commercial agent workflow: validate synthetic leads, apply explicit campaign rules, deduplicate contacts, stage fixed-payload human approvals and retain verifiable execution evidence.

```bash
python3 -m unittest discover -s tests -v
python3 -m relayops demo
python3 -m relayops serve
```

Visit http://127.0.0.1:8765. Core requires Python 3.9+ and no third-party packages. MCP requires Python 3.10+ plus the optional SDK.

The default demonstration is deterministic. The optional Ollama advisor generates summaries without tool access; Google Sheets export uses explicit operator authorization and read-back. Approvals only release a local outbox, never real email. SQLite persists identity, decisions and hash-linked events.

I used Codex to assist with implementation, tests and documentation. I chose a fictional real estate campaign to connect the demonstration to my commercial background and make the workflow publicly reproducible without exposing customer data. The repository includes source code, tests, profiles, skills and execution evidence with synthetic data under the MIT license. It does not provide access to my accounts, credentials or local environment.

The current version runs locally for one user. My next steps toward production would be role-based authentication, tenant isolation, secrets and credential lifecycle management, retention policies, telemetry and validation with real users. Live integrations require separately configured access; current boundaries are documented in the security guide.

See [architecture](architecture.md), [operational handoff](handoff.md), [decisions](decisions.md), [evidence](evidence.md) and [security](../SECURITY.md).

## Goal-driven review

A second mode uses a real local Ollama model to choose bounded review tools against a Google Sheets sandbox. It interprets messages, flags conflicts, writes assessments and verifies each row. Direct OAuth and an explicitly documented connected-host bridge are supported. See [goal-driven agent](goal-agent.md) for setup, contracts and limitations.

## Where I plan to take RelayOps

I built RelayOps as an evolving foundation for business-process agents, starting with commercial workflows where I can connect my business experience to qualification rules, approval points and verifiable actions. Local-model execution with Google Sheets has been validated, and the project also includes a bounded MCP stdio server.

My next steps are to map each client's process with the area owner, define autonomy boundaries and add CRM and other system integrations through MCP or APIs. I plan to validate each connector with a real task, develop reusable skills, document the handoff and train the team. Execution quality, adoption and cost per task would guide further improvements. These integrations and customer operations are planned work, separate from the flow already validated here.
