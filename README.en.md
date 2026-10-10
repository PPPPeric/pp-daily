# pp Daily

[中文](README.md) | [English](README.en.md)

[![CI](https://github.com/PPPPeric/pp-daily/actions/workflows/ci.yml/badge.svg)](https://github.com/PPPPeric/pp-daily/actions/workflows/ci.yml)

A personal daily check-in PWA with a warm ivory and forest-green interface. Develop on Windows, host on a Mac mini, and use it privately on your iPhone through Tailscale. No application account or login is required.

## Architecture

```text
iPhone 15 PWA (Vue 3 + TypeScript)
  ├─ IndexedDB: local snapshot and pending completions
  └─ Tailscale private HTTPS
       └─ Mac mini: FastAPI at 127.0.0.1:8000
            ├─ frontend production files
            └─ SQLite database and backups
```

The frontend and API share one origin. Project/day uniqueness makes uploads idempotent. Restore changes the dataset generation so stale clients cannot silently upload old records into restored data.

## Device support

The first release targets **iPhone 15 with iOS 17+**, using Safari or a Home Screen PWA, primarily in portrait orientation. Development layout checks use a 393 × 852 CSS-pixel viewport and a basic landscape check. The layout remains responsive for Windows previews; other phone models have no dedicated compatibility guarantee. There is no device lock or fixed physical-pixel rendering.

The UI accounts for safe areas, dynamic viewport height, landscape side insets, and touch controls of at least 44 CSS pixels. Browser layout checks do not establish real-device compatibility: follow the [iPhone 15 acceptance checklist](docs/iphone15.md). **The application UI is Chinese; the project documentation is bilingual.**

<img src="docs/images/iphone15-today.png" alt="Today screen with sample data" width="300">

## Features and rules

- **Today:** complete each project once per day. Doing nothing means incomplete. No cancellation, backdating, duration tracking, pause, or resume.
- **Calendar:** a read-only monthly calendar for one selected project. Future dates, dates before creation, and dates after archival are not applicable.
- **Statistics:** total completed days, completed days this month, current streak, and longest streak. No completion rates or trend charts.
- **Management:** create, rename, choose a color, reorder, or permanently archive projects while preserving history. Management requires a connection to the server.
- **Offline:** previously loaded pages and check-ins remain available through a Service Worker and IndexedDB. Pending records synchronize on launch, foreground return, connectivity restoration, and a 30-second foreground retry.
- **Backup:** export a complete JSON snapshot, including this device's unsynced records. Restore replaces the server dataset and automatically saves a pre-restore backup.

All dates use `Asia/Shanghai`. Before today's completion, the current streak is calculated through yesterday. Archived projects use their archive date as the streak endpoint. Valid offline records from the archive date can still synchronize; later dates cannot be completed. Background synchronization while the app is closed is not promised.

## Windows development

Requirements: Python 3.12+ and Node.js 22.12+.

```powershell
git clone https://github.com/PPPPeric/pp-daily.git
cd pp-daily
.\scripts\dev.ps1
```

Open [the local application](http://127.0.0.1:8000). The script installs dependencies, builds the frontend, and starts FastAPI. It prefers the current Codex bundled Python when available, otherwise `py` or `python`. To select another interpreter:

```powershell
.\scripts\dev.ps1 -PythonExecutable 'C:\Python312\python.exe'
```

For hot reload, keep the backend running and open a second terminal:

```powershell
cd frontend
npm run dev
```

Vite at `http://127.0.0.1:5173` proxies `/api` to FastAPI. Development mode does not register the Service Worker; use the production build served by FastAPI to test offline pages. Initial installation needs connectivity.

## Tests

From the repository root on Windows:

```powershell
.venv\Scripts\python.exe -m pytest backend\tests -q
cd frontend
npm ci
npm test
npm run build
```

On macOS/Linux, use `.venv/bin/python` instead. Tests cover date boundaries, streaks, offline persistence, duplicate uploads, archive rules, restore validation, and generation conflicts. `npm run build` includes TypeScript checks. The CI workflow runs on pushes to `main`, pull requests, and manual dispatch. It does not deploy the application.

Frontend dependencies are locked in `package-lock.json`; direct Python dependencies are pinned in `backend/requirements.txt`. Do not copy Windows `.venv` or `node_modules` to the Mac.

## Mac mini deployment

1. Install Python 3.12+, Node.js 22.12+, and Tailscale. Clone the repository into a permanent directory, such as `~/Applications/pp-daily`.
2. Connect the Mac and iPhone to your Tailscale network and restrict service access to your own devices through tailnet access controls.
3. From the project root, run:

   ```bash
   bash scripts/install-macos.sh
   ```

   The script builds the frontend and installs two user-level LaunchAgents: an automatically restarted server and a daily SQLite backup at 03:00, retaining the latest 30 backups. They run after the macOS user signs in, including after a reboot.

4. Configure private HTTPS:

   ```bash
   tailscale serve --bg http://127.0.0.1:8000
   tailscale serve status
   ```

   Follow Tailscale's HTTPS setup prompts and use the fixed `https://machine.tailnet.ts.net` address shown by the command. Use Serve, not Funnel or public router port forwarding. See [Tailscale Serve documentation](https://tailscale.com/docs/reference/tailscale-cli/serve).

5. Keep the Mac awake and connected. Inspect `data/logs/` and check:

   ```bash
   curl http://127.0.0.1:8000/api/state
   ```

6. Connect Tailscale on the iPhone, open the private HTTPS address in Safari, and choose Share → Add to Home Screen. The default name is `pp Daily`, with a forest-green double-p icon.

Public GitHub source code is separate from the private running service. The backend has no application authentication and must remain behind private network access controls. GitHub Pages cannot provide this application's FastAPI/SQLite backend.

## Updating

Create a backup first, update the source in the same directory, and rerun `scripts/install-macos.sh`. Preserve `data/` and the database. Once a PWA update is downloaded, close all old app windows and reopen to activate the new Service Worker. Future database schema changes require a backup and a migration.

## Backup and restore

Manual consistent backup, safe while the server is running:

```bash
.venv/bin/python scripts/backup.py \
  --database data/pp-daily.sqlite3 \
  --destination data/backups
```

The script uses SQLite's backup API and checks integrity. Copy at least one backup outside the Mac. The application does not automatically synchronize backups to iCloud or another cloud drive.

For normal restoration, open Management → Restore backup, select a JSON export, and confirm replacement. The server validates the version, project references, dates, and uniqueness before replacing the dataset in one transaction. Pre-restore files are saved as `data/backups/before-restore-*.json` and are not removed by the 30-file daily-backup retention policy.

For machine recovery, stop the server, replace `data/pp-daily.sqlite3` with a consistent SQLite backup, and restart. Then export and restore JSON once through Management to create a new dataset generation. On every client, export unsynced local data before choosing Reload server data.

## Sync and limitations

Completions are saved locally before being displayed as complete. Failed uploads leave the queue intact. Web Locks serialize same-origin writes where supported; SQLite provides final server-side uniqueness. Offline records keep their original operation date. The server checks that the date matches the submitted timestamp, but cannot prove that an unauthenticated offline client's clock is truthful.

A restored dataset has a new generation. Stale clients stop uploading and ask the user to export a local backup before reloading the server copy. Restoration explicitly replaces the entire dataset; historical backups are not automatically merged.

Initial loading, new-device recovery, and project management require the server. Clearing browser data can remove unsynced records. Keep the device clock correct, check the sync indicator, and export backups regularly. Mac mini deployment and actual iPhone behavior require the [real-device checklist](docs/iphone15.md); they have not been verified merely by local browser tests.

## Repository structure and contributing

```text
backend/      FastAPI, SQLite, API tests
frontend/     Vue 3, TypeScript, IndexedDB, PWA, frontend tests
scripts/      Windows development, Mac installation, backup, icon generation
docs/         Plans, verification, device checklist, sample screenshots
.github/      CI and issue / pull request templates
```

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md). Verification details are recorded in [VERIFICATION.md](docs/VERIFICATION.md) in Chinese. Credentials, personal records, databases, backups, build outputs, and installed dependencies are excluded from Git.

## License

The owner has not selected an open-source license. Public visibility enables viewing and GitHub forking under GitHub's terms; no MIT or other open-source license is implied. See [GitHub's licensing guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository).
