# ARCHITECTURE.md — Varalica WebApp

## 1. Project Summary

- **What the app is:** Varalica WebApp is a mobile-first multiplayer web app for the Balkan party game "Varalica", a social deduction / word association game.
- **Main purpose:** The app lets players create or join a room, receive private roles and words, discuss, vote, and reveal who the Varalica was.
- **Target users:** Friends and family playing together on phones or browsers in the same room session.
- **Production domain:** `https://varalica.autolovac.space`
- **Local path:** `D:\Projects\Varalica_webapp`
- **Production path:** `/opt/Varalica_webapp`
- **Current production service:** `varalica.service` running Uvicorn behind an openresty/nginx-style reverse proxy.

## 2. Tech Stack

- **Backend:** Python 3, FastAPI, Uvicorn, Pydantic, asyncio timers, WebSockets.
- **Frontend:** Vanilla HTML, CSS, and JavaScript; mobile-first dark UI.
- **Database:** SQLite, with runtime database files such as `varalica.sqlite3`.
- **Realtime communication:** WebSocket room sync between browser clients and the FastAPI backend.
- **Deployment:** Confirmed production workflow is GitHub push, server `git pull` in `/opt/Varalica_webapp`, then `systemctl restart varalica`; Render config exists but live Render usage needs manual verification.
- **Scripts/tools:** `validate_words.py`, `varalica_hint_quality_guide_v2.py`, and project scripts under `scripts/`; Python compile and word validation are the known verification tools.

## 3. Runtime Architecture

1. A browser opens `/` or `/room/{code}` and receives the static app shell.
2. A player creates a room or joins an existing room by code or invite link.
3. FastAPI handles REST actions such as room creation, join, settings changes, card confirmation, voting, reactions, new round, and reset.
4. Each connected player uses a WebSocket for live room-state updates.
5. The backend owns the authoritative room state, game state, timers, roles, word selection, voting, overtime, and result flow.
6. SQLite persists active room snapshots and per-room used-word history through `storage.py`.
7. The frontend receives public room state plus viewer-specific private data and renders the current phase.

## 4. Main Files and Responsibilities

| File/folder | Responsibility | Read frequency for agents | Edit risk |
|---|---|---:|---|
| `main.py` | FastAPI app, REST routes, WebSockets, room/game state, timers, reactions, voting, reveal flow. | High | High |
| `storage.py` | SQLite persistence for rooms and used-word history. | Medium | High |
| `words.py` | Imported/curated Serbian/Croatian word and hint database. | Low unless word task | High |
| `validate_words.py` | Word database validation. | Medium for word tasks | Medium |
| `scripts/` | Utility/import/helper scripts; exact contents depend on local task history. | As relevant | Medium |
| `static/index.html` | Static app shell, root DOM nodes, vendor include, cache-busted JS/CSS references. | High for frontend tasks | Medium |
| `static/app.js` | Client state, rendering, REST calls, WebSocket handling, gameplay UI, animations. | High for frontend tasks | High |
| `static/styles.css` | Visual layout, mobile styling, phase screens, overlays, reveal/result styling. | High for UI tasks | Medium |
| `static/vendor/qrcode.min.js` | Vendor QR generation library. | Rare | High; do not edit unless explicitly required |
| `static/assets/` | App images and visual assets for landing, cards, reveal, result, and related UI. | As relevant | Medium to high; avoid unintended binary changes |
| `requirements.txt` | Python runtime dependencies. | Medium for setup/dependency tasks | Medium |
| `render.yaml` | Render deployment config in repo; current live Render usage needs manual verification. | Low | Medium |
| `AGENTS.md` | Permanent agent workflow and safety rules. | Always before work | Low for docs, high for workflow changes |
| `CURSOR_RULES.md` | Cursor-compatible workflow and reporting rules. | Always before work | Low for docs, high for workflow changes |
| `PROJECT_STATUS_HANDOVER.md` | Source of truth for current status, deploy notes, risks, and changelog. | Always before work | Medium |

## 5. Backend Architecture

The backend is a FastAPI application in `main.py`. It exposes REST endpoints for room and gameplay actions and WebSocket endpoints for room sync. The backend keeps the authoritative in-memory room/game state while the process is running, including players, host, settings, current phase, current player, timers, reactions, votes, overtime, and results.

REST endpoints mutate game state under backend control. WebSockets broadcast room updates so all browsers render the same current phase. The backend controls reveal, discussion, voting, overtime, and result transitions, and it owns timer rules rather than trusting the frontend.

Reactions are part of the room state/UI feedback flow and are not intended to affect voting or result logic. SQLite persistence is handled through `storage.py`, which stores active room snapshots and per-room used-word history.

High-risk backend areas include voting majority/overtime logic, room code generation, WebSocket state sync, reconnect/presence handling, timer transitions, role/word assignment, and storage persistence.

## 6. Frontend Architecture

`static/index.html` is the static app shell. It defines the root views and includes the CSS, QR vendor script, and `static/app.js` with cache-busting query strings.

`static/app.js` owns client-side state, REST requests, WebSocket handling, rendering, local/session storage, phase UI, private card views, discussion controls, voting UI, reveal/result animation guards, spectator UI, and reactions.

