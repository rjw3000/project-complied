# Project Complied — Technical Requirements

Version: 0.4 | Updated: 5 October 2026 | Status: Implementation baseline

Aligned to owner answers in [Project.md](../../Project.md). Requirements below are proposed and testable. Virginia rules, forms, deadlines, and submission capabilities have not been verified in this document.

## Functional requirements and acceptance

| ID | Requirement | Acceptance evidence |
|---|---|---|
| TR-01 | Store entity, store, jurisdiction, registration, timezone, and responsible owner independently. | A pilot task resolves to one unambiguous scope. |
| TR-02 | Maintain an obligation register with source reference, applicability rationale, effective date, review status, and version. | Unreviewed discovery cannot activate an obligation. |
| TR-03 | Generate recurring tasks with explicit period boundaries, due-date rules, and exception handling. | Approved fixtures generate expected periods and dates without duplicates. |
| TR-04 | Import per-store PostalMate exports with period, database/store ID, source hash and capture time; QBO is optional reconciliation support. | A prepared total traces to the exact imported snapshot. |
| TR-05 | Validate both PostalMate store reports and map categories using versioned, reviewed rules; retain store totals before entity aggregation. | Unmapped or ambiguous records create blocking exceptions. |
| TR-06 | Link authorized Dropbox records by file identifier and version where supported, with hashes for captured evidence. | Reviewers can retrieve the record used during preparation. |
| TR-07 | Calculate amounts with decimal arithmetic and versioned, reviewed rules with authoritative sources; professional review where required. | Approved fixtures match expected totals, adjustments, and rounding. |
| TR-08 | Reconcile preparation totals to PostalMate source reports; explain QBO bank/deposit differences separately and disclose differences. | Unresolved material differences block readiness. |
| TR-09 | Bind filing approval to entity, jurisdiction, period, destination, package version, and amount. | Any material change invalidates the approval. |
| TR-10 | Require separate payment approval bound to amount, recipient, funding reference, and period. | Filing approval alone cannot execute payment; delegated actors cannot initiate payment. |
| TR-11 | Gate filing and payment adapters behind verified capability and explicit enablement. | Disabled adapters cannot issue external writes. |
| TR-12 | Persist operation identifiers and deduplicate external actions. | Repeated requests cannot knowingly create duplicate filings or payments. |
| TR-13 | Treat ambiguous external responses as unknown outcomes requiring reconciliation. | Timeout after submission does not trigger blind resubmission. |
| TR-14 | Record external acknowledgment separately from settlement or final acceptance. | A sent request cannot be displayed as completed without appropriate confirmation. |
| TR-15 | Provide manual handoff if the verified portal route lacks a suitable supported integration. | Operator receives a versioned package and can attach receipt evidence. |
| TR-16 | Maintain an append-only action history for calculations, approvals, submissions, payments, and overrides. | Sample actions resolve to actor, timestamp, scope, and version. |

## Access and data protection

Use individual accounts, MFA where supported, and role-based permissions. Distinguish preparation, review, filing approval, payment approval, and administration. Enforce authorization server-side. Store integration credentials in a secret store, encrypt sensitive data in transit and at rest, redact tokens and financial account details from logs, and restrict connector access to approved resources. Development agents use synthetic or redacted fixtures by default; production-data access requires an explicit reviewed route.

## Reliability and recovery

Persist job state before external execution. Use bounded retries for safe reads and confirmed retryable actions. Failed notifications and stale integrations create visible exceptions. Provide backup and restore procedures, operator recovery instructions, and reconciliation queues. Seven-year retention is owner-required; start/hold/deletion policy and recovery objectives remain open. Microsoft 365 email/calendar first, Google later.

## Suggested workflow states

Draft → Preparing → Needs information / Review ready → Approved → Submission pending → Accepted / Rejected / Outcome unknown → Reconciled.

Payment has its own approval and execution states. Completion depends on the obligation's defined evidence requirements, not merely worker success.

## Integration discovery gates

First inspect redacted PostalMate exports and define column contracts; never guess export columns. QBO integration is later optional accounting reconciliation; bank feeds cannot establish taxable sales. Confirm Dropbox account scope, folder permissions, and version access. Confirm Virginia registration, delegated authority, supported submission route, authentication, receipts, payment capabilities, and manual fallback before enabling writes. Do not assume an API exists.

## Release verification

Demonstrate unauthorized-access denial, stale approval invalidation, missing-data blocking, correct decimal calculations, period boundaries, token expiration recovery, duplicate prevention, unknown-outcome reconciliation, and restoration of a sample package. Validate filing/payment in a suitable test environment or controlled manual workflow before production activation.

## Import, deadline and notification contracts

Normalized synthetic records: entity_id, store_id, period_start, period_end, source_hash, mapping_version, gross_sales, taxable_sales, nontaxable_sales, refunds, adjustments and tax_collected. Decimal strings for money. This is an internal model, not a claim about PostalMate column names. Preserve raw reports securely; reject missing stores, mixed periods, duplicate snapshots, unsupported formats and unexplained totals. Define signs, tax-inclusive totals and rounding only after sample inspection.

Obligations include jurisdiction, duty type, source URL, retrieved/effective dates, applicability status (unresolved/applicable/not applicable), rationale, missing facts, registration scope, owner and review history. A due date requires a reviewed rule, timezone, period and holiday/weekend policy; do not invent dates. Unique task key: obligation version and period.

Notifications use a durable outbox and unique task/channel/reminder key. Persist attempts, provider IDs and failures; retries reconcile calendar events. Proposed cadence: 14/7/3/1 days, due-day and overdue escalation, configurable and unapproved. Use America/New_York for business presentation; persist timestamps in UTC.

## Roles, retention and tests

Server-deny delegate payment initiation across every endpoint and worker path. Owner-only payment approval is the conservative default pending clarification. Existing Python actor-string policy is a reference, not authenticated authorization.

Retain evidence and receipts seven years under a reviewed start/hold policy; do not enable destructive deletion until that policy exists. Include backup restore evidence and secret/log redaction.

Add behavior tests for store/period completeness, duplicate imports, signed refunds, source reconciliation, recurrence boundaries, notification deduplication/failure, delegated payment denial, revocation, package-change invalidation and unknown outcomes. Do not invent tax rates, tolerances or exemptions to make fixtures pass.

## Prototype recurrence implementation

See [recurrence contract](../RECURRENCE.md). The local implementation supports period lengths of 1/3/12 months with explicit anchor, effective range, short-month policy and reviewed holiday calendar coverage. It retains one task per obligation/period with immutable rule provenance and rejects competing rule versions until explicit reconciliation exists. Full obligation versioning remains a future requirement; no statutory rule is preloaded.
