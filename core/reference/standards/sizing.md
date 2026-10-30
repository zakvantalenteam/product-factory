# Story sizing

## What a story is
A thin vertical slice a user can see or use, written as "As a <role>, I want <action>, so that <value>",
meeting INVEST (Independent, Negotiable, Valuable, Estimable, Small, Testable), with 3-7 acceptance criteria
in Given/When/Then. Technical enablers (base setup, a shared component, a migration) are allowed but named
"Enabler" and kept few.

## Splitting (before sizing)
Split by workflow step, by business rule, by data variation, by role, by happy path vs edge cases,
by CRUD operation, or "simple first, rich later". Never split by layer (a "backend story" and a "frontend
story" are tasks, not stories).

## Points
Relative size, not hours: Fibonacci 1, 2, 3, 5, 8, 13. Three things decide the number:
- Complexity: rules, states, integrations, data volume.
- Uncertainty: unknowns, new technology, open questions.
- Effort: amount of work across FE, BE, DB, tests.
Reference stories anchor the scale (agreed once per product, kept in `04-stories.md`):
- 1 = change a label or add a field to an existing form with its column.
- 3 = a list page with paging, filter and a read endpoint on an existing table.
- 5 = create/edit form with validation, new table, audit, endpoint pair.
- 8 = a workflow with states and permissions, or one external integration call.
- 13 = too big: must be split before planning.
Anything 13 is split. Anything 8 is checked for a split.

## Every story carries
Id (`ST-<epic>-<n>`), epic, title, story text, acceptance criteria, points, confidence (High/Medium/Low
with the reason), dependencies, tasks (FE / BE / DB / QA, each one line, with the OpenAPI operation id),
open questions, MVP / later.

## Turning points into a plan
Velocity is unknown at the start: propose a first-sprint guess (for example 20-25 points for 2 developers
over 2 weeks), say it is a guess, and recalibrate after each sprint from actual done points. Output the MVP
slice (smallest set of stories that delivers the product's main value), then releases after it.
