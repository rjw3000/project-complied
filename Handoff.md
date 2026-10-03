# Project Complied — Continuation Handoff

Version: 0.2 | Updated: 3 October 2026 | Owner: RJ Williams

## Read first

Read [Project.md](Project.md), [AGENTS.md](AGENTS.md), [README.md](README.md), and the [technical requirements](docs/specs/02-Technical-Requirements.md). Project.md contains the latest confirmed business facts; older reconstructed specifications have unaligned assumptions. Do not restart discovery or ask the already answered 22 questions again.

## Current objective

Internal tool for Whitewater Package Depot LLC and both stores. First priority: avoid missed deadlines. Intended first preparation cycle is October 2026 sales for submission in November; deadline and required return must be verified. Owner has 40 hours/month. Manual filing is acceptable initially. All external filings and payments require separate owner/delegate approval.

## Where work stands

Repository foundation and security completed. PR #6 merged at `8882590f0e0966fd68eebe26140c39e87647e320`; security issue #4 closed. That SHA is a verified milestone, not a guarantee of current HEAD. Fetch the live repository before editing. Other PRs/issues may have changed, including Dependabot updates; inspect before acting.

No running application, production account connection, tax rule engine, notification delivery, or external execution exists. Python approval controls are a reference implementation, not a chosen production stack. The current policy assumes trusted approval objects; authentication, persistence, and concurrency-safe execution remain pending.

## Pending questions — awaiting owner answers

| ID | Question | What it resolves |
|---|---|---|
| Q01 | Each store's city/county/state and address; confirm both under the LLC | Local jurisdiction and location duties; keep exact private addresses outside public Git |
| Q02 | All charged products/services: shipping, packaging, merchandise, mailbox rental, printing, notary, freight, others | Obligation and tax-treatment discovery |
| Q03 | Separate PostalMate databases/accounts? Available monthly store/category/tax/refund/nontaxable exports? | Source-data model and store mapping |
| Q04 | How sales reach QuickBooks; whether gross sales and collected tax are separate | Accounting completeness and reconciliation |
| Q05 | Reports and figures used for the current combined return | Baseline preparation process |
| Q06 | Categories currently treated as nontaxable and where treatment is recorded | Rules requiring authoritative validation |
| Q07 | Existing taxes, fees, registrations, licenses, and renewals | Initial obligation inventory |
| Q08 | Employees, premises ownership/lease, equipment/vehicles, online/out-of-state sales | Applicability facts |
| Q09 | Deadlines missed/nearly missed and desired reminder cadence | Notification priorities |
| Q10 | Personal Outlook or M365 business; dedicated compliance calendar? | Identity/calendar integration |
| Q11 | Delegate permissions for preparation, filing approval, payment approval, reminders | Role model |
| Q12 | Confirm federal/state/local discovery scope | Research boundary |
| Q13 | Synthetic/redacted exports before close; actual October records via secure route | Pilot validation inputs |
| Q14 | Budget for hosting/software/review only or paid development too? | Recommended budget and resourcing |

Owner portal setup is pending. Professional review is optional/unarranged; owner is the initial reviewer. Do not imply accountant approval.

## Useful work while answers are pending

1. Align PRD, technical requirements, architecture, and roadmap to confirmed Project.md facts through a reviewed PR.
2. Design entity/location/activity facts, obligation provenance, unresolved applicability, recurrence, delegate roles, evidence retention, and package versioning.
3. Define a synthetic fixture format for PostalMate and accounting exports without assuming actual export columns.
4. Design deadline dashboard and notification preferences with a Microsoft-first adapter boundary and future Google support.
5. Propose a small milestone plan and budget options after identifying hosting/tool costs; do not reuse the provisional reserve as approved.

Do not connect live accounts, implement guessed tax rules, or automate portal writes while these dependencies are unresolved.

## Next sequence after answers

- Confirm facts and identify authoritative federal/state/local sources. Distinguish owner practice from verified legal treatment.
- Verify registration, actual filing frequency/form/deadline, location reporting, and November submission route.
- Establish one synthetic/reconciled monthly fixture and expected calculation package.
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
