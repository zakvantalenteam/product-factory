# Shared agent core - plan

29 Oct 2026. Draft for Zakvan's OK. Nothing outside `core/` has changed.
Backup of the current setup: `D:\product-factory-backups\2026-10-29\` (`.claude`, `.cursor`, `CLAUDE.md`,
`AGENTS.md`, `scripts`, `standards`, `base`: 72 files).
Recommended first: put `D:\product-factory` in git before the switch-over (you do the git), so step 3 can be undone.

## 1. Goal
One product-neutral core (agents, skills, hooks, scripts, reference) lives in `D:\product-factory\core\`.
Every repo uses the same core plus a small project layer. Fixes are made once in the core and reach every
repo through `install.py` today, and through a Claude Code plugin later.

The core runs two modes. A single triage step picks the mode:

| Mode | When | Flow |
|---|---|---|
| Product | an idea, PRD or "build a new product" | product-factory flow: intake, base, requirements, product review, prototype, stories, design, build, review, audit, release (S0-S9 + SP) |
| Task | a change to an existing product | Blend triage flow: answer / read-only / setup / quick fix / task, team by need, one review pass |

Both modes use the same live page, the same gates in chat (Approve/Change), the same decision cards D1-D8 and
the same guard.

## 2. Layout (plugin-ready)
```
core/
  .claude-plugin/plugin.json      name, version, description (plugin manifest)
  agents/*.md                     20 core agents + 2 domain experts
  skills/<name>/SKILL.md          sdlc, factory, prototype, dev-handoff, commit-msg, verify-push, live-check
  hooks/hooks.json                plugin hook wiring (${CLAUDE_PLUGIN_ROOT})
  hooks/guard.py rules_check.py flow_check.py
  scripts/live_status.py .html handoff_check.py cursor_sync.py install.py
          codemap.py crlf_edit.py md_to_html.py check_base.py
  reference/review/               checklist.md (generic sections), decision-card.md, plain-english.md
  reference/standards/            api, data, fe-be-split, definition-of-done, sizing, successfactors
  reference/base/                 BASE-SPEC.md, base-manifest.json (product mode S1)
  reference/platform-btp.md       BTP Cloud Foundry facts, moved out of devops-engineer
  templates/                      project.json, AGENTS core block, experts/*.md stubs
  VERSION
```
How it is installed in a repo. Everything core-owned is under `.claude/core/`, except agents and skills,
which must sit where Claude and Cursor load them:
```
.claude/agents/<core>.md + project agents     .claude/skills/<core>/ + area skills
.claude/core/{hooks,scripts,reference}/       core-owned, never hand-edited (core.lock has hashes)
.claude/project.json                          project config (section 5)
.claude/experts/<sf|ai|...>.md                repo facts for the domain experts
.claude/review/checklist.md                   project checklist sections (path-triggered)
.claude/rules/*.md                            path rules (Cursor: .mdc)
.claude/settings.json                         project-owned; install.py manages only the core hook entries
.claude/work/<id>/                            tasks (gitignored); product-factory uses work/<slug>/
```

## 3. Core vs project layer
| Core (same everywhere) | Project layer (per repo) |
|---|---|
| Triage lanes, quick-fix limits (~30 lines, 3 files), task flow, product flow | AGENTS.md: stack, build/run, repo map, hard rules |
| Agents, flow skills, decision cards D1-D8, gates in chat | `project.json`: commands, ports, protected paths, decision triggers, rules |
| Guard engine: git blocks, secret files, generated files, big reads, decision holds, code-writes gate | Area skills (`n8n-node`, `labels`, `admin-page`, ...) and path rules |
| rules_check engine, flow_check, live page, handoff check, Cursor sync | Domain facts (`.claude/experts/*.md`), project checklist sections, glossary words |
| Reference: standards, DoD MUST list, decision card, plain English, base spec | Project-only agents (`n8n-expert` for Blend) and scripts (`hana_query.py`, `n8n_node.py`, `props.py`) |

## 4. Agents: 37 combined -> 20 core + 2 domain experts
Sonnet by default and Haiku for search. Opus only for `solution-architect` and `audit-expert`; the lead may
pass `model: opus` for product-mode SP/S5 on a size-L product. Today product-factory has 16 agents on Opus.
Every agent: `Team:` line, output file first, ~20 tool calls, at most 3 web lookups, reply in 10 lines or
fewer, long reference text moved to `reference/` files that are read only when needed, under ~60 lines.

| Core agent | Built from | Action | Model | Why |
|---|---|---|---|---|
| explorer | blend-explorer | rename | haiku | cheap read-only search in any repo |
| spec-analyst | Blend spec-analyst + prd-reviewer + requirements-analyst | merge; modes `prd-review`, `spec`, `task`, `revise` | sonnet | one owner for "is the request understood"; brief/gaps in both modes |
| bug-investigator | Blend | keep | sonnet | proven root cause before a fix (task mode) |
| product-critic | pf | keep | sonnet | independent "good product?" verdict (product mode, or a large new feature) |
| story-sizer | pf | keep | sonnet | backlog, points, MVP slice (product mode, multi-story features) |
| ux-designer | pf ux-designer + prototype-designer + Blend ui-engineer | merge; modes `journeys`, `options`, `variants`, `ui-spec`, `ui-review` | sonnet | one design owner; the `prototype` skill stays for quick variants by the main session |
| solution-architect | Blend + pf solution-architect + api-designer | merge; modes `design`, `contract` (OpenAPI) | opus | design plus D3/D6 cards; still runs in parallel with data-architect |
| data-architect | Blend + pf | merge | sonnet | D2 card with "Data model explained"; volume rules from standards |
| security-architect | pf | keep, joins by need | sonnet | D4 card when roles, personal data or outside access change; threat model in product mode |
| base-builder | pf | keep | sonnet | product S1; also installs the core into the new product root |
| backend-developer | pf | keep | sonnet | product-mode build per story (task mode: the main session builds) |
| frontend-developer | pf | keep | sonnet | same, screens |
| integration-engineer | pf | keep | sonnet | outside systems: contracts, sync jobs, retries |
| devops-engineer | pf | keep; BTP facts moved to reference | sonnet | environments, pipeline, deploy plan |
| performance-engineer | Blend + pf | merge | sonnet | time budgets, baseline, design and build checks |
| code-reviewer | Blend (+ pf DoD mapping) | merge | sonnet | one pass that re-checks its own findings, keeps those scored 80+ |
| qa-engineer | pf qa-engineer + Blend test-runner | merge | sonnet | tests per criterion, before/after for refactors, never kills the running app |
| verifier | blend-verifier + system-reviewer | merge; modes `change`, `system` | sonnet | PASS/FAIL per criterion; whole-system fit in product mode |
| audit-expert | pf | keep | opus | independent go-live audit against the fixed DoD MUST list |
| release-manager | Blend + pf release-manager + technical-writer | merge; docs only when asked | sonnet | go/no-go, release notes, rollback |
| sf-expert (domain) | Blend sf-expert + pf sf-consultant | merge | sonnet | generic SuccessFactors knowledge; repo facts in `.claude/experts/sf.md` |
| ai-engineer (domain) | Blend | keep | sonnet | models, prompts, cost, latency, evals; repo facts in `.claude/experts/ai.md` |

These move into a merged agent or stop as separate files: prd-reviewer, requirements-analyst,
prototype-designer, ui-engineer, api-designer, system-reviewer, technical-writer, test-runner, sf-consultant,
blend-explorer, blend-verifier. `system-reviewer`'s design mode is now done by `handoff_check.py` (mechanical
cross-checks: every criterion has a change, every operation has a role) plus `verifier system`.
Project layer only: `n8n-expert` (only Blend uses n8n).

## 5. How a product repo plugs in
1. AGENTS.md keeps the repo's own facts and hard rules. `install.py` adds and refreshes one marked block,
   `<!-- core:start --> ... <!-- core:end -->`: the lanes, the modes, the agent list and the Cursor rule.
2. `.claude/project.json` holds every per-repo difference that is hard-coded today:
```json
{
  "name": "Blend", "ticket_prefix": "BLEN-", "work_dir": ".claude/work", "live_port": 8766,
  "app": {"url": "http://127.0.0.1:8080/lxp/", "status": "python .claude/scripts/app_status.py"},
  "commands": {"compile": "mvn -o -q compile -DskipTests", "test": "mvn -o -q surefire:test \"-Dtest={tests}\""},
  "guard": {
    "git_blocked": ["push", "commit", "stash", "reset", "checkout"],
    "blocked_commands": [{"pattern": "(^|\\s)\\./mvnw", "why": "Maven 3.5.4 is too old; use mvn"}],
    "block_while_app_up": "mvn .*(compile|package|install|clean)",
    "secret_files": ["application-local.properties"], "no_show": ["application*.properties", "*Constants.java"],
    "generated": ["createDDL.jdbc", "approuter/resources/**", "target/**"], "big_file_kb": 120,
    "read_only_roots": []
  },
  "quick_fix": {"max_files": 3, "max_lines": 30,
                "never": ["pom.xml", "application*.properties", "n8n_workflows/**", "**/domain/**", "*Entity.java"]},
  "decisions": {
    "D2": {"paths": ["src/main/java/**/*.java"], "markers": ["@Entity", "@Embeddable", "@MappedSuperclass", "@UpgradeJob"]},
    "D4": {"markers": ["@CheckPermission", "@PreAuthorize", "hasRole("]},
    "D6": {"paths": ["pom.xml", "src/main/resources/application*.properties"]}
  },
  "rules": [{"id": "rule 2", "paths": ["**/*.java"], "pattern": "@(Join)?Column\\([^)]*name\\s*=\\s*\"\\\\\"",
             "message": "quoted column name breaks schema validation"}],
  "experts": ["sf-expert", "ai-engineer", "n8n-expert"],
  "glossary": {"code_words": "\\bLXP_[A-Z_]+\\b", "words": ".claude/review/words.md"}
}
```
3. Area skills, path rules, domain facts (`.claude/experts/*.md`) and project-only agents sit next to the
   core files. `install.py` never touches a file that is not in `core.lock`.
4. Decision triggers, quick-fix limits and protected paths come only from `project.json`. The core has no
   repo names, ports, stacks or paths in its code (today Blend, TalentBox and SkillsOS each patch them by hand:
   ports 8766/8767/8768, verifier names, glossary lists, checklist ids).

## 6. Hooks and scripts (merged)
| Core file | Built from | Does |
|---|---|---|
| `hooks/guard.py` | Blend guard + pf flow_guard | git blocks, secret and generated files, big reads, command blocks; holds D2/D4/D6 edits until the card is approved; product mode: no code in the product root before S1 or G3; read-only reference roots |
| `hooks/rules_check.py` | Blend rules_check | runs `project.json` rules on added lines only, after each edit |
| `hooks/flow_check.py` | Blend flow_check + pf intake_guard | prompt: triage reminder, PRD hold-on (product lane); stop: send back once when lanes are broken or stages are left |
| `scripts/live_status.py/.html` | Blend live_status + pf tracker.py | one live page; stage sets `task` and `product`; port from config; agent rows from hooks (replaces factory_tracker) |
| `scripts/handoff_check.py` | Blend | gate documents complete; glossary from config |
| `scripts/cursor_sync.py` | Blend (generic) | `.cursor/agents`, `.cursor/rules`, `.cursor/hooks.json` from `.claude/` |
| `scripts/install.py` | new | install, update, `--check` (section 8) |
| `check_base.py`, `md_to_html.py`, `codemap.py`, `crlf_edit.py` | pf, Blend | product S1 check, offline HTML, big-file maps, CRLF-safe edits |

Every script finds the repo from `CLAUDE_PROJECT_DIR` / `CURSOR_PROJECT_DIR` / cwd, never from its own
location, so the same files run from `.claude/core/` or from a plugin folder. Hook commands use
`$CLAUDE_PROJECT_DIR`, not a relative path. Seen today: product-factory's relative
`python .claude/hooks/flow_guard.py` fails and blocks every Write once the shell's cwd moves. Hook agent
names drop a `plugin:` prefix, because plugin agents are named `<plugin>:<agent>`.

## 7. Cursor
Cursor cannot load Claude plugins, so the repo keeps real files for Cursor. `cursor_sync.py` writes the
following from `.claude/`: `.cursor/agents/*.md` (model inherit, readonly for reviewers),
`.cursor/rules/*.mdc` (from path rules) and `.cursor/hooks.json` (guard, rules_check, live_status,
flow_check stop, via Blend's launcher that finds the project root). Cursor reads AGENTS.md and
`.claude/skills/` directly. The stop hook and `install.py --check` both fail when the copies are stale.
The two gaps that remain are the same as in Blend: no prompt context (the rule lives in AGENTS.md) and no
SubagentStop (fallback: `expert ... done`).

## 8. Install and update until it ships as a plugin
`python D:\product-factory\core\scripts\install.py <repo> [--check | --dry-run]`:
- copies the core agents, skills and `.claude/core/` into the repo and writes `.claude/core/core.lock`
  (version and file hashes);
- refreshes the AGENTS.md core block, merges the core hook entries into `.claude/settings.json` (it shows the
  diff first), adds `.claude/work/` to `.gitignore`, then runs `cursor_sync.py`;
- `--check` lists core files edited by hand, missing files, an old version and stale Cursor copies. It never
  overwrites a hand-edited core file; it prints it so the fix moves into the core.
Plugin later: the same `core/` folder is the plugin (`/plugin install` from the org catalog). Claude then gets
agents, skills and hooks from the plugin. `install.py --cursor-only` keeps the repo copies that Cursor
needs. Check before shipping: how plugin skills refer to `${CLAUDE_PLUGIN_ROOT}` scripts.

## 9. product-factory on the core (step 3, after your OK)
- `core/` is the source. product-factory's own `.claude/` becomes an installed copy plus its project layer:
  `work_dir: work`, `products_root: D:/products`, `read_only_roots: [D:/skillos]`.
- Product mode: `live_status.py init <slug> --mode product` replaces `new_product.py`. The product root lives
  in the task. `base-builder` installs the core into every new product root, so each product starts on it.
- Task mode: a change to an existing product (for example DeskBook) runs either in that product's repo or from
  here with `--root D:/products/<slug>`.
- DeskBook (S9, last write 11:11 today, product root `D:/products/desk-booking`) keeps its old tracker files.
  The switch happens only with your go, when no DeskBook session is running. The backup stays.

## 10. Build order and checks (about 3 h after the OK)
1. Scripts and hooks made config-driven (largest part), with `project.json` templates for the 4 repos.
2. 22 agents and 7 skills, short, with reference files.
3. `install.py` and `cursor_sync.py`; install into a scratch copy of product-factory and of Blend (read-only
   source), then run both modes end to end in the scratchpad. Blend's test suites are ported there.
4. Your OK to switch product-factory's `.claude/`. Then `install.py --check` and `cursor_sync.py --check`
   must both be clean.
5. Migration list for Blend, TalentBox and SkillsOS: each repo's `project.json`, renames
   (`blend-verifier` -> `verifier`, `test-runner` -> `qa-engineer`, `ui-engineer` -> `ux-designer`), script
   paths (`.claude/scripts/live_status.py` -> `.claude/core/scripts/`), and what stays project-only.

## 11. Decided by default (say if you want otherwise)
- Agent names keep the Blend name where the job is the same (`spec-analyst`, `sf-expert`, `code-reviewer`)
  and the broader name otherwise (`qa-engineer`, `ux-designer`).
- The `factory` (product mode) and `sdlc` (triage, task mode) skill names stay.
- Core files are installed under `.claude/core/`, so the core and the project layer can never mix.
- Git (1.2.0): every command that changes a repo is blocked (25 verbs); `pull` passes only for the turn after the
  developer asks for it (`guard.git_on_request`). Read-only git is fine.

## 12. 1.3.0 - a lead that understands the task first, and a safety net so nothing else breaks
Asked for: a lead that understands the requirement and its complexity, picks only the agents needed, is fast,
and never ships a change that breaks something else.

| Part | What it does | Where |
|---|---|---|
| Context pack | Before the team is picked, `explorer` (Haiku, mode `context`) writes `<work>/<id>/context.md`: the impact map from `impact.py` (for every touched file or symbol its callers, REST endpoints, the screens, scripts and templates calling them, n8n nodes, MCP tools, each `path:line`; stdlib only, by name, about 1-3 s on Blend; misses interface dispatch and reflection, so a hit with no import is marked "name only"), key code, the rules that apply (checklist, path rules, lessons), risk signals and gaps. Every later agent reads it first and only fills a named gap, which it adds under `## Gaps`. | `scripts/impact.py`, `agents/explorer.md`, the "Context:" line in every agent |
| Risk from evidence | The lead sets low, medium or high from the pack (data model, a contract others call, permissions, an outside system, number of callers, unknowns). `triage.md` has the `Risk:` line, `## Risk evidence`, the team with a reason per agent and `## Not needed`. Risk sets the depth of the safety net, not the number of reviewers. | `skills/sdlc` sections 2-3, `handoff_check.py` |
| Safety net | Low: compile, full unit suite before and after, scope check. Medium and high add: characterization tests in the scratchpad (`qa-engineer` mode `characterize`) that lock today's outputs of every changed shared method and must match after Build except the spec's intended changes; every caller in the impact map checked (the reviewer marks an unchecked one MUST); Verify runs the smoke items of each area touched. All recorded in `safety.md`. | `char_test.py`, `scope_check.py`, the `flow_check` stop hook, `templates/smoke.md`, `code-reviewer`, `verifier`, `qa-engineer` |
| Scope check | At Build start a baseline of what is already uncommitted; afterwards every changed file must be in `## Planned files` (design.md, else triage.md) or added with a reason. The stop hook sends a turn back once while one is left. | `scope_check.py`, `hooks/flow_check.py` |
| Lessons loop | Every review MUST and every later bug adds one line to `.claude/review/lessons.md`; agents read the lines for their area and the reviewer fails a repeat. | `templates/lessons.md`, `skills/sdlc` section 9 |
| Speed | Explorer on Haiku, most agents on Sonnet, Opus only for high-risk architecture and audits. Design experts in parallel; Review and Test in parallel after Build. Medium risk has one gate for understanding and plan; low none. Stage time budgets by risk (overridable in `budgets`), an overrun flag on the live page, `timing.py` for where the time went. | `skills/sdlc` sections 4, 6-8, `live_status.py`, `timing.py` |

- New project keys: `commands.test_all` (full unit suite), `commands.char_run` (how to run one characterization test,
  `{file}`), `impact` (where to look for callers, endpoints, screens, outside nodes), `budgets`.
- New project files, written by `install.py` when missing and never overwritten: `.claude/smoke.md`,
  `.claude/review/lessons.md`.
- Tasks started before 1.3 (no `context.md`, no `Risk:` line) get hints, not problems, so work in flight is not held up.
- Product mode is unchanged apart from the lessons file the reviewer reads.
- Blend moves onto the core first (its fixed Ask and Pulse review items mined once into its checklist or lessons);
  then the timing report compares its next 3-5 tasks with review-next16 (spec 45, design 14, build 47, review 29 min).
  TalentBox and SkillsOS follow only on the developer's word.

## 13. 1.3.1 - fixes from moving TalentBox
- The app-up check never follows a redirect (a 302 to a login host that is down still means the app is up) and
  treats only 502-504 as starting; a 500 is up. With `app.strict` only a 2xx counts, as before.
- An access or data-model marker moved to another method (same lines, different method) needs its card.
- The Cursor live hook answers "allow" even when its input cannot be read (Cursor waits on a reply).
- `git clean --force` is blocked like `-f`.

## 14. 1.3.2 - fix from moving SkillsOS
- Only an annotation marker is tied to the method below it (1.3.1). A guard call inside a method body
  (`adminGuard.requireAdmin(`) keeps only its own line, so a statement added after it no longer needs the card.

## 15. 1.3.3 - ai-engineer: baseline, evals with thresholds, honest budgets
- `ai-engineer` writes the baseline before any recommendation, marks every step deterministic or LLM and every
  number measured, calculated, estimated or assumed, and gives P50/P95, time to first token, retries and cost per
  successful task. Each recommendation names its eval and threshold and what stays unchanged. Depth follows the
  task's risk; no section or eval that would not change the decision; project rules and quality gates win.
- `reference/domains/ai.md` gains orchestration safety, retrieval and grounding, eval types and thresholds, and
  budget metrics (read only when the task needs them).

## 16. 1.3.4 - flow simulator
- `scripts/simulate.html`: a self-contained page with 9 requests (a question, a quick fix, setup work, low,
  medium and high risk tasks, a bug, an AI change, a new product). It steps through the lane and its reason, the
  context pack, the risk and its evidence, the team (model per agent, why each joins or is left out), stages,
  files, gates (Approve, Change, Ask) and checks, with toggles for a review bug, an unplanned file and a running
  app, and a clock of estimated agent minutes against the measured review-next16 run. Two layouts, A (stepper
  with a why panel) and B (pipeline board), until one is picked.
- `scripts/simulate.py <scenario>` copies the page into the work folder and replays the request as the demo task
  `demo-<scenario>` through live_status's own commands. Demo tasks never bind a session (so the stop hook never
  sees them), never write live.js, are left out of timing reports unless named, and `--clean` removes them.

## 17. 1.3.5 - every agent in the simulator
- An Agents view: every core agent, the two domain experts and the repo's own agents (read from `.claude/agents/`),
  each with what it does, when it joins and when it is left out, its model, what it reads and writes, who it hands
  to and its time budget; picking one marks the requests it works on and outlines it in the flow.
- The requests use every agent: a SuccessFactors change (sf-expert, integration-engineer, security-architect) was
  added, the new product uses every product agent, and a repo with its own agents gets a request that uses them.
- Request texts are product-neutral (no repo's names), since every repo shares them.
- `simulate.py` opens the live page when run in a terminal (`--open`/`--no-open`), starting the live-status server
  as `live_status.py open` does; the simulator page shows the request's live tracker below the flow.

## 18. 1.3.6 - every agent on Opus
- Every core agent runs on Opus (its own `model:` line), `explorer` included, so work comes back right the first
  time; briefs need no model override.
- The agents that decide (spec-analyst, bug-investigator, solution-architect, data-architect, security-architect,
  code-reviewer, performance-engineer, product-critic, ux-designer, audit-expert, sf-expert, ai-engineer) get
  about 35 tool calls and 50 turns; the others keep about 20.
- The simulator shows each agent's model and budget from the same data.

## 19. 1.3.7 - n8n-expert in the core
- `n8n-expert` moves from Blend into the core as the third domain expert (Opus, about 35 tool calls): design
  (`n8n.md` / `05-n8n.md`), build only with the developer's OK for the workflow owner's workflow, review
  (`review-n8n.md`). Generic knowledge in `reference/domains/n8n.md`; each repo's facts in `.claude/experts/n8n.md`
  (template `templates/experts/n8n.md`).
- live_status, handoff_check, the checklist, the factory and spec-analyst tables, flow-files and the simulator know
  it; the AI request in the simulator uses it at Design.

## 20. 1.3.8 - on GitHub: sync bot and Claude plugin
- The home repo (product-factory) is a Claude Code marketplace (`.claude-plugin/marketplace.json`, name talenteam)
  with one plugin, product-factory (agent-core before 1.4.0), built into `plugin/` by `scripts/build_plugin.py` (paths into the core become
  `${CLAUDE_PLUGIN_ROOT}/`); install.py rebuilds it when it installs into the home repo. In a repo without the core,
  the plugin's SessionStart hook hands Claude the core block of AGENTS.md.
- Repos that carry the core switch the plugin off (`enabledPlugins: {"product-factory@talenteam": false}`, written by
  `--write-settings`, checked by `--check`), so no hook runs twice.
- `.github/workflows/core-sync.yml` runs `.github/core-sync/sync.py` on each push to main that changes the core:
  per repo in `targets.json` it installs the core, runs both checks and pushes one commit to dev, or opens a pull
  request when a person must look (first install, hand-edited core files, failed checks, protected branch).

## 21. 1.3.9 - non-functional needs and where it runs, asked early
- Product S0: `devops-engineer` (infra) writes `00-infra.md` next to the PRD review: platform, region, runtime,
  database, sign-in, environments, domains, CI/CD, secrets, monitoring, backup, cost, who deploys. Its questions
  join G0 (at most 10 questions in all, the platform first while open); the base (S1) waits for the platform.
- Product S2: `spec-analyst` writes `02-nfr.md`, one `N<n>` row per need with a number, who designs it and what
  checks it; it joins G1, every design expert reads it at S5, and its approved rows are extra MUSTs at the audit.
- Task mode: `.claude/project.json` `deploy` holds the deploy facts; when missing, any task (quick fixes too) asks
  the developer once and records the answer. `spec.md` gets `## Non-functional` for the needs a change touches.

## 22. 1.4.0 - the plugin is called product-factory
- The plugin is `product-factory` (it was `agent-core`), by TalenTeam Product & Engineering, in the `talenteam`
  marketplace of the public repo `zakvantalenteam/product-factory`. Its agents show as `product-factory:<name>` and
  its skills as `/product-factory:<name>`.
- install.py writes `"product-factory@talenteam": false` in repos that carry the core and removes the old
  `agent-core@talenteam` entry. Plugin users switch `enabledPlugins` to the new id.
