# AGENTS.md — Varalica WebApp

Instructions for **every future AI agent** (Cursor, Codex, or other) working on this repository.

---

## Project locations

| Environment | Path |
|-------------|------|
| **Local (Windows)** | `D:\Projects\Varalica_webapp` |
| **Production server** | `/opt/Varalica_webapp` |
| **Production domain** | `https://varalica.autolovac.space` |
| **Production service** | `varalica.service` (systemd) |
| **App process** | Uvicorn on port **8010** (behind openresty/nginx proxy) |

---

## Before you start any work

1. Read **`PROJECT_STATUS_HANDOVER.md`** — current status, bugs, deploy notes, changelog.
2. Read **`AGENTS.md`** (this file).
3. Read **`CURSOR_RULES.md`** if present.
4. Run **`git status`** and note branch + uncommitted files.
5. Understand what is implemented, what is deployed, known bugs, and the **exact task scope**.
6. **Keep scope narrow** — fix only what was requested.
7. **Do not guess** project state. If docs or code are unclear, mark **needs manual verification** or ask the user.

---

## After every meaningful change

1. Update **`PROJECT_STATUS_HANDOVER.md`** (status sections + new changelog entry).
2. Changelog entry must include:
   - Date/time
   - Tool used (Cursor / Codex / other)
   - Changed files
   - Summary
   - What was **not** changed
   - Tests run
   - Deploy status
   - Manual checks needed
   - Known issues
3. **Do not commit, push, or deploy** unless the user explicitly asks.

---

## Production deployment (confirmed workflow)

1. Push changes to GitHub (only when user requests).
2. On server: `git pull` in `/opt/Varalica_webapp`.
3. Restart: `systemctl restart varalica`.

Do **not** assume Render is production. `render.yaml` exists in the repo but **current confirmed production** is server + systemd. Render usage: **needs manual verification**.

After frontend changes, bump `?v=` in `static/index.html` before deploy so browsers load new JS/CSS.

---

## Files / areas — change with care

Do **not** modify unless the task explicitly requires it:

| Area | Reason |
|------|--------|
| `words.py` | Curated word pool; high regression risk |
| `static/vendor/qrcode.min.js` | Vendor QR library |
| Room code generation logic | Stable invite/join behavior |
| Voting majority / overtime result logic | Core game rules |
| Deploy workflow on server | Unless user requests infra change |

---

## Do not commit unless user asks

- `varalica_curated_words_sample_200_old.py` — sample/legacy file; keep untracked unless user explicitly wants it in git.
- `varalica.sqlite3` — runtime database.
- `.env` or secrets.

---

## Typical verification commands

```powershell
python -m py_compile main.py words.py validate_words.py
python -X utf8 validate_words.py
node --check static/app.js
```

Run what is relevant to your change. Record results in the handover changelog.

---

## Session handoff rule

If you stop mid-task, leave **`PROJECT_STATUS_HANDOVER.md`** accurate so the next Cursor or Codex session can continue without re-discovering state.
