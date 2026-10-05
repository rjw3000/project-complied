# Project Complied — Product Requirements

Version: 0.4 | Updated: 5 October 2026 | Status: Implementation baseline; legal rules and stack pending verification

## Purpose and confirmed scope

Internal compliance tool for Whitewater Package Depot LLC, covering Ivy (Charlottesville City) and Pantops (Albemarle County), per owner. Prevent missed deadlines, identify federal/state/local obligations, and prepare accurate reviewable returns. [Project record](../../Project.md) holds confirmed facts; [roadmap](../ROADMAP.md) defines delivery.

Employees and leased premises; no online or out-of-state sales reported. Shipping, packing, merchandise, mailbox rental, printing and freight; no notary. Discover taxes, fees, licenses, payroll duties and entity filings. Separate statutory obligations from contractual renewals. Known duties are monthly sales tax, annual state company filings and local business licenses; catalog completeness is unverified.

## Users and authority

Owner manages facts, assignments, review and separate filing/payment approvals. Owner-approved delegates can perform duties except initiate payments. Until payment approval scope is clarified, default to owner-only payment approval and initiation. Enforce rights in the server, including revocation. A professional reviewer is optional and unarranged; never imply signoff.

## Initial workflow

1. Register entity, both locations, activities and registrations.
2. Review obligation suggestions with authoritative source, applicability reasoning, missing facts and due-date rule.
3. Show upcoming, overdue, unresolved, review-ready and completed work; unresolved obligations remain visible.
4. Import a monthly PostalMate export from each independent store database. Preserve per-store totals before creating the combined entity package.
5. Validate gross sales, taxable physical goods, tax collected, refunds, adjustments and nontaxable categories against source reports.
6. Resolve discrepancies, review an immutable preparation package and approve filing.
7. Manually submit using the verified government route; attach acceptance/receipt evidence. Owner handles payment separately.

QBO is bank-feed accounting support, not the sales-tax source. Dropbox holds dated evidence. Manual imports and evidence upload precede live connectors. Microsoft 365 email/calendar first; Google later.

Owner reports physical goods taxed and tax collected/remitted, third-party shipping/packing treated as nontaxable, and handling immaterial. These are operating facts, not verified tax rules. Preserve handling amounts and classification exceptions; no blanket exemption or inferred discrepancy tolerance.

## Acceptance by milestone

- Calendar: reviewed duties carry owner, period and verified deadline; unknown dates are visibly unresolved. Synthetic recurrence/overdue tests pass.
- Reminders: persisted attempts, deduplication and delivery failure visibility; no duplicate event on retries.
- Preparation: both store reports required; totals trace to hashes, mapping and rule versions; discrepancies block readiness unless explicitly reviewed under a defined policy.
- Approval: delegate cannot initiate payment; stale or revoked approval cannot execute; filing cannot authorize payment.
- Manual completion: filing and payment receipts tracked separately; sending is not acceptance.
- Pilot: one rehearsed preparation cycle, then October sales/November submission if verified inputs and timing allow. Two consecutive reconciled cycles are the later reliability target.

## Capacity and budget

40 owner hours/month, no paid development. Proposed incremental software/hosting allowance $100/month with $150 cap; unapproved and not vendor quotes. Existing subscriptions excluded. November goal is reminders plus assisted preparation, not guaranteed full automation.

## Dependencies and exclusions

Await redacted PostalMate samples, registration notices, actual due dates/form, portal readiness, calendar choice and reviewed tax mappings. Stack/hosting remain open and need an ADR. Autonomous interpretation, portal automation, automatic payments and commercial tenancy are outside the first release. Seven-year retention required; legal triggers and holds need review.
