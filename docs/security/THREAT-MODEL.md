# Initial threat model

| Threat | Required control | Current coverage |
|---|---|---|
| Wrong entity/period/destination | Approval binds all package fields | Reference policy and tests |
| Changed approved inputs | Immutable package/version binding | Reference policy and tests; storage pending |
| Filing approval reused for payment | Separate purpose and approval | Reference policy and tests |
| Duplicate action after timeout | Unknown outcome requires reconciliation, durable idempotency | Deny gate tested; operation ledger pending |
| Credential leakage | Secret store, redaction, narrow scope | CI scan configured; connectors pending |
| Malicious PR/action | Read-only CI, SHA pins, owner review | Workflow files; server protection pending verification |
| AI changes tax treatment | Reviewed deterministic rules | Requirement only; calculation engine pending |

The reference policy does not authenticate actors, persist approval records, or prevent forged in-memory objects. A server-side trusted approval service, durable ledger, and transaction-safe execution gate are required before runtime use.
