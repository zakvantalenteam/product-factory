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
| `.claude/` | the core installed for this repo (`install.py`), plus `project.json` (work folder `work`, products under `D:/products`, read-only `D:/skillos`) |
| `work/<slug>/` | one folder per product or task: every document, question and decision, and its live status |
| `D:/products/<slug>/` | the product roots (code), outside this folder |
| `standards/`, `base/`, `scripts/` | legacy copies kept for the DeskBook run; the core's own copies are in `core/reference/` and `core/scripts/` |

## Hard rules
1. Git: no command that changes a repo (commit, push, pull, merge, stash, reset, switch, checkout, add, ...); read-only
   git is fine. `git pull` only when the developer asks for it in their own message. The developer does git. (This folder is not a git
   repo yet: nothing here can be undone, so back up before changing setup files.)
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
