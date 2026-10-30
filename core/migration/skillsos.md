# Migrate SkillsOS to the core

Repo `D:\skillos\repo\SkillsOS` | LF | live port 8768 | ticket `SKL-` | effort L | do third, after the fold-ins.
Config: `skillsos.project.json` (29 rules, D2/D4/D6, 7 generated paths, npm block, frozen migrations, 60 KB big-file limit).
Backend is `Backend/` (Maven, port 8080), frontend `Frontend/` (Vite, 5173), plus `approuter/`.

## Before
- [ ] Developer commits or parks pending work. Replaced files go to `.claude/core-backup/<date>/` (gitignored).
- [ ] Stop the live-status server (8768), close Cursor.
- [ ] Copy `migration\skillsos.checks.py` to `<repo>\.claude\scripts\checks.py`, next to `locales.py` (EP2, DB2,
      DB9, LO1). The Vite guard (a root `mvn` build runs `npm ci` under the running dev server) is
      `guard.block_while_port_up` in `skillsos.project.json`, supported since core 1.1.0.
- [ ] Move repo-only lines of the skills `--adopt` overwrites into AGENTS.md under `## Live check and verify
      notes`: app `http://localhost:5173/#/` and its hash routes, API `/skillsos/api/...`, `session/me`, the
      mock user, no irreversible actions on shared data; verify-push (`npm --prefix Frontend test`,
      `cd Frontend && npx tsc -b`, `locales.py check`, migration number and rollback); commit-msg exclusions
      (`.idea/`, `.settings/`, `Backend/releases/`, `Frontend/dist/`) and its bullets; prototype (theme tokens, MUI +
      Tailwind, D5 gate); dev-handoff owners.
- [ ] Copy `migration\skillsos.project.json` to `<repo>\.claude\project.json`; write the two expert files.
- [ ] `python D:\product-factory\core\scripts\install.py <repo> --adopt --write-settings --dry-run`, then without `--dry-run`.

## What `--adopt` replaces (15 files, originals backed up)
Agents: ai-engineer, bug-investigator, code-reviewer, data-architect, performance-engineer, release-manager,
sf-expert, solution-architect, spec-analyst. Skills: commit-msg, dev-handoff, live-check, prototype, sdlc,
verify-push. Adds 48 core files, the AGENTS.md block, `.gitignore` lines (`.claude/work/` too), new hook entries.

