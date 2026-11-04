# Claude Code setup review (Blend + product-factory plugin)

## Summary for people
- The setup is careful and mostly correct, but it is not ready for the plugin switch yet: 5 MUST, 9 SHOULD, 7 COULD.
- Biggest risk: the plugin is enabled for you at user scope. In any repo without `.claude/project.json`, its guard blocks the main session from editing any file and blocks `git merge` (tested; exit 2).
- The `sdlc` skill's description is invalid YAML. Claude sees only "Delivery flow (agent core)", so triage does not trigger from the description. The same bug is in the plugin.
- Removing `.claude/core/` silently switches off the project hooks for Claude and Cursor. Many files still point at `.claude/core/...`, and teammates have no project-level marketplace entry.
- Quick wins: move the Read checks to native `permissions.deny`, trim AGENTS.md by about 40 %, split `sdlc` into supporting files, and clean up stale backups, shims and cached plugin versions.

## Plan
- Goal: judge the setup machinery against the target: the plugin at user scope, and each repo keeping only its project layer.
- Output: this file, with findings ranked MUST, then SHOULD, then COULD, and the target layout table.
- Done when: every area 1-6 of the brief has evidence (a path:line or a doc URL) and a fix marked shared or per project.
- [x] Hooks: the bootstrap wrapper, duplicate git checks, cost, and whether the plugin no-ops in repos without the core (`settings.json:53-133`, `plugin/hooks/hooks.json`)
- [x] Skills: frontmatter YAML, size, clashes with plugin skills (`.claude/skills/*/SKILL.md`)
- [x] Rules, CLAUDE.md, AGENTS.md: `paths:` frontmatter, section sizes, the `@AGENTS.md` import
- [x] Permissions and settings, including the subagent model env var (sub-agents doc)
- [x] Plugin readiness: hard-coded `.claude/core/` paths, update flow, marketplace (host-marketplace doc)
- [x] Other: statusline, memory, stale folders, plugin cache

Docs checked (5 lookups): https://code.claude.com/docs/en/hooks, /sub-agents, /skills, /plugin-marketplaces, /plugins/host-marketplace.md.
"Doc fact" = stated on one of those pages. "Judgement" = my reading of the code and setup.

---

## MUST

### M1. The plugin guard blocks normal work in every repo without `.claude/project.json`
- **What:** `enabledPlugins.product-factory@talenteam: true` is set in user settings, so the plugin's hooks run in every repo. When there is no `project.json`, the guard falls back to DEFAULTS, and those DEFAULTS turn on routing for all files:
  - `routing.enforce: True` with a catch-all area `backend-developer: ["**"]`;
  - every git write blocked (`git_blocked: list(GIT_RULES)`), `merge` included;
  - a 120 KB limit on Read.
- **Evidence:**
  - `plugin/scripts/project.py:72` (git_blocked), `:84` (big_file_kb), `:93-94` (routing.enforce);
  - `plugin/hooks/guard.py:233` (`is_lead`) and `:245-259` (`check_route`).
  - Simulated in a scratch folder with no `.claude/`: an Edit of `app.py` gave "Blocked: app.py is product code ... Brief backend-developer" with exit 2. `git merge main` was also blocked with exit 2.
  - `~/.claude/hooks/no-git-writes.py:3-5,11` says your own policy allows pull and merge.
- **Impact:** In every other repo, the main session cannot edit any file and cannot merge. This contradicts your personal hook. It is invisible until it bites.
- **Fix:**
  1. Make all plugin hooks no-op unless `<project>/.claude/project.json` exists. That means `guard`, `rules_check`, `flow_check`, `live_status hook` and `session_start`.
  2. Optionally keep only the git rules everywhere, configurable from user level (see S2).
  3. Never apply `routing.enforce` from DEFAULTS: default it to False and let `project.json` turn it on.
- **Scope:** shared (core `project.py`, the hooks, `build_plugin.py`).

### M2. The `sdlc` skill's frontmatter is invalid YAML, so its description is lost
- **What:** The plain-scalar description contains `a task: a context pack ...`. That colon-space breaks YAML parsing ("mapping values are not allowed here", column 346).
  - Doc fact: "If the YAML between the markers doesn't parse, the skill still loads with no fields set". The listing then falls back to the first line of the body.
  - The skill list in this very session shows `sdlc: Delivery flow (agent core)`, not the trigger text.
