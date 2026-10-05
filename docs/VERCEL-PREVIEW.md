# Vercel visual preview

The Vercel project serves `public/index.html` as a **static synthetic visual preview** of the owner dashboard and upload → reconcile → review screens. It uses the same palette and workflow labels as the Python prototype, with illustrative amounts from `fixtures/synthetic/`. Its navigation is client-side; uploads, decisions, reminders, and payments are disabled. Do not enter real records here. This preview has no database, sessions, or Microsoft access.

`vercel.json` sets the static output directory to `public`. Vercel's Git integration deploys the merged main branch. The Vercel project currently has Vercel Authentication enabled; preserve that access policy. A green Vercel deployment means only that the static preview was published. It does not mean the Python app is hosted.

The authenticated Python application requires its persistent SQLite host, HTTPS, Entra registration, backup/restore checks and separately enabled reminder worker as documented in [Deployment](DEPLOYMENT.md). Its working import and review screens are available on the configured host, not on this static Vercel preview. Do not route the Python application's auth or data writes through a stateless Vercel function with ephemeral SQLite storage.
