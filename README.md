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

Open http://127.0.0.1:8080. The dashboard is loopback-only and uses synthetic data. Sign-in protects the dashboard and editing/review forms. Demo tasks have illustrative dates; real candidate duties remain unresolved. Do not load real financial data or expose this server publicly.

```sh
PYTHONPATH=src python3 -m complied.deadlines list --today 2026-10-05
python3 scripts/check_repository.py
python3 -m unittest discover -s tests -v
```

Local database is var/demo.sqlite3 (excluded from Git). Seed is repeatable. [ADR 001](docs/decisions/001-local-prototype.md) records the prototype-only stack decision. Local authenticated editing/review is implemented; production identity, notification delivery, PostalMate imports and filing/payment execution remain pending.

## Generate synthetic recurring deadlines

After seeding the demo database:

```sh
PYTHONPATH=src python3 -m complied.recurrence
PYTHONPATH=src python3 -m complied.deadlines list --today 2026-10-05
```

This adds three monthly demo periods and is safe to repeat. The dashboard shows them on refresh. No actual statutory dates are configured. [Schedule contract](docs/RECURRENCE.md) describes monthly, quarterly and annual periods, explicit short-month/holiday policies and conflict handling.

## Local sign-in and requirement review

```sh
PYTHONPATH=src python3 -m complied.access create-user --user owner-demo --role owner
PYTHONPATH=src python3 -m complied.web
```

Set a unique password at the hidden prompt. Open http://127.0.0.1:8080, sign in and use **Edit and review requirements**. Create/edit saves as unresolved; review requires a source and rationale. Every save records an actor and revision. Editing invalidates prior schedules.

To provision a delegate, use create-user with --role delegate. To revoke an account:

```sh
PYTHONPATH=src python3 -m complied.access disable-user --user delegate-demo
```

[Authentication details](docs/AUTHENTICATED-EDITING.md). These are synthetic local accounts; production Entra integration remains pending.

## Microsoft reminders

Sign in, open **Microsoft reminders**, configure destinations as owner and queue previews for verified current tasks. Email scheduling and calendar payloads are persisted with deduplication and attempt history. [Setup and behavior](docs/MICROSOFT-REMINDERS.md). Microsoft transport is disabled by default. Preview commands never send; explicit operator execution requires separately provisioned delegated authorization. OAuth and automatic scheduling remain pending.

## Review schedule changes

After reviewing applicability, open **Review schedules**. Enter the authoritative rule, preview old/proposed deadlines and confirm the batch. Stale previews, completed-task replacement and uncertain external activity are blocked. Queued reminders cancel when their schedule changes. [Schedule review](docs/SCHEDULE-REVIEW.md).

## Prepare synthetic monthly sales sources

```sh
PYTHONPATH=src python3 -m complied.imports --user owner-demo fixtures/synthetic/ivy-2026-10.csv fixtures/synthetic/pantops-2026-10.csv
```

Or sign in and open **Sales preparation** to upload both normalized CSVs in the browser; the two sources and package are committed together only after validation. Review store totals and source hashes on that screen. [Import contract](docs/SALES-IMPORTS.md). Actual PostalMate columns and tax-return calculations remain pending; packages are explicitly not return-ready.

## Review monthly source evidence

Open **Sales preparation → Review source package** to record source review, request information or reject a package. Download a signed-in JSON source packet with hashes, totals, review history and blockers. Source reviews become stale when another version for the month is imported. [Package review details](docs/PACKAGE-REVIEW.md). Reviewing sources does not approve a tax return or payment.
