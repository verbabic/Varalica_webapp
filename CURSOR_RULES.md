# CURSOR_RULES.md — Varalica WebApp

Permanent workflow rules for Cursor (and compatible agents) on this project.

---

## Before editing

1. Read **`PROJECT_STATUS_HANDOVER.md`**.
2. Read **`AGENTS.md`**.
3. Check **`git status`** (branch, untracked files, dirty files).
4. Identify the **exact requested phase/task** — do not expand scope.
5. Confirm production facts in the handover (systemd, domain, paths) before writing deploy-related docs.

---

## During editing

- Change **only the files needed** for the task.
- Do **not** rewrite large sections unnecessarily.
- **Preserve existing working behavior** unless the task is a deliberate fix.
- Do **not** change unrelated game logic (voting, Varalice rules, room codes, QR, Nova runda / Resetuj sobu unless requested).
- Do **not** edit application code when the task is documentation-only.

---

## After editing

1. Update **`PROJECT_STATUS_HANDOVER.md`** after every **meaningful** change (features, bugs, deploy, cache version, tests).
2. Add a **changelog entry** at the top of section 11 in the handover.
3. Run **relevant tests** (see `AGENTS.md`).
4. End your reply with this **output format**:

### Required end-of-task report

1. **Changed files**
2. **What was changed**
3. **What was not changed**
4. **Tests run**
5. **PROJECT_STATUS_HANDOVER.md updated:** yes / no
6. **Deploy status** (not deployed / deployed / user must deploy)
7. **Manual checks needed**
8. **Known risks/issues**

---

## Commit / push / deploy

- **Never** commit, push, or deploy unless the user **explicitly** asks.
- When the user asks to commit: follow git safety rules; never force-push `main`/`master` without warning.

---

## Documentation-only tasks

When creating or updating docs (`PROJECT_STATUS_HANDOVER.md`, `AGENTS.md`, `CURSOR_RULES.md`, `README.md`):

- Do not touch `main.py`, `static/app.js`, `static/styles.css`, or other runtime code unless explicitly requested.
- Do not invent production details; use **needs manual verification** when uncertain.

---

## Cross-tool consistency

This project is sometimes edited in **Cursor** and sometimes in **Codex**. Both must read the handover before work and update it after meaningful changes so sessions stay aligned.
