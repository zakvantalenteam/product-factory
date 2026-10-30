# Migrate TalentBox to the core

Repo `D:\blend\skill-assessment-repo2\LearningAdmin` | CRLF | live port 8767 | no single ticket prefix | effort M | do second.
Config: `talentbox.project.json` (12 rules, D2/D4/D6, quick-fix, glossary, 8 generated paths).
`ticket_prefix` is empty on purpose: tickets are OBIQ-, JPG1- and others; the commit-msg skill reads them from the task.

## Before
- [ ] Developer commits or parks pending work. Replaced files go to `.claude/core-backup/<date>/` (gitignored).
- [ ] Stop the live-status server (8767), close Cursor.
- [ ] Copy `migration\talentbox.checks.py` to `<repo>\.claude\scripts\checks.py` (the UI5 XML parse check).
- [ ] Move repo-only lines of the skills `--adopt` overwrites into AGENTS.md under `## Live check and verify
      notes`: admin UI5 `/tbx/` (`index.html`), Thymeleaf pages by `@GetMapping`, sign-in is the developer's,
      LLM actions take a minute, check a user without the menu; verify-push (XML parse, `node --check`,
      `props.py has <key>`); commit-msg exclusions (`releases/`, `target/`, `createDDL.jdbc`).
- [ ] Copy `migration\talentbox.project.json` to `<repo>\.claude\project.json`; write the two expert files.
- [ ] `python D:\product-factory\core\scripts\install.py <repo> --adopt --write-settings --dry-run`, then without `--dry-run`.

## What `--adopt` replaces (15 files, originals backed up)
Agents: ai-engineer, bug-investigator, code-reviewer, data-architect, performance-engineer, release-manager,
sf-expert, solution-architect, spec-analyst. Skills: commit-msg, dev-handoff, live-check, prototype, sdlc,
verify-push. Adds 48 core files, the AGENTS.md block, `.gitignore` lines (`.claude/work/` too), new hook entries.

## Delete after install
- `.claude/hooks/guard.py`, `flow_check.py`, `rules_check.py`
- `.claude/scripts/codemap.py`, `crlf_edit.py`, `cursor_sync.py`, `handoff_check.py`, `live_status.py`, `live_status.html`
- `.claude/review/plain-english.md`, `decision-card.md`
- `.claude/agents/talentbox-explorer.md`, `talentbox-verifier.md`
Then `python .claude/core/scripts/cursor_sync.py` and `install.py <repo> --check`.

## Stays project-only
- Scripts: `app_status.py`, `props.py`. Agents: `test-runner`, `ui-engineer`. Skills: `labels`, `talentbox-build`
- `.claude/rules/*` (ai-llm, config-deploy, java-backend, labels, thymeleaf-pages, ui5-admin)
- `.claude/review/checklist.md` (project ids; trim what the core checklist has, later), `settings.local.json`
- `settings.json` deny list (includes `Edit(**/application-local.properties)`, `releases/`, `target/`)

## Text that must change
- AGENTS.md: line 45 `crlf_edit.py`, 46 `codemap.py`, 61 `cursor_sync.py` -> `.claude/core/scripts/`; line 47 add
  `.claude/core/scripts/`; lines 51-58 (sdlc, stages, flow, agents) repeat the core block: cut. Lines 9, 12 stay.
- `.claude/agents/ui-engineer.md`: `codemap.py`, `handoff_check.py` -> `.claude/core/scripts/`.
- `.claude/review/checklist.md:205`: `talentbox-verifier` -> `verifier`.
- `.claude/scripts/README.md`: drop moved scripts. `settings.json`: nothing by hand; run `--check`.

## Expert files
`.claude/experts/sf.md` from `.claude/agents/sf-expert.md`:
- line 37 intro (TTCommon jars, bearer token calls, `LMSClientService`) -> "Clients and authentication"
- table 38-50 (11 areas: blind recruiting import, references, redact, exports, Job Profile Builder import and
  publish, Talent Intelligence Hub, skill connect, users and roles, Learning) -> "Areas"
- line 51 weak spots -> "Known traps"; lines 52-54 sister products -> "Sister repos". "Data kept": write new.
`.claude/experts/ai.md` from `.claude/agents/ai-engineer.md`:
- 21-22 shared provider path and legacy clients -> "Clients, models and config" (line 22 says never copy the
  legacy key-in-URL client: keep it as a trap)
- 23-28 features and calls (quizgen, quizzes, job profiles, skill extraction, others) -> "Areas and pipeline"
- 29-31 models, prompts in Java, no token records -> "Clients...", "Quota, cost and monitoring"
- 33 no eval harness -> "Evals"; 34 rules `ai-llm.md` LL1-LL9 -> "Guardrails"; 35 logging at INFO -> "Known traps"
Key names and `path:line` only; no secrets found in these lines.

## Core changes this repo needed (all done)
- Core 1.0.1: the Cursor-safe launcher in `templates/settings-hooks.json` (the form already in this repo's
  uncommitted `settings.json`, pointing at `.claude/core/`) and the git global-option hole.
- Core 1.1.0: `decisions.<id>.any_paths` (D2 `db/*.sql`; D4 `menu.csv`, `approuter/xs-app.json`, `xs-security.json`),
  `not_paths` on rules, the `checks` hook (UI5 XML via `talentbox.checks.py`), D4 seeing an argument-only edit of
  `@CheckPermission(...)`, codemap showing `@CheckPermission`, `ticket_prefix` as a list.
