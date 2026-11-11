# How work flows: the detail (agent core)

The core block in `AGENTS.md` keeps the lanes and the hard rules. This file holds the rest. Read it before a Task or
a Product, and whenever you need one of these details. The `sdlc` skill routes each request to its skill and holds the shared
rules; the `develop`, `fix`, `test` and `review-spec` skills (task mode) and the `factory` skill (product mode) give
the steps.

## The skills and the hand-off chain
Each flow skill owns one job, starts the agents its run needs and refuses another skill's job (it names the right
one). They hand over through the work folder: `<work>/<id>/status.json` holds the stage, the `skill` and a `next`
line, so any session can pick a ticket up.

| Skill | Owns | Ends with |
|---|---|---|
| `review-spec` | clear requirements, in plain words, with the Definition of Ready and a size per ticket; also with no product repo (requirements only) | READY requirements, then `/develop` |
| `develop` | new features and changes (feature, ui, data, config, refactor, performance) | ready for `/test` (or "test later") |
| `fix` | making something broken work again (bugs, fix-list items; `--hotfix` for a production incident) | items fixed, then `/test retest` (a bug ticket: `/test`; a hotfix: retest, then the backport) |
| `test` | the quality sign-off | SIGNED OFF, then the commit message; or a fix list, then `/fix` |
| `release` | the go or no-go of a release branch or ticket list: sign-offs, deploy plan, smoke P1 on the release candidate, release notes, rollback | Go (the developer deploys) or NO-GO items for `/test` and `/fix` |
| `sdlc` | the router and the shared rules (task start, team, briefing, safety net, live status, gates, stages, lessons) | the right skill |

The chain: `/review-spec` -> `/develop` -> `/test` -> `/fix` -> `/test retest` -> SIGNED OFF -> commit message ->
`/release <branch>`; in production `/fix --hotfix` -> `/test retest` -> backport. Size
never picks a skill: `develop` and `fix` have a small path for a change within `quick_fix` with nothing to decide.

## Task mode
- A task lives in the work folder (`work_dir` in `.claude/project.json`). First `explorer` writes the context pack
  (`context.md`: impact map with every caller, endpoint, screen and outside node as `path:line`, key code, the rules
  that apply, risk signals). The risk (low, medium, high) is set from that evidence. Then only the agents the task
  needs join, each reading the pack instead of exploring again.
- Build goes to the area agents: `backend-developer` for Java, `frontend-developer` for UI, `integration-engineer`,
  `n8n-expert` for workflows, `devops-engineer` for build and deploy files, `qa-engineer` for tests. Independent parts
  with no shared files run in parallel in one message.
- The small path of `develop` and `fix` gets a quick brief: the exact files and lines, the fix, the test; about 8
  calls, no context pack.
- `develop` checks the Definition of Ready first; a NOT READY ticket is answered on the spot by the developer when
  they are the requester, otherwise it goes to `/review-spec`. `fix` never fixes without a proven cause
  (`fix-proof.md`, checked by `handoff_check.py <id> --fix`), and every fix comes with a regression test that fails
  before and passes after, plus the regression ring.

## Safety net
- The risk sets the safety net, so nothing else breaks: compile and the full unit suite before and after, and every
  changed file planned (scope check). At medium and high also characterization tests that lock today's outputs, every
  caller checked and the smoke list of each area touched (`.claude/smoke.md`).
- The reviewer fails any change with a MUST from the review checklists. Every review MUST adds a line to
  `.claude/review/lessons.md`.

## QA
- QA signs off every task that changes code. `qa-lead` plans the tests at Design (a risk-based matrix of criterion,
  test type, role and data volume) and signs off at Test.
- `ui-qa-expert` tests every UI change in the running app against the UI checklist
  (`.claude/core/reference/qa/ui-checklist.md`: every state, paging at scale, the detail in view, cut-off text
  readable, keyboard, 360 px, 200% zoom, long labels, tenant colours, console and network).
- `e2e-qa-expert` runs the journeys across roles. `qa-engineer` writes the tests and runs the API checks
  (`.claude/core/reference/qa/api-checklist.md`).
- A checklist MUST fails Test, and no task closes without the sign-off.
- Test data: `test-data-engineer` makes the data a plan needs, so testers stop asking for it. `/test data` builds the
  QA data map once per product (`.claude/qa/data-map.md`: per need find on dev, create through the app, or ask the
  developer; seed and cleanup scripts in `.claude/qa/seed/`), approved by the developer at one gate before anything
  is created. In each `/test` it tops up what the plan misses (`QA-<ticket>-` records, `data.md`); what it cannot
  make is BLOCKED with an ask. Dev hosts only (`qa.data.hosts`), synthetic names, writes only through the app, a
  yes for batches over 100, every create logged; cleanup only on request (`/test data cleanup`).
