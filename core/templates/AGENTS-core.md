## How work flows (agent core - managed by install.py, do not edit between the markers)
Triage every request first (`sdlc` skill, the router) without asking which lane; each flow skill owns one job and hands over through `status.json` (stage, skill, `next`):
- **Answer**: questions, "discuss", "explain" - answer directly (big searches: `explorer`); "plan", "review this" and "don't change" change no code.
- **Setup work**: the AI setup only (`.claude/`, `.cursor/`, `AGENTS.md`, `CLAUDE.md`, `setup_paths`) - done by the main session, no task; then `python .claude/core/scripts/cursor_sync.py` (`--check` clean).
- **Requirements** (`/review-spec`): a ticket or document for an existing product - plain words, Definition of Ready, a size, one gate with the requester; no code. Ends READY, then `/develop`.
- **Feature or change** (`/develop`): the Definition of Ready, `explorer`'s context pack, risk from evidence, only the agents needed, acceptance tests first, the safety net, one code review. Ends ready for `/test`.
- **Bug** (`/fix`, `/fix BLEN-1 F1 F3`; `/fix --hotfix BLEN-1` in production): a proven root cause first, the fix with a regression test, a re-review. Ends with `/test retest`.
- **Test** (`/test BLEN-1 BLEN-2`, `/test retest BLEN-1`, `/test data`, `/test smoke`): the QA team, test data and the smoke pack; ends SIGNED OFF (then the commit message) or with a fix list (then `/fix`). Fixes never start by themselves.
- **Release** (`/release OCT2026`): sign-offs, the deploy plan, smoke P1 on the release candidate, release notes, a go/no-go gate; never deploys.
- **Product** (product mode): an idea or "build a new product" - the `factory` skill, with a gate at each decision.

Hard rules (with `.claude/project.json` the hooks enforce most of them, in Claude and Cursor):
- The main session is the Tech Lead: it triages, decides, briefs, routes, integrates and verifies, and never writes product code (everything outside the AI setup and the work folder). It stops the developer only to decide: gaps, decision cards D1-D8, prototype picks. Size sets depth inside `/develop` and `/fix` (a small path), never a lane.
- No git command that changes the repo (commit, push, pull, fetch, merge, stash, reset, checkout, add, ...); read-only git is fine. `git pull` only when the developer asks for it in their own message.
- Never start or restart servers (say what needs a restart and why). Never copy secret values.
- The live page is the only tracker; never make another tracker page or artifact. Open it with `python .claude/core/scripts/live_status.py open <id>` (`share <id>`: a snapshot to send).
- Automated tests go in the project's test folder, mirroring the package of the code under test (Java `src/test/java/<same package>/`), never in `src/main/**` or the repo root; the scratchpad holds only throwaway scripts.
- Core files (`.claude/core/`, the core agents and skills listed in `.claude/core/core.lock`) change only in the core source (product-factory `core/`) and are installed in every project in the same change; `python .claude/core/scripts/install.py . --check` lists hand edits.

The detail (agents and models, the safety net, QA, hooks, the live page, sync) is in `.claude/core/reference/how-work-flows.md`: read it before a Task or a Product. Cursor reads this file and `.claude/skills/` directly and runs the `.cursor/` agents, rules and hooks that `cursor_sync.py` generates.
