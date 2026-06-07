# TASK_QUEUE.md — Varalica WebApp

## 1. Purpose

This file is the working task queue for future Cursor, Codex, and local-agent sessions on the Varalica WebApp repository. Its purpose is to keep priorities visible so agents do not need to re-discover the next practical tasks from the whole repository every time.

`PROJECT_STATUS_HANDOVER.md` remains the source of truth for current project state. `TASK_QUEUE.md` is a lightweight queue of recommended next work.

## 2. Task Rules

- Keep each task small.
- One task per Codex/Cursor session when possible.
- Do not combine UI, backend, deploy, and word database work in one task.
- Always read `PROJECT_STATUS_HANDOVER.md`, `AGENTS.md`, `CURSOR_RULES.md`, and `ARCHITECTURE.md` before work.
- After meaningful changes, update `PROJECT_STATUS_HANDOVER.md`.
- Do not commit, push, or deploy unless the user explicitly asks.

## 3. P1 — Highest Priority

| ID | Task | Reason | Suggested tool | Risk | Status |
|---|---|---|---|---|---|
| P1-001 | Run full manual QA checklist for Live and Chat modes. | Handover notes manual gameplay regression risk and no automated E2E tests. | Cursor/Codex + local browser/manual multi-tab testing | Medium | Open |
| P1-002 | Update `README.md` to match current features. | Handover says README may be behind current code, including player limits and newer Chat/reaction features. | Cursor or Codex documentation session | Low | Open |
| P1-003 | Decide basic automated smoke checks / CI approach. | Handover recommends compile, word validation, and JS syntax checks; formal automated test suite status needs manual verification. | Cursor/Codex documentation or CI planning session | Medium | Open |
| P1-004 | Clarify production deploy, backup, and SSL unknowns. | Handover and architecture mark nginx/openresty config path, SSL renewal, and SQLite backup strategy as needing manual verification. | Human/server admin + documentation update | Medium | Open |
| P1-005 | Decide stale room cleanup approach. | Handover/README note old room snapshot cleanup is not implemented. | Backend planning session | Medium | Open |

## 4. P2 — Useful Improvements

| ID | Task | Reason | Suggested tool | Risk | Status |
|---|---|---|---|---|---|
| P2-001 | Improve test coverage around voting/overtime. | Voting majority/overtime result logic is a high-risk core game area. | Codex/Cursor backend test session | High | Open |
| P2-002 | Document manual multiplayer test scenarios. | Manual QA is currently important for Live, Chat, reconnect, voting, reveal, and reset flows. | Documentation-only session | Low | Open |
| P2-003 | Review duplicate/repeated hint warnings from word validation. | `validate_words.py` reports quality and duplicate/repetition warnings; current data passes structure but warnings may merit review. | Word database review session | Medium | Open |
| P2-004 | Review player privacy/GDPR notes. | Handover flags names, avatars, and room codes stored in SQLite with no formal privacy policy referenced. | Documentation/product review session | Medium | Open |
| P2-005 | Improve rollback notes. | Deployment and rollback are documented but several production details need manual verification. | Documentation-only session | Low | Open |

## 5. P3 — Later / Nice to Have

| ID | Task | Reason | Suggested tool | Risk | Status |
|---|---|---|---|---|---|
| P3-001 | Admin cleanup tooling for old room snapshots. | Old room snapshot cleanup is a known limitation. | Backend/admin tooling session | Medium | Open |
| P3-002 | Better monitoring/log review notes. | Production troubleshooting depends on server logs and service state; exact operational notes need manual verification. | Documentation/admin session | Low | Open |
| P3-003 | Optional CI workflow. | CI could automate known smoke checks once the preferred approach is decided. | Codex/Cursor CI session | Medium | Open |
| P3-004 | Product/UX improvements only after QA confirms stability. | Current priority is stability and regression control before expanding product surface. | Future UI/product session | Medium | Open |

## 6. Known Current Dirty Working Tree Items

The following items are pre-existing before `TASK_QUEUE.md` creation:

