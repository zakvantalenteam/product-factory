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
- Each person's plugin manager alone switches the plugin on or off (no project `enabledPlugins` entry since 1.11.1).
  In a repo that carries the core, the repo copy's hooks step aside while the plugin is on, so no hook runs twice.
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
- The plugin is `product-factory` (it was `agent-core`; shown as "Product Factory" through `displayName` in
  `.claude-plugin/marketplace.json`), by TalenTeam Product & Engineering, in the `talenteam`
  marketplace of the public repo `zakvantalenteam/product-factory`. Its agents show as `product-factory:<name>` and
  its skills as `/product-factory:<name>`.
- install.py writes `"product-factory@talenteam": false` in repos that carry the core and removes the old
  `agent-core@talenteam` entry. Plugin users switch `enabledPlugins` to the new id.

## 23. 1.4.1 - every screen goes to ux-designer; the live page is the only tracker
- sdlc: a new or changed screen, however small, gets `ux-designer` at Design (mode `variants`); the main session
  never designs a screen itself. The prototype skill says the same inside a flow.
- The core block of AGENTS.md: the live page is the only tracker; no other tracker page or artifact.

## 24. 1.4.2 - review and design from a pack
- Evidence (Blend, 28-30 Oct): one `code-reviewer` run took 5-13 min and 36-55 tool calls, most of them `git diff`
  per file, grep and sed, after reading 10-15 documents; the Review stage took 17-30 min with several reviewers, a
  check pass and a full re-review after each fix. `solution-architect` took 6-12 min and 27-61 calls and explored
  again despite context.md. Opus stays; the time comes out of the turns.
- `scripts/review_pack.py <id>` writes `review-pack.md` in seconds: pre-filled MUST rows (unplanned files from the
  scope check, the safety net at risk medium or high, callers nobody checked), the criteria, the approved cards and
  fixed answers, the caller table, and only the checklist sections whose path trigger matches a changed file (core
  sections have a `Paths:` line; project sections keep the globs in their heading; a project item replaces the core
  item of the same id), the hard rules, the path rules, the lessons for those paths and the matching live checks,
  then the diff with new-side line numbers (new files in full, capped, secret values masked). `--files`, `--base`
  and `--head` pack given files or a commit range; `--root` a product root.
- Re-review is a delta: `review-state.json` keeps a hash and a copy of each packed file; once `review.md` exists the
  next pack holds only the files changed since then (as the change since the review), the files whose PASS stays
  and the previous MUST rows to re-check.
- `code-reviewer` reads the pack and nothing else up front, opens code only to prove or drop a finding, about 20
  tool calls, maxTurns 30. One reviewer by default; an expert pass (ui, speed, sf, ai, n8n) joins only when most of
  the change is its area and reads the same pack. The separate `check` pass is gone: `code-reviewer` merges expert
  files that are there, and any MUST in `review.md` or a `review-<x>.md` fails the review.
- `review_pack.py <id> --design` writes `design-pack.md` (criteria, fixed answers, impact rows, the decision cards
  the paths may need, hard rules, path rules, repo facts from `.claude/experts/`, lessons) and, when there is no
  design.md, a skeleton with one Changes row per criterion and one Impact map row per impact line. Every `<fill>`
  left fails handoff_check. `solution-architect` fills it from the pack and context.md, explores only a named gap,
  about 20 calls in task mode (35 in product mode), maxTurns 40; domain experts run in parallel from the same pack.

## 25. 1.4.3 - the live page shows who is working
- Evidence (Blend ask-perf-capacity, 30 Oct): Design ran 3 experts in the background; the page named one of them,
  and 26 of 203 tool calls in the replay went to the wrong agent: with no `agent_type` the hook credited the
  stage's last-started expert, so the main session's own calls showed as `performance-engineer`.
- The hook credits a call by what Claude sends: no `agent_type` is the main session; `agent_id` ties a run to its
  expert row (bound from the background launch's `agentId`, else the first working row of that agent not yet
  taken), so two runs of one agent stay apart; events keep the run id. Cursor's tool hooks name no agent:
  `subagentStart` (now in `.cursor/hooks.json`) binds the subagent's conversation to the task and its row, and
  `subagentStop` reads `subagent_type`. Replay of the Blend session: 0 of 203 wrong.
- The page (`live_status.html`): a "now working" card while a stage has 2 or more experts or a background agent,
  one row per agent (main session first) with its team colour, role, latest action ("Waiting for ..." for the
  main session, "Wrote <file>" when done), tool calls against the "about N" of its Speed line (`calls` and `now`
  in status.json) and its time; the header says "N agents working in parallel"; the stage's activity below it has
  an agent tag per row and agent filter chips (kept in the browser), and only new rows animate.
- The demo run and the simulator's medium request run Design with 3 experts in parallel.

## 26. 1.4.4 - the working agent always shows
- Zakvan (2 Nov, Blend plan-overdue-window): the page showed the running stage but not which agent works or what it
  does; the card stayed hidden because only one agent (the main session) was working.
- The now-working card shows whenever a stage runs, waits or is being fixed, one agent or many; the activity list
  under it stays for 2 or more agents (the stage row already lists one agent's activity).
- The running stage's agent stands out: a tag in the stage colour with a breathing dot instead of grey text, and
  the header names the agent before its latest action ("main session: Ran ...").

## 27. 1.5.0 - the live page shows each agent's work in plain words
- Zakvan (3 Nov): "card per agent with rolling 3 items per agent"; the steps felt like loading, not working; no
  card on the page should look like a typical website card; inside each stage the working agent must be clear.
  Approved design: variant B of Blend `.claude/work/live-rolling/prototype.html` (a replay of review-next9-p2).
- Runs: the hook keeps one run per agent launch (`runs` in status.json): its job (the Agent call's description,
  else the plan row's why), its steps, its calls against the "about N" of its Speed line, its job phase (read the
  brief, look into it, write its file, check and finish) and, when it stops, its summary for people. A run is
  bound by Claude's `agent_id` (from the background launch's `agentId`, else the first call), Cursor's
  `subagentStart`, else the newest live run of that agent; it stops on SubagentStop, Cursor's subagentStop, the
  foreground Agent result, or its row marked done. A turn limit, an abort or an error is said plainly.