`static/styles.css` owns the visual layout: mobile-first structure, room/player panels, cards, controls, modals, reveal/countdown overlays, final result scenes, and compact scoreboard styling.

Static cache busting uses `?v=` in `static/index.html`; frontend changes should bump the relevant version string. QR generation uses `static/vendor/qrcode.min.js`. The UI is mobile-first and should preserve narrow-screen usability.

High-risk frontend areas include WebSocket reconnect handling, render/patch logic, voting privacy UI, reveal/result animation state guards, cache/version strings, QR integration, and mobile layout.

## 7. Game Flow

1. **Create/join room:** A player creates a room or joins by room code or `/room/{code}` link.
2. **Lobby:** Players gather, host controls settings, and the room waits for enough eligible players.
3. **Reveal:** Each active player privately opens and confirms their card/role/word state.
4. **Discussion:** Players discuss in Live or Chat mode, with backend-authoritative timing and current-player state.
5. **Voting:** Eligible active players vote according to the current room/game rules. Voting privacy is preserved during voting.
6. **Overtime:** Tied/no-majority cases can move into overtime according to current backend rules.
7. **Result/reveal:** The backend reveals the Varalica result and vote/statistics data; the frontend renders reveal/result visuals and scoreboard.
8. **New round:** Host starts a new round in the same room when rules allow.
9. **Reset room:** Host can reset the room flow according to existing room behavior.

## 8. Data Persistence

The project uses SQLite for runtime persistence. Known local runtime database files include `varalica.sqlite3`; runtime database files must not be committed.

SQLite stores active room snapshots so existing room/player sessions can recover after server restart, and it stores per-room used-word history so a room avoids repeating words until the available pool is exhausted.

The production SQLite path depends on server configuration and needs manual verification. Backup strategy, retention, and cleanup of stale room snapshots need manual verification. Automated cleanup for old room snapshots is noted as not implemented in the handover/README context.

## 9. Deployment Architecture

- **Local path:** `D:\Projects\Varalica_webapp`
- **Production server path:** `/opt/Varalica_webapp`
- **Production domain:** `https://varalica.autolovac.space`
- **Production service:** `varalica.service`
- **App server:** Uvicorn on port `8010`
- **Reverse proxy:** openresty/nginx-style reverse proxy observed; exact config path needs manual verification.
- **Confirmed deploy flow:** push to GitHub when requested, then on the server run `git pull` in `/opt/Varalica_webapp`, then restart with `systemctl restart varalica`.
- **Render status:** `render.yaml` exists and defines a Render web service, but current production usage of Render is unverified and needs manual verification.

## 10. Agent Reading Rules

### Always read before work

- `PROJECT_STATUS_HANDOVER.md`
- `AGENTS.md`
- `CURSOR_RULES.md` if present
- `git status`

### Read only when relevant

- `main.py` for backend/gameplay/WebSocket/timer/reaction/voting tasks.
- `storage.py` for persistence or SQLite behavior.
- `static/index.html`, `static/app.js`, and `static/styles.css` for frontend/UI/cache tasks.
- `words.py`, `validate_words.py`, and word import scripts for word database tasks.
- `requirements.txt` for dependency/setup tasks.
- `render.yaml` for deployment/config questions.
- `README.md` for user-facing setup and manual-test context, noting that freshness may need manual verification.

### Do not read unless necessary

- Runtime SQLite database files such as `varalica.sqlite3`.
- `.env` or environment/secrets files.
- Binary image assets unless the task is specifically about visual assets.
- Vendor/minified files unless the task explicitly requires vendor investigation.

### Do not edit unless explicitly requested

- `words.py`
- `static/vendor/qrcode.min.js`
- Room code generation logic
- Voting majority/overtime result logic
- Deployment workflow/server files
- Runtime database files
- `.env` or secrets
- Existing images/assets, unless the task explicitly requests asset work

## 11. High-Risk Areas

- **Voting majority/overtime result logic:** Core game rules; small changes can alter who wins.
- **Room code generation:** Directly affects invite/join stability.
- **WebSocket state sync:** Affects all connected clients, reconnect, and live room consistency.
- **Timer logic:** Drives discussion, voting availability, overtime, reveal animation timing, and cleanup behavior.
- **`words.py` word pool:** High-volume curated data; accidental edits can break validation or gameplay content.
- **QR vendor file:** Minified third-party code; avoid changes unless explicitly required.
- **Frontend cache/version string:** Missed `?v=` bumps can make production appear broken after deploy.
- **Production deploy workflow:** Confirmed systemd workflow must not be changed casually.
- **SQLite persistence:** Room restore, used-word history, and runtime DB safety depend on it.

## 12. Verification Commands

Known verification commands from the project workflow:

```powershell
python -m py_compile main.py words.py validate_words.py
python -X utf8 validate_words.py
node --check static/app.js
```

On the user's Windows setup, `node --check static/app.js` may fail with access denied (`Zugriff verweigert`) based on handover history. When that happens, use the known bundled Node runtime if available and record the exact command/result.

## 13. Unknowns / Needs Manual Verification

- Exact nginx/openresty config path.
- SSL renewal details.
- Production SQLite backup strategy.
- Render usage for live production.
- Formal automated test suite status.
- README freshness versus current implementation.
- Stale room cleanup plan.