## Delete after install
- `.claude/hooks/guard.py`, `flow_check.py`, `rules_check.py`
- `.claude/scripts/codemap.py`, `crlf_edit.py`, `cursor_sync.py`, `handoff_check.py`, `live_status.py`, `live_status.html`
- `.claude/review/plain-english.md`; `decision-card.md` after a diff (the repo copy is 5 lines longer than the core's)
- `.claude/agents/skillsos-explorer.md`, `skillsos-verifier.md`
Then `python .claude/core/scripts/cursor_sync.py` and `install.py <repo> --check`.

## Stays project-only
- Scripts: `app_status.py`, `locales.py`. Agents: `test-runner`, `ui-engineer`
- Skills: `design-system`, `i18n`, `skillsos-build`. Rules: backend-db, backend-java, config-deploy, frontend
- `.claude/review/checklist.md` (its ids AL, JA, DB, FE... are what `project.json` rules cite)
- `settings.json` deny list (application-local/test properties, `createDDL.jdbc`, `routeTree.gen.ts`)

## Text that must change
- AGENTS.md: line 41 `crlf_edit.py`, 42 `codemap.py`, 57 `cursor_sync.py` -> `.claude/core/scripts/`; line 43
  add `.claude/core/scripts/`; lines 47-54 (sdlc, stages, flow, agents) repeat the core block: cut. Line 7 stays.
- `.claude/agents/ui-engineer.md`: `codemap.py`, `handoff_check.py` -> `.claude/core/scripts/` (`locales.py` stays).
- Old agent names (`skillsos-verifier`, `skillsos-explorer`): only inside files that are replaced or deleted.
- `.claude/scripts/README.md`: drop moved scripts. `settings.json`: nothing by hand; run `--check`.

## Expert files
`.claude/experts/sf.md` from `.claude/agents/sf-expert.md`:
- line 37 intro (TTCommon 2.0.0 jars, token service, no timeout set) -> "Clients and authentication"
- table 38-46 (job profiles, families and roles, templates, publish, TIH skill library, users, Learning) -> "Areas"
- line 47 weak spots (full re-pull, `$skip` without `$orderby`, SF call inside `@Transactional`) -> "Known traps"
- lines 48-50 sister products -> "Sister repos". "Data kept": write new.
`.claude/experts/ai.md` from `.claude/agents/ai-engineer.md`:
- 21-22 the one Azure OpenAI client and its settings (config key names only) -> "Clients, models and config"
- 23-26 features that call it (job profile generation, bulk queue, translation, scores) -> "Areas and pipeline"
- 27 gaps (no timeout, no token log, one error code) -> "Known traps"; 30 cost -> "Quota, cost and monitoring"
- 32 no eval harness, JUnit + golden set -> "Evals"; 33 safety and failure -> "Guardrails"
Key names and `path:line` only; no secrets found in these lines.

## Core changes this repo needed (all done)
- Core 1.0.1: the Cursor-safe launcher in `templates/settings-hooks.json` (the form already in this repo's
  uncommitted `settings.json`, pointing at `.claude/core/`) and the git global-option hole.
- Core 1.1.0: `guard.block_while_port_up` (the Vite rule), `big_file_hints` (locales to `locales.py`),
  `decisions.<id>.any_paths` (D2 `db/*.sql`; D4 `approuter/xs-security.json`, `common/security/**`), D4 widening
  an edit to its whole line, the `checks` hook (EP2, DB2, DB9, LO1 via `skillsos.checks.py`), `redact` and
  `not_paths` on rules, codemap `.ts/.tsx/.mts`, `app.strict` (a 404 or redirect on :8080 is not our app).

## Core 1.3 (read before starting)
Blend and TalentBox moved this way; their records are `blend.md`, `blend.text-moves.md`, `blend.lessons-draft.md`,
`blend.smoke.md` (worked examples, not text to copy).

Order
1. `git status` (note other people's uncommitted work and leave it alone) and the newest file times under
   `.claude/work/*` (open tasks keep their folders; the move never edits them).
2. Back up `.claude/`, `.cursor/`, `AGENTS.md`, `CLAUDE.md`, `.gitignore` outside the repo.
3. Copy, LF: `skillsos.project.json` -> `.claude/project.json`, `skillsos.checks.py` -> `.claude/scripts/checks.py`,
   `skillsos.char_run.py` -> `.claude/scripts/char_run.py`.
4. `install.py <repo> --adopt --write-settings --dry-run`, then without `--dry-run`. Auto mode refuses `--adopt`
   (it overwrites tracked files) until the developer OKs it in that session: ask once, with the file count.
5. Delete the old copies (list above). If a task is open (`.claude/work/*` touched in the last days), leave
   forwarders at the old `.claude/scripts/{live_status,handoff_check,codemap,crlf_edit,cursor_sync}.py` paths: two
   lines each, `runpy.run_path(<.claude/core/scripts/same name>, run_name="__main__")`, so running sessions keep
   working; delete `live_status.html` (the core writes live.html from its own template). Drop forwarders once
   those tasks end.
6. `python .claude/core/scripts/cursor_sync.py`, then `install.py <repo> --check` and `cursor_sync.py --check`:
   both must print ok (the settings launcher check is part of the second).

Text moves (copy facts, then remove the old file)
- Repo facts from the replaced agents and skills go to AGENTS.md `## Live check and verify notes`, `.claude/rules/`
  or the expert files; `blend.text-moves.md` shows the mapping, one line per fact with its new place.
- Old agents `skillsos-verifier`, `skillsos-explorer`: core `verifier`, `explorer`. Blend and TalentBox also
  dropped `test-runner` and `ui-engineer` (core `qa-engineer` and the main session do that work); here they are
  listed under Stays project-only, so keep them unless the developer agrees to drop them.
- Words to avoid in owner documents: a project file `.claude/review/glossary.md`, with `glossary.words` in
  project.json set to that path (a string path is allowed). Start it from the diff of the old
  `.claude/review/plain-english.md` against the core copy.
- D3 and D7 `what` texts in project.json `decisions` if the old cards had repo words; checklist references to old
  agent names -> core names.

Lessons and smoke list (project layer, never in the core)
- Formats: `core/templates/lessons.md` and `smoke.md`. `install.py` writes starter copies; replace their bodies.
- Sources: `.claude/review/checklist.md`; fixed findings in `.claude/work/*/review*.md`; the SkillsOS review
  tracker artifact (claude.ai/artifact/L3UJwc7p925D4eP5zmtDWZ, fixed and verified findings, kept by the
  `review-sync` skill); `git log` fix commits (`fix`, `revert`, "broke"). One lesson per root cause, with the file
  area it applies to. Smoke list: the screens and API calls those fixes touched, each with one check.
- Up to 5 new checklist MUST items from repeated lessons (next free id per section, the focus table and the
  extra-pass line too); name them in the report so the developer can drop any before committing. In the
  extra-pass line, `ui-engineer (ui)` becomes `ux-designer (ui-review)` if `ui-engineer` goes.

Test commands (in `skillsos.project.json`)
- `test_all`: `mvn -f Backend/pom.xml -o -q surefire:test && npm --prefix Frontend test`. `char_run`: `python
  .claude/scripts/char_run.py "{file}"`; it uses `Backend/` when that has its own pom (the root pom only
  aggregates Backend and Frontend; the repo may keep its own runner pinned to Backend), compiles against `Backend/target/classes`
  and the cached dependency classpath, so nothing runs `mvn compile` while the app is up.
- TypeScript characterization is not covered by `char_run` (it runs Java and .js/.mjs only): put a scratch test
  next to the code under test and run `npm --prefix Frontend test -- <file>`, then delete it.
- `npm`/`mvn` builds stay blocked while the Vite port is up (`guard.block_while_port_up`).

Old scratch suites
`C:\Users\ZAKVAN~1\AppData\Local\Temp\claude\D--skillos-repo-SkillsOS\ee5e5002-c6c4-490c-836a-483b7de6ada2\scratchpad\test_*.py`
(decisions, flow_check, guard, guard_cursor, live_status, review_fixes, rules_check). Run them on a copy of the
setup after an install there, path-mapped: `.claude/scripts|hooks/` -> `.claude/core/scripts|hooks/`, review
docs -> `.claude/core/reference/review/`, `skillsos-explorer` -> `explorer`, `REPO` -> the copy. Rehearse on the
copy first; then on the repo.

Known differences (expected test changes, not regressions)
- git `commit`, `reset`, `checkout`, `restore` (and 1.3.1: `clean --force`) are blocked; a test expecting them to
  pass is out of date. `pull` passes only for the turn after the developer asks for it.
- Block messages say "Start a task" (was "Start the sdlc").
- The old "S gate" test checks a gate the core no longer has.
- `guard.APP_URL` is gone: the core reads `app.url` (strict here: a 404 or redirect on 8080 is not our app).
- live.html is written from the core template; tests reading `live_status.html` need the core path.
- A `git fetch*` allow in settings.json is redundant (fetch is blocked): remove it.
- Fixed in 1.3.1 (tests expecting the old behaviour should now pass): a redirect or a 500 from the app means it is
  up when `app.strict` is off; a marker moved to another method needs its card; the Cursor live hook answers
  "allow" on unreadable input.