- Plain steps: a Bash call shows its `description` (Cursor sends none: a short command summary); the raw command
  stays in the event, behind a details toggle, only when secret_command passes it. Read, Grep, Edit and Write
  show a verb and the file name. Steps are stored as imperatives; the page reads them as "-ing" now and past tense
  once done (a verb table).
- Summary for people: every core agent opens the output file it writes first with `## Summary for people`
  (3-5 plain lines: what it looked at, what it found or changed, the verdict or decision, what is left; an HTML
  file holds them in a comment). The hook reads the block once, when the run stops, from the first file the run
  wrote in the task folder; without it, the file's first lines, then the agent's reply.
- The page: glass panels over a slow colour field (blur, a lit top edge and tint, no shadows). Inside each stage
  one card per run, side by side: avatar with initials, name, job, calls bar, and a three-line roll (just done,
  now typing itself out, up next in its own job); a sheen crosses the card and the avatar nods on each new step;
  planned agents are dashed cards, an "Up next" line names the next agent or stage, the main session gets a card
  when it works a stage alone. Finished runs fold into a summary card (check, first line, time; opened: the
  other lines, the output file and the steps). The 1.4.3 now-working card and activity list are gone; the
  header line stays.

- Additions the same day (Zakvan): the three lines roll like variant A (all slide up one slot on a step, the up-next
  line fades in), only on the card that stepped; the other cards are not redrawn. A working agent is an orb in its
  colour that floats, blinks and glances at its step; the step's icon is a small drawn scene (reading, searching,
  writing, running) picked from its verb; the caret is hidden. The main session shows as "Tech Lead" (TL)
  everywhere on the page; status.json, events and hooks keep "main session".
- Live plan: the output file also holds `## Plan`, 4-8 `- [ ]` items the agent ticks in writes it makes anyway.
  The hook reads it on each write of that file (`run.plan`: text, done, the time first seen ticked; a finished
  run ticks the rest); a step belongs to the first item not ticked when it ran. Without a plan, the job phases
  and the times they ended; the Tech Lead's plan is the task's stages. A "Plan d/N" pill on every card (on a
  summary, right of the time) opens a glass panel (right, 410 px; a bottom sheet at 620 px or less) with a ring,
  done items with their tick time and steps, the current item with its last steps and live step, and the rest
  faint; the card's up-next line is the next item. Esc or x closes it and focus goes back to the pill.

## 28. 1.6.0 - every agent works as a certified expert
- Zakvan (3 Nov): "I want those agents to work as certified experts ... provide best solution without adding any
  complexity ... all the agents should be best in the industry type knowledge and perform superfast."
- Each of the 23 agent files has a `Certified as:` line (a real certification or industry standard for the role:
  for example OCP Java SE 17 and Spring Professional for backend-developer, AWS Solutions Architect Professional,
  SAP BTP Solution Architect and TOGAF for solution-architect, Google engineering practices, Effective Java and
  OWASP ASVS L2 for code-reviewer) and a `## Expert standard` block of 8-15 checkable rules. Files grew by at most
  15 lines: the Summary-and-plan and Context lines moved to `reference/agents/common.md`.
- `reference/agents/common.md`: the start batch (common.md, context.md and, for code work, a Grep of the stack in
  `.claude/project.json`, in one message), the output file layout, context rules, speed habits (budgets are a
  ceiling, independent reads batched, web only for version-specific facts) and the expert bar every agent shares
  (smallest good solution, reuse first, over-engineering is a defect, one rejected alternative per choice,
  evidence, versions as a ceiling).
- Stack packs in `reference/stacks/`: `java17-spring-boot3.md` (Java 17 and never above it, correctness traps,
  collections, concurrency, Spring proxies, JPA with EclipseLink, HANA and PostgreSQL, tests), `ui5-plainjs.md`,
  `react-ts.md`. `.claude/project.json` gets a `stack` key (java, spring_boot, orm, db, ui, packs), filled in all
  four repos from their pom.xml and package.json; the agents that design, write or review code read the packs it
  names.
- `review_pack.py --design` adds `## Complexity count` (new files, classes, endpoints, tables or columns, config
  keys, dependencies, each with its reason) and a "Rejected:" line to the design.md skeleton.
- Proof: an exam (3 scenarios from Blend code each for solution-architect, backend-developer and code-reviewer),
  run on the 1.5.0 and 1.6.0 files with the same prompts and graded blind against a fixed rubric, and one
  independent read of all 23 files (certifications real, rules specific, no contradiction with the hard rules,
  common.md, the packs or another agent).
- Results (3 Nov, Sonnet as the exam taker, blind grader): 1.5.0 scored 39/45 (architect 10, backend 14, reviewer 15),
  1.6.0 scored 45/45; the architect gain is the over-built parts it now cuts (a per-tenant switch, new config keys)
  and a complexity count per scenario. The independent read found outdated or wrong names (OWASP Top 10:2025 and ASVS
  5.0 now, SAP P_BTPA, C_ADBTP, C_HAMOD, C_FIORD, ITIL 4 Practitioner), task-mode files that three descriptions still
  placed in design.md, a 3 s page budget against LCP 2.5 s, a keyset example JPQL cannot run, and 19 Speed lines that
  allowed web lookups without a web tool; all fixed.

## 29. 1.7.0 - agents tagged with verified credentials and their practical knowledge
- Zakvan (3 Nov): "we need SAP certified engineers, but those engineers should be generally expert and should have
  most precious certifications in the field that applies to any software engineering company, from start up to
  enterprise, and of course Talenteam"; then "we want to get benefit of practical knowledge of such certificates" and
  "certifications should be tagged to our agents.. and read me should clearly state those".