- Smoke pack: `qa-lead` keeps `.claude/smoke.md` (areas with `paths:`, one-line items, short journeys with role,
  steps, expected and data, `[P1]` items as the release gate). Every `/test` run adds the items of the areas a ticket
  touches; `/test smoke` runs the whole pack. `/develop` and `/fix` leave `smoke: add` lines in
  `.claude/qa/smoke-inbox.md` for a new screen or journey or a release bug.
- `/test` (the `test` skill) runs the QA team on its own: one ticket, several in one run (`/test BLEN-1 BLEN-2`), or
  `/test retest BLEN-1` for the fixed items. It works in any session, because the state lives in the work folder.
  `develop` and `fix` end ready for it. "Test later" leaves the task waiting at Test.
- Fixes are never automatic. QA leaves `fix-list.md` (`.claude/core/reference/qa/fix-list.md`), and the developer
  starts `/fix BLEN-1` or `/fix BLEN-1 F1 F3`: a proven cause, the fix by its owner, a re-review, then
  `/test retest`. A ticket closes only on SIGNED OFF, and then `/test` offers the commit message.

## Requirements
- `/review-spec` (the `review-spec` skill) reviews requirements with spec-analyst, product-critic, ux-designer, the
  domain experts the topic needs and qa-lead (testability). It writes plain words for product owners, analysts and
  managers, and checks the Definition of Ready (`.claude/core/reference/requirements/definition-of-ready.md`). It
  stops at one gate with the requester. It is read-only on code.
- READY requirements (`Requirements: READY` in `spec.md`, a Jira comment, or a file the developer points to) skip the
  business questions in `/develop`. The technical agents add only the technical part, and any change to a criterion goes
  back to the requester.
- Each READY ticket carries a size (`story-sizer`, mode `estimate`: points, confidence and a split proposal when it
  is too big) in `estimate.md`.
- With no `.claude/project.json` (a product owner's own folder) `/review-spec` runs as requirements only: files in
  `requirements/<id>/`, no live page, no code read, and the output says the "what exists today" check is left to
  `/develop`.

## The Tech Lead and the gates
- The main session keeps triage, the gates and decision cards, quick live checks in the browser (the UI and E2E QA
  experts test in their own browser tabs), the final checks and setup work.
- The team is picked by need, not by size; a stage with nobody on it is skipped.
- The developer (or product owner) is stopped only for something to decide: gaps in the brief, decision cards D1-D8
  (scope, data model, API, access, UI, dependencies and config, other owners, go-live) and prototype picks. One gate
  per stage, with its full text in the chat and an Approve/Change question.

## Hooks
Hooks enforce the flow in Claude and Cursor, only in a repo with `.claude/project.json`. A guard that fails blocks
the call instead of letting it through.
- The guard holds data-model, access and config edits until their card is approved.
- It blocks the main session's edits to product code (Claude Code; Cursor's hooks cannot tell the main session from an
  agent, so there the rule and the live page's chip hold it).
- It blocks git commands that change the repo (pull passes only when the developer asked for it) and edits to
  generated files, and (product mode) product code before the base stage or the design approval.
- A rules check runs after each edit. A turn that changed files outside these lanes is sent back once.

## Live page
The live page shows every task at agent level and is the only tracker: each agent's work on its own card, the Tech
Lead's decisions and routing on its card (with a chip when it edited product code itself), and the Tech Lead's share
of the work. Open it with `python .claude/core/scripts/live_status.py open <id>`. Each run shows its tokens and an
estimated cost (the price table is `costs` in project.json). For people without the page: `live_status.py share <id>`
(one offline HTML snapshot in plain words) and `share --all` (every open task, for an engineering manager).

## Agents and skills
- Flow skills: `sdlc` (the router and the shared rules), `review-spec` (requirements team), `develop` (features and
  changes), `fix` (bugs and fix-list items), `test` (QA team), `factory` (product mode); helpers `prototype`,
  `dev-handoff`, `commit-msg`, `verify-push`, `live-check`. The flow skills are team leads: each run picks the agents
  it needs and starts them, in parallel where independent.
- Agents: `explorer` (search), `spec-analyst`, `bug-investigator`, `product-critic`, `story-sizer`, `ux-designer`,
  `solution-architect`, `data-architect`, `security-architect`, `base-builder`, `backend-developer`,
  `frontend-developer`, `integration-engineer`, `devops-engineer`, `performance-engineer`, `code-reviewer`, `qa-lead`,
  `qa-engineer`, `ui-qa-expert`, `e2e-qa-expert`, `test-data-engineer`, `verifier`, `audit-expert`, `release-manager`; domain experts
  `sf-expert`, `sf-skills-expert` (SuccessFactors job profiles and skills), `ai-engineer`, `n8n-expert` (repo facts in
  `.claude/experts/`). The repo's own agents, area skills and path rules sit next to them.
- Every agent is tagged with verified credentials (frontmatter `certifications:`, general first, then SAP) and works to
  their practical knowledge: its practice pack `.claude/core/reference/practice/<agent>.md` and its `## Expert
  standard` (the simplest good solution, no new layer or dependency without a stated need; rules marked (SAP) apply
  only when `stack.platform` is `sap-btp`).
- Each agent reads `.claude/core/reference/agents/common.md`, its practice pack and the task's `context.md` first (code
  agents also the stack packs `.claude/project.json` `stack` names). It writes its output file first. The file opens
  with `## Summary for people` and a `## Plan`: a Goal, Output and Done when line for this task, then 4-8 items it
  ticks as it goes, each naming a file, endpoint, node, screen, criterion or decision. The live page shows both and
  flags a generic plan.
