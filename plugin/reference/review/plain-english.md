# Plain English for the people who decide

Everything a developer or product owner reads at a gate follows this page: `brief.md` / `02-gaps.md`,
`01-prd-review.md`, `03-product-review.md`, the "How it will work" part of a design, and every decision card
(`decisions/D*.md`). The reader is new to this module and must decide in five minutes from this document
alone. `handoff_check.py` blocks a gate when a required part is missing and gives hints for the points below.

## Rules
1. Start with the point: what is decided or what changes, in one sentence. For the product owner the first
   thing on the page is the count and the list of blockers.
2. Short sentences: about 15-20 words, never over 30. One idea per sentence.
3. Say who does what: "The daily job deletes old rows", not "old rows are deleted".
4. Explain each technical word the first time, in brackets, or under `## Words used here`. The table below has
   ready-made explanations; a project adds its own words in `.claude/project.json` `glossary`.
5. Show an example with real-looking, made-up data: a person ("Asha, a manager in Pune"), a record, a number.
6. Say what changes for people: users, managers, admins, other developers. Before and after.
7. Numbers, not adjectives: "up to 50 rows per user", not "a few rows".
8. Keep the human part free of file paths, class names, annotations and table names. They belong in the spec,
   in the technical sections of a card (2-6) and in the design's "Changes".
9. Lists for steps and options; tables only to compare or to list columns.
10. Never "see design.md" or "as discussed": copy the fact the decision depends on.
11. Recommend: every question comes with your recommended answer and what happens if they take it.

## Product-owner documents
- One item = one line of problem + one line "Recommended:" + one line "If not decided:" (the consequence).
- Mark impact with a word at the start of the line: **BLOCKER** (cannot build without it), **HIGH** (builds the
  wrong thing), **MEDIUM** (rework later), **LOW** (polish).
- Quote the requirement document by section and a few words, so the owner can find it.
- No more than 12 items per document; group the rest as "Smaller points" in one list.
- End with "What happens next" in two lines.
- Every product-owner document also gets an offline HTML copy:
  `python ${CLAUDE_PLUGIN_ROOT}/scripts/md_to_html.py <file.md>`.

## Words used here (reuse these explanations)
| Word | Plain explanation |
|---|---|
| table, row, column | a table is a list of records; each row is one record; each column is one field of it |
| primary key | the column that names each row uniquely, usually a number the database gives |
| foreign key | a column that points at a row in another table; a database rule can stop it pointing at nothing |
| relation "1 to many" | one row on one side has many rows on the other, e.g. one user has many saved items |
| nullable | the column may be left empty |
| index | a lookup list the database keeps so it finds rows fast; it costs a little on every write |
| unique constraint | a database rule that stops two rows having the same value |
| cascade | deleting (or saving) a row also deletes (or saves) the rows that hang off it |
| orphan row | a row that points at a row that no longer exists |
| entity | the class in the code that stands for one table |
| migration | a change to the shape of the database, or the script that makes it |
| backfill | filling a new column for rows that already exist |
| schema validation | a startup check that the database tables match the code; a mismatch stops the deployment |
| endpoint | an address the browser or another system calls, e.g. `/api/items` |
| payload | the data sent in a call or returned by it |
| tenant | one customer company using the product |
| idempotent | running it twice has the same effect as once |
| DTO | a plain object that carries data between layers |
| role, permission | a role is a group of users; a permission says what that group may do |

## Before and after
Before: "Adds `APP_SAVED_ITEM` with FK to `APP_ITEM`, nullable=false, unique(USER_ID, ITEM_ID), no cascade."

After: "We add one table for the items a user saved. Each saved row points to one item and one user. A user can
save an item only once. Deleting an item does not delete the saved row; the page shows 'No longer available'
instead."
