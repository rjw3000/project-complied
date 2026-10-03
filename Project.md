# Project Complied — Project Record

Version: 0.2 | Updated: 3 October 2026 | Owner: RJ Williams
Status: Internal pilot planning; repository foundation implemented

## Purpose and authority

Build an internal tool for Whitewater Package Depot LLC that identifies applicable statutory obligations, tracks deadlines, prepares filings, and obtains owner or delegated approval before government submission or payment. Avoiding missed deadlines is the first priority.

This is the living business-scope and decision record. [Handoff.md](Handoff.md) records continuation steps. User-confirmed facts here supersede conflicting assumptions in the reconstructed [specifications](docs/specs/01-PRD.md). Align those specifications through reviewed changes; do not treat stale estimates or proposals as commitments.

## Confirmed business facts

| Topic | Confirmed information |
|---|---|
| Entity and coverage | Whitewater Package Depot LLC; both stores |
| Intended audience | Internal tool for now |
| Accounting | One QuickBooks Online company; stores are not currently differentiated |
| Point of sale | PostalMate; no interaction with QuickBooks Online |
| Current operator | RJ prepares, reviews, files, and pays |
| Filing structure | Stores file combined under one legal entity, per owner |
| Virginia portal | Access/setup not yet completed; RJ plans to arrange it |
| Historical example | Not available now; owner can perform a test |
| Documents | One sales-tax filing folder in Dropbox, organized by date |
| Known complexity | Sales that are not considered taxable; categories and legal treatment unverified |
| Reviewer | Owner initially; professional reviewer may be available later |
| Approval authority | Business owner or a delegate; filing and payment separately approved |
| Notifications | Email and a tax calendar in Outlook or Google |
| Identity/calendar ecosystem | Microsoft currently; eventual Google support desired |
| Retention | Seven years, as an owner requirement; legal sufficiency and retention trigger still to be reviewed |
| Initial filing route | Manual filing acceptable; automation desired eventually |
| Operating capacity | Owner will implement/operate; 40 hours per month |
| Budget | Recommended dollar budget requested; not yet determined or approved |
| Development tools | Has not used Claude Code or Grokbot; open to either; framework not selected |
| Pilot cycle | October 2026 sales, with intended submission in November 2026; actual due date unverified |

## Outcomes and scope

Success means identifying applicable statutory requirements, tracking deadlines through email/calendar, and preparing an accurate return ready for submission from reliable source data. Initial proposed acceptance: reconcile a complete monthly package, obtain owner approval, and retain filing receipt; exact tolerances and notification timing remain open.

Scope includes statutory filings, taxes, fees, licenses, registrations, payroll-related filings, entity annual reports, and other applicable obligations. Insurance renewals are also desired calendar items; distinguish contractual/operational renewals from statutory duties. Federal/state/local discovery is proposed pending location and activity facts.

Each discovered obligation should carry authority/source, effective date, applicability rationale, jurisdiction, required business facts, owner, recurrence, due-date rule, evidence requirements, and review status. Missing facts produce an explicit “applicability unresolved” state. Do not claim comprehensive coverage before discovery and review are complete.

## Execution direction

Recommended approach, not a final stack decision: preparation-first hybrid internal app. Build calendar and obligation register first; use exports and manual submission initially; progressively add connectors, filing, and payment. Track both stores as business locations even if accounting imports begin combined. Whether location-specific tax allocation is necessary remains unresolved.

PostalMate → bookkeeping → tax preparation is a critical dependency. QuickBooks cannot be assumed to contain taxable/nontaxable sales detail or the full gross-sales ledger. Confirm the source and reconciliation path before implementing calculations.

Use deterministic, versioned calculations with reviewed rules. AI may assist discovery, extraction, explanation, and exception triage; it does not establish statutory applicability or filing correctness by itself.

## Current implementation and protections

Repository: https://github.com/rjw3000/project-complied

Implemented: reconstructed PRD/technical/architecture drafts and diagram, roadmap, dependency-free Python approval reference, seven approval tests, documentation/workflow checks, CI, CodeQL, Gitleaks, Dependabot, CODEOWNERS, contribution guidance, issue templates, security policy, and threat model.

Main protection requires pull requests, current branches, resolved conversations, and three GitHub Actions checks; applies to administrators. Force pushes/deletion prohibited. Approval count is zero for the solo-owner workflow; independent code-owner approval is not enforced. Actions have an allowlist, full SHA pinning, read-only token defaults, no automated PR approval, and external-contributor run approval. Private vulnerability reporting, dependency graph, Dependabot alerts/security updates, secret protection and push protection are enabled. See [verified settings](docs/security/GITHUB-SETTINGS.md).

PR #6 merged as `8882590f0e0966fd68eebe26140c39e87647e320`; issue #4 closed. All three checks passed on that PR before merge. This is not evidence of application completion or production readiness.

Not implemented: application UI/auth, live connectors, verified obligation catalog, tax calculation engine, durable approval service, operation ledger, filing/payment adapters, calendar/email delivery, production deployment.

## Source and schedule note

Virginia Tax states sales-tax accounts officially move to its new Online Services platform on 9 November 2026; eForms and Web Upload remain available: https://www.tax.virginia.gov/modernize (researched 3 October 2026). Reverify the applicable route before November pilot execution. No supported filing API, precise return form, or filing deadline has been established for this entity.

Earlier 12–16-week-or-longer pilot and $5,000–$15,000 reserve figures were provisional reconstructed planning assumptions. They are not approved estimates. Replan against 40 hours/month and the narrowed November goal: reminders and an assisted preparation package, subject to source-data and rule validation.

## Maintenance

Update after each material user answer, decision, implementation milestone, or verification. Label facts as confirmed, proposed, unresolved, or verified. Record decision date and provenance. Preserve superseded decisions in the change log. Keep Project.md and Handoff.md consistent in the same PR. Never commit credentials, actual tax returns, financial records, or private location/personnel details to this public repository.

## Change log

- 3 October 2026 — v0.2: captured 22 owner answers; internal scope, both stores, PostalMate gap, deadline priority, delegated approvals, seven-year retention, 40 hours/month, and intended October/November pilot. Stack, budget, dates, and tax applicability remain open.
