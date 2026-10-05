# Single-host internal pilot deployment

Updated 5 October 2026. The repository includes a deployable container layout; it has **not** been provisioned in a Microsoft tenant or on a host. Use synthetic data for first boot. The existing SQLite database requires a local persistent disk and a single host; do not use Azure Files/App Service mounts for SQLite or scale this Compose setup across hosts. App and worker share one local Docker volume. Secrets and business records never belong in GitHub.

## Prerequisites

- A private Linux host with Docker Engine and Compose, persistent encrypted disk, restricted administration and a backup destination separate from the live volume. Budget and host selection require owner review.
- A DNS name for the host, with inbound 80/443 directed to Caddy. The app container's port 8080 is exposed only inside Compose. Caddy obtains TLS for the domain.
- An Entra workforce tenant and a **single-tenant Web application** registration with redirect URI `https://YOUR-DOMAIN/auth/callback`. Register delegated Microsoft Graph User.Read, Mail.Send and Calendars.ReadWrite; grant appropriate consent. Do not add broad application permissions. Require MFA through the tenant's Conditional Access policy.
- The owner's immutable Entra object ID (`oid`), tenant ID, application client ID and server-side client secret; add delegate object IDs only when individually approved. The owner must have a mailbox and access to the selected dedicated calendar. Keep the secret and generated Fernet key in the host's private `.env` or a secret manager.

## Configure and boot

1. Clone the protected main branch on the host. Copy `.env.example` to `.env`, fill the domain, origin, tenant/client/owner IDs, secret and a generated Fernet key. Keep `COMPLIED_LIVE_SEND=0`. Set permissions so only the deployment operator can read `.env`; never paste its contents into chat, CI or tickets.
2. Point DNS to the host and verify ports 80/443. Run `docker compose config`, then `docker compose up --build -d app proxy`.
3. Visit the configured HTTPS origin. Microsoft sign-in accepts only the configured owner and approved delegates; local password sign-in is disabled in Microsoft mode. Check that owner-only **Connect Microsoft reminders** requests Graph consent, then select a calendar and recipient. Test an internal synthetic due item and confirm the event/mail in Microsoft 365 before enabling worker delivery.
4. To enable due queued reminders after the controlled test, change `COMPLIED_LIVE_SEND=1` in the host environment and run `docker compose --profile live-reminders up -d worker`. The worker claims one due request each interval. Mail 202 means accepted for processing, not delivered. Graph errors or interrupted operations require explicit reconciliation; they never retry blindly.
5. For a controlled stop, run `docker compose stop worker` and set `COMPLIED_LIVE_SEND=0`. Disconnecting the owner account removes the local encrypted delegated token cache. Rotate the Entra client secret and cache key under an operator plan; rotating the cache key without reconnecting makes existing caches unreadable.

## Data and recovery

Source snapshots, user sessions, audit and encrypted delegated tokens share `complied-data`. Protect that volume, backups and the host's environment. Mount a separate encrypted off-host destination at `/backups`, then run `docker compose run --rm -v /private/backup-mount:/backups app python scripts/backup_sqlite.py --db /data/complied.sqlite3 --output-dir /backups` from an authorized context; replace `/private/backup-mount` with the real mount and grant the container user write access. The script uses SQLite's online backup API, verifies integrity and writes owner-readable files. Test restore on an isolated host before real records; stop app and worker before replacing a live database. Maintain off-host encrypted copies and verify retention/holds and access rules for the required seven years. The project does not yet automate retention or off-host transfer.

No automatic filing/payment, actual PostalMate export mapping or tax-return calculation is included. Do not load real records until authentication, backup restore, recipient/calendar and reviewed import mapping have passed a controlled pilot.

Sources: [MSAL confidential web apps](https://learn.microsoft.com/en-us/entra/msal/python/getting-started/client-applications), [Microsoft authorization code flow](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow), [Graph calendar permissions](https://learn.microsoft.com/en-us/graph/api/calendar-post-events?view=graph-rest-1.0), [Caddy HTTPS](https://caddyserver.com/docs/quick-starts/https), [Azure SQLite mount guidance](https://learn.microsoft.com/en-us/azure/app-service/configure-connect-to-azure-storage?pivots=container-linux&tabs=portal).
