# Compliance Automation — System Architecture

Version: 0.1-R | Date: 3 October 2026 | Status: Reconstructed draft

Reconstructed from the available conversation and proposed diagram. Technology choices are proposals, not selected products. This document does not establish verified tax rules or portal capabilities.

## Architecture approach

Begin with a modular application, a durable relational database, an evidence store, and a background worker. Separate preparation from approval and external execution. This keeps the pilot manageable while allowing connectors and jurisdiction adapters to evolve independently.

## Components

| Component | Responsibility |
|---|---|
| Owner dashboard | Calendar, exceptions, package review, approvals, receipts, and status. |
| Application API | Authentication, authorization, scope resolution, commands, and review queries. |
| Obligation register | Reviewed requirements, applicability, provenance, versions, and recurrence. |
| Scheduler and workflow engine | Periodic tasks, dependencies, durable states, reminders, and recovery. |
| Connector layer | Scoped QuickBooks Online and Dropbox reads with capture metadata. |
| Preparation module | Deterministic decimal calculations and evidence-package creation. |
| Review and approval service | Exception gates, version-bound approval, and approval invalidation. |
| Jurisdiction adapter | Verified Virginia submission or documented manual handoff. |
| Payment adapter | Separately approved payment execution and reconciliation. |
| Audit and evidence services | Action history, snapshots, hashes, receipts, and traceability. |

## Runtime flow

1. Owner-confirmed business facts and reviewed obligations establish the calendar.
2. Scheduler opens a scoped task for the filing period.
3. Connectors capture authorized accounting data and supporting records.
4. Preparation creates a versioned calculation package and reconciliation results.
5. Review resolves exceptions and obtains professional input where required.
6. Owner approves the exact filing package. Changed inputs invalidate approval.
7. A verified adapter submits or creates a manual filing handoff.
8. Submission acknowledgment and final acceptance are tracked separately.
9. Payment requires its own owner approval; settlement is reconciled separately.
10. Receipts and completed evidence return to the owner dashboard.

Rejected packages return to preparation. Unknown external outcomes enter a reconciliation queue and cannot be blindly retried.

## Proposed data model

Entities, stores, jurisdictions, registrations, obligations, obligation versions, tasks, periods, connector accounts, source snapshots, document references, calculation rules, package versions, exceptions, approvals, external operations, receipts, payment operations, and audit events.

Each operational record carries scope and timestamps. Approval references an immutable package version. External operations carry durable deduplication keys. Secrets are stored separately from application records. QuickBooks remains the accounting source; Dropbox remains the supporting-document source; the application owns workflow state and approval history.

## Deployment and trust boundaries

Deploy application and worker with distinct service permissions. Restrict database and secret-store access to authorized services. Limit integration credentials by purpose and account scope. Keep external writes behind the approval service and enabled adapters. Retain source evidence according to a policy agreed before launch. Hosting provider, language, database product, notification channel, and recovery objectives remain open.

## Development coordination

Grokbot is proposed as the development coordinator, Claude Code as the implementation agent, and ChatGPT as the QA reviewer. The Grokbot framework is not selected. These are development roles; runtime filing and payment authority remains with the application approval controls and the owner.

A proposed delivery cycle is: reviewed specification → implementation branch → automated checks → ChatGPT QA evidence → reviewed release. Production secrets do not enter prompts or source control. Use synthetic/redacted fixtures for development.

## Delivery phases

- Phase 1: business facts, requirement discovery, reviewed obligation register, and calendar.
- Phase 2: QuickBooks and Dropbox reads, source capture, and store mapping.
- Phase 3: monthly preparation, reconciliation, review, approvals, and internal pilot.
- Phase 4: verified Virginia filing route, receipts, and manual fallback.
- Phase 5: separate payment approval, execution, and settlement reconciliation.

The earlier estimate of 12–16 weeks or longer applies provisionally to the internal pilot, not guaranteed full filing/payment automation.

## Decisions required before implementation

Confirm QuickBooks store dimensions, Virginia account/access and submission route, pilot entity scope, review ownership, calculation rules, retention, hosting, and Grokbot framework. Choose technologies after these constraints are resolved.
