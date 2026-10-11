# Management interface — 10 October 2026

## Shared design system

`public/styles.css` is the common visual source for the Vercel preview and the authenticated Python shell. It defines the navy/green workspace navigation, typography, spacing, semantic badges, cards, tables, forms, dialogs, focus indicators and responsive layouts. Docker copies this asset so Python can embed it under its existing CSP. The runtime uses only its implemented server routes; preview-only screens do not imply new backend endpoints.

The management preview includes overview, monthly upload/reconcile/review, requirement register, calendar, review queue, evidence, integrations and settings. All money comes from the public October CSV fixtures. Metrics describe source work and unresolved requirements; no compliance score, verified tax rate or statutory date is fabricated.

## Interaction contract

- Location selection scopes dashboard and reconciliation figures; both stores remain in the package being reviewed.
- Requirement search and type filters work locally; detail dialogs identify missing authority and deadline review.
- Detail panels use native dialogs with focus return and Escape dismissal. Mobile navigation uses an inert background, keyboard containment and Escape dismissal.
- Sample CSV downloads match fixture bytes and hashes. Packet export is explicitly synthetic and always has `return_ready: false`.
- Review notes produce only an escaped, unsaved summary. No upload, account connection, persistent review, reminder, filing or payment is performed by the static preview.
- Unknown deadlines remain unverified. The calendar is an empty planning view until authoritative date rules are reviewed.

## Verification

Run existing application checks and the browser suite:

```sh
python3 scripts/check_repository.py
python3 -m unittest discover -s tests -v
node --check public/app.js
npm install --prefix /tmp/complied-ui-deps --no-save playwright@1.58.2
/tmp/complied-ui-deps/node_modules/.bin/playwright install chromium
NODE_PATH=/tmp/complied-ui-deps/node_modules node scripts/check_preview.cjs
```

The suite checks navigation, exact scoped totals, requirement filtering, detail dialogs, fixture-download hashes, unsaved decision escaping, calendar geometry, sample packet boundaries, mobile navigation and page overflow. Set `COMPLIED_UI_OUTPUT` to a scratch directory for desktop/mobile screenshots. It launches its own loopback static server and makes no live connector requests.

The Python HTTP and workflow tests exercise authenticated editing, two-store upload, reconciliation, source review, revocation and separate approval safeguards. UI styling changes do not establish production readiness. The Vercel Git integration publishes the preview after merge; preserve its existing authentication policy.
