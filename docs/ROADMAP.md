# Project Complied — Delivery Plan

Updated: 5 October 2026 | Capacity: 40 owner hours/month

## Milestones and completion gates

| Milestone | Work | Acceptance |
|---|---|---|
| M1: Deadline prototype | Stack ADR, local app instructions, schema/migrations, synthetic seeds, location/entity facts, obligation register, dashboard | Runnable locally; upcoming/overdue/unresolved states; verified rules only generate deadlines; no live secrets |
| M2: Reminder reliability | M365 adapter boundary, durable outbox, preferences, event deduplication and failure history | Synthetic retry/failure tests pass; authorized controlled delivery before live use |
| M3: Monthly preparation | Inspect redacted reports, PostalMate imports per store, hashes, mappings, decimal reconciliation, combined package | Both stores/one period; totals traceable; missing data and unexplained differences block readiness |
| M4: Review/manual handoff | Authenticated delegation, immutable approvals, separate payment gate, audit, receipt upload | Delegate cannot initiate payment; changed/revoked approvals denied; filing/payment evidence separate |
| M5: Internal pilot | Rehearse one monthly package and owner dashboard; measure effort; backup restore | Owner confirms reconciled package and usability; October/November cycle only if deadline and inputs verified |
| Later | Optional QBO/Dropbox connectors, Google, verified portal adapters | Separate capability, access, security and operational review |

M1 is the next implementation task. M2/M3 can progress independently after M1; M4 precedes real filing workflow use. Proposed first 40-hour allocation: 4h stack/schema decisions, 16h register/dashboard, 8h recurrence tests, 8h import/sample design, 4h owner validation. This is a capacity allocation, not a guarantee; re-estimate after scaffold and sample inspection.

## Inputs and blockers

Owner confirms Ivy is Charlottesville City; Pantops is Albemarle County. Registration/location reporting remains to verify. Obtain redacted monthly reports from both PostalMate databases, license/state notices, verified sales-tax form/frequency/deadline and portal readiness. Do not delay synthetic dashboard work for these inputs.

Physical goods taxable and tax collected/remitted per owner; handling immaterial per owner. Immateriality does not establish an exemption or tolerance. Keep amounts and classification exceptions visible.

## Cost and release plan

Proposed incremental allowance $100/month, cap $150/month pending approval and current vendor quotes; no paid development. Existing subscriptions excluded. Select hosting after ADR and compare actual database, backup, notification and tool costs.

Each milestone uses a focused PR, appropriate behavior tests, repository checks, CodeQL and Gitleaks. Record results at the exact head. No bot auto-merge or auto-approval. Current security settings remain in force. Do not treat old 12–16 week/$5k–$15k estimates as commitments.

November target is deadline tracking and assisted preparation; complete automation is not promised. After the first cycle, review discrepancies and operating effort; two consecutive reconciled cycles establish the later reliability target.
