---
name: sdlc
description: "Use at the start of any request that may change code, when the developer types /sdlc, or when unsure what step comes next. Triages every request into its lane (answer, read-only, setup work, quick fix routed to its area agent, a new product to the factory skill, task) and runs task mode: a context pack first, a risk level from its evidence, only the agents the task needs (the Tech Lead decides and routes, the area agents write the code), a safety net scaled by risk, and the developer's OK where there is something to decide."
---
# Delivery flow (agent core)

Paths: the work folder `<work>` is `work_dir` in `.claude/project.json` (default `.claude/work`); scripts are
`python ${CLAUDE_PLUGIN_ROOT}/scripts/<name>.py` (below just `live_status.py`); file names per mode are in
`${CLAUDE_PLUGIN_ROOT}/reference/flow-files.md`; the agents, models, QA, hooks and sync rules that the `AGENTS.md` core block
leaves out are in `${CLAUDE_PLUGIN_ROOT}/reference/how-work-flows.md`. The longer sections are files next to this one, read when their step comes: [team.md](team.md) (section 3), [briefing.md](briefing.md) (4), [safety-net.md](safety-net.md) (5) and [stages.md](stages.md) (8); every rule in them applies.

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
The usual team: `qa-lead` at Design (test plan), the area agents at Build (you brief and route them), `code-reviewer` at Review, the QA experts the plan names and `qa-lead` (sign-off) at Test, you at Verify and Wrap-up. Any other agent joins only for a reason the task gives. Read [team.md](team.md) before you write `## Who will work on this`: which need brings which agent (spec, bug, speed, product, design, data, access, screens, outside systems, deploy, domain experts, the area agent per code path, QA), who owns what when they overlap, and the speed budget.

## 4. Briefing agents (keeps them fast)
Every brief opens with `Goal:`, `Output:` and `Files:` lines; a quick brief adds `Quick fix:` (the exact files and lines, the fix, the test; about 8 calls, no context pack). Read [briefing.md](briefing.md) before the first brief of a task: what a brief holds, models and budgets, the design and review packs, what runs in parallel, and the QA experts' browser, runbook and consult lines.

## 5. Safety net (nothing may break; depth set by risk)
Before Build: the scope baseline, compile and the full unit suite (and characterization tests at risk medium and high); after Build: compile, the full suite, the characterization diff and the scope check; QA plan and sign-off at every risk; smoke items at Verify from medium. Read [safety-net.md](safety-net.md) when Build starts: the steps per risk, `safety.md`, and what a new failure or an unplanned file means.

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
Spec, Design, Build, Review and Test in parallel, Verify, Release and Wrap-up; a stage with nobody on it is skipped. Read [stages.md](stages.md) when each stage starts: who runs it, its output files in `<work>/<id>/` and when it is done (Test only with `qa-signoff.md` SIGNED OFF; any MUST or failing test goes back to Build).

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