- Call budget: about 35 tool calls for an agent that decides (spec, investigation, audit, domain experts, data and
  security design), about 20 otherwise (`code-reviewer` and `solution-architect` work from a pack: `review_pack.py`).
  Web lookups only for version-specific facts (at most 3, agents with a web tool). Replies in 10 lines or fewer.
  Reviewers are read-only.
- Models (each agent's `model:` line): Opus for the agents that decide (`solution-architect`, `security-architect`,
  `data-architect`, `ai-engineer`, `code-reviewer`, `ux-designer`, `spec-analyst`, `product-critic`,
  `bug-investigator`, `audit-expert`, `performance-engineer`, `sf-expert`, `sf-skills-expert`), Opus at high effort
  (`effort: high`) for every QA and dev agent (`qa-lead`, `qa-engineer`, `ui-qa-expert`, `e2e-qa-expert`, `test-data-engineer`, `verifier`,
  `backend-developer`, `frontend-developer`, `integration-engineer`, `devops-engineer`, `base-builder`, `n8n-expert`),
  Sonnet 5.5 for the rest (`explorer`, `release-manager`, `story-sizer`). `maxTurns` is about 1.5 times the call budget. Cursor has no per-agent model
  or effort control: it runs every agent on the session's model.

## Git, servers and secrets
- No git command that changes the repo: commit, push, pull, fetch, merge, rebase, stash, reset, checkout, switch,
  restore, add, branch, tag, ... Read-only git (status, diff, log, show) is fine. `git pull` only when the developer
  asks for it in their own message.
- Never start or restart servers; say what needs a restart and why. Never copy secret values.

## Core files and sync
- Core files (`.claude/core/`, the core agents and skills listed in `.claude/core/core.lock`) are changed only in the
  core source and installed with its `install.py`; `python .claude/core/scripts/install.py . --check` lists hand
  edits.
- All projects stay in sync: every project with the core (product-factory, Blend, TalentBox, SkillsOS and any
  product made since) and the product-factory plugin run the same core version.
- A change to the shared setup (an agent, skill, hook, script, rule or the flow) is made once in the core source
  (product-factory `core/`) and installed in every project in the same change: `python core/scripts/install.py <repo>
  --write-settings` from product-factory for each, then `install.py . --check` and `cursor_sync.py --check` clean in
  each.
- Only when the developer asks for a change in one project does it go in that project's own files (its
  `.claude/project.json`, its own agents, skills and rules, AGENTS.md outside the core block), never in a core file,
  and the reply says which projects now differ. In a repo without the core source, say the change belongs in
  product-factory's `core/` and which projects it reaches.

## Claude Code and Cursor
- Claude Code reads `AGENTS.md` through `CLAUDE.md`. Cursor reads it directly and loads `.claude/skills/` itself.
- The product-factory plugin is switched on or off only in each person's plugin manager (no project setting). When it
  is on, Claude uses its `product-factory:<name>` agents and `/product-factory:<name>` skills and the repo copy's hooks
  step aside; when it is off or not installed, the repo copy in `.claude/core/` works as before.
- The Cursor agents, rules and hooks in `.cursor/` are generated by `cursor_sync.py`. Every setup change must keep
  working for Cursor in the same change.
