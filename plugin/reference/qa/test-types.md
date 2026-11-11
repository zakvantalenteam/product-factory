# Test types (qa-lead's plan)

Every test plan has a `## Test types` section with one line per type below: the matrix rows of that type, or
`n/a: <reason>` when the change or the project has none of it ("no screen changed", "the project has no AI
answers", "no data change"). A type is never left out silently. The slug in brackets is the stage tag of a lesson
(`[test <slug>]` in `.claude/review/lessons.md`) and of a `/fix` escape line.

Where the project keeps its facts: the QA facts file (`qa.facts` in `.claude/project.json`) names the eval set,
the languages, the browsers and devices, and how to get a copy of existing rows. The core names no product: a type
whose facts are missing is planned from the change itself, and the gap is a line under `## Consults` for the
developer.

| Type (slug) | When it applies | Owner | A row checks |
|---|---|---|---|
| Unit (`unit`) | logic, rules, calculations | `qa-engineer` | the rule per criterion, boundaries, decision tables |
| API (`api`) | a new or changed endpoint, tool or message | `qa-engineer` | AQ1-AQ10 of `api-checklist.md` |
| UI (`ui`) | a template, script, style, view or label a user sees | `ui-qa-expert` | the UI MUST checklist on each changed screen |
| E2E journey (`e2e`) | a step across screens, roles or features, a notification, a status flow | `e2e-qa-expert` | the journey per role, cross-feature effects, two users at once |
| Exploratory (`exploratory`) | an unknown or high-risk area | `e2e-qa-expert` or `ui-qa-expert` | a charter: explore <area> with <role, data> to discover <risk> |
| Accessibility (`accessibility`) | any screen change | `ui-qa-expert` | keyboard path, focus, labels, contrast, 200% zoom |
| Speed (`speed`) | a list that grows, a heavy query, an AI answer with a budget | `qa-engineer` (budget from `performance-engineer` when on the team) | the budget at the real volume |
| Security (`security`) | roles, permissions, personal data, outside input | `qa-engineer` | access per role (allowed and denied), another tenant, injection and odd input |
| AI answer quality (`ai-quality`) | a change to an AI answer, prompt, model, retrieval, tool or guardrail | `qa-engineer`; `ai-engineer` reviews the rows and the result when an AI change is in scope | the project's eval set (where the QA facts say) run before and after with the judge it names, a score per case and the pass bar; the guardrail and abuse cases (prompt injection, off-topic, personal data, another language); new cases added where the facts say |
| Languages and long labels (`languages`) | a new or changed label, message, date, number or sort | `ui-qa-expert` | the second language row, the longest language the facts name, missing keys shown as keys, dates and numbers per locale |
| Data upgrade and migration (`data-upgrade`) | a table, column, default, enum, status or stored format that changes | `qa-engineer` | the migration on a copy of existing rows (null and old values, the largest table size the facts name), the old screens and reports reading the new rows, the rollback step |
| Browsers and devices (`browsers`) | a screen change | `ui-qa-expert` | the browsers and devices the facts list (default: the latest Chrome, Edge, Firefox and Safari, one phone at 360-375 px) |
| Smoke (`smoke`) | every run | per item | the `.claude/smoke.md` items of the areas the change touches |

- Each row still has a role, a data volume and a priority in the matrix; a high risk gets several types.
- `ai-quality` with no eval set in the facts: the first row is "build the starting eval set" (10-20 cases from the
  criteria, including 3 abuse cases) for the developer to approve, and the type is BLOCKED until it exists.
