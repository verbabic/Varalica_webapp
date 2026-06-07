# BUGS_KNOWN.md — Varalica WebApp

## 1. Purpose

This file tracks confirmed bugs, known limitations, suspected issues, and regression risks for the Varalica WebApp repository. It exists so future Cursor, Codex, and local-agent sessions do not need to re-scan the full handover and changelog before understanding the current bug landscape.

`PROJECT_STATUS_HANDOVER.md` remains the source of truth for current project state. This file is a bug-focused companion document.

## 2. Bug Handling Rules

- Do not fix bugs without a narrow task.
- First reproduce or confirm the bug if possible.
- Do not mix multiple unrelated bugfixes.
- Do not change voting/overtime/game-state logic casually.
- Update `PROJECT_STATUS_HANDOVER.md` after meaningful fixes.
- Move fixed bugs to the resolved section instead of deleting them immediately.
- Mark unconfirmed issues as `suspected` or `needs manual verification`.

## 3. Open Confirmed Issues

| ID | Issue | Area | Impact | Evidence/source | Status | Suggested tool | Risk |
|---|---|---|---|---|---|---|---|
| BUG-001 | `README.md` may be out of date versus current code/features. | Documentation | Docs can mislead testers and future agents. | `PROJECT_STATUS_HANDOVER.md` notes README may be behind current code; `TASK_QUEUE.md` lists README update as P1. | Open | Documentation-only Cursor/Codex session | Low |
| BUG-002 | Old room snapshot cleanup is not implemented. | Persistence/admin | SQLite room snapshot data can grow over time. | `PROJECT_STATUS_HANDOVER.md`, `ARCHITECTURE.md`, and `TASK_QUEUE.md` all note stale room cleanup as missing/needed. | Open | Backend planning/admin tooling session | Medium |
| BUG-003 | Manual gameplay regression risk due lack of formal automated E2E tests. | Testing/QA | UI/gameplay regressions can reach production without full automated coverage. | `PROJECT_STATUS_HANDOVER.md` notes manual gameplay regression risk and no formal E2E suite confirmed; `TASK_QUEUE.md` prioritizes manual QA and smoke checks. | Open | QA/testing session | Medium |
| BUG-004 | Production config details need manual verification. | Deployment/operations | Unknown server details can make deploy, rollback, SSL, or backup work risky. | `PROJECT_STATUS_HANDOVER.md` and `ARCHITECTURE.md` mark production config, backup, SSL, and Render details as needing manual verification. | Open | Human/server admin + documentation session | Medium |

## 4. Suspected / Needs Manual Verification

| ID | Issue | Why it matters | What to check | Suggested check method | Status |
|---|---|---|---|---|---|
| VERIFY-001 | Exact nginx/openresty config path unknown. | Needed for production troubleshooting and proxy/header changes. | Actual reverse proxy config path and active server block. | Inspect production server config. | Needs manual verification |
| VERIFY-002 | SSL renewal details unknown. | Certificate expiration/renewal failures could break HTTPS. | Certificate provider, renewal mechanism, renewal schedule, alerting. | Inspect production server/certbot/openresty setup. | Needs manual verification |
| VERIFY-003 | Production SQLite backup strategy unknown. | Room snapshots and used-word history can be lost without backup. | Database path, backup schedule, restore procedure. | Inspect production environment and backup jobs. | Needs manual verification |
| VERIFY-004 | Render usage unknown. | `render.yaml` exists but production is believed to be systemd. | Whether Render is active, historical, or unused. | Check Render dashboard/repo deploy settings. | Needs manual verification |
| VERIFY-005 | Formal automated test suite status needs confirmation. | Determines whether QA relies mostly on manual testing. | Existing CI/test files beyond known compile/validation checks. | Inspect repository and GitHub Actions/settings. | Needs manual verification |
| VERIFY-006 | README freshness needs confirmation. | README can misstate limits, timers, word count, or current features. | Compare README against current handover and code. | Documentation review session. | Needs manual verification |
| VERIFY-007 | Production last deploy time needs confirmation. | Helps correlate reported bugs with deployed code/cache version. | Current production commit/version and service restart time. | Inspect server git log/service status and deployed HTML asset versions. | Needs manual verification |
| VERIFY-008 | Privacy/GDPR documentation status needs confirmation. | Player names, avatars, and room codes are stored in SQLite. | Whether privacy notes/policy exist and whether they match behavior. | Documentation/product review. | Needs manual verification |

## 5. Regression Risk Areas

