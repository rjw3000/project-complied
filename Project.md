# Project Complied — Project Record

Version: 0.5 | Updated: 5 October 2026 | Owner: RJ Williams
Status: Internal pilot; synthetic local deadline prototype and recurrence under development

## Purpose and authority

Build an internal tool for Whitewater Package Depot LLC that identifies applicable statutory obligations, tracks deadlines, prepares filings, and obtains owner or delegated approval before government submission or payment. Avoiding missed deadlines is the first priority.

This is the living business-scope and decision record. [Handoff.md](Handoff.md) records continuation steps. User-confirmed facts here supersede conflicting assumptions in the reconstructed [specifications](docs/specs/01-PRD.md). Align those specifications through reviewed changes; do not treat stale estimates or proposals as commitments.

## Confirmed business facts

| Topic | Confirmed information |
|---|---|
| Entity and coverage | Whitewater Package Depot LLC; both stores |
| Intended audience | Internal tool for now |
| Accounting | One QuickBooks Online company; bank-feed bookkeeping; stores are not currently differentiated. PostalMate is the sales-tax source |
| Point of sale | PostalMate; separate database per store; monthly store/category/tax/refund/nontaxable reports can be exported |
| Current operator | RJ prepares, reviews, files, and pays |
| Filing structure | Stores file combined under one legal entity, per owner |
| Virginia portal | Access/setup not yet completed; RJ plans to arrange it |
| Historical example | Not available now; owner can perform a test |
| Documents | One sales-tax filing folder in Dropbox, organized by date |
| Goods and handling | Physical goods are taxable; owner reports tax is collected and remitted. Handling is immaterial per owner, not an exemption or approved tolerance. |
| Known complexity | Owner currently treats third-party shipping cost and packing services as nontaxable; legal treatment remains unverified |
| Reviewer | Owner initially; professional reviewer may be available later |
| Approval authority | Owner-authorized delegate may perform all duties except initiate payments. Filing and payment remain separate approvals; owner alone initiates payment |
| Notifications | Email and a tax calendar in Outlook or Google |
| Identity/calendar ecosystem | Microsoft 365 business; Microsoft-first, eventual Google support desired |
| Retention | Seven years, as an owner requirement; legal sufficiency and retention trigger still to be reviewed |
| Initial filing route | Manual filing acceptable; automation desired eventually |
| Operating capacity | Owner will implement/operate; 40 hours per month |
| Budget | Software and hosting only; no paid development help. Proposed planning allowance: $100/month with a $150/month cap, excluding existing subscriptions; not an approved spend or vendor quote |
| Development tools | Has not used Claude Code or Grokbot; open to either; framework not selected |
| Pilot cycle | October 2026 sales, with intended submission in November 2026; actual due date unverified |

## Outcomes and scope

Success means identifying applicable statutory requirements, tracking deadlines through email/calendar, and preparing an accurate return ready for submission from reliable source data. Initial proposed acceptance: reconcile a complete monthly package, obtain owner approval, and retain filing receipt; exact tolerances and notification timing remain open.

Scope includes statutory filings, taxes, fees, licenses, registrations, payroll-related filings, entity annual reports, and other applicable obligations. Insurance renewals are also desired calendar items; distinguish contractual/operational renewals from statutory duties. Federal/state/local discovery is confirmed. Employees and leased premises are confirmed; no online or out-of-state sales reported. Equipment/vehicle ownership remains unanswered.

Each discovered obligation should carry authority/source, effective date, applicability rationale, jurisdiction, required business facts, owner, recurrence, due-date rule, evidence requirements, and review status. Missing facts produce an explicit “applicability unresolved” state. Do not claim comprehensive coverage before discovery and review are complete.

## Execution direction

Recommended approach, not a final stack decision: preparation-first hybrid internal app. Build calendar and obligation register first; use exports and manual submission initially; progressively add connectors, filing, and payment. Track both stores as business locations even if accounting imports begin combined. Whether location-specific tax allocation is necessary remains unresolved.

PostalMate exports → per-store validation → reviewed tax mapping → combined entity package is the preparation path. QBO bank feeds support accounting reconciliation only and cannot establish taxable sales. Preserve store detail even when the final filing is combined; local jurisdiction and location reporting require verification.

Use deterministic, versioned calculations with reviewed rules. AI may assist discovery, extraction, explanation, and exception triage; it does not establish statutory applicability or filing correctness by itself.


## Follow-up facts confirmed 5 October 2026

- Two Virginia stores; owner supplied exact addresses in conversation. Keep them outside this public repository; owner confirms Ivy is Charlottesville City and Pantops is Albemarle County. Official validation of registrations and location reporting remains pending.
- Activities: shipping, packing, merchandise, mailbox rental, printing, and freight; no notary. Exact invoice categories and bundled charges await sample reports/receipts.
- Known duties: annual state company filings, monthly sales tax, and annual county/city business licenses. These owner-reported duties are a discovery seed, not a verified complete statutory catalog.
- Monthly sales-tax deadlines have been missed; prioritize reminders and overdue visibility.
- Synthetic/redacted exports can be supplied. Actual business records require a secure route outside GitHub.

