# PROJECT STATUS HANDOVER

> Main source of truth for project state. Update this file after every significant change.

---

## 1. Project Overview

- **Project name:** Varalica WebApp
- **Short description:** Mobile-first multiplayer web app for the Balkan party game “Varalica” (social deduction / word association).
- **Main purpose:** Let players create or join a room, receive secret roles/words, discuss, vote, and reveal who the Varalica (impostor) was.
- **Target users:** Friends/family playing together on phones or browsers in the same room session.
- **Current project phase:** Active development / production maintenance on `https://varalica.autolovac.space`.

---

## Permanent agent workflow

Every future **Cursor** or **Codex** session must:

**Before work:** read `PROJECT_STATUS_HANDOVER.md`, `AGENTS.md`, and `CURSOR_RULES.md`; check `git status`; understand scope and known issues.

**After meaningful changes:** update this file (including changelog), list changed files, tests run, deploy status, manual checks, and known issues. Do not commit/push/deploy unless the user explicitly asks.

---

## 2. Current Status

### What is currently implemented

- FastAPI backend with REST API and WebSocket room sync (`main.py`)
- Mobile-first dark frontend (`static/index.html`, `static/app.js`, `static/styles.css`)
- Room create/join by code or `/room/{code}` link
- Player names, optional emoji avatars, host role, kick/transfer-host
- Lobby settings: category, discussion duration, Varalica count (1 or 2 when >6 players)
- Full round flow: reveal → discussion → voting → results
- Private role/word screen, host change-word, confirm-seen flow
- Backend-authoritative discussion timer and overtime timer
- Live mode and Chat mode (`play_mode`: live / chat)
- Chat associations with player-list bubbles and overlay banners between monitor and player list
- Emoji reactions during discussion/overtime (Live current player + Chat association targets)
- Player-list reaction feedback shown next to **sender** (3s pulse)
- Multi-reaction support on active targets with duplicate repulse
- Majority/overtime voting logic, host manual reveal
- Nova runda, Resetuj sobu
- QR code and room link copy (client-side QR via `qrcode.min.js`)
- SQLite persistence for room snapshots and per-room used-word history (`storage.py`)
- Reconnect / presence handling (away, idle, tab-close, leave)
- Frontend cache busting via query string on static assets
- HTML no-cache headers on `/` and `/room/{room_code}` (inferred from latest commit on `master`)
- Word validation tooling (`validate_words.py`, 1000 curated words in `words.py`)

### What is partially implemented

- README may be behind current code in places (e.g. player limits, newer Chat/reaction features) — **TODO: confirm** and align README with code.
- Admin cleanup for old room snapshots — noted in README as not implemented.

### What is not implemented yet

- Automated admin cleanup for stale room snapshots (per README)
- Bot framework / AI services — not applicable to this project
- Formal automated test suite (unit/integration/e2e) — **TODO: confirm**

### What is currently deployed

- **Production domain:** `https://varalica.autolovac.space`
- **Server path:** `/opt/Varalica_webapp`
- **Service:** `varalica.service` (systemd)
- **App:** Uvicorn on port **8010**
- **Reverse proxy:** openresty/nginx-style headers observed in production — **needs manual verification** for exact config path on server
- **Deploy flow:** GitHub push → server `git pull` → `systemctl restart varalica`
- **`render.yaml`:** exists in repo, but **current confirmed production deployment is server/systemd**. Render usage: **needs manual verification** (possible old or alternative config).

### Current environment

- **Local:** `D:\Projects\Varalica_webapp` — Python + FastAPI/Uvicorn (typically port 8000 for dev), SQLite (`varalica.sqlite3` or `VARALICA_DB_PATH`)
- **Production:** `/opt/Varalica_webapp` — Uvicorn port 8010 behind openresty/nginx; SQLite path per server config — **needs manual verification**

### Current branch

- `master` (inferred from git at handover creation time)

---

## 3. Tech Stack

