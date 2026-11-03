# Common rules for every core agent

Every core agent reads this file once, at its start. Your own agent file adds your certification, your expert
standard, your call budget and your modes. The hard rules in `AGENTS.md`, confirmed answers and approved decisions
win over this file and over your own habits; when one conflicts with your standard, follow it and say so.

## Start (no extra round trip)
- First message, in parallel: this file, `<work>/<id>/context.md` when the task has one (or the pack your file
  names), and, when you design, write or review code, a Grep of `.claude/project.json` for `"stack"` (8 lines after).
- Next message, next to your first code reads: the stack packs `stack.packs` names that match the files you touch
  (`.claude/core/reference/stacks/<pack>.md`), and the lines of `.claude/review/lessons.md` for your area
  (mistakes this repo has already made).

## Output file (the live page reads it)
The output file you write first starts, under its title, with `## Summary for people` (3-5 plain lines: what you
looked at, what you found or changed, the verdict or decision, what is left; no code, paths or ids), then `## Plan`:
4-8 plain-words items as `- [ ]`. Tick an item `- [x]` when it is finished, only in a write you make anyway (no
extra calls). An HTML file holds both in a `<!-- Summary for people` comment at the top, with a `Plan` line before
the items. Keep them true as you work: the live page shows the plan live and the summary when you finish.

## Context
Read `<work>/<id>/context.md` first when the task has one, and do not explore beyond it. If you need something it
lacks, find only that and add it under its `## Gaps` as `### <gap> (by <your name>)` with `path:line`, so the next
agent has it.

## Speed
- The call budget in your Speed line is a ceiling, not a target: stop as soon as your output meets the bar.
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

## Stack packs (`.claude/core/reference/stacks/`)
| Pack | For | Read by |
|---|---|---|
| `java17-spring-boot3.md` | Java 17, Spring Boot 3, JPA with EclipseLink, SAP HANA or PostgreSQL | backend-developer, base-builder, code-reviewer, performance-engineer, qa-engineer, integration-engineer, solution-architect (design), data-architect |
| `ui5-plainjs.md` | SAP UI5 views and controllers, plain JS widgets, approuter | frontend-developer, code-reviewer, performance-engineer, ux-designer (ui-review) |
| `react-ts.md` | React 19 with TypeScript and Vite | frontend-developer, base-builder, code-reviewer, performance-engineer, ux-designer (ui-review) |
