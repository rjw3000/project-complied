# Microsoft reminder workflow

5 October 2026. Local queue/preview and an opt-in Microsoft web sign-in and delegated worker are implemented. Tenant credentials, host and live delivery remain unprovisioned.

## Use

Sign in as owner and open Microsoft reminders. Configure reminder email and dedicated calendar ID. Queue an email reminder for a chosen number of days before a verified task, or one calendar event. Delegates may queue reminders but cannot change destinations. Unknown, completed or stale task revisions are rejected.

Email scheduling is 09:00 America/New_York on the configured date. Calendar events are all-day deadlines and can be queued immediately. The UI displays request previews, status, attempts and reconciliation flags. Preview CLI:

```sh
PYTHONPATH=src python3 -m complied.reminders
```

This command never sends.

## Persistence and failure handling

Outbox identity binds task, obligation revision, channel, email offset and destination version. Repeated requests produce one row. Calendar offsets normalize to a single event identity. Dispatch claims one row in an immediate transaction before an external request; concurrent workers do not claim the same row.

Accepted mail is recorded as accepted, not delivered. Calendar creation requires a returned event ID. Timeout, unexpected response and interrupted attempts become unknown and never automatically retry. Explicit crash recovery marks inflight attempts unknown. Known failure remains visible; automatic retry is not configured.

Queued stale work cancels before sending. Previously created events whose task/destination changes are flagged for reconciliation; event update/deletion and review-driven reconciliation remain future work. A narrow edit-during-send race cannot recall a request already in flight.

## Graph adapter and setup gate

MicrosoftGraphAdapter accepts an injected HTTP post transport and translates official v1.0 request/response contracts. No credentials are accepted by the UI, saved in the database or exposed in request previews. GraphHTTPTransport uses a fixed commercial Graph HTTPS endpoint, denies redirects and restricts supported paths. It is disabled by default. No OAuth consent or live credentials have been provisioned.

Before live use, configure an Entra application, supported delegated sign-in/token storage and consent, select the dedicated calendar and confirm the recipient. User-calendar creation requires Calendars.ReadWrite; mail requires Mail.Send. Choose the supported delegated flow after runtime hosting is selected. Do not use broad application permissions by default.

Official sources consulted 5 October 2026:
https://learn.microsoft.com/en-us/graph/api/calendar-post-events?view=graph-rest-1.0
https://learn.microsoft.com/en-us/graph/api/user-sendmail?view=graph-rest-1.0

Calendar payload includes transactionId for duplicate protection. Mail 202 is acceptance only. Tests use synthetic transports; no emails or events are sent. Live completion requires controlled account testing, OAuth provisioning/token refresh, scheduler deployment and reconciliation UI.

## Explicit operator execution

After Entra app setup and recipient/calendar confirmation, a local authorized operator may supply a delegated token at a hidden prompt. No token is stored. This sends at most one due request:

```sh
PYTHONPATH=src python3 -m complied.microsoft --execute --user owner-demo
```

Without --execute, the command previews only. Supplying a delegated token is not automated OAuth provisioning. Do not put tokens in arguments, Git, chat or CI. No background sender or token refresh is configured. Interrupted inflight records require explicit recovery and reconciliation before any resend.

## Microsoft-connected mode

A single-tenant MSAL authorization-code flow signs in only configured owner/delegate object IDs. Owner consent separately connects Mail.Send and Calendars.ReadWrite to a dedicated calendar and recipient. The delegated token cache is encrypted at rest with a host-owned Fernet key; access tokens never appear in the UI or Git. Owner disconnect deletes the cache. Sessions expire after one hour, and changes to the allowed object IDs invalidate existing sessions. The scheduled worker is a separate Compose profile and refuses to run unless `COMPLIED_LIVE_SEND=1`. It obtains a refreshed owner token before claiming each due outbox item. See [single-host deployment](DEPLOYMENT.md). Live tenant/browser delivery and recovery still require controlled validation.
