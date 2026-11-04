# Common rules for every core agent

Every core agent reads this file once, at its start. Your own agent file adds your certification, your expert
standard, your call budget and your modes. The hard rules in `AGENTS.md`, confirmed answers and approved decisions
win over this file and over your own habits; when one conflicts with your standard, follow it and say so.
Core paths: a path that starts with the core folder (`.claude/core` in a repo that carries the core,
`${CLAUDE_PLUGIN_ROOT}` in the plugin, `.cursor/runtime` in Cursor once the repo uses the plugin) means the folder
two levels above this file.

## Start (no extra round trip)
- First message, in parallel: this file, your practice pack (`.claude/core/reference/practice/<your name>.md`: the
  practical knowledge behind your credentials), `<work>/<id>/context.md` when the task has one (or the pack your
  file names), and, when you design, write or review code, a Grep of `.claude/project.json` for `"stack"` (8 lines
  after).
- Next message, next to your first code reads: the stack packs `stack.packs` names that match the files you touch
  (`.claude/core/reference/stacks/<pack>.md`), and the lines of `.claude/review/lessons.md` for your area
  (mistakes this repo has already made).

## Output file (the live page reads it)
The output file you write first starts, under its title, with `## Summary for people` (3-5 plain lines: what you
looked at, what you found or changed, the verdict or decision, what is left; no code, paths or ids), then `## Plan`
in this shape, so a person on the live page sees what you are doing for this task:

    ## Plan
    Goal: <what this run must achieve for this task, one plain line>
    Output: <what the person gets at the end: the file and what is in it; for a build, the files changed and the behaviour>
    Done when: <the check that proves it: the tests or cases that pass, the criterion that holds>
    - [ ] <4-8 items, each naming the concrete thing in this task>

- Start from the brief's `Goal:` and `Output:` lines; make them sharper if the work shows more.
- Each item names the concrete thing: a file, endpoint, node, screen, criterion id, or a decision with its options.
  Good: "Map how `AiSearchTurnHub` sends events to the widget", "Change Build Widgets in 02 to stream text first",
  "Decide: shadow mode or blocking for the injection check". Process steps are not plan items: "Read the brief",
  "Check every caller", "Write lessons", "Note suggestions".
- A plan with no Goal or Output line, or with generic items, gets a "plan too generic" chip on the live page and a
  note to fix it in your next write to the file.
- Tick an item `- [x]` when it is finished, only in a write you make anyway (no extra calls). An HTML file holds the
  summary and the plan in a `<!-- Summary for people` comment at the top, with a `Plan` line, then the Goal, Output
  and Done when lines and the items. Keep both true as you work: the live page shows the plan live and the summary
  when you finish.

## Context
Read `<work>/<id>/context.md` first when the task has one, and do not explore beyond it. If you need something it
lacks, find only that and add it under its `## Gaps` as `### <gap> (by <your name>)` with `path:line`, so the next
agent has it.

## Briefs from the Tech Lead (code agents)
The main session is the Tech Lead: it triages, decides, briefs, routes, integrates and verifies, and every change to
product code comes to the area agent as a brief, quick fixes too. A brief opens with `Goal:` (what this run
must achieve for this task, one plain line), `Output:` (what you hand back: the files changed and the behaviour,
or the file you write) and `Files:` (the files you work on); the live page shows the goal and the files on your
card, and your plan starts from the goal and the output. An older brief may open with `Job:` instead of `Goal:`.
- Quick brief (it says `Quick fix:`; there is no task folder): the exact files and lines, the fix and the test to run.
  Do just that in about 8 calls: this file, your practice pack and the named files in one message, the edit, the
  named test, then reply with the change (`path:line`) and the test result. No context pack and no output file. If
  the fix is bigger than the brief or needs a decision, stop and say so in the reply.
- Task brief: build the planned files (`design.md` or `triage.md` `## Planned files`) as the approved cards say; a
  file outside the plan is a stop-and-ask in your reply, never a silent change.
- Area skills: agents cannot run skills. The brief names the repo's area skill files that apply (for example
  `.claude/skills/<name>/SKILL.md`): read each one and follow it as instructions.
- Parallel parts: other agents may be editing other files at the same time; touch only your brief's files.
- Where tests live (hard rule, every code agent and `qa-engineer`): an automated test always goes in the project's
  test folder, mirroring the package or folder of the code under test (Java `src/test/java/<same package>/`;
  JavaScript in the test folder your stack pack names). Never in `src/main/**`, the repo root or any other folder.
  The session scratchpad holds only throwaway scripts and characterization runs, never a test meant to stay. The
  rules check flags a test file written under `src/main/` or in the repo root.

## Speed
- The call budget in your Speed line is a ceiling, not a target: stop as soon as your output meets the bar. Your
  `maxTurns` is about 1.5 times that budget: a run that hits it stops, so the output file written first is your result.
- Batch: every independent Read, Grep and Glob goes in one message; never one file per turn.
- Write the output file first, then improve it with Edit.
- Big files: `python .claude/core/scripts/codemap.py <file>` or Grep first, then Read with offset and limit.
- Never re-read a file you already hold, and never re-check what a script already checked.
- Web (agents with a web tool): only for a version-specific or outside fact the repo cannot answer (an API field,
  a library or platform version, a limit), at most 3 lookups, each cited with its URL; never for general knowledge.
  Agents without one mark such a fact "not confirmed" and name what to check.

## The expert bar (all agents)
1. Simplest good solution: the smallest change, design or answer that meets every criterion. Reuse what the repo
   already has (name it, `path:line`) before you add anything.
2. Over-engineering is a defect: no new layer, abstraction, service, table, dependency, config key, flag or
   schedule without a stated need tied to a criterion or a measured number. An interface needs two real
   implementations today; a factory needs two types.
3. Each recommendation names one rejected alternative and why, in one line.
4. Evidence for every claim: `path:line`, a command result or a cited source. Write "not confirmed" instead of a guess.
5. Versions are a ceiling: never use a language, framework or library feature above what `stack` names.
6. Name the trade-off, the risk and the check that proves it (a test, a query, a live step).
7. Precise terms for code, plain words for people.

## Credentials and platform
Your `Certified as:` line (generated from the `certifications:` list in your frontmatter) names general credentials
first (valid at any software company, startup to enterprise), then after `SAP:` the SAP ones. You work to the
practical knowledge those exams test (your practice pack); you do not claim to hold them. A rule, or the part of a rule, marked (SAP) applies only when `stack.platform` in
`.claude/project.json` is `sap-btp`; every other rule always applies. On another platform use its own services and
docs, and bring no SAP advice (XSUAA, destinations, HANA, UI5, Fiori, SAP Activate) to it.

## Stack packs (`.claude/core/reference/stacks/`)
| Pack | For | Read by |
|---|---|---|
| `java17-spring-boot3.md` | Java 17, Spring Boot 3, JPA with EclipseLink, SAP HANA or PostgreSQL | backend-developer, base-builder, code-reviewer, performance-engineer, qa-engineer, integration-engineer, solution-architect (design), data-architect |
| `ui5-plainjs.md` | SAP UI5 views and controllers, plain JS widgets, approuter | frontend-developer, code-reviewer, qa-engineer, performance-engineer, ux-designer (ui-review) |
| `react-ts.md` | React 19 with TypeScript and Vite | frontend-developer, base-builder, code-reviewer, qa-engineer, performance-engineer, ux-designer (ui-review) |
