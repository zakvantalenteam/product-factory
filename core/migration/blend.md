# Migrate Blend to the core

Repo `D:\blend\repo\LearningContentPack` | CRLF | live port 8766 | ticket `BLEN-` | effort S | do this one first.
Config: `blend.project.json` (7 rules, D2/D4/D6, quick-fix, glossary). Draft fixed: rule 2 now also checks
commented-out lines (as Blend's hook does) and `glossary.words` is set.

## Before
- [ ] Developer commits or parks pending work, so the migration is one clean diff. Nothing else to back up:
      the installer copies every file it replaces to `.claude/core-backup/<date>/` and gitignores that folder.
- [ ] Stop the live-status server (8766) and close Cursor.
- Git (decided 29 Oct): the core default applies - every git command that changes the repo is blocked, read-only
  git passes, and `git pull` passes only in the turn after the developer asks for it (Blend's hook blocked only push).
- [ ] Move the repo-only lines of the skills `--adopt` will overwrite into AGENTS.md, under `## Live check and
      verify notes` (outside the core markers): Ask `/lxp/widget/ai/search` (`?debug=true`), compact,
      Pulse `/lxp/widget/ai/pulse`, admin `/lxp/`; verify-push n8n diff and `run_offline.mjs`; area owners.
- [ ] Copy `migration\blend.project.json` to `<repo>\.claude\project.json` (1.3: `impact`, `commands.test_all`,
      `commands.char_run`), `blend.smoke.md` to `.claude\smoke.md`, `blend.char_run.py` to `.claude\scripts\char_run.py`.
- [ ] Lessons (1.3, once): the fixed Ask + Pulse review findings not already in a rule go to
      `.claude\review\lessons.md`; up to 5 general ones become checklist items.
- [ ] Write `.claude/experts/sf.md` and `ai.md` (below).
- [ ] Dry run, then install:
      `python D:\product-factory\core\scripts\install.py <repo> --adopt --write-settings --dry-run`
      `python D:\product-factory\core\scripts\install.py <repo> --adopt --write-settings`

## Done 30 Oct 2026 (core 1.3.0, tasks still in flight)
- Moved with widget-custom-css, ask-perf-capacity, review-next8 and review-next16 open; their folders untouched.
- `.claude/scripts/{live_status,handoff_check,codemap,crlf_edit,cursor_sync}.py` are forwarders to `.claude/core/scripts/`,
  so sessions started before the move keep working; delete them once those tasks end. `live_status.html` is gone (the
  core writes `live.html` from its own template).
- `ui-engineer`, `test-runner`, `blend-explorer`, `blend-verifier` removed; their Blend facts are in `.claude/rules/*`
  and AGENTS.md `## Live check and verify notes`. Glossary with explanations: `.claude/review/glossary.md`.
- Open: AGENTS.md repo map and `rules/mcp-tools.md` still name `docs/agentic/` (gone; inventory is
  `docs/wiki/reference/mcp-tools.md`); `rules/mcp-tools.md` "same commit" inventory rule vs docs-at-release.

## What `--adopt` replaces (15 files, originals backed up)
Agents: ai-engineer, bug-investigator, code-reviewer, data-architect, performance-engineer, release-manager,
sf-expert, solution-architect, spec-analyst. Skills: commit-msg, dev-handoff, live-check, prototype, sdlc,
verify-push. It also adds 48 core files, a marked block in AGENTS.md, `.gitignore` lines, and replaces the old
guard/flow_check/rules_check/live_status entries in settings.json and launch.json.

## Delete after install (the core owns these now)
- `.claude/hooks/guard.py`, `flow_check.py`, `rules_check.py`
- `.claude/scripts/codemap.py`, `crlf_edit.py`, `cursor_sync.py`, `handoff_check.py`, `live_status.py`, `live_status.html`
- `.claude/review/plain-english.md`, `decision-card.md` (core copies in `.claude/core/reference/review/`)
- `.claude/agents/blend-explorer.md`, `blend-verifier.md` (core `explorer`, `verifier`)
Then `python .claude/core/scripts/cursor_sync.py` and `install.py <repo> --check`.

## Stays project-only
- Scripts: `app_status.py`, `hana_query.py`, `n8n_node.py`, `n8n_callback_proxy.mjs`, `props.py`
- Agents: `n8n-expert`, `test-runner`, `ui-engineer`. Skills: `admin-page`, `blend-build`, `labels`, `mcp-tool`, `n8n-node`
- `.claude/rules/*` (6 files), `.claude/review/checklist.md` (trim the parts the core checklist now has, later)
- `settings.json` deny list and `n8n_workflows/eval/wfrev.py` permission; `settings.local.json`

## Text that must change
- AGENTS.md: line 42 `crlf_edit.py`, 43 `codemap.py`, 60 `cursor_sync.py` -> `.claude/core/scripts/`; line 45
  ("reuse `.claude/scripts/`") add `.claude/core/scripts/`; lines 50-57 (triage, team, agents, flow) repeat the
  core block: cut to Blend-only facts. Lines 9, 12, 37 stay.
- `.claude/agents/ui-engineer.md`, `n8n-expert.md`: `codemap.py`, `handoff_check.py` -> `.claude/core/scripts/`.
- `.claude/scripts/README.md`: drop the moved scripts. `.claude/review/checklist.md:218`: `blend-verifier` -> `verifier`.
- `settings.json`: nothing by hand; the installer adds `Bash(python .claude/core/scripts/*)`. Run `--check`.
- Leave `.claude/work/**` as it is (history).

## Expert files
`.claude/experts/sf.md` (core template `templates/experts/sf.md`), copy from `.claude/agents/sf-expert.md`:
- line 39 intro: TTCommon clients, token service, timeouts -> "Clients and authentication"
- table 40-50 (MCP guard, team members, goals, learning plan, training, recommendations, history, sync
  jobs, writes) -> "Areas"
- line 51 weak spots -> "Known traps"; lines 52-54 sister products -> "Sister repos"
- "Data kept" has no source: write it new.
`.claude/experts/ai.md` (template `ai.md`), copy the Blend-only bullets from `.claude/agents/ai-engineer.md`:
- 23-25 Ask pipeline, models per n8n step, prompts -> "Areas and pipeline", "Clients, models and config"
- 26-27 MCP tools, `aiquota` ledger -> "Tools and data", "Quota, cost and monitoring"
- 29-30 eval harness, guardrails -> "Evals", "Guardrails"; 31-32 memory, debug capture -> "Quota..." / "Known traps"
No secrets in these lines (key names and `path:line` only); re-read before saving.

## Core changes this repo needed (all done)
- Core 1.0.1: the Cursor-safe launcher in `templates/settings-hooks.json` (Blend's form, pointing at
  `.claude/core/`), and git global options (`-C`, `-c`, `--no-pager`, `--git-dir=`) no longer hide a blocked verb.
- Core 1.1.0: `expert_docs` (set in `blend.project.json` for `n8n.md`: Workflows touched, Today's flow, Plan,
  Eval and rollout, Handoff), the five flow skills reading the AGENTS.md `## Live check and verify notes` section,
  and D4 seeing an argument-only edit of `@CheckPermission(...)`.
