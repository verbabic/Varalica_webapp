# AI_USAGE_AUDIT.md — Varalica WebApp

## 1. Purpose

This file defines how to reduce GPT Plus, Codex, Cursor Pro, and project-agent usage limits by keeping context small and routing tasks to the right tool. The goal is to avoid repeated project discovery, avoid unnecessary Heavy-mode work, and use the existing documentation set before reading large code files.

## 2. Current AI Tool Setup

- **ChatGPT Plus:** Planning, mentoring, prompt preparation, debugging strategy, explaining reports, and deciding what to do next.
- **Codex:** Repo analysis, documentation generation from repo files, larger code changes, backend/game logic work, architecture analysis, and high-risk changes after narrow scoping.
- **Cursor Pro:** Code editing, smaller UI/frontend changes, visual polish, reviewing diffs, manual code navigation, and small refactors.
- **Local/light agent:** Read-only analysis, file discovery, prompt preparation, changelog drafting, test checklist drafting, TODO extraction, and documentation consistency checks.

## 3. Main Limit-Wasting Patterns

| Pattern | Why it wastes limits | Example in this project | Better approach |
|---|---|---|---|
| Asking Codex/Cursor to inspect the whole project every time. | Re-reads large files and burns context before the actual task begins. | Starting every UI task by reading backend, words, assets, and vendor files. | Read `PROJECT_STATUS_HANDOVER.md`, `ARCHITECTURE.md`, and only task-relevant files. |
| Combining multiple unrelated tasks. | Forces broad analysis and increases regression risk. | Mixing reveal UI, voting rules, word database, and deploy notes in one session. | One narrow task per session when possible. |
| Asking for code changes before task scope is clear. | Agent may inspect or modify too much while guessing. | "Fix the game" without reproduction or allowed files. | Use ChatGPT/local agent to narrow scope and produce a precise prompt first. |
| Using Codex/Cursor for documentation summaries that a local agent can prepare. | High-value coding tools spend limits on low-risk text extraction. | Asking Codex Heavy to summarize known docs. | Use local/light agent for summaries, then Codex only for final repo write if needed. |
| Repeatedly re-explaining project status instead of relying on docs. | Duplicates prompt tokens and risks inconsistency. | Pasting long project context already in handover. | Point agents to `PROJECT_STATUS_HANDOVER.md`, `ARCHITECTURE.md`, `TASK_QUEUE.md`, and `BUGS_KNOWN.md`. |
| Letting agents read assets/vendor files unnecessarily. | Binary/minified files are expensive and rarely useful. | Reading `static/vendor/qrcode.min.js` or image assets during a docs task. | Avoid unless the task explicitly targets QR or assets. |
| Using Heavy mode for documentation-only tasks. | Consumes stronger model budget without proportional value. | Creating a simple docs file with Heavy. | Use Low/Easy/Standard for docs; Medium for this AI usage audit. |
| Not keeping `PROJECT_STATUS_HANDOVER.md` updated. | Future sessions must rediscover what changed. | Missing changelog entries after bugfixes. | Update handover after meaningful changes. |

## 4. Files That Reduce Context Usage

| File | Why it saves context | Who should read it | When to update |
|---|---|---|---|
| `AGENTS.md` | Captures permanent workflow and safety rules. | All agents | When workflow rules change. |
| `CURSOR_RULES.md` | Captures Cursor-compatible editing/reporting rules. | Cursor and compatible agents | When Cursor workflow changes. |
| `PROJECT_STATUS_HANDOVER.md` | Source of truth for current status, deploy notes, risks, tests, and changelog. | All agents | After meaningful changes. |
| `ARCHITECTURE.md` | Summarizes architecture, file responsibilities, high-risk areas, and verification commands. | Agents planning repo work | When architecture or major responsibilities change. |
| `TASK_QUEUE.md` | Keeps priorities visible without re-reading the whole repo. | User, ChatGPT, Codex, Cursor, local agents | After QA, prioritization, or task status changes. |
| `BUGS_KNOWN.md` | Keeps confirmed/suspected bugs and regression risks in one place. | Agents fixing or triaging bugs | After bug confirmation or resolution. |
| `AI_USAGE_AUDIT.md` | Defines tool routing and context-saving behavior. | User and all agents | When tool workflow or usage-limit strategy changes. |

## 5. Tool Routing Rules

### ChatGPT Plus

Use for:

- deciding next step
- preparing exact Codex/Cursor prompts
- interpreting logs and reports
- planning QA and deploy
- beginner-friendly guidance

Do not use for:

- large direct repo edits
- guessing file contents without repo output

### Codex

Use for:

- documentation generation from repo
- backend/game logic work
- multi-file changes
- architecture analysis
- larger bugfixes
- high-risk code changes after narrow scoping

Do not use for:

- small one-line text edits
- repeated project discovery
- tasks that can be handled by local agent

### Cursor Pro

Use for:

- small/medium code edits
- visual UI/frontend edits
- reviewing diffs
- manual code navigation
- small refactors

Do not use for:

