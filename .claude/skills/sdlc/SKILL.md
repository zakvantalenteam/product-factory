---
name: sdlc
description: "(repo copy - with the plugin on use /product-factory:sdlc) Use at the start of any request that may change code, when the developer types /sdlc, or when unsure which skill or step comes next. The router: triages every request to the one skill that owns it (requirements to review-spec, a feature or change to develop, a bug or fix-list items to fix (a production incident to fix --hotfix), testing to test, a release's go or no-go to release, a new product to factory; answers, read-only work and setup work it handles itself) and holds the shared rules those skills use: starting a task, the team, briefing, the safety net, live status, gates and decision cards, the stages and the lessons loop."
---
# Delivery flow (agent core): the router and the shared rules

Paths: the work folder `<work>` is `work_dir` in `.claude/project.json` (default `.claude/work`); scripts are
`python .claude/core/scripts/<name>.py` (below just `live_status.py`); file names per mode are in
`.claude/core/reference/flow-files.md`; the agents, models, QA, hooks and sync rules that the `AGENTS.md` core block
leaves out are in `.claude/core/reference/how-work-flows.md`. The longer sections are files next to this one, read when their step comes: [team.md](team.md) (section 3), [briefing.md](briefing.md) (4), [safety-net.md](safety-net.md) (5), [stages.md](stages.md) (8); every rule in them applies.

Each flow skill owns one job and starts the agents its run needs: `review-spec` clear requirements, `develop`
new features and changes, `fix` making something broken work again (`--hotfix` for production), `test` the QA sign-off, `release` the go or
no-go of a release, `factory` a new product. They hand over through the work folder (`<work>/<id>/status.json`: the stage, the skill and a `next`
line), so any session can pick a ticket up. Sections 2-9 are shared: `develop` and `fix` use them and never copy
them.

## 1. Triage (every request, first)
Pick the skill yourself; never ask the developer which one. Say it in one line when you hand over.