- `PROJECT_STATUS_HANDOVER.md` — pre-existing before `TASK_QUEUE.md` creation
- `static/assets/Logo_title.png` — pre-existing before `TASK_QUEUE.md` creation
- `ARCHITECTURE.md` — pre-existing before `TASK_QUEUE.md` creation
- `Fotos/` — pre-existing before `TASK_QUEUE.md` creation
- `scripts/prepare_avatar_transparency.py` — pre-existing before `TASK_QUEUE.md` creation
- `static/assets/eyes_normal.png` — pre-existing before `TASK_QUEUE.md` creation
- `varalica_curated_words_sample_200_old.py` — pre-existing before `TASK_QUEUE.md` creation

These files must not be accidentally committed without review.

## 7. What Not To Do Now

- Do not start new gameplay refactor.
- Do not change voting/overtime logic.
- Do not change room code generation.
- Do not change `words.py` unless the task is specifically word database work.
- Do not deploy before local review.
- Do not mix asset/logo work with backend work.

## 8. Recommended Next Session Types

### Documentation-only session

- **Best tool:** Codex or Cursor
- **Recommended difficulty level:** Low / Easy / Standard
- **What files to read first:** `PROJECT_STATUS_HANDOVER.md`, `AGENTS.md`, `CURSOR_RULES.md`, `ARCHITECTURE.md`, and the target documentation file.
- **What must not be touched:** Runtime code, assets, `.env`, SQLite database files, vendor files.

### QA/testing session

- **Best tool:** Cursor/Codex with local browser/manual multi-tab testing
- **Recommended difficulty level:** Medium
- **What files to read first:** `PROJECT_STATUS_HANDOVER.md`, `AGENTS.md`, `CURSOR_RULES.md`, `ARCHITECTURE.md`, `README.md`.
- **What must not be touched:** Application code unless a separate bugfix task is explicitly opened.

### Small bugfix session

- **Best tool:** Codex or Cursor
- **Recommended difficulty level:** Medium
- **What files to read first:** `PROJECT_STATUS_HANDOVER.md`, `AGENTS.md`, `CURSOR_RULES.md`, `ARCHITECTURE.md`, plus only files directly relevant to the bug.
- **What must not be touched:** Unrelated gameplay logic, word database, QR vendor, assets unless the bug is specifically asset-related.

### Frontend/UI session

- **Best tool:** Codex or Cursor with browser verification
- **Recommended difficulty level:** Medium
- **What files to read first:** `PROJECT_STATUS_HANDOVER.md`, `AGENTS.md`, `CURSOR_RULES.md`, `ARCHITECTURE.md`, `static/index.html`, `static/app.js`, `static/styles.css`.
- **What must not be touched:** Backend game rules, room code generation, voting/overtime result logic, word database, QR vendor file.

### Backend/game-logic session

- **Best tool:** Codex Heavy or Cursor
- **Recommended difficulty level:** High
- **What files to read first:** `PROJECT_STATUS_HANDOVER.md`, `AGENTS.md`, `CURSOR_RULES.md`, `ARCHITECTURE.md`, `main.py`, and `storage.py` if persistence is involved.
- **What must not be touched:** Frontend assets, QR vendor, word database unless explicitly part of the task.

### Deploy session

- **Best tool:** Human/server admin with Codex/Cursor assistance if requested
- **Recommended difficulty level:** Medium / High
- **What files to read first:** `PROJECT_STATUS_HANDOVER.md`, `AGENTS.md`, `CURSOR_RULES.md`, `ARCHITECTURE.md`, deployment notes, current `git status`, and current commit history.
- **What must not be touched:** `.env`, production service config, or server state unless explicitly requested and reviewed.

## 9. Current Best Next Step

The best next practical step after documentation setup is a focused QA/testing session for the full manual multiplayer flow, especially Live mode, Chat mode, reactions, voting, overtime, reveal/results, Nova runda, Resetuj sobu, reconnect, tab close, and production cache behavior.

After QA, update `PROJECT_STATUS_HANDOVER.md` and this task queue with confirmed findings, closed tasks, and any new bugs.
