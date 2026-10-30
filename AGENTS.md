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
   `--check` must be clean. Every other repo gets the same version with the same command.

<!-- core:start -->
## How work flows (agent core - managed by install.py, do not edit between the markers)
Triage every request first (`sdlc` skill), without asking which lane:
- **Answer**: questions, "discuss", "explain" - answered directly (big searches go to `explorer`). "plan", "review this" and "don't change" change no code.
- **Quick fix**: obvious and small (up to ~30 lines in up to 3 files, nothing to decide) - done directly, then `python .claude/core/scripts/live_status.py quick "<what>"`.
- **Setup work**: changes to the AI setup only (`.claude/`, `.cursor/`, `AGENTS.md`, `CLAUDE.md`) - no task; run `python .claude/core/scripts/cursor_sync.py`, then `--check` must be clean.
- **Task** (task mode): every other change to an existing product - a task in the work folder (`work_dir` in `.claude/project.json`). First `explorer` writes the context pack (`context.md`: impact map with every caller, endpoint, screen and outside node as `path:line`, key code, the rules that apply, risk signals); the risk (low, medium, high) is set from that evidence; then only the agents the task needs, each reading the pack instead of exploring again. The risk sets the safety net, so nothing else breaks: compile and the full unit suite before and after, every changed file planned (scope check); at medium and high also characterization tests that lock today's outputs, every caller checked and the smoke list of each area touched (`.claude/smoke.md`). Every review MUST adds a line to `.claude/review/lessons.md`.
- **Product** (product mode): an idea, a PRD or "build a new product" - never built straight from the document: the `factory` skill runs intake, base, requirements, product review, prototype, stories, design, build, review, audit and release with a gate at each decision.

The team is picked by need, not by size; a stage with nobody on it is skipped. The developer (or product owner) is stopped only for something to decide: gaps in the brief, decision cards D1-D8 (scope, data model, API, access, UI, dependencies and config, other owners, go-live) and prototype picks - one gate per stage, with its full text in the chat and an Approve/Change question. Hooks enforce the flow in Claude and Cursor: the guard holds data-model, access and config edits until their card is approved, blocks git commands that change the repo (pull passes only when the developer asked for it) and generated files, and (product mode) blocks product code before the base stage or the design approval; a rules check runs after each edit; a turn that changed files outside these lanes is sent back once. The reviewer fails any change with a MUST from the review checklists. The live page shows every task and is the only tracker (never make another tracker page or artifact): `python .claude/core/scripts/live_status.py open <id>`.

## Agents and skills (agent core)
- Flow skills: `sdlc` (triage, task mode), `factory` (product mode), `prototype`, `dev-handoff`, `commit-msg`, `verify-push`, `live-check`.
- Agents: `explorer` (search), `spec-analyst`, `bug-investigator`, `product-critic`, `story-sizer`, `ux-designer`, `solution-architect`, `data-architect`, `security-architect`, `base-builder`, `backend-developer`, `frontend-developer`, `integration-engineer`, `devops-engineer`, `performance-engineer`, `code-reviewer`, `qa-engineer`, `verifier`, `audit-expert`, `release-manager`; domain experts `sf-expert`, `ai-engineer`, `n8n-expert` (repo facts in `.claude/experts/`). This repo's own agents, area skills and path rules sit next to them.
- Every agent reads the task's `context.md` first, writes its output file first, uses about 35 tool calls if it decides (spec, design, review, audit, domain experts) or about 20 otherwise, at most 3 web lookups, and replies in 10 lines or fewer. Reviewers are read-only. Models: every agent on Opus.
- No git command that changes the repo (commit, push, pull, fetch, merge, rebase, stash, reset, checkout, switch, restore, add, branch, tag, ...); read-only git (status, diff, log, show) is fine. `git pull` only when the developer asks for it in their own message. Never start or restart servers (say what needs a restart and why); never copy secret values.
- Core files (`.claude/core/`, the core agents and skills listed in `.claude/core/core.lock`) are changed only in the core source and installed with its `install.py`; `python .claude/core/scripts/install.py . --check` lists hand edits.
- Claude Code reads this file through `CLAUDE.md`; Cursor reads it directly and loads `.claude/skills/` itself. The Cursor agents, rules and hooks in `.cursor/` are generated by `cursor_sync.py`; every setup change must keep working for Cursor in the same change.
<!-- core:end -->
