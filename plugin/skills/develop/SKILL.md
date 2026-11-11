---
name: develop
description: "Use when the developer types /develop, asks to build a feature or change existing behaviour (kind of work feature, ui, data, config, refactor, performance), or the sdlc triage routes a feature or change here. Owns building new behaviour: the Definition of Ready check first, then the context pack, the risk from evidence, the technical spec, Design with only the agents needed (cards, gates, prototype), the test plan, the acceptance tests written first and seen failing, Build by the area agents until they pass, with the safety net and one code review. Ends ready for /test. Never signs off its own work, never fixes bugs (/fix), never reviews requirements for a requester (/review-spec)."
---
# Develop (features and changes)

Paths: `<work>` is `work_dir` in `.claude/project.json` (default `.claude/work`); `live_status.py` is
`python ${CLAUDE_PLUGIN_ROOT}/scripts/live_status.py`; file names are in `${CLAUDE_PLUGIN_ROOT}/reference/flow-files.md`. The shared
rules live once, in the `sdlc` skill: [start a task](../sdlc/SKILL.md) (section 2), [team.md](../sdlc/team.md),
[briefing.md](../sdlc/briefing.md), [safety-net.md](../sdlc/safety-net.md), gates and decision cards (sdlc section
7), live status (section 6), [stages.md](../sdlc/stages.md) and the lessons loop (section 9). Every rule in them
applies here; this file adds only what is particular to building a change.

You are the Tech Lead of this run. You check the request is ready, pick the agents the change needs, start them with
the Agent tool (every independent one in the same message), decide at the gates with the developer, integrate and
run the checks. You never write product code: the area agents do.

## One job
| The request | Whose |
|---|---|
| New or changed behaviour: a feature, a screen, data, config, a refactor, speed | yours |
| Something broken that should already work (a bug, fix-list items, "fix BLEN-1") | `/fix`: say so in one line and stop |
| Requirements to check or write for a product owner, analyst or manager | `/review-spec` |
| Testing, QA sign-off, retest | `/test` |
| A new product from an idea or a PRD | the `factory` skill |

A request that mixes a bug and a change: the bug goes to `/fix`, the change stays here as its own ticket; say the
split in one line. One ticket per run. With several features, run them one after another, or offer one session each
(they run in parallel there).

## Commands
| Command | What runs |
|---|---|
| `/develop BLEN-1` | the whole flow for that ticket, ending ready for `/test` |
| `/develop "<what>"` | the same with a short slug as the id |
| `/develop BLEN-1 plan` (or "plan", "design only") | Definition of Ready, Spec and Design, then stop (read-only on code) |

## 1. Start
1. `live_status.py init <id> --mode task --skill develop --title "<goal>" --size S|M|L --tool claude|cursor`. The
   folder exists already: read `status.md` and go on from the first unfinished stage (`skill <id> develop` when
   another skill had it). Never redo a finished stage.
2. The request as it came goes to `<work>/<id>/request.md`, unchanged: the Jira issue (with the Atlassian connector:
   summary, description, acceptance criteria, comments), the pasted text or the document's words.
3. Size decides depth. The small path (below) is for a tiny change; everything else takes the full path.

## 2. Definition of Ready (first, before any design)
- `spec.md` has `Requirements: READY` (from `/review-spec`), or the developer points to approved requirements: pass,
  no agent.
- Otherwise `spec-analyst` (mode `dor`) checks the request against
  `${CLAUDE_PLUGIN_ROOT}/reference/requirements/definition-of-ready.md`. It writes `spec.md` with the request's criteria as
  given, the `## Definition of Ready` table and each failing item as a plain question `Q<n>` with a recommended answer.
- READY: add `Requirements: READY (checked at /develop, <date>)` to `spec.md` and go on.
- NOT READY: show the failing items and their questions in the chat and ask one question: "Answer them now, or send
  them to the requester?" (Claude desktop app: buttons "Answer now" and "Send to review-spec").
  - The developer is the requester and answers: `spec-analyst` (mode `revise`), then
    `Requirements: READY (confirmed by <developer>, <date>)` and go on.
  - Otherwise: `live_status.py next <id> "/review-spec <id> (open: R3, R5)"` and stop. The requester's answers come
    back through `/review-spec`; then `/develop <id>` goes on from here.

