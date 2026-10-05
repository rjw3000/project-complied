# ADR 001: Local deadline prototype

Date: 5 October 2026 | Status: Accepted for synthetic prototype only

Use Python 3.12 standard library, SQLite, and a read-only loopback HTTP dashboard for M1. This extends the existing test setup without hosting spend or new dependencies. It does not select the production stack.

Database management is a local CLI, not unauthenticated web writes. SQLite foreign keys, transactional migrations and unique obligation/period keys protect scope and duplicate tasks. Fixtures are synthetic and explicitly labeled. Business duties remain unresolved until reviewed with an authoritative source. No tax rates, real deadlines, live accounts, approvals or payments are enabled.

Production identity, private evidence storage, notifications and server deployment require subsequent design. Do not expose this development HTTP server publicly or load financial records into it.
