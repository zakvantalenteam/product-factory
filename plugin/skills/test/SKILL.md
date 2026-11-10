---
name: test
description: "Use when the developer types /test, wants one or several tickets tested (now, at the end of the work, or in a separate session), asks to retest fixes (/test retest <id>), or when the sdlc Test stage runs. QA team lead: checks the build is ready, starts the group of QA agents each ticket needs (in parallel where independent), and ends with a QA sign-off and a practical fix list per ticket. Never fixes anything; the developer starts the fixes."
---
# Test (QA team lead)

Paths: `<work>` is `work_dir` in `.claude/project.json` (default `.claude/work`); `live_status.py` is
`python ${CLAUDE_PLUGIN_ROOT}/scripts/live_status.py`; file names are in `${CLAUDE_PLUGIN_ROOT}/reference/flow-files.md`; the fix list
format is `${CLAUDE_PLUGIN_ROOT}/reference/qa/fix-list.md`. Several tickets in one run: also read
[several-tickets.md](several-tickets.md) before step 3.

You are the QA team lead of this run. Each run you pick the group of agents it needs and start them with the Agent
tool, every independent one in the same message. You never plan, test, sign off or fix yourself: `qa-lead` plans and
signs off, the QA experts test, the area agents fix only when the developer says so. You run the scripts and the entry
check, brief and start the agents, keep the live page current and report.

All state lives in files (`<work>/<id>/` per ticket, `<work>/test-runs/` per run), so a run works in any session: a new
session reads the files and goes on from the first missing one.

## Commands
| Command | What runs |
|---|---|
| `/test BLEN-1` | One ticket: entry check, plan (reused when the code is unchanged), the QA experts, sign-off, fix list |
| `/test BLEN-1 BLEN-2 BLEN-3` | Several tickets in one run on one build, one `qa-lead` per ticket in parallel ([several-tickets.md](several-tickets.md)) |
| `/test retest BLEN-1` | Only the fix-list items with status `fixed`: their failed rows plus the regression ring; each item becomes `verified` or `reopened` |

## 1. Start the run
1. `live_status.py testrun start <ID> [<ID>...] [--title "<T>"]`. It prints the run name (`<YYYY-MM-DD>-<n>`) and each
   ticket's fingerprint, binds this session to the run and creates any missing `<work>/<id>/`. Keep the run name and
   the fingerprints for the briefs. Show the live page on the run's card: `live_status.py open <RUN>`. A ticket made
   by an intake has no changed files yet: `testrun check` takes its baseline once `qa-brief.md` exists
   (`testrun refresh <RUN> <ID>` re-takes it on purpose).
2. A ticket with an sdlc task (`<work>/<id>/triage.md` exists): also `stage <id> test start`.

## 2. Entry check (once per run: all tickets share one build)
Read the repo's "Live check and verify notes" (in AGENTS.md, or the file AGENTS.md points to, for example
`.claude/flow-notes.md`). Then check:
- The app is up: `app.status` in `.claude/project.json` says UP, or `app.url` answers.
- The served asset is the new code: the notes' asset check, or fetch the asset URL and find a line of the change.
- The unit suite passes: `commands.test_all`, else `commands.test` with no filter. With the app up never run the
  compile, package, install or clean commands (`guard.block_while_app_up`); a new test class that is not found means
  the developer builds in the IDE.

A check fails: each ticket it affects is BLOCKED (`testrun ticket <RUN> <ID> --verdict BLOCKED --note "<what is
needed>"`). Tell the developer exactly what is needed: which server to start or restart and why. Never start or
restart anything. A failing unit test in one ticket's files blocks only that ticket. Step 3 still runs for blocked
tickets, so the next run starts at the experts.

