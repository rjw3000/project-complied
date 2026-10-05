# Schedule preview and confirmation

5 October 2026. Authenticated local prototype; no statutory dates are preconfigured.

Use **Review schedules** after reviewing applicability. Enter a source-backed monthly/quarterly/annual rule and a bounded period range. Preview shows old/proposed dates and create, keep, replace or blocked actions. Nothing changes operationally until confirmation. Unused immutable rule definitions may remain as review provenance.

Confirmation is bound to the reviewing user, expires after 15 minutes and can be used once. Current obligation revision, task state and reminder states must exactly match the preview. The entire batch is atomic.

Completed tasks can be kept unchanged but cannot be replaced. Inflight/unknown external attempts and created calendar events block replacement until separate reconciliation is implemented. No external event is changed by this screen.

Approved replacements preserve before/after context and actor in append-only audit, increment task schedule revision, and cancel queued reminders. Reminder identity and dispatch checks now include schedule revision so an old request cannot serve a new schedule. New reminders must be explicitly queued after review.

Tests cover stale forms, expiry, actor/session revocation, completed-task preservation, atomic rollback, send/confirmation races, reminder identity and the HTTP preview/confirmation flow. Schema v5 is additive.