| Lane | When | Whose |
|---|---|---|
| Answer | A question, general knowledge, "discuss", "explain", "how does X work" | You: answer from what you know or the code (big searches to `explorer`). No work folder, no agents. |
| Read-only | "plan", "don't change", "review this" | "plan": `/develop <id> plan` (Definition of Ready, Spec and Design, then stop). "review this": `review_pack.py <id>` (`--files` or `--base <rev> --head <rev>`), then one `code-reviewer` run (`focus: all`), report, fix nothing. |
| Setup work | Changes only to the AI setup: `.claude/**`, `.cursor/**`, `AGENTS.md`, `CLAUDE.md` (and `setup_paths`) | You, directly: no task, no agents, no gates. Core files are changed only in the core source, and a shared setup change goes to every project in the same change (product-factory, Blend, TalentBox, SkillsOS and the plugin: `install.py <repo> --write-settings`, then both checks in each) unless the developer asks for one project only (then that project's own files, and say which projects now differ). Before you finish run `cursor_sync.py`, then `--check` must be clean (the stop hook checks it). Throwaway checks go in the session scratchpad. |
| Requirements | "review the requirements/spec", "is this ready", a ticket, PRD, document or idea for an existing product to check before any build; a product owner, analyst or manager asking | `review-spec`: ends with READY requirements and a size per ticket, then `/develop`. No code; also runs in a folder with no product repo (requirements only). |
| Feature or change | New or changed behaviour: a feature, screen, data, config, refactor or speed work, "build", "add", "change", "/develop" | `develop`: ends ready for `/test`. |
| Bug or fix | Something that should work and does not, a bug ticket, "fix BLEN-1", "fix BLEN-1 F1 F3" after QA, "/fix" | `fix`: a proven cause first, then the fix and its regression test; ends with `/test retest` (or `/test`). |
| Hotfix | Something broken in production now, an incident, "hotfix", "/fix --hotfix" | `fix --hotfix`: impact first, the smallest proven fix on the release branch, a backport note and an incident note. Never deploys. |
| Test | "/test", "test BLEN-1 BLEN-2", "QA this", "retest BLEN-1", testing someone else's push | `test`: ends SIGNED OFF (then the commit message) or with a fix list (then `/fix`). It fixes nothing. |
| Release | "/release OCT2026", "go or no-go", "release notes", "is the release ready" | `release`: the tickets in it, their sign-offs, the deploy plan, smoke P1 on the release candidate, release notes, one gate. Never deploys, merges or pushes. |
| Product | An idea or a PRD for something that does not exist yet, "build a new product/app/system" | `factory` (product mode, stage intake); never built from the document directly. |

Size never picks a lane: it sets the depth inside `develop` and `fix` (their small path is for a change within
`quick_fix` in project.json with nothing to decide). Anything that needs a decision card (D2-D8) takes their full
path, however small. A request with both a bug and a change is split: the bug to `fix`, the change to `develop`.

The chain: `/review-spec` -> `/develop` -> `/test` -> (`/fix` -> `/test retest`) -> SIGNED OFF -> commit message ->
`/release <branch>` (go or no-go). In production: `/fix --hotfix` -> `/test retest` -> backport.
A skill asked for another skill's job says whose it is in one line and hands over; it never does that job.

You are the Tech Lead: you triage, decide, brief, route, integrate and verify. Every change to product code (everything outside the AI setup and the work folder) goes to its area agent, small changes too; the guard blocks your own edits there (Claude Code). You keep triage, the gates and decision cards, the final checks and setup work; the QA team (`qa-lead`, `qa-engineer`, `ui-qa-expert`, `e2e-qa-expert`) tests, and its UI and E2E experts drive the browser in their own tabs.

Deploy facts (any skill that changes code, small changes too): `.claude/project.json` `deploy` holds where the app runs, its environments, how a change reaches each one, who deploys and what needs a restart. When it is missing or empty, ask the developer once, in one question with an answer recommended from the repo (`manifest.yml`, `Dockerfile`, pipeline files), write the answer there and never ask again. A change that depends on a deploy fact nobody knows stops for that question before Design.

## 2. Start a task (shared by `develop` and `fix`)
1. Task id = the ticket (`<ticket_prefix>1234`; `ticket_prefix` may list several) or a short slug. Outputs go in `<work>/<id>/`.
2. If that folder exists, read `status.md` and continue from the first unfinished stage (`init` again to bind this session). Never redo a finished stage. READY requirements (a `spec.md` with `Requirements: READY` from the `review-spec` skill, the approved requirements in a Jira comment, or a file the developer points to) mean no business questions: `spec-analyst` (mode `task`) adds only the technical part (affected areas as `path:line`, kind of work, team, decision cards), and any change to a criterion goes back to the requester as a question. A Spec stage that `review-spec` closed (spec.md has `Requirements: READY` but no `Kind of work:` line) is not finished for this flow: `stage <id> spec start` again for that technical part.
3. `live_status.py init <id> --mode task --skill develop|fix --title "<goal>" --size S|M|L --tool claude|cursor` (`--root <path>` when the product lives outside this repo). Size is a label (S: one layer, a few files; M: several files or layers; L: a new screen, schema, contract or cross-layer work); the team decides which stages run.
4. Context pack, before anyone is picked: `explorer` (mode `context`) writes `<work>/<id>/context.md` - the impact map from `impact.py` (callers, endpoints, the screens and scripts calling them, n8n nodes, tools, each `path:line`), key code, the rules that apply, risk signals and gaps. Every later agent reads it instead of exploring again. Only a change inside one or two files with no callers outside them skips it; then write a five-line `context.md` yourself.
5. Risk, from the pack's evidence (not from size). It sets how deep the safety net goes (section 5) and which gates open (section 7), not how many reviewers join:

   | Risk | Any one of |
   |---|---|
   | high | data model or migration; a contract others call (an endpoint used by n8n or another app, a tool, an outside API, a message); permissions or personal data; an external system in the path (SF, n8n, an LLM); more than ~10 callers or 3+ client screens; an unknown that could change the design |
   | medium | a shared method with callers outside the change; a new or changed screen; config; 3+ files across layers |
   | low | one or two files, no callers outside them, no contract, data or permission change |
6. Write `<work>/<id>/triage.md`: the goal in one line, `Kind of work: <feature|bug|performance|ui|data|config|refactor>`, `Risk: low|medium|high`, `## Risk evidence` (one bullet per signal, citing the pack: "14 callers (context.md)", "endpoint /api/x is called by n8n node Y"), `## Acceptance criteria` (AC1.., each checkable), `## Who will work on this` (`| Stage | Expert | Why |`, one row per expert with a one-line reason, from section 3), `## Not needed` (one line per agent left out and why) and, when no Design stage runs, `## Planned files` (one bullet per file the build may touch). Then `plan <id> --file triage.md`: stages with nobody on them are skipped; Build (its rows name the area agents) and Wrap-up (you) always run.
7. Show the live page (section 6) and tell the developer the skill, the risk with its strongest evidence, and the team, in two lines.

## 3. Who joins (by need, not by size)
The usual team: `qa-lead` at Design (test plan), the area agents at Build (you brief and route them), `code-reviewer` at Review, the QA experts the plan names and `qa-lead` (sign-off) at Test, you at Verify and Wrap-up. Any other agent joins only for a reason the task gives. Read [team.md](team.md) before you write `## Who will work on this`: which need brings which agent (spec, bug, speed, product, design, data, access, screens, outside systems, deploy, domain experts, the area agent per code path, QA), who owns what when they overlap, and the speed budget.

## 4. Briefing agents (keeps them fast)
Every brief opens with `Goal:`, `Output:` and `Files:` lines; a quick brief (the small path of `develop` and `fix`) adds `Quick fix:` (the exact files and lines, the fix, the test; about 8 calls, no context pack). Read [briefing.md](briefing.md) before the first brief of a task: what a brief holds, models and budgets, the design and review packs, what runs in parallel, and the QA experts' browser, runbook and consult lines.

## 5. Safety net (nothing may break; depth set by risk)
Before Build: the scope baseline, compile and the full unit suite (and characterization tests at risk medium and high); after Build: compile, the full suite, the characterization diff and the scope check; QA plan and sign-off at every risk; smoke items at Verify from medium. Read [safety-net.md](safety-net.md) when Build starts: the steps per risk, `safety.md`, and what a new failure or an unplanned file means.

## 6. Live status
`live_status.py` keeps `<work>/<id>/status.json` (+ `status.md`) and the page `<work>/live.html`. Hooks add reads, edits, commands, agents, guard blocks and rule flags; you add the stage boundaries and gates:
- Page: Claude desktop app: start the `live-status` preview (`.claude/launch.json`, the one server this flow starts itself) and open `http://localhost:<live_port>/live.html?task=<id>`. Cursor and the CLI: `live_status.py open <id>`.
- Each stage that runs: `stage <id> <stage> start`, then `stage <id> <stage> done --out "<evidence>"` (`fail --out "<why>"` on a MUST or a failing test). A stage that runs again after a later one is its next round on the page (`Build (fix round 2)`, `Test (retest)`); a start closes the earlier live stages with no agent at work. Each agent's run shows in its home stage. A task from before 1.14.1 that groups them wrongly: `live_status.py repair <id>` (`--dry-run` first).
- Your card shows what you decide and where you route, not your reads: agent launches show as `route` by themselves (from the brief's `Goal:` and `Files:` lines); risk, team and gate outcomes as decisions. Add `decide <id> "<what>"` for a decision with no gate (the lane, a split into parallel parts, a re-run, a scope cut) and `integrate <id> "<what>"` when you merge the agents' results or run the after-build checks. A product-code edit of yours shows as a chip on your card.
- Sharing: `live_status.py share <id>` writes `<work>/<id>/share.html`, one offline file in plain words (stages, who did what, decisions, open questions, the QA result, tokens and cost) for a product owner, QA or manager; `share --all` writes `<work>/share-all.html` with every open task. Sending or publishing it is a separate step the developer asks for. Each agent run shows its tokens and an estimated cost (prices in `costs` of project.json).
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
Spec, Design, Build and Review (`develop` and `fix`), then Test, Verify, Release and Wrap-up (`test`); a stage with nobody on it is skipped. Read [stages.md](stages.md) when each stage starts: who runs it, its output files in `<work>/<id>/` and when it is done (Test only with `qa-signoff.md` SIGNED OFF; any MUST or failing test goes back to Build).

## 9. Lessons loop
Every MUST from a review (once fixed) and every bug `fix` finds in a change this flow made adds one line to `.claude/review/lessons.md`: `- <date> <task id> [<stage>]: <the rule, one line> (<area or path glob>)`, from the `## Lessons` of `review.md` or `spec.md`, or a `/fix` escape line. The stage tag says who must catch it next time: `[review-spec R<n>]` (spec-analyst and qa-lead's requirements review), `[develop review]` (code-reviewer, through the review pack; a line with no tag counts as this), `[test <type>]` (qa-lead's plan, a type of `test-types.md`). Add only what the project checklist and lessons do not already say; for a repeat, add ` (again <date>)` to the existing line. Agents read the lines for their stage and area, and the reviewer fails a repeat. A missing check that belongs in the core goes to `.claude/review/core-escapes.md` for the core owner (the `fix` skill, section 4), never into core files.

## Rules
- Hand-offs run on ids: `AC#`, `Q#`, `A#`, `D#`; the reviewer fails a change that goes against a confirmed answer or an approved card.
- A MUST or a failing test sends the task back to Build: brief the same area agent with the exact findings (`path:line` and the fix); re-run only the stage that failed. Never wrap up while `review.md` says FAIL or `qa-signoff.md` is not SIGNED OFF.
- You never write product code yourself, not even a one-line fix: route it. Your own edits stay in the AI setup, the work folder and the scratchpad.
- Work another owner must do goes into a handoff, never into their files without asking.
- Add to "For release" (under `## Notes` in `status.md`) what the release needs: changed labels, new config keys, migrations, restarts.
- The flow never commits, pushes, deploys or restarts the app, and runs no git that changes the repo (`git pull` only when the developer asks for it); the developer does. Say what needs a restart and why.
- Finish a task with the stage table from `status.md` and the developer's next action.
