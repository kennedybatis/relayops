# Working on RelayOps

Run `python3 -m unittest discover -s tests -v` after behavior changes. The core runs without network or third-party packages. Keep runtime databases, credentials, caches and real contact data out of Git.

Preserve these invariants: no external send implementation; model output grants no authority; fixed approval payload; final decisions; idempotent replay; changed payload under existing ID fails. Update business criteria, skills and tests together.

Do not claim live integrations were validated when only contract mocks passed. Document code-agent assistance and meaningful limitations. No fabricated ROI, production tenure or authorship history.
