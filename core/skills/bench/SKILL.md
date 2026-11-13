---
name: bench
description: The bug test bench. Use when the developer types /bench, asks how many real escaped bugs the team would catch, wants an escaped bug added as a bench case, a bench run after a core release, the catch-rate report, or proposals from the misses. /bench add <fix-list item | Jira key>, /bench run [--stage S] [--project NAME|all] [--case GLOB], /bench report, /bench propose. Claude Code only (claude plugin eval); never changes code or a repo's git.
---
# Bug test bench

Measures how many real escaped bugs each stage of the team catches (review-spec, code-reviewer, qa-lead plan),
on every core release, and turns each miss into one proposed agent or checklist change. The case format, the
stages and the rules that keep it honest: `.claude/core/reference/bench.md` (read it first). The script:
`python .claude/core/scripts/bench.py` (`cases`, `check`, `run`, `report`). The main session runs this skill
itself (setup work, no task folder); it never edits product code.

Claude Code only: a run needs `claude plugin eval` (Claude Code 2.1.269 or later). In Cursor, say that a run needs
Claude Code, and offer `add`, `check` and `report`, which work there.

## /bench add <fix-list item | Jira key>
1. Find the bug's records: the fix-list item and its fix-proof block (`<work>/<task>/fix-list.md`,
   `fix-proof*.md`), else the work folder of the ticket. No proven root cause (path:line) or no committed fix:
   stop and say so; a case needs both.
2. Brief one `explorer` (Sonnet, about 40 tool calls) to write the case folder in `.claude/bench/cases/<id>/` per
   the reference: the ground truth from the fix-proof and the fix diff; the fix commit (`git log -S'<fixed text>'`
   or `log -L`); the introducing commit with read-only git (`git log -S'<defective text>'`, `git blame
   <fix>~1 -- <file>`, `log -L`); `ticket.md` from what existed before the change (never the bug report, which goes
   to `bug-report.md`); `caught_at` from the fix-proof's "Should have been caught at" line, else judged; one rubric
   per stage that could have seen it. Read-only git only; no writes outside the case folder.
3. `python .claude/core/scripts/bench.py check`. Fix what it lists.
4. Check for leaks yourself: the lessons at `<fixed>~1` must not already describe this bug (else set `layer_rev`),
   `ticket.md` must not describe the bug, and the rubric must FAIL a generic answer.
5. Show the developer one line per case (id, caught_at, stages, rubric's PASS line) for an OK. They commit it.

## /bench run [--stage S] [--project NAME|all] [--case GLOB]
1. `bench.py check` (invalid cases are skipped and listed).
2. `bench.py run <args> --max-cost-usd <ceiling> --dry-run`: the number of runs, the projected usage and the
   plugin under test. Always 3 runs per case and stage.
3. Never real money: the bench runs on the claude.ai subscription's tokens only, and `bench.py run` refuses when
   the claude CLI is not signed in with claude.ai or an API key or cloud provider is set (sign in with
   `claude auth login`; never add a key). The $ figures are list-price estimates of subscription usage, not a bill.
   Show the projection and the ceiling (`--max-cost-usd`, required on every run) before a full run; a run the
   developer asked for goes ahead.
4. Run it in the background (it takes minutes per case): `bench.py run <args> --max-cost-usd <ceiling>`. It
   writes `.claude/bench/history/<stamp>.json` (to commit) and `.claude/bench/runs/<stamp>/` (report, replies;
   gitignored), and prints the catch-rate table.
5. Report the table, the cost and any invalid runs (the agent did not start) or a partial run (the ceiling was
   hit). Then offer `/bench propose` for the misses.

From the home repo, `--project all` runs every repo in `release.local.json` that has cases. After a core release,
run the bench with the released plugin (`--plugin` defaults to the home repo's `plugin/`).

## /bench report
`bench.py report [--project NAME|all]`: catch rate per stage and agent, the rate at the stage where each bug
should have been caught, and every case whose verdict changed since the run before. Say plainly what got better or
worse and by how many cases.

## /bench propose
For each case the latest run marked missed at its expected stage (and each other stage that missed):
1. Read the case (`case.json`, the rubric), the replies of its missed runs (`.claude/bench/runs/<stamp>/replies/`),
   the agent file and the checklist sections and lessons that applied (the review pack's sections for the files).
2. Say why the agent missed it in one line (not in its checklist, in the checklist but not applied, out of its
   input, judged wrongly).
3. Propose one change: the file (a core agent, a core checklist or reference file, or the project's own
   `.claude/review/checklist.md`, `lessons.md` or `.claude/rules/*.md`), the exact text to add or change, why it
   would have caught this bug, and the risk of noise on other changes. Prefer a general check over the bug's
   specifics (for example "every name passed to a lookup with a silent fallback exists in the table", not
   "chev is in PATHS").
4. Write them to `.claude/bench/proposals.md` (one row each: case, stage, why missed, change, core or project,
   state `proposed`) and show them as a numbered list. Never apply a proposal without the developer's yes.
5. On a yes: a core change goes in the core source (`core/` in the home repo) and ships with the next release
   (`release.py`); a project change goes in that project's files. Then rerun the bench on those cases
   (`--case`) to show the catch, and mark the row `applied in core <version>` or `applied (project)`.
