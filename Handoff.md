# Project Complied — Continuation Handoff

Version: 0.5 | Updated: 5 October 2026 | Owner: RJ Williams

## Read first

Read [Project.md](Project.md), [AGENTS.md](AGENTS.md), [README.md](README.md), [specifications](docs/specs/02-Technical-Requirements.md) and [roadmap](docs/ROADMAP.md). Do not repeat answered business questions. Latest owner facts override old planning assumptions.

## Implemented state

Main milestone 1159fbc contains merged PRs #7–#11: aligned specs, local SQLite register/dashboard, reviewed recurrence, authenticated requirement editing/review, audit trail and Microsoft reminder outbox/previews with explicitly enabled operator transport. Those changes passed 49 tests, smoke checks, CodeQL and Gitleaks. Fetch current main before editing.

This increment adds authenticated schedule preview/confirmation, additive schema v5 and schedule-revision-bound reminders. See [schedule review](docs/SCHEDULE-REVIEW.md). Previous implementation remains synthetic local development; production hosting/identity and live integrations are not configured.

## Business scope

Whitewater Package Depot LLC; Ivy/Charlottesville City and Pantops/Albemarle County, per owner. PostalMate has one database per store and is the sales-tax source; QBO bank feeds support accounting reconciliation. Internal tool; federal/state/local discovery; missed sales-tax deadlines first. Employees and leased premises. Physical goods taxed per owner; handling immaterial per owner, not an inferred legal exemption or tolerance.

Owner has 40 hours/month; no paid development. Proposed incremental software/hosting allowance $100/month, cap $150, unapproved. Microsoft 365 first; Google later. Owner-approved delegates may perform duties except payment initiation. Payment approval defaults to owner until clarified. Seven-year retention required; triggers/holds remain open.

## Next work

1. Synthetic per-store import contract, source snapshot capture and reconciliation package; map actual PostalMate columns only after sample review.
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