## 3. Plan, per ticket
| The ticket folder has | Then |
|---|---|
| `test-plan.md` whose `Fingerprint:` equals the one `testrun start` printed, or is `none` (written at the sdlc Design stage, before the code) | reuse it, no agent |
| `test-plan.md` with another fingerprint | `qa-lead` `plan`: a new plan that keeps the rows that still apply |
| criteria (`spec.md` or `triage.md`), no plan | `qa-lead` `plan` |
| no criteria (a hand-built ticket, a teammate's push) | `qa-lead` `intake`, which writes `qa-brief.md` and then `test-plan.md` in the same run |

Before an intake, get the ticket text: with the Atlassian connector, read the Jira issue (summary, description,
acceptance criteria, comments) into `<work>/<id>/ticket.md`; without it, ask the developer to paste it (one question
for every ticket that needs it). Name the code to test: the uncommitted changes, a commit range, or the commits that
name the ticket (`git log --oneline --grep <ID>`, read-only); ask once when it is unclear. `qa-brief.md` must list
the changed files under `## Changed files` (one bullet per file, the path in backticks): `live_status.py` fingerprints
those files.

Start every `qa-lead` of this step in one message. Each brief opens with `Goal:`, `Output:` and `Files:` lines, then
`Run: <RUN>`, `Fingerprint: <fp>`, `Test data prefix: QA-<ID>-` and, in a run of several tickets, `Tickets in this
run:` with each ticket's changed-file source.

## 4. The QA experts
Start the experts each `test-plan.md` names under `## Who runs`, for every ticket, in one message:

| Expert | Mode | Tests | Writes |
|---|---|---|---|
| `qa-engineer` | `test` | unit tests and the API checks (AQ1-AQ10) | `test.md` |
| `ui-qa-expert` | `ui` | the UI checklist on every changed screen part | `qa-ui.md` |
| `e2e-qa-expert` | `journeys` | journeys across roles and features | `qa-e2e.md` |
| `verifier` | `change` | the criteria against pushed or pulled code (a commit range) | `verify.md` |

Brief each with the app URL, the role to sign in as, the plan rows it owns, `Test data prefix: QA-<ID>-`, its
`Browser:` line (below) and, with several tickets, the other tickets in the run and where their changed files are
listed. Every record, name and file QA creates starts with the prefix; QA never changes or deletes other data.

Browser rule: the built-in browser's tabs share one sign-in (one cookie store).
- Browser checks as the user signed in now, and every non-browser check, run in parallel: `Browser: shared` (never
  sign in, out or switch user; a row that needs another user is NOT RUN, `queued: <role>`).
- Browser checks that need a different user are queued, one at a time: each starts after the previous one returns,
  with `Browser: exclusive as <role>` (switch to that user, switch back at the end).
- An expert whose rows need several users is split: its shared rows in the parallel message, the rest as queued runs.

Cursor has no browser: there the UI and E2E experts write `## Runbook` steps for a person to run, and those rows stay
NOT RUN until the results come back; then start the expert again with the results to judge them.

A `Consult: <expert>: <question>` line in a QA file: brief that expert (quick brief, about 8 calls) and pass the
answer back. An expert that stops short: start it again for its NOT RUN rows only.

## 5. Staleness, sign-off and fix list
1. `live_status.py testrun check <RUN>`. Exit 1 lists the tickets whose changed files differ from the start: give
   their `qa-lead` the change, so the sign-off lists the rows that ran on old code (rerun or accept; the developer
   decides).
2. `qa-lead` `sign-off` for every ticket, in one message: `qa-signoff.md` with the verdict SIGNED OFF, FAILED or
   BLOCKED and, when any defect is left, `fix-list.md` in the format file's layout.
3. Per ticket: `testrun ticket <RUN> <ID> --verdict SIGNED-OFF|FAILED|BLOCKED --must <N> --should <N> --blocked <N>`
   (open MUST and SHOULD items from the fix list, BLOCKED rows from the sign-off). A ticket with an sdlc task: also
   `stage <id> test done` on SIGNED OFF, else `stage <id> test fail --out "<MUST ids>"`.
4. `live_status.py testrun done <RUN>`: it writes `<work>/test-runs/<RUN>.md` and prints the summary table.

## 6. Report and the fix loop
In the chat:
- The summary table `| Ticket | Verdict | MUST open | SHOULD | Blocked |` from `testrun done`.
- Per ticket with a fix list: the counts from `live_status.py fixes <ID>` and each MUST item in one line (id, title,
  owner agent).
- Intake questions still open, what is BLOCKED and what it needs, rows that ran on old code.

Then tell the developer: fixes start only when they say so, with `fix <id>` (every open item) or `fix <id> F1 F3`
(the sdlc fix loop), and `/test retest <id>` checks them. Never fix anything and never brief an area agent from this
skill. Jira bugs only when the developer asks: ask before creating each one. A ticket closes only on SIGNED OFF.

## Retest (`/test retest <id>`)
1. `live_status.py fixes <id>`. No item is `fixed`: say so with the counts and stop.
2. `testrun start <id> --title "retest <id>"`, then the entry check (step 2).
3. `qa-lead` `retest`: plans only the `fixed` items' retest rows plus their regression ring (from `fix-list.md`).
4. The experts it names, those rows only (step 4).
5. `testrun check`, then `qa-lead` `sign-off` of the retest run: each item `verified` or `reopened` with a History
   line; a new defect in the ring gets a new id. Then steps 5.3 to 6.

## sdlc link
- The sdlc Test stage runs this skill for its task: the same plan, experts, sign-off and fix list (one code path).
- "Test later": the task waits at Test and cannot wrap up until `qa-signoff.md` is SIGNED OFF or the developer accepts
  the risk in their own words.

## Rules
- Parallel where independent: every `qa-lead` of a step in one message, every expert of step 4 in one message;
  only queued browser runs wait.
- Never start or restart servers, never commit, no git that changes the repo.
- Keep the live page current: each ticket's verdict as it lands (`testrun ticket ... --verdict RUNNING --note` while
  its experts work).
- Finish with the summary table and the developer's next action.
