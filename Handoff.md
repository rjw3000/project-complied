# Project Complied — Continuation Handoff

Version: 0.6 | Updated: 5 October 2026 | Owner: RJ Williams

## Read first

Read [Project.md](Project.md), [AGENTS.md](AGENTS.md), [README.md](README.md), [specifications](docs/specs/02-Technical-Requirements.md) and [roadmap](docs/ROADMAP.md). Do not repeat answered business questions. Latest owner facts override old planning assumptions.

## Implemented state

Main milestone 1159fbc contains merged PRs #7–#11: aligned specs, local SQLite register/dashboard, reviewed recurrence, authenticated requirement editing/review, audit trail and Microsoft reminder outbox/previews with explicitly enabled operator transport. Those changes passed 49 tests, smoke checks, CodeQL and Gitleaks. Fetch current main before editing.

Schedule preview/confirmation merged green in PR #12 at ba66c78. This increment adds schema v6 and authenticated normalized synthetic sales imports, immutable source snapshots and two-store preparation packages. See [schedule review](docs/SCHEDULE-REVIEW.md). Previous implementation remains synthetic local development; production hosting/identity and live integrations are not configured.

## Business scope

Whitewater Package Depot LLC; Ivy/Charlottesville City and Pantops/Albemarle County, per owner. PostalMate has one database per store and is the sales-tax source; QBO bank feeds support accounting reconciliation. Internal tool; federal/state/local discovery; missed sales-tax deadlines first. Employees and leased premises. Physical goods taxed per owner; handling immaterial per owner, not an inferred legal exemption or tolerance.

Owner has 40 hours/month; no paid development. Proposed incremental software/hosting allowance $100/month, cap $150, unapproved. Microsoft 365 first; Google later. Owner-approved delegates may perform duties except payment initiation. Payment approval defaults to owner until clarified. Seven-year retention required; triggers/holds remain open.

## Next work

1. Validate actual PostalMate sample columns and refund/adjustment semantics against docs/SALES-IMPORTS.md. Synthetic imports/packages are implemented; real adapters, tax treatment and return-line calculations remain pending.
2. Extend review workflow for externally created calendar events and unknown outcomes; never blindly resend.
3. Provision production identity/hosting and Microsoft delegated OAuth/token refresh, dedicated calendar and recipient confirmation before live testing.
4. Verify duty sources, registration/location reporting, actual tax form/frequency/deadline and portal route.
5. Prepare a rehearsed monthly package and then the October/November pilot if inputs and verified timing allow.

## Inputs still needed

Redacted monthly reports from both stores, sample receipt classifications, registration/license notices, portal readiness, calendar/recipient, equipment/vehicle inventory and reminder cadence. Exact addresses and financial records remain outside public Git. Professional review unarranged; never imply signoff.

## Controls and validation

Source-linked unresolved applicability stays visible. Edits invalidate prior review and schedules. Completed records retain history. Separate filing/payment approval, owner-only payment initiation, immutable package scope, operation deduplication and unknown-outcome reconciliation survive every change. Reference approval objects are not a production filing service.

Run:

```sh
python3 scripts/check_repository.py
python3 -m unittest discover -s tests -v
```

Use branches/PRs and validate the exact head with required checks. User has authorized PR creation and merge when green in this session; address review findings first. No bot auto-approval or auto-merge. No live secrets or business records in Git/CI. Maintain Project.md and this handoff with each milestone.

Reminder compatibility fix: enqueue recognizes pre-v5 semantic identities and preserves original IDs; existing duplicate identities block dispatch for reconciliation, including unknown outcomes. Never regenerate a key to bypass uncertain prior delivery.

## Source-package review increment

PR #13 merged green at 7cf91b1. This increment adds schema v7, authenticated source decisions, append-only review history and JSON exports. Review context includes all known monthly source versions; corrections invalidate earlier review until explicit revalidation. Tax-return blockers stay visible and return_ready is always false. Follow docs/PACKAGE-REVIEW.md. Next: verified actual report mapping and return rules after sample inputs; runtime production identity and live Microsoft OAuth still pending.

Source-write hardening: every application connection enables recursive SQLite triggers so REPLACE cannot bypass append-only/immutable guards. Imports and preparation acquire an immediate write transaction and reauthorize after locking; revoked sessions cannot finish a delayed write.

## Browser workflow increment (5 October 2026)

A responsive common UI shell and authenticated two-store CSV upload flow are under development. Browser uploads accept only the documented normalized monthly CSV contract, with per-file 64 KiB and total 150 KiB limits. The pair import is atomic, idempotent and source-hashed; a failed report leaves no new source snapshots or package. Actual PostalMate export mapping is still an input. Microsoft tenant registration, consent, selected calendar/recipient, token refresh and production hosting credentials are not yet provisioned.
