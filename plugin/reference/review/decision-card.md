# Decision card (fixed layout)

Every decision D2-D8 gets one card. Copy this layout exactly: same eight sections, same order, in `<work>/<id>/decisions/D<n>-<slug>.md` (for example `D2-data-model.md`, `D3-api.md`, `D4-access.md`, `D6-dependencies.md`, `D8-go-live.md`). A D2 card also starts with section 0, "Data model explained" (below). D1 Scope is `brief.md`, written by `spec-analyst`. The cards of one stage are reviewed together in one gate.

Rules for the writer:
- Plain English, as in `${CLAUDE_PLUGIN_ROOT}/reference/review/plain-english.md`. A term the module's newcomers may not know gets a one-line explanation the first time it appears, or a line under `### Words used here`.
- A developer new to the module must be able to decide from the card alone. No "see design.md" for facts the decision depends on.
- Link every change to a spec criterion (`AC3`), and to the confirmed answer it follows (`Q2`), and every code claim to `path:line`.
- Never put secret values in a card: config keys by name only.
- Sections 7 and 8 stay empty when you write the card.
- Run `python ${CLAUDE_PLUGIN_ROOT}/scripts/handoff_check.py <id> decisions/<card>.md` and fix every PROBLEM line before you finish.

## Template

```
# D<n> <name> - <task id>

## 1. Decision needed
<One sentence: what the developer decides.>
Approve with: `approve D<n>`. To change it: `change D<n>: <what>`. To ask: just ask; the gate stays open.

## 2. What changes (before -> after)
| Item | Before | After | Notes |
|---|---|---|---|
<one row per column / endpoint field / permission / key / dependency>

## 3. Why
| Change (row) | Spec criterion | Reason |
|---|---|---|

## 4. Options considered
1. **Recommended: <option>** - why it wins.
2. <option> - why not.
3. <option, optional> - why not.

## 5. Impact
Existing data | Users | Other teams or callers | Performance | Restart needed (yes/no, why)

### Query speed
<D2 cards only, always present. Per new or changed read: the columns it looks up, filters or sorts by, and whether an index serves them. Any loop that runs one query per row, and how it is avoided. Expected rows per table after one year (per user and in total).>

## 6. Risks and rollback
Risk -> how it shows up -> how we undo it (steps, not "revert").

## 7. Questions and answers
<Empty while the card is drafted. The main session appends "Q (date): ... / A: ... (path:line)" while the gate is open.>

## 8. Decision
<Empty until approved. Then: approved | changed, by whom, when, and the change text.>
```

## Worked example row (D2, a column added; made-up column)

| Table | Column | Code type -> database type | Length | Nullable | Default | Index | Relation | Before -> after |
|---|---|---|---|---|---|---|---|---|
| `APP_ITEM` | `DISMISS_REASON` (`dismissReason`) | `String` -> `VARCHAR` | 40 | yes | none (null = no reason given) | no | none | column absent -> nullable column; existing rows keep null, so nothing changes for them |

Below the table a D2 card also says: what happens to existing rows (kept as they are), the migration or data fix needed ("none, new nullable column"), deploy order (deploy the build, the app restarts, schema validation adds the column), rollback (older build ignores the column; drop it later through a migration, never by hand), and a size estimate when the table is large.

## D2 only: section 0, before section 1

The developer must understand how the tables connect before approving. Section 0 is plain English with no code or database types; the technical rows stay in section 2.

````
## 0. Data model explained (read this first)

### In one sentence
<What we store, for whom, and what does not change.>

### Picture (before -> after)
```text
BEFORE
  [User] 1 ----< many [Item]
AFTER
  [User] 1 ----< many [Item]
      1                      1
      +----< many [Saved item] >----+      NEW
```
`1 ----< many` means: one row on the left, many rows on the right. Use the business name in brackets
([User], [Item]); mark new tables and links NEW, removed ones GONE. Show every table the
change touches and the existing tables it points to.

### How the tables relate
- One sentence per link, both directions: "One user can save many items. Each saved row belongs to exactly one user."
- Required or optional: "every saved row must have a card; a card may have no saved rows".
- Whether the link is a real database rule (foreign key) or only a stored id that the code keeps right.

### Example rows
| <columns in plain words> |
|---|
<2-3 made-up rows per new or changed table, with names next to ids: "Priya (user 4711)">

### What happens when...
- a row is created; the parent row is deleted or archived (deleted too, kept, or blocked); a user leaves;
  the daily job runs; we deploy and existing rows meet the new column; we roll back.

### Why this shape
<The recommended shape against the main alternative, in two or three sentences.>

### Words used here
- <term>: <plain explanation>
````

## Per decision: what section 2 lists

| Card | Section 2 rows |
|---|---|
| D1 Scope | no card: `brief.md` / `02-gaps.md` (what was understood, gaps with recommended answers, assumptions, not doing) |
| D2 Data model | section 0 explained in plain English (above); then per table, one row per new, changed or removed column; section 5 always has `### Query speed` |
| D3 API and contracts | request and response fields before -> after with an example; every caller affected |
| D4 Access and privacy | role x action matrix; who can now see what; manager scope |
| D6 Dependencies and config | dependency or key, why, licence, default value, restart needed |
| D7 Other owners | no card: `dev-handoff` writes one handoff per owner |
| D8 Go-live | restart, migrations and data fixes, labels pass, other owners' deploy order, rollback |
