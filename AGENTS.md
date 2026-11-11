# Product factory

Home of the shared agent core (`core/`) and the place where new products are made. Every new product starts from
a fresh base project (built from the core's base spec), then goes through intake, requirements, product review,
prototype, stories, design, build, review, audit and release with the user deciding at fixed gates (product mode,
`factory` skill). Changes to an existing product run as tasks (task mode, `sdlc` skill), either in that product's
own repo (the core is installed there by `base-builder`) or from here with `--root <product root>`.

## Repo map
| Path | What |
|---|---|
| `core/` | the agent core source (plugin layout): agents, skills, hooks, scripts, reference, templates; `core/core-plan.md` is its design, `core/migration/` the notes for moving other repos onto it |
| `plugin/` | the Claude Code plugin `product-factory` (by TalenTeam Product & Engineering), built from `core/` by `core/scripts/build_plugin.py` (never edited by hand); `.claude-plugin/marketplace.json` makes this repo the `talenteam` marketplace |
| `.github/` | the sync bot: `workflows/core-sync.yml` and `core-sync/` (script, target repos, AWS role policies); on a push to `main` it installs the core into each product repo |
| `.claude/` | the core installed for this repo (`install.py`), plus `project.json` (work folder `work`, products under `D:/products`, read-only `D:/skillos`) |
| `work/<slug>/` | one folder per product or task: every document, question and decision, and its live status |
| `D:/products/<slug>/` | the product roots (code), outside this folder |
| `standards/`, `base/`, `scripts/` | legacy copies kept for the DeskBook run; the core's own copies are in `core/reference/` and `core/scripts/` |

## Hard rules
1. Git: no command that changes a repo (commit, push, pull, merge, stash, reset, switch, checkout, add, ...); read-only
   git is fine. `git pull` only when the developer asks for it in their own message. The developer does git (this folder is the
   public GitHub repo `zakvantalenteam/product-factory`; a push to `main` ships the core to every product repo).
2. Never start or restart servers. Say what needs a restart and why. The one exception is the live-status page
   (`live-status` in `.claude/launch.json`).
3. Repos used as reference (for example `D:\skillos\repo\SkillsOS`) are read-only: `git show`, `git ls-tree`,
   `git grep`, Read only.
4. Secrets: never copy values from `application*.properties`, `manifest.yml`, `xs-security.json` or `*Constants*`
   files into code, docs or chat. Use placeholders.
5. Product-owner documents: short, plain words, the gap or issue highlighted first, no jargon
   (`.claude/core/reference/review/plain-english.md`); each also gets an offline HTML copy
   (`python .claude/core/scripts/md_to_html.py <file.md>`).
6. Replies to the user: 6 lines or fewer unless asked, plain words, end with one status line and `Next:`.
7. The core is changed only in `core/`; then `python core/scripts/install.py .` installs it here and
   `--check` must be clean. Every other repo gets the same version with the same command, in the same change:
   product-factory, Blend, TalentBox and the plugin stay in sync (SkillsOS uses the plugin, no repo install) unless the developer asks for a change in one
   project only (then it goes in that project's own files and the reply says which projects differ).

<!-- core:start -->
## How work flows (agent core - managed by install.py, do not edit between the markers)
Triage every request first (`sdlc` skill, the router), without asking which lane. Each flow skill owns one job and hands over through the work folder (`status.json`: stage, skill, `next`):
- **Answer**: questions, "discuss", "explain" - answered directly (big searches go to `explorer`); "plan", "review this" and "don't change" change no code.
- **Setup work**: the AI setup only (`.claude/`, `.cursor/`, `AGENTS.md`, `CLAUDE.md`, `setup_paths`) - done by the main session, no task; then `python .claude/core/scripts/cursor_sync.py`, and its `--check` must be clean.
- **Requirements** (`/review-spec`): a ticket or document to make ready - plain words, the Definition of Ready, one gate with the requester; no code. Ends READY, then `/develop`.
- **Feature or change** (`/develop`): the Definition of Ready check, `explorer`'s context pack, risk from evidence, only the agents needed, the safety net, one code review. Ends ready for `/test`.
- **Bug** (`/fix`, also `/fix BLEN-1 F1 F3` for fix-list items): a proven root cause first, the fix with a regression test, a re-review. Ends with `/test retest`.
- **Test** (`/test BLEN-1 BLEN-2`, `/test retest BLEN-1`, `/test data`, `/test smoke`): the QA team, with `test-data-engineer` for the data and `qa-lead`'s smoke pack; ends SIGNED OFF (then the commit message) or with a fix list (then `/fix`). Fixes never start by themselves.
- **Product** (product mode): an idea, a PRD or "build a new product" - the `factory` skill, with a gate at each decision.

Hard rules (in a repo with `.claude/project.json` the hooks enforce most of them, in Claude and Cursor):
- The main session is the Tech Lead: it triages, decides, briefs, routes, integrates and verifies, and never writes product code (everything outside the AI setup and the work folder). It stops the developer only for something to decide: gaps, decision cards D1-D8 and prototype picks. Size sets depth inside `/develop` and `/fix` (a small path), never a lane.
- No git command that changes the repo (commit, push, pull, fetch, merge, stash, reset, checkout, add, ...); read-only git is fine. `git pull` only when the developer asks for it in their own message.
- Never start or restart servers (say what needs a restart and why). Never copy secret values.
- The live page is the only tracker; never make another tracker page or artifact. Open it with `python .claude/core/scripts/live_status.py open <id>`.
- Automated tests go in the project's test folder, mirroring the package of the code under test (Java `src/test/java/<same package>/`), never in `src/main/**` or the repo root; the scratchpad holds only throwaway scripts.
- Core files (`.claude/core/`, the core agents and skills listed in `.claude/core/core.lock`) change only in the core source (product-factory `core/`) and are installed in every project in the same change; `python .claude/core/scripts/install.py . --check` lists hand edits.

The detail (the agents and their models, how they work, the safety net, QA, the hooks, the live page and the sync rules) is in `.claude/core/reference/how-work-flows.md`: read it before a Task or a Product. Cursor reads this file and `.claude/skills/` directly and runs the `.cursor/` agents, rules and hooks that `cursor_sync.py` generates.
<!-- core:end -->