- broad unclear tasks
- large backend refactors without preparation
- deploy/server operations

### Local/light agent

Use for:

- read-only repo scanning
- finding relevant files
- extracting TODOs
- drafting task prompts
- summarizing git diff
- preparing manual test checklists
- drafting changelog entries
- checking documentation consistency

Do not use for:

- changing production code without review
- deploy/server changes
- secrets/.env handling
- high-risk game logic changes

## 6. Recommended Difficulty Levels

| Task type | Recommended tool | Difficulty level | Notes |
|---|---|---|---|
| Docs-only file creation | Codex | Low / Easy / Standard | Keep scope to docs and handover. |
| AI usage audit | Codex | Medium | Requires cross-document synthesis but no code changes. |
| README update | Codex/Cursor | Low-Medium | Confirm README freshness against handover/architecture. |
| Manual QA checklist | ChatGPT or local agent | Low | No repo edit needed unless saving checklist. |
| Small UI/CSS change | Cursor | Medium | Read frontend files only; bump cache if needed. |
| Backend endpoint change | Codex | Medium/High | Read `main.py` and relevant docs; run Python checks. |
| WebSocket/state sync | Codex | High | High regression risk; narrow scope and manual QA needed. |
| Voting/overtime logic | Codex | High | Core game rules; do not change casually. |
| Deploy/server/systemd/nginx | ChatGPT step-by-step + terminal | High risk | Production details need manual verification. |
| Large refactor | Codex | High/Heavy only if necessary | Avoid unless explicitly scoped and justified. |

## 7. Recommended Workflow Per Task

1. User describes problem or task.
2. ChatGPT chooses agent/tool and difficulty.
3. Local/light agent or Codex reads only required docs.
4. Local/light agent prepares a narrow prompt if needed.
5. Codex/Cursor changes only allowed files.
6. User runs one verification command at a time.
7. Handover is updated.
8. User reviews git diff.
9. Commit/push/deploy only if explicitly requested.

## 8. Read Scope Rules

### Always read

- `PROJECT_STATUS_HANDOVER.md`
- `AGENTS.md`
- `CURSOR_RULES.md` if present
- `ARCHITECTURE.md`

### Read when planning work

- `TASK_QUEUE.md`
- `BUGS_KNOWN.md`
- `AI_USAGE_AUDIT.md`

### Read only when relevant

- `main.py`
- `storage.py`
- `static/app.js`
- `static/styles.css`
- `words.py`
- `validate_words.py`
- `README.md`
- `scripts/`

### Avoid reading unless needed

- `static/vendor/qrcode.min.js`
- `static/assets/`
- `Fotos/`
- runtime database files
- large generated/sample files

## 9. Good Prompt Templates

1. **Local/light agent: find relevant files for a bug**

   Read `PROJECT_STATUS_HANDOVER.md`, `AGENTS.md`, `CURSOR_RULES.md`, `ARCHITECTURE.md`, `TASK_QUEUE.md`, and `BUGS_KNOWN.md`. Preserve the dirty tree. Do not edit files, commit, push, or deploy. For this bug: `[describe bug]`, identify the smallest likely files/functions to inspect and list manual checks.

2. **Local/light agent: prepare Codex prompt**

   Read the project docs first and preserve the dirty tree. Do not edit files, commit, push, or deploy. Prepare a narrow Codex prompt for `[task]` with allowed files, forbidden files, required tests, handover update, and rollback notes if relevant.

3. **Codex: fix one scoped bug**

   Before editing, read `PROJECT_STATUS_HANDOVER.md`, `AGENTS.md`, `CURSOR_RULES.md`, `ARCHITECTURE.md`, `TASK_QUEUE.md`, and `BUGS_KNOWN.md`; check `git status` and preserve dirty files. Fix only `[exact bug]`. Change only `[allowed files]`. Do not commit, push, deploy, or modify `.env`. Run `[tests]` and update `PROJECT_STATUS_HANDOVER.md`.

4. **Cursor: small UI/CSS edit**

   Read project docs first and check `git status`. Keep scope to `[specific UI/CSS issue]`. Preserve dirty tree. Do not touch backend, words, QR, assets, or deploy files. If frontend files change, bump cache. Do not commit/push/deploy. Update handover if meaningful.

5. **Local/light agent: review git diff**

   Read project docs first and preserve dirty tree. Do not edit files, commit, push, or deploy. Summarize `git diff` by file, identify unrelated changes, list tests already run or missing, and draft a concise handover changelog if needed.

6. **Local/light agent: draft `PROJECT_STATUS_HANDOVER.md` changelog**

   Read project docs first and preserve dirty tree. Do not edit files, commit, push, or deploy. Based on this completed task summary and diff: `[paste summary]`, draft a handover changelog entry with changed files, summary, what was not changed, tests, deploy status, manual checks, and known risks.

## 10. Bad Prompts To Avoid