- Each agent's frontmatter has `role:` and `certifications:` (1-4, general first, then SAP; each checked on its
  official page on 3 Nov). `project.certified_line()` writes the `Certified as:` line from that list;
  `build_plugin.py` fails on drift and writes the README "Certified agents" table between its markers (`--check`
  fails when the table is stale). cursor_sync strips the new keys (Cursor frontmatter is rebuilt from name,
  description and readonly).
- Dropped or swapped: NVIDIA NCP-AAI (not released), AWS ML Specialty (retired 31 Mar 2026), n8n Level 2 (a course,
  retired), SVPG (workshops only), Pragmatic PMC (gone), CSPO (PSPO II), ITIL 4 (ITIL Version 5), "TOGAF 10" (not a
  name), SAP-C02 (SAP-C03), EDB Associate/Professional (Essentials/Advanced), C_CPE (tests CAP, we build Spring Boot).
  No SAP BTP security credential and no respected general front-end credential exists. Watch: 1Z0-829 retires
  28 Feb 2027, the CISSP outline changes 15 Apr 2027.
- `reference/practice/<agent>.md` (23 packs, 40-80 lines): what a holder of each credential does differently on the
  job, as decision rules, checklists, traps and numbers. Each agent reads its pack in the first message with
  common.md and context.md. Agent files keep 8-12 headline rules (body +0 to +3 lines).
- `stack.platform` in project.json (template empty; `sap-btp` in all four repos). Rules marked (SAP) apply only
  there; common.md "Credentials and platform" says the agents work to the practical knowledge and do not hold the
  credentials, and bring no SAP advice to another platform.
- Live page: the plan panel shows the agent's credentials under its name (muted, 12px, separated by ·).
- Proof (3 Nov, Sonnet exam taker, blind Sonnet graders, fixed rubric, 5 points per scenario): 9 exams (sa, be, cr
  from 1.6.0, new ux, da, sec, fe, qa, ai), 1.6.0 131/135, 1.7.0 134/135. New six 87 -> 90; old three 44 -> 44 (cr +1,
  be -1 on one rubric point in all three 1.7.0 runs: it drops a pointless `@Async` for sound reasons but does not name
  the self-call caveat). One independent Opus read of the 23 packs found 3 wrong (EN 301 549 V4.1.1 now cites WCAG
  2.2 AA), 6 risky (AI Act: advisory is no exemption; SuccessFactors upserts can start workflows; Kubernetes-only
  lines read as general; the CF memory calculator; CI credentials; 403 or 404) and 4 wrong (SAP) marks; all fixed.
  The exam premise says SkillsOS is not on SAP (it is on BTP); both runs saw the same text. The pack writers did not
  see the exams; the exam author also wrote the agent rules.
- Cost: one more Read in the same first message (+1 tool call per run, no extra round trip) and about 60 lines of
  context; exam time 1326 s -> 1471 s over 9 runs (+16 s a run, inside the run-to-run spread: da 218 s and 253 s).

## 30. 1.8.0 - the Tech Lead routes, the area agents build, Sonnet for the doers
- Zakvan (3 Nov): "our agents in general take a lot of time for any task", "tech lead works the most, instead of
  taking decisions and routing work to respective expert it works itself", "I want the tracker looking at which the
  user knows exactly whats going on in agent level detail"; then "small fix should also be handed over to respective
  agent".
- The main session is the Tech Lead: triage, decide, brief, route, integrate, verify. Every product-code change goes
  to its area agent (`routing.areas` in project.json, first match wins: tests qa-engineer, build and deploy files
  devops-engineer, n8n n8n-expert, UI frontend-developer, docs release-manager, the rest backend-developer), quick
  fixes too, with a quick brief (`Job:`, `Files:`, `Quick fix:` - the files and lines, the fix, the test; about 8
  calls, no context pack); independent parts run in parallel. The lead keeps triage, gates and cards, browser live
  checks, the final checks and setup work (`setup_paths`, `.claude/`, `.cursor/`, AGENTS.md, CLAUDE.md, the work
  folder). common.md "Briefs from the Tech Lead"; agents read the area SKILL.md files the brief names.
- Guard (Claude Code): a main-session Edit, Write, `sed -i` or `crlf_edit.py` on product code is blocked with the
  area agent to brief (`routing.enforce`). A tool event without `agent_id`/`agent_type` is the main session. Cursor
  has no equivalent: its tool hooks do not say which agent calls them (only subagentStart carries `subagent_id`), so
  Cursor gets the rule from AGENTS.md and the live page's chip.
- Live page: event kinds route ("Routed Build to backend-developer: <job>", from the Agent call's `Job:` and
  `Files:` lines), decide (triage.md, risk) and integrate (other task files); `live_status.py decide|integrate|route`.
  The Tech Lead card shows Deciding, Routing, Integrating, Checking or Waiting with the working agents and its last
  routes and decisions, never reads and edits; each agent's work stays on its own card; a warn chip names any
  product file the lead edited. New stat: Tech Lead share (lead vs agent tool events).
- Models in frontmatter: Opus for the deciders (solution-, security-, data-architect, ai-engineer, code-reviewer,
  ux-designer, spec-analyst, product-critic, bug-investigator, audit-expert, performance-engineer, sf-, n8n-expert),
  Sonnet 5.5 for the doers (backend-, frontend-developer, integration-, devops-engineer, base-builder, qa-engineer,
  verifier, explorer, release-manager, story-sizer). maxTurns about 1.5 times the call budget (30 for 20, 52 for 35,
  base-builder 60 for 40). The README table gets a Model column. Cursor runs on the session model.
- Hooks: the live hook runs `async` (off the critical path) in the plugin and the repo settings; the plugin's hooks
  use the exec form (`command: python` plus `args`, no Git Bash: about 260 ms less per hook on Windows); repo settings
  keep the shell form because Cursor reads them. install.py now reports a missing `async`. Per call: guard Read
  81 -> 69 ms, guard Edit 130 -> 105 ms; live 94 -> 105 ms but async. No merge needed: one sync hook per call left.
