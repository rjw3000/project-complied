# Compliance Automation — Product Requirements

Version: 0.1-R | Date: 3 October 2026 | Status: Reconstructed draft

This document reconstructs the proposed scope from the available conversation. It is not a verbatim recovery of the original draft. Unconfirmed details remain open.

## Purpose

Give a business owner one place to discover obligations, track deadlines, gather records, prepare monthly sales-tax work, approve actions, and retain proof of completion. Start with an internal pilot using QuickBooks Online and Dropbox, with Virginia sales-tax preparation as the first recurring workflow.

## Users and responsibilities

- Owner: confirms business facts, reviews exceptions, approves filings and separately approves payments.
- Operator: maintains the calendar, resolves missing records, and prepares work for review.
- Professional reviewer: validates tax treatment and applicable requirements when needed; engagement and cost are open.

## Pilot scope

1. Capture entities, stores, jurisdictions, registrations, responsible people, and data sources.
2. Create a reviewable obligation register with authoritative references, applicability rationale, effective dates, recurrence, and owner.
3. Build a calendar of tasks, reminders, due dates, dependencies, and overdue exceptions.
4. Connect authorized QuickBooks Online accounting data and Dropbox supporting records.
5. Prepare a monthly sales-tax package with source totals, adjustments, exceptions, and supporting evidence.
6. Present a concise approval view showing entity, jurisdiction, period, calculation version, amount, exceptions, and next action.
7. Record approvals, receipts, reconciliation, and recovery actions.

Filing and payment are later phases, enabled only after Virginia's submission route and account access are verified. Discovery suggestions require review before becoming active obligations.

## Owner experience

The dashboard shows what is due, what needs attention, what is ready for approval, and what is complete. Each task opens its source records, calculation explanation, outstanding questions, and history. Changes to approved inputs return the package to review. Filing approval does not authorize payment.

## Out of initial scope

Multi-state automated filing, autonomous tax interpretation, unsupervised payments, commercial multi-tenant delivery, and replacing professional judgment are excluded from the pilot.

## Proposed pilot acceptance criteria

- All owner-confirmed pilot obligations appear in the calendar with an accountable owner.
- At least two consecutive monthly preparation cycles complete with documented reconciliation and review.
- Every prepared amount traces to a source snapshot and approved calculation version.
- Missing records or unresolved material exceptions prevent approval readiness.
- No filing or payment executes without the relevant valid approval.
- Duplicate-action and uncertain-submission recovery scenarios are demonstrated.
- Owner preparation/review time is measured against a baseline; reduction target is agreed before pilot launch.

These criteria are proposed, not confirmed commitments.

## Delivery and economics

The earlier planning estimate was 12–16 weeks or longer for an internal pilot. It remains provisional because capacity details and integration constraints are unavailable here. The earlier $5,000–$15,000 reserve remains provisional pending integration, hosting, and professional-review costs.

## Open decisions

- Does QuickBooks identify stores through classes, locations, another dimension, or separate companies?
- Is the Virginia tax-portal account established, and who has authority to file and pay?
- Which Grokbot framework will coordinate development?
- What entities, stores, registrations, filing frequencies, and historical records belong in the pilot?
- Who provides professional review, and what are the retention and notification requirements?
