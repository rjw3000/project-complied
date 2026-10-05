# Authenticated local editing and review

5 October 2026. Prototype-only local accounts; production Microsoft identity remains pending.

Create an owner or delegate via the local getpass CLI; no password is written to source or passed on the command line. Passwords use salted scrypt. Sessions last one hour, store only hashed bearer tokens, and are rejected immediately if the user is disabled. Logout revokes the session. Five failed account logins cause a five-minute lockout.

The loopback UI requires sign-in, checks Host and Origin, requires session-bound CSRF tokens for mutations, limits form bodies and uses HttpOnly/SameSite cookies. Loopback HTTP intentionally omits Secure; production requires HTTPS, secure cookies and a reviewed identity provider. No public deployment is configured.

Both owner and owner-provisioned delegate can create, edit and review requirements. Delegates are denied payment initiation in the authorization policy. No payment execution endpoint exists.

Edits reset applicability to unresolved and increment an optimistic revision. Review requires source/rationale and an applicable/not-applicable decision; actor and change details are append-only audit events. Existing schedules are bound to the prior obligation revision and remain unresolved after a new review. Old rules cannot generate additional tasks. Stale form saves fail.

Immutable prior tasks are not automatically rewritten. Explicit schedule reconciliation remains the next review workflow; completion of stale tasks is denied. Review metadata does not imply professional signoff.

User management is a trusted local CLI. Live business data and Microsoft connections are outside this prototype. The authentication and HTTP tests validate expiry, logout/revocation, role denial, lockout, CSRF/origin checks, conflicting edits and schedule invalidation.