- **Evidence:**
  - `.claude/skills/sdlc/SKILL.md:3` (same text in `plugin/skills/sdlc/SKILL.md` and `core/skills/sdlc/SKILL.md`).
  - https://code.claude.com/docs/en/skills
  - The other 11 skills parse fine.
- **Impact:** The triage skill that the whole flow depends on will not auto-trigger from "Use at the start of any request that may change code". It works only when invoked by name, or because AGENTS.md tells Claude to use it.
- **Fix:**
  - Quote the value, or use `description: >-` with the text indented below it.
  - Add a YAML parse of every SKILL.md and agent frontmatter to `install.py --check` and `build_plugin.py`, so a bad frontmatter fails the build.
- **Scope:** shared (core).

### M3. Deleting `.claude/core/` silently turns off the guard for Claude and for Cursor
- **What:** Every project hook goes through a `python -c` wrapper. The wrapper runs `os.path.isfile(p) or sys.exit(0)` and exits 0 when the script is missing. So:
  - once the folder is gone, the guard, the rules check, the flow check and live-status logging stop without any message;
  - Cursor has no plugin, and `.cursor/hooks.json` calls `.claude/core/hooks/guard.py --cursor` the same way;
  - AGENTS.md (which Cursor reads directly) still describes the core flow and points at `.claude/core/...`.
- **Evidence:**
  - `.claude/settings.json:60,70,82,92,104,116,127` (wrapper plus `.claude/core/hooks/*.py`);
  - `.cursor/hooks.json` (beforeShellExecution → `.claude/core/hooks/guard.py --cursor`);
  - AGENTS.md rule "every setup change must keep working for Cursor" (`AGENTS.md:56`).
- **Impact:**
  - Teammates without the plugin, and every Cursor user, lose the secret, generated-file, mvn and git blocks with no warning.
  - This breaks the Cursor-parity rule outright.
- **Fix:** Decide the Cursor runtime before the switch. My recommendation (judgement):
  - `cursor_sync.py` (shipped in the plugin) vendors a minimal runtime into `.cursor/runtime/`: `guard.py`, `rules_check.py`, `project.py`, a slim `live_status`. It is generated, never hand-edited, and stamped with the plugin version.
  - Claude uses the plugin.
  - In the Claude wrapper, replace the silent `sys.exit(0)` on a missing script with a one-line stderr warning, or a SessionStart check that warns when neither the core nor the plugin is present.
- **Scope:** shared (core `cursor_sync.py`, the wrapper template in `install.py`), output per project.

### M4. Hard-coded `.claude/core/` paths break once the folder is gone, inside the plugin too
- **What:** `build_plugin.py` rewrites `.claude/core/` to `${CLAUDE_PLUGIN_ROOT}/` only in agent and skill text (`core/scripts/build_plugin.py:7,110`). Everything else keeps the old path.
- **Evidence (plugin, files with `.claude/core/` references):**
  - `hooks/guard.py` (5: crlf_edit, codemap and cursor_sync hints at `:169,196,214-219`)
  - `hooks/flow_check.py:180`
  - `reference/agents/common.md` (4; every agent reads it first)
  - `reference/review/checklist.md` (2), `decision-card.md` (2), `plain-english.md` (1)
  - `reference/flow-files.md` (2)
  - `templates/AGENTS-core.md` (6; `session_start.py:18` rewrites these, good)
  - `scripts/*` (scope_check 5, handoff_check 5, cursor_sync 10, install 10, live_status 4, simulate 9, ...)
- **Evidence (Blend project layer):**
  - `AGENTS.md:45,47,87,94-106` (11 references)
  - `.claude/scripts/{codemap,crlf_edit,cursor_sync,handoff_check,live_status}.py`: forwarder shims to `../core/scripts`
  - `.claude/experts/{ai,n8n,sf}.md`, `.claude/review/glossary.md`
  - `.claude/settings.json:43-44` allow `Bash(python .claude/core/scripts/*)`
- **Impact:**
  - Agents are told to run scripts that do not exist, and they waste calls or improvise.
  - Block messages give dead commands.
  - Permission prompts appear for plugin script paths.
  - Not verified (I had no doc lookup left): whether `${CLAUDE_PLUGIN_ROOT}` is substituted inside agent and skill markdown, or exists in the Bash tool's environment. The hooks doc confirms it only for hooks, MCP and scripts. Test it with a scratch repo before the switch.