- `"Look at the whole project and fix everything."` — too broad; causes excessive file reading and unsafe changes.
- `"Make it better."` — unclear success criteria; invites subjective edits and scope creep.
- `"Refactor the game."` — high-risk and not tied to a specific bug or outcome.
- `"Deploy it."` — production operations need explicit steps, current status, and confirmation.
- `"Check all files and optimize."` — wastes limits reading unrelated files and can create risky churn.
- `"Fix all bugs."` — mixes unrelated issues and makes testing/rollback hard.

## 11. Project-Specific Limit Savers

| Area | Current risk | How to save limits |
|---|---|---|
| Game flow | Many phases interact and regressions are easy. | Use `ARCHITECTURE.md` and manual QA checklist before reading code. |
| WebSocket sync | State sync touches many clients. | Narrow to a specific symptom and inspect only relevant WebSocket/render paths. |
| Voting/overtime | Core winner logic is high risk. | Avoid changes unless task is explicit; use scenario table before editing. |
| Frontend rendering | `static/app.js` is broad and easy to over-read. | Search exact render function/classes first; avoid full-file rereads when possible. |
| Static assets | Binary files are large and often irrelevant. | Read asset names/paths only; avoid opening images unless task requires visual inspection. |
| Word database | Large curated file with validation warnings/history. | Use `validate_words.py` and importer docs; do not inspect full `words.py` unless word task. |
| Deploy workflow | Production facts have unknowns. | Use handover/architecture and verify server details only when deploy/admin task is active. |
| QA/manual tests | Manual tests can consume time if unfocused. | Use `TASK_QUEUE.md` and `BUGS_KNOWN.md` to pick the next targeted checklist. |
| Dirty working tree | Existing asset/docs changes can be accidentally included. | Always run `git status`; separate docs commits from asset/logo/avatar work. |

## 12. Current Dirty Working Tree Handling

Current known dirty/untracked files, pre-existing before `AI_USAGE_AUDIT.md` creation:

- `PROJECT_STATUS_HANDOVER.md` — pre-existing before `AI_USAGE_AUDIT.md` creation
- `static/assets/Logo_title.png` — pre-existing before `AI_USAGE_AUDIT.md` creation
- `ARCHITECTURE.md` — pre-existing before `AI_USAGE_AUDIT.md` creation
- `TASK_QUEUE.md` — pre-existing before `AI_USAGE_AUDIT.md` creation
- `BUGS_KNOWN.md` — pre-existing before `AI_USAGE_AUDIT.md` creation
- `Fotos/` — pre-existing before `AI_USAGE_AUDIT.md` creation
- `scripts/prepare_avatar_transparency.py` — pre-existing before `AI_USAGE_AUDIT.md` creation
- `static/assets/eyes_normal.png` — pre-existing before `AI_USAGE_AUDIT.md` creation
- `varalica_curated_words_sample_200_old.py` — pre-existing before `AI_USAGE_AUDIT.md` creation

Do not accidentally commit all files. Review documentation changes separately from asset/logo/avatar work. `varalica_curated_words_sample_200_old.py` should not be committed unless explicitly requested.

## 13. Recommended Next Actions To Reduce Limits

| Priority | Action | Tool | Difficulty | Expected limit saving |
|---|---|---|---|---|
| P1 | Finish documentation set. | Codex | Low/Medium | Reduces repeated project explanation and rediscovery. |
| P1 | Verify docs with `git diff`. | Local/light agent or user terminal | Low | Separates documentation intent from accidental changes. |
| P1 | Separate docs commit from asset work. | User/Codex if asked | Low | Prevents accidental binary/untracked file commits. |
| P1 | Create standard prompt snippets. | ChatGPT/local agent | Low | Reduces long repeated task prompts. |
| P1 | Run manual QA checklist. | User + ChatGPT/local checklist | Low/Medium | Finds real bugs before spending Codex/Cursor fixes. |
| P2 | Avoid Heavy for documentation. | User/tool routing | Low | Saves high-tier usage for risky code. |
| P2 | Use local/light agent for file discovery. | Local/light agent | Low | Keeps Codex/Cursor context focused. |
| P2 | Keep handover updated. | Any agent after meaningful change | Low | Prevents future rediscovery. |
| P2 | Do one task per session. | User + chosen agent | Low | Reduces context, testing, and rollback complexity. |
| P3 | Verify production unknowns only when needed. | Human/server admin + ChatGPT | Medium | Avoids spending repo-agent time on server facts too early. |

## 14. Final Recommendation

- **ChatGPT Plus:** Use for deciding the next step, preparing narrow prompts, understanding reports/logs, planning QA, and step-by-step deploy guidance.
- **Codex:** Use for repo-backed documentation generation, backend/game logic work, multi-file changes, architecture analysis, and larger/high-risk bugfixes after scope is narrow.
- **Cursor Pro:** Use for small/medium edits, visual frontend work, manual code navigation, and reviewing diffs.
- **Local/light agent:** Use for read-only scanning, finding files, summarizing diffs, drafting prompts, drafting changelogs, and preparing checklists.

The next practical action in this repository should be to review the new documentation set with `git diff`, keep docs separated from existing asset/logo work, then run the focused manual QA checklist before opening new bugfix sessions.
