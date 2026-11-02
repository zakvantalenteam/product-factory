---
name: sdlc
description: Triage every request, then run the delivery flow only for real work - answer questions directly, do obvious small changes as quick fixes, do AI-setup work (.claude, .cursor, AGENTS.md) with no task, send a new product (idea, PRD, "build a new product") to the factory skill, and give every other change a task: a context pack first, a risk level from its evidence, only the agents it needs, a safety net scaled by risk so nothing else breaks, and the developer's OK where there is something to decide. Use at the start of any request that may change code, when the developer types /sdlc, or when unsure what step comes next.
---
# Delivery flow (agent core)

Paths: the work folder `<work>` is `work_dir` in `.claude/project.json` (default `.claude/work`); scripts are
`python .claude/core/scripts/<name>.py` (below just `live_status.py`); file names per mode are in
`.claude/core/reference/flow-files.md`.

## 1. Triage (every request, first)
Pick the lane yourself; never ask the developer which one. Say the lane in one line only when you start a task.

| Lane | When | What you do |
|---|---|---|
| Answer | A question, general knowledge, "discuss", "explain", "how does X work" | Answer from what you know or the code (big searches to `explorer`). No work folder, no agents. |
| Read-only | "plan", "don't change", "review this" | "plan": a task with Spec and Design only, then stop. "review this": `review_pack.py <id>` (`--files` or `--base <rev> --head <rev>` for given files or commits), then one `code-reviewer` run (`focus: all`), report, fix nothing. |
| Setup work | Changes only to the AI setup: `.claude/**`, `.cursor/**`, `AGENTS.md`, `CLAUDE.md` (and `setup_paths`) | Do it directly: no task, no agents, no gates. Core files are changed only in the core source. Before you finish run `cursor_sync.py`, then `--check` must be clean (the stop hook checks it). Tests go in the session scratchpad. |
| Quick fix | Obvious and small: up to ~30 lines in up to 3 files (`quick_fix` in project.json), the change is clear, nothing to decide (no table, permission, contract, config, dependency or other owner's file) | Do it yourself. Check the diff against the hard rules in AGENTS.md and `.claude/rules/`, run its existing tests, then `live_status.py quick "<what changed and why>"`. If it grows past the limits, stop and start a task. |
| Product | An idea, a PRD or requirement document, "build a new product/app/system" | Never build from it directly: the `factory` skill (product mode, stage intake). |
| Task | Everything else | Sections 2-9, with only the agents the task needs. |

Anything that needs a decision card (D2-D8) is a task, however small.

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
6. Write `<work>/<id>/triage.md`: the goal in one line, `Kind of work: <feature|bug|performance|ui|data|config|refactor>`, `Risk: low|medium|high`, `## Risk evidence` (one bullet per signal, citing the pack: "14 callers (context.md)", "endpoint /api/x is called by n8n node Y"), `## Acceptance criteria` (AC1.., each checkable), `## Who will work on this` (`| Stage | Expert | Why |`, one row per expert with a one-line reason, from section 3), `## Not needed` (one line per agent left out and why) and, when no Design stage runs, `## Planned files` (one bullet per file the build may touch). Then `plan <id> --file triage.md`: stages with nobody on them are skipped; Build and Wrap-up always run (you).
7. Show the live page (section 6) and tell the developer the lane, the risk with its strongest evidence, and the team, in two lines.

## 3. Who joins (by need, not by size)
The usual task is: you at Build, `code-reviewer` at Review (one pass), you at Test (existing tests), you at Verify, you at Wrap-up. An agent joins only when the task gives it the reason:

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
| A domain the repo lists in `experts` (SuccessFactors, AI, ...) | that domain expert (Design; Review `<expert> (<domain>)` only when most of the change is in that domain, reading the same review pack) |
| Any code change | `code-reviewer` (Review), one pass |
| Risk medium or high | `qa-engineer` (Design, mode `characterize`: lock today's outputs before Build) |
| New tests to write | `qa-engineer` (Test); existing tests: `main session` |
| A pushed change to verify, or many criteria | `verifier` (Verify, mode `change`); otherwise `main session` |
| A release branch or go-live | `release-manager` (Release) |

- With no Spec agent, `triage.md` is the spec. With no Design agent and a small plan, write a short `design.md` yourself only when a decision card needs one.
- Owners when they overlap: `performance-engineer` keeps the time budget and baseline, `ai-engineer` decides model, prompt, cache and cost, a domain expert answers its domain's facts.
- Speed budget unless the spec says otherwise: first useful content 3 s, fully usable 6 s, a server call 2 s, an AI answer's first words 5 s (median of 3, measured by you in the browser; agents cannot open it).
- When a Spec agent ran, it writes the team into `spec.md`; run `plan <id>` again. After the spec gate the team changes only with a reason: `plan <id> --why "<reason>"`.
- Agents move their own row on the page through the hooks. Without a SubagentStop hook (Cursor) run `expert <id> <stage> "<expert>" done`.

## 4. Briefing agents (keeps them fast)
- Brief each agent with the task id, the folder, its mode, the risk, what it must write and the scratchpad folder for any test or script. Keep your view of the solution out: the reviewer gets the diff, not your opinion of it.
- Start every brief with: "Read `<work>/<id>/context.md` first and do not explore beyond it; fill only a named gap and add it there." End it with: "Write your output file first, then improve it. Stay within the tool-call budget in your agent file, at most 3 web lookups. Reply in 10 lines or fewer."
- Models: every agent runs on Opus (its own `model:` line), `explorer` included, so the work comes back right the first time; a brief needs no model override. `code-reviewer` and `solution-architect` (task mode) work from a pack in about 20 tool calls; the other agents that decide (spec, investigation, audit, domain experts, data and security design) have about 35, the others about 20.
- Packs (seconds, no agent): before Design run `review_pack.py <id> --design` (`design-pack.md`: criteria, impact rows, the cards the paths may need, hard rules, path rules, repo facts and lessons for the paths in `context.md`; plus a `design.md` skeleton with one Changes row per criterion and one Impact map row per impact line). Before Review run `review_pack.py <id>` (`review-pack.md`: the diff with line numbers, scope, safety and unchecked callers as pre-filled MUST rows, criteria, cards, and only the checklist sections, rules and lessons for the changed paths). Brief the agent with the pack, not with a list of documents to read.
- Parallel by default: all Design experts in one message; after Build, Review (`code-reviewer`) and Test (`qa-engineer` or your test run) in one message. Run them in the background when you have other work; wait only when the next step needs the result.
- Agents cannot run skills, open the browser or see the running app. You run `prototype`, `live-check` and reproductions that need the app, and pass them the results.

## 5. Safety net (nothing may break; depth set by risk)
| Step | low | medium | high |
|---|---|---|---|
| Before Build: `python .claude/core/scripts/scope_check.py baseline <id>`; `commands.compile`; the full unit suite (`commands.test_all`, else `commands.test` with no filter); record pass and fail counts | yes | yes | yes |
| Characterization tests: `qa-engineer` (mode `characterize`) locks today's outputs of every changed shared method in the session scratchpad; `char_test.py run <id> before` passes | - | yes | yes |
| After Build: compile; the full unit suite (no new failure); `char_test.py run <id> after` and `char_test.py diff <id>` (no change outside `## Intended changes`); `scope_check.py check <id>` (every changed file planned) | yes | yes | yes |
| Review: every caller in the impact map checked by someone | - | yes | yes |
| Verify: the changed flow, plus the `.claude/smoke.md` items for each area touched | flow | + smoke | + smoke |

- Record it in `<work>/<id>/safety.md`: `## Before build`, `## After build` (commands, counts, results) and `## Intended changes` (one bullet per characterization test whose output the spec changes on purpose, with the `AC#`).
- A test that already failed before Build is noted, never fixed silently. A new failure after Build sends the task back to Build.
- An unplanned file is a MUST: drop it, or accept it with `scope_check.py add <id> <path> --why "<reason>"`. The stop hook sends the turn back once while one is left.
- Commands come from `.claude/project.json` (`commands`); never one that `guard.block_while_app_up` blocks while the app runs.

## 6. Live status
`live_status.py` keeps `<work>/<id>/status.json` (+ `status.md`) and the page `<work>/live.html`. Hooks add reads, edits, commands, agents, guard blocks and rule flags; you add the stage boundaries and gates:
- Page: Claude desktop app: start the `live-status` preview (`.claude/launch.json`, the one server this flow starts itself) and open `http://localhost:<live_port>/live.html?task=<id>`. Cursor and the CLI: `live_status.py open <id>`.
- Each stage that runs: `stage <id> <stage> start`, then `stage <id> <stage> done --out "<evidence>"` (`fail --out "<why>"` on a MUST or a failing test).
- Each stage has a time budget by risk (`budgets` in project.json overrides the core's); the page flags an overrun. Over budget: say why in one line and go on, or cut scope with the developer. `python .claude/core/scripts/timing.py --last 5` reports where the time went.
- To show how the flow works (not for real work): `python .claude/core/scripts/simulate.py <scenario>` writes `<work>/simulate.html` (requests step by step, and every agent: what it does, when it joins, what it reads and writes, its model and budget) and replays the request as `demo-<scenario>` on the live page, opened in the browser; demo tasks never bind a session and are left out of timing; `--clean` removes them.

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

- Cards live in `<work>/<id>/decisions/` in the layout of `.claude/core/reference/review/decision-card.md`; a D2 card starts with "Data model explained". `ok` records each approval in `decisions.md`. With no Design stage, gate a card on `build`.
- The guard blocks edits that trigger D2, D4 or D6 (as configured) until that card is approved for the session's task. Only the developer approves: run `ok` only on their reply. Build follows the approved cards; anything they don't cover needs a change card (`decisions/D2-change-1.md`), gated, never a silent change.

## 8. Stages

| # | Stage | Who | Output in `<work>/<id>/` | Done when |
|---|---|---|---|---|
| 1 | Spec (when on the team) | `spec-analyst`, `bug-investigator` or `performance-engineer` | `brief.md`, `spec.md` (bugs: reproduction and root cause; speed: `perf.md`) | `handoff_check.py` passes; `plan <id>` |
| 2 | Design (when on the team) | `review_pack.py <id> --design`, then `solution-architect` and the design experts on the team, all in one message, all reading `design-pack.md` (you merge their notes into `design.md`); `qa-engineer` (`characterize`) at risk medium or high; `ux-designer` builds the prototype for UI and you ask for the pick | `design.md` (with `## Planned files`), `decisions/*.md`, `ui.md` / `perf.md` / `sf.md` / `ai.md`, `safety.md` `## Before build` | Every criterion maps to a planned change; `handoff_check.py` passes |
| 3 | Build | You, after the "before" steps of section 5 | The code change | Follows AGENTS.md, `.claude/rules/`, the repo's area skills and the planned files; the "after" steps of section 5 pass |
| 4+5 | Review and Test, in parallel | `review_pack.py <id>`, then one `code-reviewer` run (`focus: all`, re-checks its own findings) and, in the same message, `qa-engineer` (`test`) or your run of the tests; an expert review pass (ui, speed, sf, ai, n8n) only when most of the change is its area, in the same message and reading the same pack. No check pass: the verdict is FAIL when `review.md` or any `review-<x>.md` has a MUST | `review.md`, `test.md` or one line per criterion under `## Notes`, `safety.md` `## After build` | Verdict PASS and tests green. Any MUST or failing test = FAIL: list each (`path:line` + fix), `stage <id> review fail`, back to Build, re-run only what failed. A re-review runs `review_pack.py <id>` again: a delta pack (the files changed since the review and the previous MUSTs to re-check) for the same reviewer |
| 6 | Verify | You: `live-check` when the app is up, otherwise each criterion against the diff; `verifier` when on the team; smoke items at risk medium or high | PASS/FAIL per criterion and smoke item in `status.md` | Every criterion and smoke item PASS. A restart needed first: say why and leave the stage open |
| 7 | Release (when on the team) | `release-manager` | `release.md` | READY |
| 8 | Wrap-up | `commit-msg` skill; `dev-handoff` when another owner must act; the lessons (section 9) | Commit message; `handoff-<developer>.md` | The developer has what they need to commit or hand over |

## 9. Lessons loop
Every MUST from a review (once fixed) and every bug found later in a change this flow made adds one line to `.claude/review/lessons.md`: `- <date> <task id>: <the rule, one line> (<area or path glob>)`, from the `## Lessons` of `review.md` or `spec.md`. Add only what the project checklist and lessons do not already say; for a repeat, add ` (again <date>)` to the existing line. Agents read the lines for their area, and the reviewer fails a repeat.

## Rules
- Hand-offs run on ids: `AC#`, `Q#`, `A#`, `D#`; the reviewer fails a change that goes against a confirmed answer or an approved card.
- A MUST or a failing test sends the task back to Build; re-run only the stage that failed. Never wrap up while `review.md` says FAIL.
- Work another owner must do goes into a handoff, never into their files without asking.
- Add to "For release" (under `## Notes` in `status.md`) what the release needs: changed labels, new config keys, migrations, restarts.
- The flow never commits, pushes, deploys or restarts the app, and runs no git that changes the repo (`git pull` only when the developer asks for it); the developer does. Say what needs a restart and why.
- Finish a task with the stage table from `status.md` and the developer's next action.
