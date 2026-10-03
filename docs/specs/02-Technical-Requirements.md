# Compliance Automation — Technical Requirements

Version: 0.1-R | Date: 3 October 2026 | Status: Reconstructed draft

Reconstructed from available conversation scope, not recovered verbatim. Requirements below are proposed and testable. Virginia rules, forms, deadlines, and submission capabilities have not been verified in this document.

## Functional requirements and acceptance

| ID | Requirement | Acceptance evidence |
|---|---|---|
| TR-01 | Store entity, store, jurisdiction, registration, timezone, and responsible owner independently. | A pilot task resolves to one unambiguous scope. |
| TR-02 | Maintain an obligation register with source reference, applicability rationale, effective date, review status, and version. | Unreviewed discovery cannot activate an obligation. |
| TR-03 | Generate recurring tasks with explicit period boundaries, due-date rules, and exception handling. | Approved fixtures generate expected periods and dates without duplicates. |
| TR-04 | Import authorized QuickBooks Online records with source identifiers and capture time. | A prepared total traces to the exact imported snapshot. |
| TR-05 | Map accounting records to stores using an owner-confirmed mapping. | Unmapped or ambiguous records create blocking exceptions. |
| TR-06 | Link authorized Dropbox records by file identifier and version where supported, with hashes for captured evidence. | Reviewers can retrieve the record used during preparation. |
| TR-07 | Calculate amounts with decimal arithmetic and versioned, professionally reviewed rules. | Approved fixtures match expected totals, adjustments, and rounding. |
| TR-08 | Reconcile preparation totals to source accounting reports and disclose differences. | Unresolved material differences block readiness. |
| TR-09 | Bind filing approval to entity, jurisdiction, period, destination, package version, and amount. | Any material change invalidates the approval. |
| TR-10 | Require separate payment approval bound to amount, recipient, funding reference, and period. | Filing approval alone cannot execute payment. |
| TR-11 | Gate filing and payment adapters behind verified capability and explicit enablement. | Disabled adapters cannot issue external writes. |
| TR-12 | Persist operation identifiers and deduplicate external actions. | Repeated requests cannot knowingly create duplicate filings or payments. |
| TR-13 | Treat ambiguous external responses as unknown outcomes requiring reconciliation. | Timeout after submission does not trigger blind resubmission. |
| TR-14 | Record external acknowledgment separately from settlement or final acceptance. | A sent request cannot be displayed as completed without appropriate confirmation. |
| TR-15 | Provide manual handoff if the verified portal route lacks a suitable supported integration. | Operator receives a versioned package and can attach receipt evidence. |
| TR-16 | Maintain an append-only action history for calculations, approvals, submissions, payments, and overrides. | Sample actions resolve to actor, timestamp, scope, and version. |

## Access and data protection

Use individual accounts, MFA where supported, and role-based permissions. Distinguish preparation, review, filing approval, payment approval, and administration. Enforce authorization server-side. Store integration credentials in a secret store, encrypt sensitive data in transit and at rest, redact tokens and financial account details from logs, and restrict connector access to approved resources. Development agents use synthetic or redacted fixtures by default; production-data access requires an explicit reviewed route.

## Reliability and recovery

Persist job state before external execution. Use bounded retries for safe reads and confirmed retryable actions. Failed notifications and stale integrations create visible exceptions. Provide backup and restore procedures, operator recovery instructions, and reconciliation queues. Recovery objectives, retention periods, and notification channels are open decisions.

## Suggested workflow states

Draft → Preparing → Needs information / Review ready → Approved → Submission pending → Accepted / Rejected / Outcome unknown → Reconciled.

Payment has its own approval and execution states. Completion depends on the obligation's defined evidence requirements, not merely worker success.

## Integration discovery gates

Confirm QuickBooks company access, available records/reports, store mapping, and API constraints. Confirm Dropbox account scope, folder permissions, and version access. Confirm Virginia registration, delegated authority, supported submission route, authentication, receipts, payment capabilities, and manual fallback before enabling writes. Do not assume an API exists.

## Release verification

Demonstrate unauthorized-access denial, stale approval invalidation, missing-data blocking, correct decimal calculations, period boundaries, token expiration recovery, duplicate prevention, unknown-outcome reconciliation, and restoration of a sample package. Validate filing/payment in a suitable test environment or controlled manual workflow before production activation.