- **Backend:** Python 3, FastAPI, Uvicorn, Pydantic, asyncio timers, WebSockets
- **Frontend:** Vanilla HTML/CSS/JavaScript (no framework), mobile-first UI
- **Database:** SQLite (`varalica.sqlite3`) — room snapshots + used-word indexes
- **Bot framework:** N/A
- **AI/API services:** N/A
- **Infrastructure:** Linux server with systemd (`varalica.service`), openresty/nginx reverse proxy, Uvicorn on 8010
- **Deployment:** GitHub → server git pull → `systemctl restart varalica`. Repo also contains `render.yaml` — **not confirmed as current production**; needs manual verification.
- **Other tools:** `validate_words.py`, `varalica_hint_quality_guide_v2.py`, git

---

## 4. Important Files / Modules

### Main backend files

- `main.py` — app routes, game state, WebSocket, timers, reactions, voting
- `storage.py` — SQLite read/write for rooms and used words
- `words.py` — word/hint data (do not change casually)
- `validate_words.py` — word pool validation script

### Main frontend files

- `static/index.html` — shell, asset includes, cache-bust query strings
- `static/app.js` — client state, rendering, WebSocket, gameplay UI
- `static/styles.css` — layout, phases, reactions, overlay, reveal styling
- `static/vendor/qrcode.min.js` — QR generation
- `static/assets/` — reveal/smoke/ring SVG assets

### Database / migration files

- `varalica.sqlite3` — runtime DB (local; not committed)
- Schema created in `storage.py` (`rooms`, `room_used_words`) — no separate migration tool

### Config files

- `requirements.txt` — Python dependencies
- `render.yaml` — Render config in repo (production systemd deploy is confirmed; Render: needs manual verification)
- `.gitignore` — **TODO: confirm** contents
- `.env` — **TODO: confirm** if used locally (not inspected; do not commit secrets)

### Bot files

- N/A

### Admin files

- N/A (no dedicated admin UI found)

### Deployment files

- `render.yaml` (alternative/unverified deploy config)
- Server: `/etc/systemd/system/varalica.service` — **needs manual verification** on server

### Documentation files

- `README.md` — setup and manual test notes
- `PROJECT_STATUS_HANDOVER.md` — this file (main status source of truth)
- `AGENTS.md` — agent workflow (read before work, update handover after)
- `CURSOR_RULES.md` — Cursor-specific editing and reporting rules

---

## 5. Known Bugs / Issues

| Issue | Impact | Current suspected cause | Status |
|-------|--------|-------------------------|--------|
| README out of date vs code | Docs misleading for testers | README not updated after Chat/reactions/cache changes | Open — **TODO: confirm** |
| Old room snapshot cleanup missing | DB growth over time | No admin/cron cleanup (per README) | Known limitation |
| Manual gameplay regression risk | UX bugs after deploy | No automated E2E tests | Ongoing — manual test after releases |

_Add new rows here when bugs are found._

---

## 6. Risks / Warnings

- **Technical risks:** Single-process in-memory timers + WebSocket state; server restart relies on SQLite snapshot restore; concurrent edits mostly serialized through room lock patterns — **TODO: confirm** scaling limits.
- **GDPR/privacy risks:** Player names, avatars, room codes stored in SQLite; no formal privacy policy referenced in repo — **TODO: confirm**.
- **Deployment risks:** Forgetting to bump static asset `?v=` after frontend changes; forgetting `systemctl restart varalica` after server pull; stale HTML mitigated by no-cache headers on HTML routes.
- **Data risks:** SQLite on production server — backup/restore strategy **needs manual verification**.
- **Business/product risks:** Game rules complexity (Live/Chat, 1/2 Varalice, overtime) increases regression surface; requires disciplined manual QA.

---

## 7. Testing Status

### Last tests run

- **2026-05-31** (inferred from recent development session): `python -m py_compile main.py`, `python -X utf8 validate_words.py`, `node --check static/app.js` — passed during reaction/cache work.

### What passed

- Python compile (`main.py`, `words.py`, `validate_words.py`)
- Word validation script (1000 words, categories, hints)
- JS syntax check (`static/app.js`)

### What failed

- None recorded at handover creation.

### What still needs manual testing