## 3. Context, risk and the technical part
sdlc section 2, steps 4-7: `explorer` writes `context.md`, the risk comes from its evidence, you write `triage.md`
(`Kind of work: feature|ui|data|config|refactor|performance`, the criteria from `spec.md`, the team from team.md,
`## Not needed`), then `plan <id> --file triage.md`. `spec-analyst` (mode `task`) adds only the technical part to
`spec.md`: affected areas as `path:line`, kind of work, team, decision cards. Any change to a criterion goes back
to the requester as a question.

## 4. Design
stages.md row 2: `review_pack.py <id> --design`, then in one message `solution-architect` and only the design
experts the change needs (`data-architect`, `security-architect`, `ux-designer` with a prototype for a new screen
(the `prototype` skill; the developer picks), `integration-engineer`, the domain experts), `qa-lead` (mode `plan`)
for `test-plan.md`, and `qa-engineer` (mode `characterize`) at risk medium or high. Decision cards D2-D8 and the gates
by risk as sdlc section 7. With `plan`: stop here and tell the developer `/develop <id>` builds it.

## 5. Acceptance tests first (after the test plan, before Build)
1. `qa-engineer` (mode `acceptance`) writes the automated acceptance tests from the criteria in `spec.md`, in the
   project's test folder, and runs them with the project's safe test command (`app.status` first; never a command
   that kills the running app). Each must fail first, for the right reason; the result goes in `test.md`
   `## Acceptance tests` (`${CLAUDE_PLUGIN_ROOT}/reference/qa/acceptance-tests.md`).
2. A criterion that cannot be automated (visual only, or it needs the running app) goes under `## Not automated`
   with `ui-qa-expert` or `e2e-qa-expert` as its owner; `qa-lead`'s plan gets a row for each. None is skipped
   silently.
3. `handoff_check.py <id> test.md` passes before Build starts. A test that passed before Build, or that needs the
   developer to build in the IDE first, is settled here.

## 6. Build
The area agents from your build briefs (briefing.md), in parallel where their files do not overlap, after the
"before" steps of safety-net.md; you integrate and run the "after" steps. Each build brief names the acceptance
tests its criteria own; the agent never edits them (a test it thinks is wrong goes to `questions.md` for
`qa-engineer`). Build is done when every acceptance test passes (the counts in `safety.md` `## After build`).
Anything the approved cards do not cover needs a change card, never a silent change.

## 7. Review and hand-off
1. `review_pack.py <id>`, then one `code-reviewer` run (`focus: all`). A MUST goes back to the same area agent with
   the exact findings; a re-review reads the delta pack. `stage <id> review done` on PASS.
2. `live_status.py next <id> "/test <id>"` and tell the developer, with the stage table: "/test <id> now, or test
   later". Test later: the task waits at Test and cannot wrap up until it is SIGNED OFF, or the developer accepts the
   risk in their own words (stages.md).
3. A new screen or journey: one line in `.claude/qa/smoke-inbox.md` (`- [ ] <date> <id>: smoke: add <area>: <item>`)
   so `qa-lead` folds it into the smoke pack.
4. You never sign off your own work and never run the QA experts from here: `/test` owns that.

## Small path (a tiny change)
Up to `quick_fix` in `.claude/project.json` (about 30 lines in up to 3 files), clear, nothing to decide (no table,
permission, contract, config, dependency or other owner's file):
1. Say the goal and what done looks like in one line (that is the Definition of Ready here); anything unclear takes
   the full path.
2. No context pack: a quick brief (`Quick fix:` line, briefing.md) to the area agent, which writes the test for the
   goal first, sees it fail, makes the change and sees it pass.
3. Self-check: the diff against the hard rules in AGENTS.md and `.claude/rules/`; a screen change also gets
   `ui-qa-expert` (mode `quick`).
4. `live_status.py quick "<what changed and why>" --skill develop` (`--id <id>` with a ticket). Past the limits,
   stop and take the full path.

## Rules
- Shared rules are the sdlc skill's; never copy or change them here.
- Never commit, push, start or restart servers; no git that changes the repo.
- Keep the live page current: the stage lines, gates and `next`. Finish with the stage table and the developer's
  next action.
