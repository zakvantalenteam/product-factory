---
name: sdlc
description: Triage every request, then run the delivery flow only for real work - answer questions directly, route obvious small changes to their area agent as quick fixes, do AI-setup work (.claude, .cursor, AGENTS.md) with no task, send a new product (idea, PRD, "build a new product") to the factory skill, and give every other change a task: a context pack first, a risk level from its evidence, only the agents it needs (the Tech Lead decides and routes, the area agents write the code), a safety net scaled by risk so nothing else breaks, and the developer's OK where there is something to decide. Use at the start of any request that may change code, when the developer types /sdlc, or when unsure what step comes next.
---
# Delivery flow (agent core)

Paths: the work folder `<work>` is `work_dir` in `.claude/project.json` (default `.claude/work`); scripts are
`python ${CLAUDE_PLUGIN_ROOT}/scripts/<name>.py` (below just `live_status.py`); file names per mode are in
`${CLAUDE_PLUGIN_ROOT}/reference/flow-files.md`.

## 1. Triage (every request, first)
Pick the lane yourself; never ask the developer which one. Say the lane in one line only when you start a task.

| Lane | When | What you do |
|---|---|---|
| Answer | A question, general knowledge, "discuss", "explain", "how does X work" | Answer from what you know or the code (big searches to `explorer`). No work folder, no agents. |
| Read-only | "plan", "don't change", "review this" | "plan": a task with Spec and Design only, then stop. "review this": `review_pack.py <id>` (`--files` or `--base <rev> --head <rev>` for given files or commits), then one `code-reviewer` run (`focus: all`), report, fix nothing. |
| Setup work | Changes only to the AI setup: `.claude/**`, `.cursor/**`, `AGENTS.md`, `CLAUDE.md` (and `setup_paths`) | Do it directly: no task, no agents, no gates. Core files are changed only in the core source, and a shared setup change goes to every project in the same change (product-factory, Blend, TalentBox and the plugin: `install.py <repo> --write-settings`, then both checks in each; SkillsOS uses the plugin and gets no repo install) unless the developer asks for one project only (then that project's own files, and say which projects now differ). Before you finish run `cursor_sync.py`, then `--check` must be clean (the stop hook checks it). Throwaway checks go in the session scratchpad. |
| Quick fix | Obvious and small: up to ~30 lines in up to 3 files (`quick_fix` in project.json), the change is clear, nothing to decide (no table, permission, contract, config, dependency or other owner's file) | Route it to its area agent (section 3) with a quick brief (section 4): it makes the fix and runs the test. Then check the diff against the hard rules in AGENTS.md and `.claude/rules/` and `live_status.py quick "<what changed and why>"`. A fix that changes a screen also gets `ui-qa-expert` (mode `quick`, about 10 calls) before you close it. If it grows past the limits, stop and start a task. |
| Product | An idea, a PRD or requirement document, "build a new product/app/system" | Never build from it directly: the `factory` skill (product mode, stage intake). |
| Task | Everything else | Sections 2-9, with only the agents the task needs. |

Anything that needs a decision card (D2-D8) is a task, however small.

You are the Tech Lead: you triage, decide, brief, route, integrate and verify. Every change to product code (everything outside the AI setup and the work folder) goes to its area agent, quick fixes too; the guard blocks your own edits there (Claude Code). You keep triage, the gates and decision cards, the final checks and setup work; the QA team (`qa-lead`, `qa-engineer`, `ui-qa-expert`, `e2e-qa-expert`) tests, and its UI and E2E experts drive the browser in their own tabs.

Deploy facts (any lane that changes code, quick fixes too): `.claude/project.json` `deploy` holds where the app runs, its environments, how a change reaches each one, who deploys and what needs a restart. When it is missing or empty, ask the developer once, in one question with an answer recommended from the repo (`manifest.yml`, `Dockerfile`, pipeline files), write the answer there and never ask again. A change that depends on a deploy fact nobody knows stops for that question before Design.

## 2. Start a task
1. Task id = the ticket (`<ticket_prefix>1234`; `ticket_prefix` may list several) or a short slug. Outputs go in `<work>/<id>/`.
2. If that folder exists, read `status.md` and continue from the first unfinished stage (`init` again to bind this session). Never redo a finished stage.
3. `live_status.py init <id> --mode task --title "<goal>" --size S|M|L --tool claude|cursor` (`--root <path>` when the product lives outside this repo). Size is a label (S: one layer, a few files; M: several files or layers; L: a new screen, schema, contract or cross-layer work); the team decides which stages run.
4. Context pack, before anyone is picked: `explorer` (mode `context`) writes `<work>/<id>/context.md` - the impact map from `impact.py` (callers, endpoints, the screens and scripts calling them, n8n nodes, tools, each `path:line`), key code, the rules that apply, risk signals and gaps. Every later agent reads it instead of exploring again. Only a change inside one or two files with no callers outside them skips it; then write a five-line `context.md` yourself.
5. Risk, from the pack's evidence (not from size). It sets how deep the safety net goes (section 5) and which gates open (section 7), not how many reviewers join:

   | Risk | Any one of |
   |---|---|
   | high | data model or migration; a contract others call (an endpoint used by n8n or another app, a tool, an outside API, a message); permissions or personal data; an external system in the path (SF, n8n, an LLM); more than ~10 callers or 3+ client screens; an unknown that could change the design |
   | medium | a shared method with callers outside the change; a new or changed screen; config; 3+ files across layers |
   | low | one or two files, no callers outside them, no contract, data or permission change |
6. Write `<work>/<id>/triage.md`: the goal in one line, `Kind of work: <feature|bug|performance|ui|data|config|refactor>`, `Risk: low|medium|high`, `## Risk evidence` (one bullet per signal, citing the pack: "14 callers (context.md)", "endpoint /api/x is called by n8n node Y"), `## Acceptance criteria` (AC1.., each checkable), `## Who will work on this` (`| Stage | Expert | Why |`, one row per expert with a one-line reason, from section 3), `## Not needed` (one line per agent left out and why) and, when no Design stage runs, `## Planned files` (one bullet per file the build may touch). Then `plan <id> --file triage.md`: stages with nobody on them are skipped; Build (its rows name the area agents) and Wrap-up (you) always run.
7. Show the live page (section 6) and tell the developer the lane, the risk with its strongest evidence, and the team, in two lines.

## 3. Who joins (by need, not by size)
The usual task is: `qa-lead` at Design (test plan), the area agents at Build (you brief and route them), `code-reviewer` at Review (one pass), the QA experts the plan names and `qa-lead` (sign-off) at Test, you at Verify, you at Wrap-up. An agent joins only when the task gives it the reason:

| The task has | Agent (stage) |
|---|---|
| A goal with real gaps, or many affected areas | `spec-analyst` (Spec, mode `task`) |
| A bug whose cause is not obvious | `bug-investigator` (Spec) |
| Something slow | `performance-engineer` (Spec, Design, Verify) |
| A large new feature: is it a good product? | `product-critic` (Spec), `story-sizer` when it splits into several stories |
| A new approach, or a change across layers | `solution-architect` (Design) |
| Table or entity changes (D2) | `data-architect` (Design) |
| New roles, permissions, personal data or outside access (D4) | `security-architect` (Design); a small permission change: `solution-architect` |
| A new or changed screen, however small (a demo or a single file too) | `ux-designer` (Design, mode `variants`: it builds the prototype by the `prototype` skill's rules; you show it and ask for the pick; Review `ux-designer (ui)` only for a large screen change). Never design a screen yourself |
| An outside system (sync, API client, SSO, files) | `integration-engineer` (Design) |
| Deploy, environment or pipeline changes | `devops-engineer` (Design) |
| SuccessFactors job profiles, roles, competencies or skills (Job Profile Builder, Talent Intelligence Hub, the skills model, Career Development or Opportunity Marketplace where they use skills) | `sf-skills-expert` (Design, modes `fit` then `field`; Review `sf-skills-expert (sf-skills)` only when most of the change is in this area); other SuccessFactors data stays with `sf-expert`, and a need that spans both gets both |
| A domain the repo lists in `experts` (SuccessFactors, AI, ...) | that domain expert (Design; Review `<expert> (<domain>)` only when most of the change is in that domain, reading the same review pack) |
| Any code change | its area agent at Build, quick fixes too: `backend-developer` (Java and server code), `frontend-developer` (UI: JS, TS, HTML, CSS, views), `integration-engineer` (a connection to an outside system), `n8n-expert` (workflow JSON), `devops-engineer` (build, deploy and pipeline files), `qa-engineer` (tests); `routing.areas` in project.json maps paths to agents. One agent per part; parts with no shared files run in parallel |
| Any code change | `code-reviewer` (Review), one pass |
| Risk medium or high | `qa-engineer` (Design, mode `characterize`: lock today's outputs before Build) |
| Any task that changes code | `qa-lead` (Design, mode `plan`: `test-plan.md`, the risk-based test matrix and who tests what; Test, mode `sign-off`: `qa-signoff.md`, one verdict from every QA result). No task closes without the sign-off |
| A UI change: a template, script, style, view or label a user sees | `ui-qa-expert` (Test, mode `ui`: every item of `${CLAUDE_PLUGIN_ROOT}/reference/qa/ui-checklist.md` in the running app) |
| A journey change: a step across screens, roles or features, a notification, a status flow | `e2e-qa-expert` (Test, mode `journeys`: end-to-end and exploratory, across roles, real data volumes) |
| A new or changed endpoint, or new tests to write | `qa-engineer` (Test: the tests, and the API checks of `${CLAUDE_PLUGIN_ROOT}/reference/qa/api-checklist.md` for each endpoint); existing tests only: `main session` |
| A pushed change to verify, or many criteria | `verifier` (Verify, mode `change`); otherwise `main session` |
| A release branch or go-live | `release-manager` (Release) |

- With no Spec agent, `triage.md` is the spec. With no Design agent and a small plan, write a short `design.md` yourself only when a decision card needs one.
- Owners when they overlap: `performance-engineer` keeps the time budget and baseline, `ai-engineer` decides model, prompt, cache and cost, a domain expert answers its domain's facts.
- Speed budget unless the spec says otherwise: first useful content 3 s, fully usable 6 s, a server call 2 s, an AI answer's first words 5 s (median of 3, measured in the browser by `ui-qa-expert`, or by you).
- When a Spec agent ran, it writes the team into `spec.md`; run `plan <id>` again. After the spec gate the team changes only with a reason: `plan <id> --why "<reason>"`.
- Agents move their own row on the page through the hooks. Without a SubagentStop hook (Cursor) run `expert <id> <stage> "<expert>" done`.

## 4. Briefing agents (keeps them fast)
- Every brief opens with three lines: `Goal: <what this run must achieve for this task, one plain line>`, `Output: <what it hands back: the files changed and the behaviour, or the file it writes and what is in it>` and `Files: <the files it works on>`. The live page shows the goal and the files on the agent's card and in your route event, and the agent's `## Plan` starts from the goal and the output, so make the goal specific to this task ("Decide how Ask shows the answer sentence by sentence without changing the cards", not "Design the change"). Then the task id, the folder, its mode, the risk, what it must write and the scratchpad folder for any test or script. Keep your view of the solution out: the reviewer gets the diff, not your opinion of it.
- Build briefs: the planned files of this part, the approved cards that cover them, the commands to run (`commands` in project.json) and the repo's area skill files that apply (`.claude/skills/<name>/SKILL.md`, for example a labels, admin-page or mcp-tool skill): agents cannot run skills, so they read the named files as instructions. Split the build by area; parts whose files do not overlap go in one message, in parallel.
- Quick brief (quick fix lane, no task folder): `Goal:`, `Output:` and `Files:`, then `Quick fix:` with the exact files and lines, the fix and the test to run; no context pack. The agent's budget is about 8 calls, so the handoff costs about 1-2 minutes.
- Start every brief with: "Read `<work>/<id>/context.md` first and do not explore beyond it; fill only a named gap and add it there." End it with: "Write your output file first, then improve it. Stay within the tool-call budget in your agent file, at most 3 web lookups. Reply in 10 lines or fewer."
- Models: each agent's own `model:` line, so a brief needs no model override: Opus for the agents that decide (spec, investigation, product review, design, data, security, AI, review, audit, speed, domain experts), Sonnet 5.5 for the ones that build and check (the developers, integration, devops, base, tests, verify, explorer, release, sizing). `code-reviewer` and `solution-architect` (task mode) work from a pack in about 20 tool calls; the other agents that decide have about 35, the others about 20; `maxTurns` is about 1.5 times that.
- Packs (seconds, no agent): before Design run `review_pack.py <id> --design` (`design-pack.md`: criteria, impact rows, the cards the paths may need, hard rules, path rules, repo facts and lessons for the paths in `context.md`; plus a `design.md` skeleton with one Changes row per criterion and one Impact map row per impact line). Before Review run `review_pack.py <id>` (`review-pack.md`: the diff with line numbers, scope, safety and unchecked callers as pre-filled MUST rows, criteria, cards, and only the checklist sections, rules and lessons for the changed paths). Brief the agent with the pack, not with a list of documents to read.
- Parallel by default: all Design experts in one message; the Build parts with no shared files in one message; after Build, Review (`code-reviewer`) and Test (the QA experts `test-plan.md` names) in one message, then `qa-lead` (sign-off) once they are done. Run them in the background when you have other work; wait only when the next step needs the result.
- Agents cannot run skills. Only `ui-qa-expert` and `e2e-qa-expert` use the browser (each in its own tab, with the browser tools named in its frontmatter); for the others you run `prototype`, `live-check` and reproductions that need the app, and pass them the results. Brief a QA expert with the app URL, the role to sign in as and the test data the plan names.
- A QA expert with no browser tools (Cursor) writes `## Runbook`: run its steps in the browser and send it the results. A line `Consult: <expert>: <question>` in a QA file (for example `sf-expert`, `sf-skills-expert`, `n8n-expert`, `ai-engineer`): brief that expert with the question (quick brief, about 8 calls) and pass the answer back; QA agents cannot start agents.

## 5. Safety net (nothing may break; depth set by risk)
| Step | low | medium | high |
|---|---|---|---|
| Before Build: `python ${CLAUDE_PLUGIN_ROOT}/scripts/scope_check.py baseline <id>`; `commands.compile`; the full unit suite (`commands.test_all`, else `commands.test` with no filter); record pass and fail counts | yes | yes | yes |
| Characterization tests: `qa-engineer` (mode `characterize`) locks today's outputs of every changed shared method in the session scratchpad; `char_test.py run <id> before` passes | - | yes | yes |
| After Build: compile; the full unit suite (no new failure); `char_test.py run <id> after` and `char_test.py diff <id>` (no change outside `## Intended changes`); `scope_check.py check <id>` (every changed file planned) | yes | yes | yes |
| Review: every caller in the impact map checked by someone | - | yes | yes |
| QA: `qa-lead`'s plan at Design and sign-off at Test; the UI checklist on every changed screen and the API checklist on every changed endpoint; a checklist MUST fails Test | yes | yes | yes |
| Verify: the changed flow, plus the `.claude/smoke.md` items for each area touched | flow | + smoke | + smoke |

- Record it in `<work>/<id>/safety.md`: `## Before build`, `## After build` (commands, counts, results) and `## Intended changes` (one bullet per characterization test whose output the spec changes on purpose, with the `AC#`).
- A test that already failed before Build is noted, never fixed silently. A new failure after Build sends the task back to Build.
- An unplanned file is a MUST: drop it, or accept it with `scope_check.py add <id> <path> --why "<reason>"`. The stop hook sends the turn back once while one is left.
- Commands come from `.claude/project.json` (`commands`); never one that `guard.block_while_app_up` blocks while the app runs.

## 6. Live status
`live_status.py` keeps `<work>/<id>/status.json` (+ `status.md`) and the page `<work>/live.html`. Hooks add reads, edits, commands, agents, guard blocks and rule flags; you add the stage boundaries and gates:
- Page: Claude desktop app: start the `live-status` preview (`.claude/launch.json`, the one server this flow starts itself) and open `http://localhost:<live_port>/live.html?task=<id>`. Cursor and the CLI: `live_status.py open <id>`.
- Each stage that runs: `stage <id> <stage> start`, then `stage <id> <stage> done --out "<evidence>"` (`fail --out "<why>"` on a MUST or a failing test).
- Your card shows what you decide and where you route, not your reads: agent launches show as `route` by themselves (from the brief's `Goal:` and `Files:` lines); risk, team and gate outcomes as decisions. Add `decide <id> "<what>"` for a decision with no gate (the lane, a split into parallel parts, a re-run, a scope cut) and `integrate <id> "<what>"` when you merge the agents' results or run the after-build checks. A product-code edit of yours shows as a chip on your card.
- Each stage has a time budget by risk (`budgets` in project.json overrides the core's); the page flags an overrun. Over budget: say why in one line and go on, or cut scope with the developer. `python ${CLAUDE_PLUGIN_ROOT}/scripts/timing.py --last 5` reports where the time went.
- To show how the flow works (not for real work): `python ${CLAUDE_PLUGIN_ROOT}/scripts/simulate.py <scenario>` writes `<work>/simulate.html` (requests step by step, and every agent: what it does, when it joins, what it reads and writes, its model and budget) and replays the request as `demo-<scenario>` on the live page, opened in the browser; demo tasks never bind a session and are left out of timing; `--clean` removes them.

## 7. Gates (by risk; only for something to decide)
| Risk | Gates |
|---|---|
| low | none, unless a decision card or a prototype needs one: say what was understood in 3 lines and go on |
| medium | one gate, at the end of the last planning stage, covering understanding and plan together: the brief's gaps, the design, the cards, the planned files (`--file brief.md --file design.md --file decisions/...`) |
| high | the spec gate (the brief's gaps), then the design gate |

1. `gate <id> <stage> "<question>" --file <doc>` (repeat `--file` for every document of the gate; `--open prototype.html` for a prototype). A spec or design gate opens only when `handoff_check.py` finds no problem; `--skip-check "<reason>"` only for a real reason.
2. The command prints the gate's full text. Put it in your reply in full, so the developer reads everything in the chat; `chat <id>` prints it again.
3. Ask for the approval and stop. Claude desktop app: end the turn with the next-step box, question "Approve the <stage>?", buttons Approve and Change. Cursor and the CLI: the last line asks "Reply approve, or say what to change."
4. Their reply: "approve" -> `ok <id> <stage>`. Per card -> `ok <id> <stage> --decision Dn` for each approved one, `changes <id> <stage> "<summary>" --decision Dn` for each to change; change only those and gate again. A question is neither: answer it from the documents and the code (cite `path:line`), run `ask <id> "<question>" --answer "<short answer>" [--decision Dn]`, and keep the gate open.

| Decision | When the change touches (triggers in `.claude/project.json` `decisions`) | Card by |
|---|---|---|
| D1 Scope | a Spec agent ran: `brief.md` | `spec-analyst` |
| D2 Data model | an entity, a new write query, a migration or data fix | `data-architect` |
| D3 API and contracts | an endpoint, a message or event shape, another system's payload | `solution-architect` |
| D4 Access and privacy | permission checks, roles, new personal data in a response | `security-architect` or `solution-architect` |
| D5 UI | a new screen, widget, card or dialog | you, `prototype` skill |
| D6 Dependencies and config | build files, app config keys, new jobs | `solution-architect` |
| D7 Other owners | files another developer owns | `dev-handoff` |
| D8 Go-live | a release branch or go-live | `release-manager` |

- Cards live in `<work>/<id>/decisions/` in the layout of `${CLAUDE_PLUGIN_ROOT}/reference/review/decision-card.md`; a D2 card starts with "Data model explained". `ok` records each approval in `decisions.md`. With no Design stage, gate a card on `build`.
- The guard blocks edits that trigger D2, D4 or D6 (as configured) until that card is approved for the session's task. Only the developer approves: run `ok` only on their reply. Build follows the approved cards; anything they don't cover needs a change card (`decisions/D2-change-1.md`), gated, never a silent change.

## 8. Stages

| # | Stage | Who | Output in `<work>/<id>/` | Done when |
|---|---|---|---|---|
| 1 | Spec (when on the team) | `spec-analyst`, `bug-investigator` or `performance-engineer` | `brief.md`, `spec.md` (bugs: reproduction and root cause; speed: `perf.md`) | `handoff_check.py` passes; `plan <id>` |
| 2 | Design (when on the team) | `review_pack.py <id> --design`, then `solution-architect` and the design experts on the team, all in one message, all reading `design-pack.md` (you merge their notes into `design.md`); `qa-engineer` (`characterize`) at risk medium or high; `qa-lead` (`plan`) in the same message; `ux-designer` builds the prototype for UI and you ask for the pick | `design.md` (with `## Planned files`), `test-plan.md`, `decisions/*.md`, `ui.md` / `perf.md` / `sf.md` / `ai.md`, `safety.md` `## Before build` | Every criterion maps to a planned change; `handoff_check.py` passes |
| 3 | Build | The area agents from your build briefs (section 4), in parallel where their files do not overlap, after the "before" steps of section 5; you integrate their results and run the "after" steps | The code change | Follows AGENTS.md, `.claude/rules/`, the repo's area skills and the planned files; the "after" steps of section 5 pass |
| 4+5 | Review and Test, in parallel | `review_pack.py <id>`, then one `code-reviewer` run (`focus: all`, re-checks its own findings) and, in the same message, the QA experts `test-plan.md` names (`qa-engineer` `test` with the API checks, `ui-qa-expert` `ui` for any UI change, `e2e-qa-expert` `journeys` for any journey change), then `qa-lead` (`sign-off`) when they are done; an expert review pass (ui, speed, sf, ai, n8n) only when most of the change is its area, in the same message and reading the same pack. No check pass: the verdict is FAIL when `review.md` or any `review-<x>.md` has a MUST | `review.md`, `test.md`, `qa-ui.md`, `qa-e2e.md`, `qa-signoff.md`, `safety.md` `## After build` | Verdict PASS, tests green and `qa-signoff.md` SIGNED OFF (`stage <id> test done` refuses otherwise). Any MUST, failing test or checklist MUST = FAIL (the QA expert re-runs its failed checks after the fix, then `qa-lead` signs off again): list each (`path:line` + fix), `stage <id> review fail`, back to Build, re-run only what failed. A re-review runs `review_pack.py <id>` again: a delta pack (the files changed since the review and the previous MUSTs to re-check) for the same reviewer |
| 6 | Verify | You: the criteria and smoke items the QA files did not cover (`live-check` when the app is up, otherwise against the diff); `verifier` when on the team; smoke items at risk medium or high | PASS/FAIL per criterion and smoke item in `status.md` | Every criterion and smoke item PASS. A restart needed first: say why and leave the stage open |
| 7 | Release (when on the team) | `release-manager` | `release.md` | READY |
| 8 | Wrap-up | `commit-msg` skill; `dev-handoff` when another owner must act; the lessons (section 9) | Commit message; `handoff-<developer>.md` | The developer has what they need to commit or hand over |

## 9. Lessons loop
Every MUST from a review (once fixed) and every bug found later in a change this flow made adds one line to `.claude/review/lessons.md`: `- <date> <task id>: <the rule, one line> (<area or path glob>)`, from the `## Lessons` of `review.md` or `spec.md`. Add only what the project checklist and lessons do not already say; for a repeat, add ` (again <date>)` to the existing line. Agents read the lines for their area, and the reviewer fails a repeat.

## Rules
- Hand-offs run on ids: `AC#`, `Q#`, `A#`, `D#`; the reviewer fails a change that goes against a confirmed answer or an approved card.
- A MUST or a failing test sends the task back to Build: brief the same area agent with the exact findings (`path:line` and the fix); re-run only the stage that failed. Never wrap up while `review.md` says FAIL or `qa-signoff.md` is not SIGNED OFF.
- You never write product code yourself, not even a one-line fix: route it. Your own edits stay in the AI setup, the work folder and the scratchpad.
- Work another owner must do goes into a handoff, never into their files without asking.
- Add to "For release" (under `## Notes` in `status.md`) what the release needs: changed labels, new config keys, migrations, restarts.
- The flow never commits, pushes, deploys or restarts the app, and runs no git that changes the repo (`git pull` only when the developer asks for it); the developer does. Say what needs a restart and why.
- Finish a task with the stage table from `status.md` and the developer's next action.