Virginia shipping/handling validation sources (reviewed 5 October 2026):
https://law.lis.virginia.gov/admincode/title23/agency10/chapter210/section6000/
and https://www.tax.virginia.gov/laws-rules-decisions/rulings-tax-commissioner/15-115
Separately stated transportation may be excluded; handling and bundled charges require separate analysis. Do not encode a blanket packing exemption.

Budget allowance is a project planning choice, not researched product pricing: target $100/month, maximum $150/month pending owner approval, covering incremental hosting, database/backups, notification delivery, and development tools. Existing Microsoft/QBO/PostalMate/Dropbox costs are excluded until identified. Prefer reuse of existing subscriptions. Establish current vendor quotes before selecting or purchasing services.

## Current implementation and protections

Repository: https://github.com/rjw3000/project-complied

Implemented: reconstructed PRD/technical/architecture drafts and diagram, roadmap, dependency-free Python approval reference, seven approval tests, documentation/workflow checks, CI, CodeQL, Gitleaks, Dependabot, CODEOWNERS, contribution guidance, issue templates, security policy, and threat model.

Main protection requires pull requests, current branches, resolved conversations, and three GitHub Actions checks; applies to administrators. Force pushes/deletion prohibited. Approval count is zero for the solo-owner workflow; independent code-owner approval is not enforced. Actions have an allowlist, full SHA pinning, read-only token defaults, no automated PR approval, and external-contributor run approval. Private vulnerability reporting, dependency graph, Dependabot alerts/security updates, secret protection and push protection are enabled. See [verified settings](docs/security/GITHUB-SETTINGS.md).

PR #6 merged as `8882590f0e0966fd68eebe26140c39e87647e320`; issue #4 closed. All three checks passed on that PR before merge. This is not evidence of application completion or production readiness.

Implemented in the local synthetic prototype: dashboard, authenticated editing/review, recurrence and reminder outbox/previews. Still pending: production identity/hosting, verified obligation catalog, tax calculations, durable filing/payment execution, live account connections and automated delivery.

## Source and schedule note

Virginia Tax states sales-tax accounts officially move to its new Online Services platform on 9 November 2026; eForms and Web Upload remain available: https://www.tax.virginia.gov/modernize (researched 3 October 2026). Reverify the applicable route before November pilot execution. No supported filing API, precise return form, or filing deadline has been established for this entity.

Earlier 12–16-week-or-longer pilot and $5,000–$15,000 reserve figures were provisional reconstructed planning assumptions. They are not approved estimates. Replan against 40 hours/month and the narrowed November goal: reminders and an assisted preparation package, subject to source-data and rule validation.

## Maintenance

Update after each material user answer, decision, implementation milestone, or verification. Label facts as confirmed, proposed, unresolved, or verified. Record decision date and provenance. Preserve superseded decisions in the change log. Keep Project.md and Handoff.md consistent in the same PR. Never commit credentials, actual tax returns, financial records, or private location/personnel details to this public repository.

## Change log

- 3 October 2026 — v0.2: captured 22 owner answers; internal scope, both stores, PostalMate gap, deadline priority, delegated approvals, seven-year retention, 40 hours/month, and intended October/November pilot. Stack, budget, dates, and tax applicability remain open.

- 5 October 2026 — v0.3: resolved follow-up business questions; PostalMate primary, owner-only payment initiation, Microsoft 365, federal/state/local discovery, owner development, software/hosting budget allowance proposed.

- 5 October 2026 — v0.4: owner confirms Ivy/Charlottesville City and Pantops/Albemarle County, physical goods taxed, handling immaterial. Specifications and delivery plan aligned; monetary tolerance remains unset.

## Implementation progress — 5 October 2026

PR #8 adds the local SQLite/read-only dashboard prototype; CI, CodeQL and Gitleaks passed at 0d0d1d3. This branch adds immutable reviewed recurrence rules, atomic task generation, explicit calendar policies and migration tests. These are synthetic capabilities, not verified statutory dates. Production identity, notifications and imports remain pending.

- 5 October 2026 — specifications, local dashboard and recurrence merged into main at b5f1055 after green checks. Local authenticated editing/review increment now in development; Microsoft reminders follow. Production identity remains unselected.

- 5 October 2026 — authenticated local edit/review merged at 48a5a711 after green checks. Microsoft reminder queue/preview and injected adapter now added; OAuth, live connection and account testing remain pending; explicit operator transport is disabled by default.

- 5 October 2026 — schedule review increment: authenticated preview/confirmation, preserved task history, completed/external-outcome blocks, queued reminder cancellation and schedule revision binding. Main milestone 1159fbc contains prior PRs #7–#11; no live Microsoft account connected.

- 5 October 2026 — PR #12 schedule review merged at ba66c78 after green checks. Sales-source increment adds synthetic normalized CSVs, immutable snapshots and same-month/two-store preparation manifests. Source reconciled does not mean return-ready; actual PostalMate mapping and tax rules remain unverified.