| Area | Why risky | Files usually involved | Minimum check before/after change |
|---|---|---|---|
| Voting majority/overtime result logic | Core game rules; small mistakes change winners. | `main.py`, sometimes `static/app.js` for UI display | Reproduce 1-Varalica and 2-Varalice vote scenarios, ties, overtime, and final reveal. |
| Room code generation | Breaks create/join/invite flow if altered. | `main.py` | Create room, join by code, join by `/room/{code}` link. |
| WebSocket sync/state updates | Affects every connected player and reconnect behavior. | `main.py`, `static/app.js` | Multi-tab create/join, reconnect, room updates, phase transitions. |
| Backend timers | Controls discussion, voting availability, overtime, tab-close cleanup, and reveal flow triggers. | `main.py` | Check timer start/stop, phase transitions, reconnect behavior, and host controls. |
| Reveal/discussion/voting/result phases | Phase transitions are central to the app experience. | `main.py`, `static/app.js`, `static/styles.css` | Full round manual QA from reveal to new round/reset. |
| `words.py` and word import/validation | Large data file; bad changes can break role/word delivery or validation. | `words.py`, `validate_words.py`, `scripts/` import tools | Run compile and `python -X utf8 validate_words.py`; inspect import counts if word task. |
| Static app rendering | Render logic can affect many states at once. | `static/app.js`, `static/styles.css`, `static/index.html` | Run JS syntax check and targeted mobile/desktop manual UI checks. |
| Frontend cache version string | Missing bump can make production look unchanged/broken. | `static/index.html`, `static/app.js` asset constants | Confirm `?v=` values after frontend changes and hard-refresh production/local. |
| QR vendor library | Minified vendor file; accidental edits can break QR/link sharing. | `static/vendor/qrcode.min.js` | Avoid editing; if touched, verify QR display and room link copy. |
| SQLite persistence | Affects room restore and used-word history. | `storage.py`, `main.py` | Restart/reconnect scenario, used-word persistence, database path checks. |
| Production deploy workflow | Wrong deploy/restart can put production in inconsistent state. | Server workflow, git, systemd; docs in handover | Confirm branch/commit, static cache version, service restart, rollback path. |

## 6. Validation / Test Gaps

The available documentation confirms useful smoke checks, but does not confirm a formal E2E test suite. Manual multiplayer QA is still needed for Live mode, Chat mode, reactions, voting, overtime, reveal/results, Nova runda, Resetuj sobu, reconnect, tab close, and cache behavior.

Known verification commands exist:

```powershell
python -m py_compile main.py words.py validate_words.py
python -X utf8 validate_words.py
node --check static/app.js
```

These checks do not prove full gameplay correctness. They catch syntax/structure issues only. Also, `node --check static/app.js` may fail on the user's Windows setup with access denied (`Zugriff verweigert`) based on handover history; use the known bundled Node runtime if needed and record the exact command/result.

## 7. Resolved / Historical Issues

- Excel word import changes were handled in previous `PROJECT_STATUS_HANDOVER.md` changelog entries.
- Balkan category removal and word import history should be checked through `PROJECT_STATUS_HANDOVER.md` if needed.
- Earlier UI/reveal/cache/spectator fixes are recorded in `PROJECT_STATUS_HANDOVER.md`; do not assume they are fully regression-tested without manual QA.

## 8. Bug Report Template

- **Title:**
- **Date found:**
- **Environment:**
- **Steps to reproduce:**
- **Expected behavior:**
- **Actual behavior:**
- **Screenshots/logs:**
- **Suspected files:**
- **Severity:**
- **Workaround:**
- **Status:**

## 9. Fix Session Template

- **Read files:** `PROJECT_STATUS_HANDOVER.md`, `AGENTS.md`, `CURSOR_RULES.md`, `ARCHITECTURE.md`, `TASK_QUEUE.md`, `BUGS_KNOWN.md`, then only files relevant to the bug.
- **Confirm dirty tree:** Run `git status` and preserve unrelated dirty/untracked files.
- **Define exact bug:** State the reproduction, expected behavior, and actual behavior.
- **Files allowed to change:** List the smallest file set needed for the fix.
- **What must not change:** Explicitly list unrelated game logic, assets, QR, word database, deployment, or `.env` restrictions.
- **Tests/checks to run:** Choose relevant compile, validation, JS syntax, `git diff --check`, and manual QA checks.
- **Handover update required:** Update `PROJECT_STATUS_HANDOVER.md` with changed files, summary, tests, deploy status, manual checks, and known risks.

## 10. Current Best Next Bug-Related Step

The best practical next bug-related step is a focused full manual QA checklist before fixing new issues. Confirm Live mode, Chat mode, reactions, voting, overtime, reveal/results, Nova runda, Resetuj sobu, reconnect, tab close, and production cache behavior. Record confirmed bugs in this file and update `PROJECT_STATUS_HANDOVER.md` before opening narrow fix sessions.
