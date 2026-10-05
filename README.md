# Project Complied

Owner-approved compliance workflow automation. Initial pilot: requirement discovery, calendar, per-store PostalMate imports, Microsoft 365 reminders, Dropbox evidence, and Virginia monthly sales-tax preparation.

## Specifications

- [Product requirements](docs/specs/01-PRD.md)
- [Technical requirements](docs/specs/02-Technical-Requirements.md)
- [Architecture](docs/specs/03-System-Architecture.md)
- [Delivery roadmap](docs/ROADMAP.md)

Current topology: [architecture](docs/specs/03-System-Architecture.md). The existing PNG is a historical draft.

## Current implementation

Repository foundation, a dependency-free Python approval reference, and a local synthetic deadline dashboard. This is not a running tax application. Python is a provisional reference implementation, not a final technology selection. No live integrations, tax rules, filing, or payments are enabled.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_repository.py
```

CI checks the repository and approval tests. CodeQL analyzes Python. Gitleaks scans commit history. Dependabot opens weekly action-update PRs. Bot updates require human review; no automatic approvals or merges.

## Security

See [SECURITY.md](SECURITY.md), [threat model](docs/security/THREAT-MODEL.md), and [GitHub settings](docs/security/GITHUB-SETTINGS.md). This public repository holds synthetic fixtures and source code only. Never commit business records, credentials, tax returns, or payment details.

Specifications aligned 5 October 2026. Owner confirms Ivy/Charlottesville City and Pantops/Albemarle County. PostalMate drives sales-tax preparation; QBO supports accounting reconciliation. Tax rules, registration reporting, deadlines and portal capabilities require verification.

Start with [Project.md](Project.md) and [Handoff.md](Handoff.md). Next build: M1 deadline prototype in the roadmap. Stack/hosting selection remains open; local deadline prototype now added; authenticated production app remains pending.

## Run the synthetic deadline prototype

Requires Python 3.12 with timezone data. From the repository root:

```sh
PYTHONPATH=src python3 -m complied.deadlines seed
PYTHONPATH=src python3 -m complied.web
```

Open http://127.0.0.1:8080. The dashboard is read-only, loopback-only, and uses synthetic data. Demo tasks have illustrative dates; real candidate duties remain unresolved. Do not load real financial data or expose this server publicly.

```sh
PYTHONPATH=src python3 -m complied.deadlines list --today 2026-10-05
python3 scripts/check_repository.py
python3 -m unittest discover -s tests -v
```

Local database is var/demo.sqlite3 (excluded from Git). Seed is repeatable. [ADR 001](docs/decisions/001-local-prototype.md) records the prototype-only stack decision. No authenticated editing, notification delivery, PostalMate import or filing/payment execution exists yet.
