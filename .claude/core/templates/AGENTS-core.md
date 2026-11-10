## How work flows (agent core - managed by install.py, do not edit between the markers)
Triage every request first (`sdlc` skill), without asking which lane:
- **Answer**: questions, "discuss", "explain" - answered directly (big searches go to `explorer`); "plan", "review this" and "don't change" change no code.
- **Quick fix**: obvious and small (up to ~30 lines in up to 3 files, nothing to decide) - routed to its area agent with a quick brief, then `python .claude/core/scripts/live_status.py quick "<what>"`.
- **Setup work**: the AI setup only (`.claude/`, `.cursor/`, `AGENTS.md`, `CLAUDE.md`, `setup_paths`) - done by the main session, no task; then `python .claude/core/scripts/cursor_sync.py`, and its `--check` must be clean.
- **Task** (task mode): every other change to an existing product - a task in the work folder: `explorer`'s context pack first, a risk level from its evidence, only the agents it needs, a safety net set by the risk, and the QA sign-off before it closes.
- **Product** (product mode): an idea, a PRD or "build a new product" - the `factory` skill, with a gate at each decision; never built straight from the document.
- **Requirements**: "review the requirements", a ticket or document to check before any build - the `review-spec` skill: plain words, the Definition of Ready, one gate with the requester; no code.
- **Test and fix**: "/test BLEN-1 BLEN-2", "retest", "fix BLEN-1" - the `test` skill (the QA team, a fix list at the end) and the sdlc fix loop; fixes never start by themselves.

Hard rules (in a repo with `.claude/project.json` the hooks enforce most of them, in Claude and Cursor):
- The main session is the Tech Lead: it triages, decides, briefs, routes, integrates and verifies, and never writes product code (everything outside the AI setup and the work folder). It stops the developer only for something to decide: gaps in the brief, decision cards D1-D8 and prototype picks.
- No git command that changes the repo (commit, push, pull, fetch, merge, stash, reset, checkout, add, ...); read-only git is fine. `git pull` only when the developer asks for it in their own message.
- Never start or restart servers (say what needs a restart and why). Never copy secret values.
- The live page is the only tracker; never make another tracker page or artifact. Open it with `python .claude/core/scripts/live_status.py open <id>`.
- Automated tests go in the project's test folder, mirroring the package of the code under test (Java `src/test/java/<same package>/`), never in `src/main/**` or the repo root; the scratchpad holds only throwaway scripts.
- Core files (`.claude/core/`, the core agents and skills listed in `.claude/core/core.lock`) change only in the core source (product-factory `core/`) and are installed in every project in the same change; `python .claude/core/scripts/install.py . --check` lists hand edits.

The detail (the agents and their models, how they work, the safety net, QA, the hooks, the live page and the sync rules) is in `.claude/core/reference/how-work-flows.md`: read it before a Task or a Product. Cursor reads this file and `.claude/skills/` directly and runs the `.cursor/` agents, rules and hooks that `cursor_sync.py` generates.
