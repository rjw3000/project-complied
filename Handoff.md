# Project Complied — Continuation Handoff

Version: 0.4 | Updated: 5 October 2026 | Owner: RJ Williams

## Read first

Read [Project.md](Project.md), [AGENTS.md](AGENTS.md), [README.md](README.md), and the [technical requirements](docs/specs/02-Technical-Requirements.md). Project.md contains the latest confirmed business facts; specifications are aligned to the 5 October owner answers. Do not restart discovery or ask the already answered 22 questions again.

## Current objective

Internal tool for Whitewater Package Depot LLC and both stores. First priority: avoid missed deadlines. Intended first preparation cycle is October 2026 sales for submission in November; deadline and required return must be verified. Owner has 40 hours/month. Manual filing is acceptable initially. Filings may be handled by an owner-authorized delegate; payment initiation is owner-only. Separate filing/payment approvals remain required.

## Where work stands

Repository foundation and security completed. PR #6 merged at `8882590f0e0966fd68eebe26140c39e87647e320`; security issue #4 closed. That SHA is a verified milestone, not a guarantee of current HEAD. Fetch the live repository before editing. Other PRs/issues may have changed, including Dependabot updates; inspect before acting.

No running application, production account connection, tax rule engine, notification delivery, or external execution exists. Python approval controls are a reference implementation, not a chosen production stack. The current policy assumes trusted approval objects; authentication, persistence, and concurrency-safe execution remain pending.

## Follow-up answers received 5 October 2026

All 14 follow-up topics received owner responses; do not repeat the questionnaire. See Project.md for confirmed facts. Exact location addresses stay outside public Git.

Remaining targeted inputs:

- Owner confirms Ivy/Charlottesville City and Pantops/Albemarle County. Verify registration and location reporting; do not re-ask the jurisdiction question.
- Redacted monthly PostalMate report from each database, plus sample receipt lines separating shipping, packing labor, materials, and bundled charges. Column names and totals must be inspected before choosing an import contract.
- State/company and local license notices; verify annual fee/report terminology, filing form, frequency, dates, and receipt requirements.
- Portal readiness, dedicated M365 calendar, reminder timing, and equipment/vehicle inventory remain open.
- Determine delegate payment-approval scope separately from the confirmed prohibition on delegate payment initiation; default to owner-only payment approval and initiation until clarified.

Owner portal setup is pending. Professional review is optional/unarranged; owner is the initial reviewer. Do not imply accountant approval.

## Next implementation work

1. Execute milestone M1 in docs/ROADMAP.md: application scaffold, schema, synthetic seed, obligation register and deadline dashboard. Record stack decision before adding dependencies.
2. Design entity/location/activity facts, obligation provenance, unresolved applicability, recurrence, delegate roles, evidence retention, and package versioning.
3. Define a synthetic fixture format for PostalMate and accounting exports without assuming actual export columns.
4. Design deadline dashboard and notification preferences with a Microsoft-first adapter boundary and future Google support.
5. Propose a small milestone plan and budget options using the proposed $100/month allowance and $150/month cap; validate actual vendor costs; do not reuse the provisional reserve as approved.

Do not connect live accounts, implement guessed tax rules, or automate portal writes while these dependencies are unresolved.

## Next sequence

- Confirm facts and identify authoritative federal/state/local sources. Distinguish owner practice from verified legal treatment.
- Verify registration, actual filing frequency/form/deadline, location reporting, and November submission route.
- Establish per-store PostalMate synthetic/reconciled monthly fixtures and one combined entity package with expected totals.
- Select stack and hosting; build obligation register, calendar, reminders, and owner dashboard.
- Add source collection and deterministic preparation, review, separate approvals, and receipts.
- Validate monthly process before enabling filing; payment follows with its own gate.

## Controls that must survive

- Business data stays out of public Git, CI logs, and agent prompts unless explicitly authorized for an approved route.
- Unknown applicability and incomplete source records remain visible; do not present unsupported completeness.
- Approval binds entity, jurisdiction, period, amount, destination, and immutable package version.
- Changed packages invalidate approvals. Filing approval cannot authorize payment.
- Durable operation identifiers and unknown-outcome reconciliation are prerequisites to external execution.
- Seven-year retention is confirmed; retention start, deletion/hold policy, backup scope, and legal sufficiency remain open.
- Full SHA-pinned Actions, reviewed PRs, passing checks, and restricted bot privileges remain enforced.

## Validation and delivery

From repository root:

```sh
python3 scripts/check_repository.py
python3 -m unittest discover -s tests -v
```

Use meaningful tests for new behavior. Verify CI/CodeQL/Gitleaks at the PR head before release. Respect main protection and use branches/PRs. This handoff does not grant blanket merge or account-write authorization. Follow current session authorization; obtain explicit approval when an automatic approval review requires it.

## Maintaining the records

For new answers: update Project.md facts and remove/resolve the matching pending question here. For decisions: record selected option, date, rationale, and remaining dependencies. For implementation: record PR/commit, checks and scope of completion. For unresolved blockers: state the evidence and exact next action. Update both files together; do not record secrets or sensitive evidence in either.

## Change log

- 3 October 2026 — v0.2: first living handoff, incorporating owner answers and 14 pending follow-up questions; security foundation complete and application build pending.

- 5 October 2026 — v0.3: follow-up answers recorded; replaced answered questions with concrete validation inputs. Prioritize deadline prototype and PostalMate imports. QBO-first assumptions are superseded.

- 5 October 2026 — v0.4: jurisdiction and handling clarifications captured; implementation-ready specifications and milestone plan published. The Mermaid architecture is current; the old PNG is historical.

## Local deadline prototype added

ADR 001 selects Python standard library/SQLite for synthetic M1 only. Use README seed/run commands. Added persistent obligation/task schema, loopback read-only dashboard, review gates, duplicate task prevention, and behavior tests. Still pending: authenticated editing, versioned obligation changes, recurrence generation, notifications, imports and production selection. Existing approval module remains a reference. CI must validate this implementation; offline workspace prevented local execution. Do not call M1 complete yet.