- **Fix:**
  1. In `build_plugin.py`, rewrite all text files (reference, templates, hook and script messages).
  2. Better: hooks and scripts build paths from `CORE_DIR` (they already have it in `project.py:15`).
  3. Have `session_start.py` always inject one line with the resolved plugin root, so prose can say `<core>/scripts/x.py`.
  4. Replace the Blend shims and the AGENTS.md references in the same change as the switch.
- **Scope:** shared (core), plus per project (AGENTS.md, shims, experts files).

### M5. Teammates on a fresh machine do not get the plugin
- **What:**
  - Only your user settings declare the `talenteam` marketplace (a git URL under a personal GitHub account) and enable the plugin.
  - Neither Blend's nor LearningAdmin's `.claude/settings.json` has `extraKnownMarketplaces`.
  - Both set `enabledPlugins: {"product-factory@talenteam": false}`.
- **Evidence:**
  - `.claude/settings.json:134-136` (Blend);
  - LearningAdmin `.claude/settings.json` (enabledPlugins false, no marketplaces);
  - `~/.claude/settings.json` extraKnownMarketplaces.talenteam.
  - Doc fact: "run `claude plugin marketplace add your-org/your-marketplace --scope project` ... commit the `.claude/settings.json` ... Claude Code then registers the marketplace for each teammate who trusts the folder". Private repos need stored git credentials or an ssh-agent key, because Claude Code never prompts (https://code.claude.com/docs/en/plugins/host-marketplace.md).
- **Impact:** After the switch, a teammate gets no agents, skills, guard or flow, silently (see M3).
- **Fix:**
  1. Move the marketplace repo to the TalenTeam org (judgement).
  2. In each product repo, add `extraKnownMarketplaces.talenteam` (`--scope project`) and set `enabledPlugins` to `true` in `.claude/settings.json`.
  3. Onboarding note: `gh auth login` and `gh auth setup-git`, or `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` when there is no SSH key.
- **Scope:** per project (settings), shared (marketplace hosting).

---

## SHOULD

### S1. Make the switch atomic per repo to avoid doubled hooks and skills
- **What:** If the plugin is turned on while the project hooks or the core skill copies remain:
  - the guard and live-status run twice. Doc fact: "If you define the same handler in more than one settings file, it runs once. A plugin's or skill's copy of the same handler stays separate" (hooks doc);
  - skills appear twice (`sdlc` and `/product-factory:sdlc`). Doc fact: a plugin skill and a project skill with the same name both load, because plugin skills are namespaced (skills doc);
  - agents behave differently: a project agent beats a plugin agent of the same name (doc fact, sub-agents doc), so stale in-repo copies would shadow `product-factory:<name>` only when called by the bare name.
- **Fix:** One change per repo does all of the following:
  - remove the `hooks` block from settings.json;
  - remove the core agents and skills listed in `core.lock` and `.claude/core/`;
  - flip `enabledPlugins` to true;
  - replace the shims;
  - run `cursor_sync`.
  - Do Blend and LearningAdmin in the same release: both are on core 1.9.0.
- **Scope:** per project, driven by a shared `install.py --uninstall-core` (judgement).

### S2. Git rules are enforced twice and with different policies
- **What:**
  - `~/.claude/hooks/no-git-writes.py` (user scope, Bash|PowerShell) blocks 8 verbs and allows pull and merge.
  - The guard's `GIT_RULES` block 25 verbs, merge included, with pull only on request.
  - Both start a Python process on every Bash call. They run in parallel (doc fact, hooks doc), so the extra cost is CPU, not latency.
- **Evidence:** `no-git-writes.py:11`; `plugin/scripts/project.py:20-57,72`.
- **Fix:**
  - Make the plugin the single enforcer.
  - Let a user-level file (for example `~/.claude/product-factory.json` with `git_on_request: ["pull","merge"]`) override the defaults.
  - Then delete `no-git-writes.py` and its user hook.
- **Scope:** shared (plugin reads the user config), plus user settings.

### S3. A Python process on every Read: replace the Read checks with native deny rules
- **What:** About 170 ms per Read and 207 ms per Bash call, of which 128 ms is the bare interpreter. Read is the most frequent tool. What the guard checks on Read:
  - `secret_files` and `no_read` (n8n JSON): native `permissions.deny` covers these at zero cost. Blend already has `Read(**/application-local.properties)` at `settings.json:48`.
  - The big-file size check, which the Read tool already limits with `limit` and its own size errors.
  - Doc fact: `matcher` matches only the tool name, and an `if` permission-rule filter is available on PreToolUse (hooks doc).
- **Fix:**
  1. `install.py` and `cursor_sync` generate `permissions.deny` `Read(...)` entries from `project.json` `guard.secret_files` and `no_read`.
  2. Drop `Read` from the PreToolUse matcher, or keep it with an `if` for the few patterns that need a custom message.
  3. Keep Bash, PowerShell, Edit and Write on the guard.
  4. Cursor keeps `beforeReadFile`.
  - Saves about 170 ms of CPU and wall time on every Read.
- **Scope:** shared (generator), output per project.

### S4. The plugin SessionStart injects about 2.4k tokens into every session in every repo
- **What:** `session_start.py` emits the whole core block, up to 9,500 characters, whenever AGENTS.md lacks `<!-- core:start -->`. That includes repos that never use the flow.
- **Evidence:** `plugin/hooks/session_start.py:13-29`.
- **Fix:**
  - Gate it on `.claude/project.json`, as in M1.
  - Inject a short pointer of about 600 characters: the lanes, "use /product-factory:sdlc", and the plugin root path. Let the `sdlc` skill carry the detail.
- **Scope:** shared.

### S5. Trim the always-loaded AGENTS.md (22.5 KB, about 5.6k tokens) without losing hard rules
- **Evidence (section sizes in characters):**

| Section | Lines | Size |
|---|---|---|
| Hard rules | 29-42 | 3,578 |
| Live check / Verify / Sdlc team rows / Release / Search tips | 58-89 | 4,498 |
| Core block | 90-109 | 9,383 |
| Repo map | 14-28 | 1,126 |
| Build, run, test | 7-13 | 1,001 |
| Working with files | 43-50 | 1,157 |

- **Fix (judgement):**
  - Keep the Hard rules, Build, Repo map and Working with files: about 7 KB.
  - Move "Live check and verify notes" (lines 58-89) to `.claude/experts/blend-flow.md` and point at it from the skills that read it. Its own header says it is "Read by the core live-check, verify-push, ... skills and by verifier and explorer", so it is on-demand material. Cursor skills can read the same file.
  - Shrink the core block to a summary of about 1.5 KB for Cursor and for Claude. Move the agent roster, model list and "All projects stay in sync / core files" maintainer text into the plugin's `sdlc` reference.
  - Result: about 10 KB, or about 2.5k tokens, saved on every turn.
- **The `@AGENTS.md` import is fine:** CLAUDE.md is a 3-line pointer and Cursor reads AGENTS.md directly.
- **The rule files are valid:** all six `.claude/rules/*.md` files have valid `paths:` YAML lists of quoted globs.
- **Scope:** per project (Blend part), shared (core block template `templates/AGENTS-core.md`).

### S6. `sdlc` (26.9 KB) and `factory` (11.3 KB) load in full on every invocation
- **What:**
  - Doc fact: "every line is a recurring token cost"; keep SKILL.md under 500 lines and move detail into supporting files that load on demand (skills doc).
  - `sdlc` has only 156 lines, but they are very long: about 6.7k tokens each time it loads.
- **Fix:**
  - Keep sections 1 (Triage), 2 (Start a task) and 7 (Gates, summary) in SKILL.md, about 7 KB.
  - Move §3 (Who joins), §4 (Briefing), §5 (Safety net), §8 (Stages) and §9 (Lessons) into `skills/sdlc/*.md`, linked from SKILL.md.
  - Do the same for `factory`, with one file per stage.
  - Shorten the descriptions too: `sdlc` is 714 characters and `factory` 500. Both are under the 1,536 cap but long; put the trigger first.
- **Scope:** shared.

### S7. Fail-open is silent, and Windows has a fail-closed trap
- **What:** All three failure paths let the call through without a trace:
  - the wrapper sets `sys.excepthook` to `os._exit(0)` (`settings.json:60`);
  - the guard's `__main__` turns any exception into exit 0 (`guard.py:512-520`);
  - doc fact: a timed-out PreToolUse hook does not block unless `onFailure: "block"` is set (hooks doc).

  Doc fact, the trap: on Windows without Git Bash, shell-form hooks run in PowerShell, and "any exit code other than 0 or 2 ... counts as a failure" that can block. A teammate without `python` on PATH, or with the Microsoft Store alias, then has every tool call blocked.
- **Fix:**
  - Log guard exceptions to `${CLAUDE_PLUGIN_DATA}/guard-errors.log` and surface the count in SessionStart or the statusline.
  - Split the tiny git and secret checks into their own hook with `onFailure: "block"`.
  - Document Python 3.12+ on PATH as an onboarding prerequisite.
  - The plugin already uses exec form (`command: "python"` with `args`), which the doc confirms is valid.
- **Scope:** shared.

### S8. Permission and settings hygiene
- **What and evidence:**
  - `settings.local.json:4-7`: `mcp__learnhub__*` entries are stale. No `learnhub` server is configured: no `.mcp.json`, nothing in `~/.claude.json`.
  - `settings.local.json:8`: `Bash(mvn -q -o compile -DskipTests)` skips the prompt for a command that AGENTS.md hard rule "never compile while the app is UP" forbids. The guard still blocks it when the app is UP, but the prompt was a second gate.
  - Blend's deny list lacks the `Edit(**/application-local.properties)`, `Edit(/target/**)` and `Edit(/releases/**)` that LearningAdmin has.
  - `Bash(ls*)` (no space) also matches any command starting with `ls` (judgement, from documented prefix matching). Use `Bash(ls)` plus `Bash(ls *)`.
  - `Bash(git branch*)` allowlists `git branch -D`. The guard blocks it, but allow rules should be read-only: use `Bash(git branch --list*)` and `Bash(git branch -a*)`, or drop it.
  - After the switch, plugin scripts live under a versioned cache path, so `Bash(python .claude/core/scripts/*)` is dead. Add a user-level allow rule for the plugin scripts folder (judgement; check the wildcard form).
- **Fix:**
  - Clean `settings.local.json` down to personal entries only.
  - Align the deny lists across products from one generated template.
  - Add the plugin-scripts allow rule at user level.
- **Scope:** per project, plus user settings for the plugin path.

### S9. The plugin hooks do not force UTF-8 on stderr outside Blend
- **What:**
  - Blend sets `PYTHONUTF8` and `PYTHONIOENCODING` in `settings.json:3-6`; other repos do not.
  - With Python 3.12.10 and piped stderr, the encoding is cp1252 (measured).
  - A block message containing a non-cp1252 file name would raise inside `except Blocked`. The outer `except Exception: sys.exit(0)` then lets the call through.
- **Fix:** Call `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` and the same for stderr at the top of each hook.
- **Scope:** shared.

---

## COULD

### C1. Stale folders and shims
- `.claude/core-backup/2026-10-30` (agents, skills, settings) and `2026-11-03` (settings) are leftover install backups. They are gitignored (`.gitignore:43`, written by `install.py:251`). Delete them after each verified install. LearningAdmin has the same folder.
- The `.claude/scripts/` forwarder shims say they should be deleted "once no running task uses the old path" (`.claude/scripts/live_status.py:1-2`, 30 Oct).
- Scope: per project.

### C2. Plugin cache and update flow
- **On disk:** `~/.claude/plugins/cache/talenteam/product-factory` holds 9 versions (1.4.0 to 1.9.0) plus the old `agent-core/1.3.9`, about 14 MB. Remove the old ones.
- **Doc facts (host-marketplace doc):**
  - Users get a new copy only when the `version` string changes. `plugin.json` 1.9.0 must be bumped by `build_plugin.py` on every release.
  - Do not set `version` in both `plugin.json` and the marketplace entry. Today it is set in only one place, which is correct.
  - Background auto-update is off by default and is turned on per user in `/plugin` → Marketplaces, or by an admin in managed settings.
- **Check:** `autoUpdate: true` in your user `extraKnownMarketplaces` really shows as enabled in `/plugin`.
- Scope: shared, plus user.

### C3. `CLAUDE_CODE_SUBAGENT_MODEL` does not override the agents' `model:` lines
- **Doc fact (sub-agents doc):** the order is:
  1. the per-invocation `model` parameter;
  2. the frontmatter `model:`;
  3. the env var;
  4. the main model.

  Before v2.1.251 the env var came first. Confirm the installed version with `claude --version` (`claude` is not on Git Bash's PATH here).
- **Risk (judgement):** your CLAUDE.md line "Subagents default to Sonnet; pass `model: \"opus\"` only for ..." invites the main session to pass `model` explicitly. That would override the Opus agents.
- **Fix:** Reword it as "omit `model` for core agents; their frontmatter decides; the env var covers built-in agents only".
- Scope: user.

### C4. Add a statusline
- None is set at user or project level.
- A cheap statusline would show the project name, the live task id and port, the plugin version, app UP/DOWN and the guard error count (see S7).
- It makes the fail-open state and the plugin-versus-core state visible.
- Scope: user settings; the plugin can ship the script.

### C5. Memory hygiene
- MEMORY.md (about 2.2k tokens, always loaded) lists about 25 "Active work" items. Several are superseded or old:
  - "Go-live tracker — SUPERSEDED 21 Oct";
  - "Ask latency — RESUME 8 Oct";
  - "Delivery tracker" and "Ask redesign 9 Oct".
- Run `consolidate-memory`, keep only live items and move the rest to `archive/`.
- Scope: user.

### C6. `bashOutputMaxChars` (`settings.json:7`) is not a key I could confirm
- The control I know of is the env var `BASH_MAX_OUTPUT_LENGTH`.
- Unknown keys are ignored silently. Check it against the schema or `/doctor`, and switch to the env var if needed (judgement, not verified).
- Scope: per project.

### C7. `effortLevel: low` at user scope
- It applies to every session.
- Deciding agents (Opus) may then run at low effort unless their frontmatter sets `effort`.
- Consider `effort:` on the deciding agents' frontmatter, or `medium` as the user default (judgement).
- Scope: shared (agent frontmatter) or user.

---

## Target layout

| Piece | Lives after the switch | Notes |
|---|---|---|
| Core hooks: guard, rules_check, flow_check, session_start, live-status logging | Plugin `hooks/hooks.json` (exec form, `${CLAUDE_PLUGIN_ROOT}`) | No-op without `.claude/project.json` (M1, S4) |
| Core scripts: live_status (+html), project, codemap, crlf_edit, review_pack, scope_check, impact, char_test, timing, handoff_check, md_to_html, check_base, cursor_sync | Plugin `scripts/` | Paths from `CORE_DIR`, no `.claude/core/` strings (M4) |
| `install.py`, `build_plugin.py` | Core source (product-factory repo) | `install.py` gains an uninstall-core mode (S1) |
| 27 core agents | Plugin `agents/` (`product-factory:<name>`) | Remove the in-repo copies, or they shadow bare names |
| Core skills: sdlc, factory, prototype, commit-msg, dev-handoff, live-check, verify-push | Plugin `skills/` (`/product-factory:<name>`) | Fix the sdlc YAML (M2); split into supporting files (S6) |
| Core reference: practice packs, review checklists, stacks, base spec, templates | Plugin `reference/`, `templates/` | Rewrite paths (M4) |
| AGENTS.md core block | Short summary in AGENTS.md (Cursor and Claude); full detail in the plugin skill | S5 |
| AGENTS.md project part: hard rules, repo map, build, files | Repo | Move the live-check and verify notes to `.claude/experts/blend-flow.md` |
| `CLAUDE.md` (`@AGENTS.md`) | Repo | Unchanged |
| `.claude/project.json` | Repo | The switch that turns the plugin on for this repo |
| `.claude/rules/*.md` | Repo | Valid already |
| Project skills: admin-page, blend-build, labels, mcp-tool, n8n-node | Repo `.claude/skills/` | Unchanged |
| `.claude/scripts/`: app_status, hana_query, n8n_node, props, char_run, n8n_callback_proxy | Repo | Delete the 5 core forwarder shims (C1) |
| `.claude/review/` (checklist, lessons, glossary), `.claude/experts/`, `.claude/smoke.md` | Repo | Fix the `.claude/core/` references |
| `.claude/settings.json` | Repo | Permissions, env, `extraKnownMarketplaces` + `enabledPlugins: true`, generated Read deny rules; no hooks |
| `.claude/settings.local.json` | Repo, personal, not shared | Stale entries removed (S8) |
| `.cursor/` (hooks.json, rules, agents) + Cursor runtime | Repo, generated by the plugin's `cursor_sync` | Vendored minimal guard runtime (M3) |
| `core.lock`, `.claude/core/`, `core-backup/` | Removed | |
| `no-git-writes.py` | User, then retired | Once the plugin honours the user git policy (S2) |
| `CLAUDE_CODE_SUBAGENT_MODEL`, outputStyle, effortLevel, statusline, plugin-scripts allow rule | User settings | C3, C4, S8 |
| Marketplace `talenteam` | Org GitHub repo, private | Version bump per release; teammates need stored git credentials (M5, C2) |