- Proof (3 Nov): baseline 86 core runs 27 Oct - 3 Nov (median 6.9 min, 0.83 turns per call, so the 1.3 target was
  already met; time 50% model, 24% tools, 29% client gap); Tech Lead share of live events 34% over 8794 events. A/B
  exam be, fe, qa: 15/15 on both models, Opus 9.9 min, Sonnet 7.2 min (-27%). Quick-fix replay (3 fixes, Java, JS,
  a test): lead does it on Opus 31.4 s, 11 turns, 14 calls, 698k input tokens; routed to the area agent on Sonnet
  29.3 s, 11 turns, 15 calls (+1 Grep for the brief section), 129k input tokens (-81%), tests pass in all six; lead
  share for those fixes 100% -> 17% (3 Agent calls of 18), and three independent fixes run in parallel (about 30 s
  wall instead of about 94 s one after another).
- Plan shape (Zakvan, 3 Nov: "each agent should have plan about what they need to achieve in the iteration, expected
  output etc.. the clear information that a human can understand about the task the agent is doing"): every output
  file's `## Plan` opens with `Goal:`, `Output:` and `Done when:` for this task, then 4-8 items that each name the
  concrete thing (a file, endpoint, node, screen, criterion id, or a decision with its options); process steps ("Read
  the brief", "Check every caller", "Write lessons") are not items. Briefs open with `Goal:`, `Output:` and `Files:`
  (`Job:` still read), and the route event carries the goal. `live_status.plan_issues` flags a plan with no Goal or
  Output line or with items that match a short banned list or carry no task-specific noun (a path, a name in
  backticks, an id or number, a capitalised term after the verb, or "Decide: X or Y"); the card shows a quiet "plan
  too generic" chip and rules_check (sync) adds a one-time note per file as additional context (no error). The
  card shows the Goal under the agent name; the plan panel shows Goal, Output and Done when above the checklist.
- All projects in sync (Zakvan, 3 Nov: "make sure all projects are in sync, add this in rule unless asked to change
  specifically in single project"): AGENTS-core, the sdlc Setup work row, README release step 5 and the home
  AGENTS.md rule 7 say a shared setup change is installed in product-factory, Blend, TalentBox and SkillsOS in the
  same change; a one-project change goes in that project's own files and the reply names the projects that differ.
- Watch: the exec hook form needs a Claude Code version that supports `args` (checked on 2.1.309); in a new session
  check the live page updates and the guard still blocks. Cursor attribution assumes a subagent's tool calls carry
  `conversation_id == subagent_id`.

## 31. 1.9.0 - a QA team that tests like manual testers, tests in the test folder
- Why: the Blend Violations admin screen shipped without real UI testing: the detail panel opened top-right (the
  admin had to scroll back up), cut-off table text had no tooltip, the pager was easy to miss. Zakvan (4 Nov): "QA
  should not miss anything from testing as it can become a production issue"; agents "should be able to perform end
  to end testing also like manual QAs do if I open the system".
- QA team (Quality): `qa-lead` (Opus; CTAL-TM v3.0, CTAL-AT v2.0, SAP C_STC) writes the risk-based test plan at
  Design (`test-plan.md`: risks, a matrix of criterion x test type x role x data volume, who tests what, test data,
  exit criteria) and the sign-off at Test (`qa-signoff.md`: SIGNED OFF, NOT SIGNED OFF or BLOCKED). `ui-qa-expert`
  (Opus; CTAL-TA v4.0, CT-UT, IAAP WAS, NN/g UX) tests every UI change in the running app against
  `reference/qa/ui-checklist.md` (UQ0-UQ18). `e2e-qa-expert` (Sonnet; CTAL-TA v4.0, CT-AcT) runs journeys across
  roles with charters and session notes. `qa-engineer` keeps automation and gains the API checks
  (`reference/qa/api-checklist.md`, AQ1-AQ7: contract, paging bounds, filters, access, input, big data, speed).
  Product mode: `05-test-plan.md`, `07-qa-ui.md`, `07-qa-e2e.md`, `07-qa-signoff.md`.
- Every list that can pass one screen needs server paging with a total, a visible pager and a reset to page 1 on a
  filter change, tested with three or more pages; a list seen with a handful of rows is BLOCKED, not PASS.
- Enforced: `handoff_check` fails a team without `qa-lead` when Review or Test runs, and a `ui` task without
  `ui-qa-expert`; `live_status.py stage <id> test done` (product: review) refuses until the sign-off says SIGNED OFF.
  A quick fix that changes a screen gets `ui-qa-expert` mode `quick` (about 10 calls).
- Browser: proven on 4 Nov that a subagent can drive the built-in browser (`mcp__Claude_Browser__*`: navigate,
  get_page_text, read_console_messages on the live page). An agent with a fixed `tools:` list sees only what it
  lists, so the UI and E2E experts name the browser tools in frontmatter; each works in its own tab (`tabs_create`,
  `tabId`, `tabs_close`). Cursor subagents have no built-in browser: there the experts write a numbered
  `## Runbook` that the Tech Lead runs. QA agents cannot start agents: `Consult: <expert>: <question>` lines are
  routed by the Tech Lead.
- Test location (hard rule, common.md, every code agent and qa-engineer, the stack packs): automated tests always go
  in the project's test folder, mirroring the package of the code under test (Java `src/test/java/<same package>/`,
  JS the stack pack's folder); never `src/main/**` or the repo root; the scratchpad holds only throwaway scripts and
  characterization runs. `rules_check` flags a new test file under `src/main/` or in the root (built in, no config).
- Watch: the named browser tools in `tools:` are checked in the first new session (agent files load at session
  start); without them the experts fall back to the runbook.
- SuccessFactors job profiles and skills: `sf-skills-expert` (Opus, Domain experts; SHRM-SCP, SAP C_THR85
  Succession Management, SAP C_THR95 Career Development Planning and Mentoring, names checked on learning.sap.com on
  4 Nov; no SAP certification for Job Profile Builder, Talent Intelligence Hub or Opportunity Marketplace was found,
  so none is claimed). Scope: Job Profile Builder, the skills model and Talent Intelligence Hub, competency and skill
  mapping to roles, Career Development and Opportunity Marketplace where they use skills, with the OData entities,
  effective dating, ids, permissions, paging, delta and imports. Modes fit, field and review like `sf-expert`:
  `sf-skills.md`, product `02-sf-skills-fit.md` and `05-sf-skills-fields.md`, review `review-sf-skills.md`. Joins
  when a change touches job profiles, roles, competencies or skills (sdlc team table, spec-analyst, factory S2, S5
  and S7); the QA agents' `Consult:` lines can name it.
- Sync scope (4 Nov, from the developer): SkillsOS gets no repo install from 1.9.0 on; its developers use the
  product-factory plugin and the repo's agents are being removed. "All projects in sync" now means product-factory,
  Blend, TalentBox and the plugin (AGENTS-core, sdlc Setup work, README step 5, AGENTS.md rule 7).

## 32. 1.10.0 - ready for the switch to the plugin
- Why: the setup review of 4 Nov (`work/claude-setup-review/`), MUST and SHOULD approved by the developer. The plugin
  is on at user level, so its guard blocked edits and `git merge` in every repo without the core; the `sdlc` header
  was not valid YAML (its description was lost); removing `.claude/core/` would have switched the guard off without
  a word, for Claude and Cursor; teammates had no way to get the plugin.
- Opt-in by `.claude/project.json` (M1, S4): plugin.json `defaultEnabled: false`; every hook (guard, rules_check,
  flow_check, live_status hook, session_start) exits 0 at once without project.json (`project.hook_start`).
  SessionStart adds nothing there, nothing when the repo carries the core, one line naming the plugin folder when
  AGENTS.md has the core block, the block itself otherwise.
- Headers (M2): `project.front_errors` (PyYAML when installed, plus the plain-value rules YAML applies) runs in
  build_plugin.py (the build stops), install.py --check and cursor_sync --check, for every agent and SKILL.md;
  build_plugin also checks plugin.json against VERSION and runs `claude plugin validate --strict` when the CLI is on
  PATH (a warning when not).
- Fail closed (M3, S7, S9): the guard blocks on an internal error (exit 2, Cursor deny) with a one-line reason and a
  log line (`project.error_log()`: `$CLAUDE_PLUGIN_DATA` or the temp folder), and its hook entry has
  `"onFailure": "block"` (Claude Code 2.1.295+). The launcher warns on stderr and exits 1 for a missing script or a
  launcher error (the guard entry then blocks; other hooks show the warning). rules_check and flow_check warn and
  exit 1. Hooks write UTF-8 and strip a byte-order mark from their input (a piped BOM made the guard fail).
- Paths (M4): build_plugin rewrites `.claude/core/` to `${CLAUDE_PLUGIN_ROOT}/` in every markdown file of the plugin;
  scripts and hook messages use `project.core_path()` (relative inside the repo, the absolute core folder from the
  plugin); install.py turns the plugin's paths back when it installs from the plugin. common.md says what a core path
  means in each layout.
- Read work off the guard (S3): `--write-settings` adds `Read(//**/<glob>)` deny rules for `guard.secret_files` and
  `guard.no_read`; the guard's matcher drops Read (Cursor keeps beforeReadFile). The big-file check on Read goes (the
  Read tool's own limits remain) and no-read hints are now the plain deny. Measured (median of 15, Blend): bare
  python 120 ms; guard on Read 254 ms before, none after; on Bash 245 ms before, 229 after.
- Cursor runtime (M3): cursor_sync writes `.cursor/runtime/` (guard, rules and flow checks, project.py, live_status
  with its page and imports, VERSION, README) and `.cursor/hooks.json` runs those. In a repo without the in-repo
  core it writes the whole core there (skills too, so cursor_sync and install --check run from the copy) and the core
  agents and skills into `.cursor/agents/` and `.cursor/skills/`, with core paths pointing at `.cursor/runtime/`.
- Switch (M5, S1): `install.py <repo> --switch-to-plugin` does it in one change: removes the locked core files and
  `.claude/core/`, removes the core hooks, writes `extraKnownMarketplaces.talenteam` (autoUpdate) and
  `enabledPlugins: true` from `templates/plugin-source.json` (`--marketplace-url` overrides), points the core paths
  in AGENTS.md, CLAUDE.md, .claude/ text files, the forwarder shims, the allow rules and launch.json at
  `.cursor/runtime/`, and regenerates `.cursor/`. It refuses on hand-edited core files (`--force`), and install.py
  refuses to re-add the in-repo core to a switched repo. Tested on a scratch copy of Blend only.
- Skills (S6): `sdlc` keeps triage, start, live status, gates and rules (27 KB to 15 KB); Who joins, Briefing,
  Safety net and Stages are `team.md`, `briefing.md`, `safety-net.md`, `stages.md` with their section numbers, each
  linked with a summary of its rules. `factory` keeps the playbook and a stage table (11 KB to 6 KB) with one file
  per stage. Both descriptions are quoted and lead with when to use them.
- Core block (S5): the `AGENTS.md` block, always loaded in every repo, went from 9.4 KB to 2.8 KB. It keeps the five
  lanes (one line each) and the hard rules (Tech Lead writes no product code, no repo-changing git, no servers, no
  secrets, the live page is the only tracker, tests in the test folder, core files only from the core source). The
  rest (agents, models, how agents work, safety net, QA, hooks, live page, sync, Cursor) moved to
  `reference/how-work-flows.md`, linked from the block and from `sdlc`; the paths resolve in every layout (repo,
  plugin, `.cursor/runtime/`).
- Permissions (S8): `templates/settings-permissions.json` is the one source for the permissions `--write-settings`
  writes (and `--switch-to-plugin`, retargeted): read-only allow rules (`Bash(ls)` and `Bash(ls *)`, `git branch
  --list*` and `-a*`, the work folder, read-only browser tools), the same deny list everywhere (git writes, `target`,
  `releases`, `createDDL.jdbc`, `approuter/resources`), plus Read deny rules for `guard.secret_files` and `no_read`
  and Edit deny rules for `secret_files`. Broad forms (`Bash(ls*)`, `Bash(git branch*)`) are replaced; the project's
  own rules stay. `install.py --check` lists a missing or broad rule. The switch also adds a user-level allow rule
  for the plugin's script folder (`--user-settings` picks the file), since `.claude/core/scripts/*` points nowhere
  after it.

## 33. 1.11.0 - QA checks from two years of bugs
- Why: the MAY26 bug-pattern study (Blend's two years of Jira bugs and ObservIQ's, `qa-bug-patterns/patterns.md` in
  Blend's work folder), approved by the developer on 5 Nov. Most escaped bugs fall in a few repeatable patterns
  (parity across views and content types, state after reopen, a second language, desktop widths, time zones, values
  against the source, reports and exports, jobs, roles).
- UI checklist UQ19-UQ27 (parity, reopen and return, second language, variants with a new-type sweep, desktop widths
  and scroll, dates and time zones, copy pass, values against the source, an other-browser runbook); UQ2, UQ6, UQ16
  extended. API checklist AQ3, AQ4 (a second user of the same role, a user without the permission, a direct URL) and
  AQ7 extended; AQ8 reports and exports, AQ9 time, AQ10 jobs added.
- QA agents: `qa-lead`'s matrix gets a parity set, a variant table, language and role columns, and a regression ring
  for bug fixes; `ui-qa-expert` UQ1-UQ27 and a data recipe in its practice pack; `e2e-qa-expert` standard charters
  and a `release-sweep` mode; `qa-engineer` AQ8-AQ10.
- Build agents get one prevention rule each (spec-analyst, explorer, frontend, backend, integration, ai-engineer,
  n8n-expert, code-reviewer); the review checklist gets the matching MUST and SHOULD items.
- New project key `qa.facts`: a path to the project's QA facts file. The QA agents, spec-analyst and explorer read it
  when set; the installer never overwrites a project's `project.json`.

## 34. 1.11.1 - the plugin manager decides
- Why: `--write-settings` wrote `enabledPlugins: {"product-factory@talenteam": false}` into each repo's settings, and a
  project setting beats the user's toggle, so the plugin could not be switched on from the plugin manager (and a
  switched repo's `true` could not be switched off). The developer: the plugin manager alone decides, in every
  project; when it is on Claude always uses it; nobody is forced, so teammates without it keep the repo copy.
- No project entry: `--write-settings` and `--switch-to-plugin` never write `enabledPlugins` for the plugin and remove
  an existing one (`--check` lists it). In a switched repo `--write-settings` does only that. `--switch-to-plugin`
  still writes `extraKnownMarketplaces`, so people get the install prompt. A switched repo is recognised by that
  marketplace entry.
- plugin.json has no `defaultEnabled`: an installed plugin is on until its owner turns it off (build_plugin refuses
  the key). M1 holds: every hook does nothing without `.claude/project.json`.
- The repo copy steps aside (Claude only): `project.hook_start` and the live_status hook gate exit 0 when the hook runs
  from `.claude/core/` and `project.plugin_active()` is true (the highest settings scope that names the plugin -
  local, project, user - says true, and `installed_plugins.json` has it installed for the user or for this repo).
  Unreadable or missing: false, so the repo copy keeps guarding. Cursor is unaffected.
- The plugin's SessionStart in a repo that carries the core: a short note to use `product-factory:<name>` agents and
  `/product-factory:<name>` skills, not the bare-named copies, and to update one side when the versions differ.

## 35. 1.12.0 - a QA team on its own, a fix-list loop and a requirements team
- Why (approved by the developer, 6 Nov): developers test at the end, several tickets at once or in another session;
  fixes after QA are never automatic; requirement review is open to non-technical people. In the developer's words,
  "these are skills, use necessary agents when people execute them, can be a group of agents": `test` and
  `review-spec` are team leads that pick and start the agents each run needs, in parallel where independent, and do
  none of their work themselves.
- `test` skill: `/test ID`, `/test ID ID ...`, `/test retest ID`. Per ticket: entry check (app up, the served asset is
  the new code, the unit suite passes; else BLOCKED), plan (test-plan.md reused when the fingerprint matches, or
  qa-lead `intake` writes qa-brief.md from the ticket text and the diff), the QA experts in parallel, qa-lead sign-off.
  Several tickets: one qa-lead each in parallel, test data prefixed `QA-<ticket>-`, one shared build, defects
  attributed by changed files (else cross-ticket), browser checks that need another user queued one at a time (one
  cookie store). Fingerprints at start; `testrun check` before sign-off lists rows that ran on old code. One summary
  table per run in `<work>/test-runs/<date>-<n>.md`. The sdlc Test stage runs the same skill; "test later" keeps the
  task at Test until SIGNED OFF or the developer accepts the risk in words.
- Fix list (`reference/qa/fix-list.md`): qa-lead writes `fix-list.md` at sign-off (F1.., MUST or SHOULD, owner agent,
  7 statuses, one block per defect with steps, evidence, suspected area and retest rows). The sdlc fix loop
  (`skills/sdlc/fix-loop.md`): `fix ID [F1 F3]` groups items by owner, bug-investigator only for an unknown cause,
  briefs the area agents, safety net, a re-review of the changed lines, items `fixed`, then `/test retest` flips them
  to `verified` or `reopened`. A ticket closes only on SIGNED OFF; Jira bugs only on request.
- `review-spec` skill: spec-analyst `requirements` leads, with product-critic, ux-designer (journeys), the domain
  experts the topic needs and qa-lead `testability`. Plain words, the Definition of Ready
  (`reference/requirements/definition-of-ready.md`, R1-R11, READY or NOT READY), one gate with the requester, then
  `Requirements: READY (confirmed by <name>, <date>)` in spec.md, a Jira comment (asked first) and an offline HTML copy.
  sdlc starts from READY requirements without the business questions. Read-only on code.
- live_status: `testrun start|ticket|check|done` (a run card across tickets), `fixes ID` and fix counts on the task
  card, a requirements chip. handoff_check: the fix list format and the Definition of Ready.
- Triage gets the Requirements, Test and Fix lanes (sdlc and the AGENTS.md block, now 3.2 KB). SkillsOS is back on the
  in-repo core (5 Nov), so "all projects in sync" names it again.

## 36. 1.13.0 - five flow skills, each with one job
Zakvan: "they all should have clear responsibilities". Each flow skill owns one job, starts the agents its run needs,
refuses another skill's job (it names the right one) and hands over through the work folder (`status.json`: stage,
`skill`, `next`), so any session can pick a ticket up.
- `review-spec` owns clear requirements: ends READY, `next` = `/develop <id>`.
- `develop` (new, `skills/develop/SKILL.md`) owns features and changes (feature, ui, data, config, refactor,
  performance): the Definition of Ready check first (spec-analyst mode `dor`; NOT READY: the developer answers on the
  spot when they are the requester, else `/review-spec`), then the task flow (context pack, risk, the technical part,
  Design with only the agents needed, the test plan, Build with the safety net, one code review). Ends ready for
  `/test`. One ticket per run; a small path for a change within `quick_fix`.
- `fix` (new, `skills/fix/SKILL.md`, replaces `skills/sdlc/fix-loop.md`) owns making something broken work again: a
  bug ticket, fix-list items or several bugs. bug-investigator proves the cause first (`fix-proof.md`: reproduction,
  `Proven: yes` at `path:line`, regression test, regression ring, fix plan; `handoff_check.py ID --fix`); an unproven
  cause is never fixed. The owner writes the regression test first, then fixes; safety net; a re-review of the changed
  lines; items `fixed`, `next` = `/test retest <id>`. Never changes scope (`/develop`). A small path for an obvious bug.
- `test` owns the sign-off: SIGNED OFF (Verify, Release, Wrap-up, then the commit message offered) or a fix list
  (`next` = `/fix <id>`, set by `testrun ticket`).
- `sdlc` is the router and the one home of the shared rules (task start, team, briefing, safety net, live status,
  gates and cards, stages, lessons). The Quick fix lane is gone: size sets depth inside `develop` and `fix`. `quick`
  stays as the small path's record (the stop hook accepts it).
- live_status: `init --skill`, `skill ID NAME`, `next ID "TEXT"`; a skill chip and the Next line on the page.
  The stop hook names the task's skill when it sends a turn back.

## 37. 1.14.0 - a test data engineer and a smoke pack with an owner
Why: `/test` often ended BLOCKED for missing data volumes, variants, roles and long-text records; the QA facts list
the records needed ("Test data recipe") but nobody made them; `.claude/smoke.md` had no owner.
- `test-data-engineer` (QA team, Opus at high effort, no browser in v1). Mode `learn` (`/test data`): the data map
  `.claude/qa/data-map.md` (one row per need: volume, source find / create / ask, how, cleanup, status) and draft seed
  and cleanup scripts in `.claude/qa/seed/`; runs nothing; one gate, nothing created before `Approved:`. Mode
  `top-up` (the new Data step of `/test`, after the plan): finds or creates only what is missing, `QA-<ticket>-`
  prefix, `data.md` with ids per matrix row; what it cannot make is asked and BLOCKED. Mode `cleanup`: only the
  records its log lists. Safety: `qa.data.hosts` only, never production; synthetic names; writes only through the
  app; read-only query command for lookups (counts and ids); test sign-ins; a yes for batches over 100; every create
  logged in `.claude/qa/create-log.jsonl`.
- `qa-lead` mode `smoke` owns `.claude/smoke.md`: today's format plus `[P1]` items and `### Journey:` blocks (Role,
  Steps, Expected, Data); every plan adds the smoke items of the areas a ticket touches as `S` rows; the sign-off has
  `## Smoke` (a P1 FAIL fails). `/develop` and `/fix` add `smoke: add` lines to `.claude/qa/smoke-inbox.md`.
- `/test data`, `/test data cleanup`, `/test smoke` (`skills/test/data-and-smoke.md`); `qa.data` in project.json
  (map, hosts, query, seed, cleanup `keep`: one lasting `QA-DATA-` dataset, top-ups per ticket, cleanup on request).
- live_status: `data ID`, `smoke ID`, `testrun ticket --data --smoke-*`, Data and Smoke columns. handoff_check:
  `--data-map`, `--smoke`, `data.md`.
- `.claude/qa/` is product-owned like `.claude/experts/`: the guard does not block it, install.py and cursor_sync
  leave it alone.

## 38. 1.14.1 - each agent's work in its home stage, fix rounds, no stale runs
Why: on a /fix task the live page showed the builders, n8n-expert and a re-review under Test, two background runs from
19 hours before as still working, and every stage live at once.
- Home stages (task mode, `home_stage`): builders Build, code-reviewer Review, the QA agents and test-data-engineer
  Test (qa-lead plans at Design until Test starts; qa-engineer locks today's behaviour at Design), verifier Verify,
  domain experts by the first stage word anywhere in their job (else Design), explorer's context pack Spec. It holds
  with no plan rows and when an agent's rows are finished. A resumed agent (same agent id, SendMessage) goes on in its
  earlier run's stage; its steps show there too.
- Rounds: a stage that already ran starts its next round when another stage ran since (`Build (fix round 2)` on the
  fix skill, `Test (retest)`, else `round 2`), on the stage header, the feed and the run cards. /fix calls
  `stage build start|done` and `stage review start|done`; /test retest calls `stage test start`.
- One live stage: a stage start (by `stage start` or an agent's run) closes the earlier live stages with no run at
  work; the QA sign-off stage stays open until SIGNED OFF.
- Stale runs: each run keeps `lim` (2 minutes per maxTurns, 30-180) and its session; a live run with no tool call for
  longer is `stopped (no finish signal)` on every save, leaves the background list flow_check waits on and holds no
  stage open; the new SessionEnd hook stops the ending session's runs; the page applies the same limit.
- `live_status.py repair <id> [--dry-run]` re-attributes a task from before 1.14.1 (backup `status.json.bak`).

## 39. 1.15.0 - a release lane, hotfixes, a shareable snapshot and token costs
Why: product owners got sent to `factory` for a ticket on an existing product, teammates with the plugin saw every
skill twice, and releases, production fixes and status for managers had no lane.
- Prompt hook (`flow_check.py prompt_lane`): a new product goes to `factory`; a requirement, PRD or user stories for
  an existing product go to `/review-spec`. Side-session, system and tool-event wrappers, code blocks and paths are
  ignored, so pasted logs do not trigger it.
- Repo copies: `install.py` starts each installed skill's description with "(repo copy - with the plugin on use
  /product-factory:<name>)"; the SessionStart text says which to type. The core and the plugin keep the plain text.
  The final fix is plugin-only (no repo copy of the skills where the plugin is on); that is later, not in 1.15.0.
- `/release <branch or tickets>` (new `release` skill): tickets from read-only git log against the last release and
  the work folders, qa-lead `release` (sign-offs, missing = NO-GO), devops-engineer `deploy-plan` (migrations,
  upgrade jobs, config keys, labels, restarts), `/test smoke` P1 on the release candidate, release-manager `release`
  (notes for the business and technical notes, rollback), one gate (D8). Never deploys or pushes.
  `init --skill release` keeps only Test, Release and Wrap-up.
- `/fix --hotfix <ticket>`: severity and impact first, evidence with no personal data, bug-investigator `hotfix`
  (smallest change), the fix on the release branch the developer names, a regression test, a risk-first review,
  `/test retest` plus the touched areas' P1 smoke, `backport.md`, and `incident.md` feeding lessons and the QA facts.
- `live_status.py share <id>` writes one offline `share.html` snapshot; `share --all` an overview for a manager.
  Sending is up to the developer.
- Tokens per run and task, read from the transcripts (deduped by message id), with a cost estimate from the one price
  table in `project.py` (`costs`); agents' models and effort are unchanged.
- `/review-spec` sizes each ticket (story-sizer `estimate`: points, confidence, a split proposal when too big) and
  works with no `.claude/project.json` (requirements only, `requirements/<id>/`, the code check skipped and said so).
- Repo root: README "Start here by role" and `ONBOARDING.md` (install, first command per role, where things land,
  approvals).

## 40. 1.16.0 - requirements checked properly, tests first, more QA types, learning from missed bugs
Why: in the last 12 task folders per repo QA barely ran (ui-qa-expert 2 runs; e2e-qa-expert, test-data-engineer and
verifier none), `/review-spec` agents only read code to learn what exists, the Definition of Ready checked only that
parts were present, spec-analyst graded its own draft, qa-lead's test types had no AI answer quality, languages,
data upgrade or browsers, and lessons came only from review MUSTs.
- Definition of Ready R12-R16: clear (no vague words, a glossary), consistent (within the text, other named tickets,
  today's behaviour), complete behaviour (create, change, remove, cancel, states and who moves them, limits,
  duplicates, two people at once), assumptions as `A<n>`, traceable to the goal. Specs made READY before keep R1-R11.
- Writer and checker apart: qa-lead's `testability` mode became `requirements-review` (`requirements-review.md`,
  method in `reference/requirements/requirements-review.md`); each finding quotes the sentence and asks one plain
  question; its results fill R10 and R12-R16. spec-analyst writes and merges; its review-spec layout moved to
  `reference/requirements/requirements-spec.md` (the agent file got smaller). `dor` applies R12-R16 to the request
  as given, quoting each criterion.
- `handoff_check.py`: vague words in the requirement part of `spec.md` are PROBLEM lines (core list
  `reference/requirements/vague-words.md` plus `glossary.vague_words`); quoted text, code, comments, questions, the
  glossary, the table and the technical appendix are skipped. It takes a folder path for requirements-only runs.
- With code there, `/review-spec` runs `explorer` (`context`) first and the spec gets `## Today vs asked` per
  criterion (plain words; path:line in the appendix; each conflict a question; checked by handoff_check).
- `/develop`: acceptance tests first (qa-engineer `acceptance`, `reference/qa/acceptance-tests.md`): written from the
  criteria after the test plan, run with the safe test command, each seen failing for the right reason; Build is done
  when they pass; criteria that cannot be automated go to ui-qa-expert or e2e-qa-expert (`## Not automated`).
- qa-lead's plan has `## Test types` (`reference/qa/test-types.md`): AI answer quality (eval set, judge, abuse cases
  from the QA facts; ai-engineer reviews an AI change), languages and long labels, data upgrade on existing rows,
  browsers and devices, each n/a with a reason when it does not apply. The product-specific eval path left
  qa-engineer.
- `/fix` escape check: bug-investigator adds `Should have been caught at: <stage> - <missing check>` (`(core)` when it
  applies to any product) to each block; `/fix` records a project check as a lesson tagged `[review-spec R<n>]`,
  `[develop review]` or `[test <type>]` (or the checklist, or the QA facts) and a core check in
  `.claude/review/core-escapes.md` for the core owner. The review pack leaves out lessons tagged for other stages.
