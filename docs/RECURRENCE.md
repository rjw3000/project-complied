# Reviewed recurring deadline contract

Implemented for the synthetic local prototype, 5 October 2026.

A rule records obligation ID, source, reviewer, review date and immutable definition. Its SHA-256 identity covers all of those fields. Database triggers reject rule modification/deletion. Review identities are local metadata, not authenticated professional signoff.

## Definition

| Field | Meaning |
|---|---|
| anchor | First day of a month; recurrence alignment starts here |
| period_months | 1, 3 or 12; supports fiscal anchors |
| due_month_offset | Additional months after the end of the period, 0 through 12 |
| due_day | Day of target month, 1 through 31 |
| short_month | reject or last_day; never silently infer end-of-month treatment |
| roll | none or next_business_day; neither is an asserted jurisdiction rule |
| holidays | Explicit ISO date list for the supplied reviewed calendar |
| calendar_start / calendar_end | Inclusive coverage for next_business_day; null for none |
| effective_start / effective_end | Inclusive range of eligible period-start months |

For a monthly period beginning October 1, zero additional offset means a due date in November. A quarterly period beginning October 1 ends before January 1; zero offset means January. An annual period beginning January 1 uses January of the next year. These are engine semantics, not business filing instructions.

Weekend/holiday adjustment fails outside supplied calendar coverage. The caller must verify completeness and authority of that calendar before any real use. Empty holiday lists are allowed only as an explicit input; no holiday knowledge is embedded.

## Generation and changes

Generation accepts a canonical YYYY-MM first period and 1–120 periods. Unreviewed or inapplicable obligations are rejected. Rule effective bounds and anchor alignment apply to every generated period.

A single immediate transaction makes the batch atomic. Exact reruns return the existing task IDs. Any existing task with a different date, different rule version or missing rule provenance causes a conflict and rolls back the batch. Completed tasks and their evidence are preserved. New rules do not automatically replace old tasks; reconciliation UI and audit for approved replacement remain future work.

The current prototype keeps one task per obligation and period and records immutable rule provenance in task_rules. This deliberately blocks concurrent rule versions for the same period. Full obligation versioning remains pending.

## Migration and validation

Additive schema version 2 preserves v1 tasks, including unresolved and completed rows. Old manual demo tasks have no rule association. Tests cover leap years, year boundaries, fiscal alignment, short months, weekends/holidays, calendar coverage, effective bounds, rule immutability, repeat generation, review revocation and atomic rollback.

Use the README commands for the synthetic demo. The UI remains read-only; no background scheduler or external reminders are connected.