- Full multiplayer flow (4+ players): reveal, discussion, Live next-player, Chat Pošalji/auto-next
- Emoji reactions: Live target, Chat target, sender player-list placement, multi-reaction, 3s expiry
- Voting, overtime, reveal sequence, Nova runda, Resetuj sobu
- Cache behavior after deploy: fresh HTML + new `?v=` assets
- Mobile reconnect / tab close / leave room
- Production smoke test on `https://varalica.autolovac.space` — **TODO: confirm**

---

## 8. Deployment Status

- **Is the project deployed:** Yes — `https://varalica.autolovac.space`
- **Server path:** `/opt/Varalica_webapp`
- **Domain:** `https://varalica.autolovac.space`
- **Service:** `varalica.service` (systemd)
- **App bind:** Uvicorn on port **8010**
- **Reverse proxy:** openresty/nginx (observed via response headers) — exact config: **needs manual verification**
- **SSL status:** HTTPS active on production domain — certificate renewal: **needs manual verification**
- **Docker status:** Not used for confirmed production workflow
- **Last deploy:** **needs manual verification** (latest local commit on `master` at doc update: no-cache HTML headers work)
- **Rollback notes:** Revert git on server (`git pull` previous commit) + `systemctl restart varalica` — **needs manual verification**
- **Render:** `render.yaml` in repo only; **not confirmed** as live production host

---

## 9. Cache / Version Notes

- **Frontend cache/version string:** `v=20260531_1` (verified in `static/index.html` for `styles.css`, `app.js`, `qrcode.min.js`)
- **Last frontend version update:** 2026-05-31 (inferred from version string)
- **Browser cache notes:**
  - Static assets: cache-busted via `?v=...` — **bump version on every frontend deploy**
  - HTML (`/`, `/room/{code}`): `Cache-Control: no-store, no-cache, must-revalidate, max-age=0`, `Pragma: no-cache`, `Expires: 0` via `html_page_response()` in `main.py`

---

## 10. Next Recommended Steps

1. Run full manual QA checklist (Live, Chat, reactions, voting, reveal, Nova runda, Resetuj sobu) on local and production.
2. Bump `?v=` in `static/index.html` whenever `app.js` or `styles.css` changes, then deploy.
3. Update `README.md` to match current features (Chat mode, reactions, player limits, cache/deploy notes).
4. Add automated smoke tests or CI (compile + `validate_words.py` + `node --check`) — **TODO: confirm** preference.
5. Plan/admin tooling for old room snapshot cleanup.

---

## 11. Changelog

### 2026-05-31 — Added permanent agent workflow documentation

- **Tool used:** Cursor
- **Changed files:**
  - `PROJECT_STATUS_HANDOVER.md`
  - `AGENTS.md`
  - `CURSOR_RULES.md`
- **Summary:**
  - Added permanent rules so Cursor/Codex sessions read the handover before work and update it after meaningful changes.
  - Corrected production deployment facts (systemd, server path, Uvicorn 8010); clarified Render is unverified.
- **What was not changed:**
  - No application code changed.
  - No backend/frontend logic changed.
  - No deployment performed.
- **Tests run:**
  - Not applicable; documentation-only change.
- **Deploy status:**
  - Not deployed.
- **Manual checks needed:**
  - User should review the documentation and commit it if correct.
- **Known issues:**
  - None for application runtime.
- **Notes:**
  - Future agents must keep `PROJECT_STATUS_HANDOVER.md` updated.

### 2026-05-31 — Initial handover file created

- **Tool used:** Cursor
- **Changed files:**
  - `PROJECT_STATUS_HANDOVER.md`
- **Summary:**
  - Created the main project handover/status documentation file.
- **What was not changed:**
  - No application code was changed.
  - No environment variables were changed.
  - No deployment was performed.
- **Tests run:**
  - Not applicable; documentation-only change.
- **Deploy status:**
  - Not deployed.
- **Manual checks needed:**
  - User should fill in deploy confirmation, SSL/nginx details, privacy/GDPR notes, and validate README vs code.
- **Known issues:**
  - Current project status may still need manual completion (sections marked **TODO: confirm**).
- **Notes:**
  - This file should be updated after every significant change.

---

## Appendix: Quick local run

```powershell
cd D:\Projects\Varalica_webapp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open: `http://localhost:8000`
