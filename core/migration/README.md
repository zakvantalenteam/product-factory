# Migrating Blend, TalentBox and SkillsOS to the core

One repo at a time, in this order. Each repo has its own checklist and its own `<repo>.project.json`.

Every core blocker is fixed in core 1.1.0 (list below); what is left per repo is a decision or a copy step.

| Repo | Effort | Left before the move | Order |
|---|---|---|---|
| Blend (`blend.md`) | S | moved 30 Oct on core 1.3.0 (uncommitted); forwarders at the old script paths until its in-flight tasks end | 1: done |
| TalentBox (`talentbox.md`) | M | copy `talentbox.checks.py` to `.claude/scripts/checks.py`; list the ticket prefixes if wanted (`ticket_prefix` is empty) | 2: same stack and CRLF as Blend |
| SkillsOS (`skillsos.md`) | L | copy `skillsos.checks.py` to `.claude/scripts/checks.py` (next to `locales.py`) | 3: 29 rules, LF, second frontend |

Fixed in core 1.0.1 (was a blocker for all three): `templates/settings-hooks.json` now uses the Cursor-safe
launcher (exit 0 when Cursor runs the Claude hooks or `CLAUDE_PROJECT_DIR` is empty), the same form TalentBox and
SkillsOS already carry as an uncommitted `settings.json` change (made 29 Oct at 15:59, not by this task), so
`install.py --write-settings` keeps it, pointing at `.claude/core/`. Git global options (`-C`, `-c`, `--no-pager`,
`--git-dir=`) no longer hide a blocked verb.

## Steps for every repo
1. Developer commits or parks pending work (one clean diff). The installer backs up what it replaces in
   `.claude/core-backup/<date>/`.
2. Stop the live-status server for that repo and close Cursor.
3. Move the repo-only lines of the six adopted skills into AGENTS.md (`## Live check and verify notes`).
4. Copy `migration\<repo>.project.json` to `<repo>\.claude\project.json` and, when there is one,
   `migration\<repo>.checks.py` to `<repo>\.claude\scripts\checks.py`; write `.claude/experts/sf.md`, `ai.md`.
5. `python D:\product-factory\core\scripts\install.py <repo> --adopt --write-settings --dry-run`, read it, then run
   it again without `--dry-run`.
6. Delete the old hooks, scripts, review copies and `*-explorer` / `*-verifier` agents (list in the repo's md).
7. Fix the text that still names the old paths and agents (list in the repo's md).
8. `python .claude/core/scripts/cursor_sync.py`, then `install.py <repo> --check` and `cursor_sync.py --check`.
9. Try three things: `git push` is blocked, a secrets file read is blocked, an edit to `pom.xml` asks for D6.
   Developer starts live-status and opens the page.

## Core 1.3.0 (all repos)
Each repo's `project.json` gets `impact` (where impact.py looks for callers, endpoints, screens, n8n nodes and
tools), `commands.test_all` (the full unit suite, safe while the app runs) and `commands.char_run` (one
characterization test); `.claude/smoke.md` (neighbours to check per area) and `.claude/review/lessons.md` are written
by the installer when missing and then filled by the repo. Blend: `blend.smoke.md`, `blend.char_run.py`, impact set.
SkillsOS: impact set; smoke list, test_all and char_run still to write. TalentBox: all four still to write.

## Git (core 1.2.0, all repos)
Every git command that changes the repo is blocked by default (25 verbs in `project.GIT_RULES`); read-only git
passes. `guard.git_on_request` (default `["pull"]`) lets a verb through in the turn after the developer's own message
asks for it; "pull request" does not count. Cursor has no prompt hook, so there pull stays blocked. The repo configs
no longer list `git_blocked`, so they take the core default.

## project.json keys added in core 1.1.0 (all supported; the repo files use them)
- `decisions.<id>.any_paths`: protect a whole file, no marker needed (TalentBox, SkillsOS)
- D4 line markers now see an edit to only the argument of a marked line (`@CheckPermission("A")` -> `("B")`)
- `rules[].not_paths`: skip files a rule would otherwise hit (TalentBox, SkillsOS)
- `rules[].redact`: do not echo the matched line in the message (SkillsOS secret rules)
- `guard.block_while_port_up`: block a command while a TCP port answers (SkillsOS, Vite on 5173)
- `guard.big_file_hints`: say which script to use for a big file (SkillsOS locales)
- `checks: [{id, paths, command, message}]`: the repo's own check script, run as `<command> "<path>"` with the hook
  JSON on stdin; exit 1 = one problem per stdout line. UI5 XML parse (TalentBox), EP2, DB2, DB9, LO1 (SkillsOS)
- `expert_docs`: required headings for a project expert's document (Blend `n8n.md`)
- `ticket_prefix` as a list; `app.strict`: only a 2xx counts as the app being up, not a 404 or redirect (SkillsOS)
- codemap reads `.ts/.tsx/.mts/.cts` and shows `@CheckPermission`; the five flow skills (live-check, verify-push,
  prototype, commit-msg, dev-handoff) read the AGENTS.md `## Live check and verify notes` section first

## Checked
The three JSON files load and every regex compiles. The core `rules_check` gives the same result as each repo's own
hook on about 200 sample lines (known differences: a CSS line starting with `#` is treated as a comment; a
properties line without `=` is checked under `part: value`). Core 1.1.0: 34 checks for the new keys (17 of them fail
on 1.0.1), and 6 more running both check scripts through the real core hook. Tests live in the scratchpad.
