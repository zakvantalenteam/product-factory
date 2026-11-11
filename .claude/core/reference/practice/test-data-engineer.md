# Practice pack: test-data-engineer

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a
holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## Safety rules (the same as in your agent file; they win over any brief)
- Only the hosts in `qa.data.hosts`; never production, never a customer tenant. A URL that is not listed: stop.
- Writes only through the app (REST API, import, an admin action exposed as an API); never a database write.
- Lookups only with the project's read-only query command (`qa.data.query`): one SELECT, counts and ids only.
- Synthetic data only ("QA Learner 01", `@example.test` emails); never data copied from a real person.
- Test sign-ins only; tokens and passwords come from the environment and are never written or printed.
- A batch over 100 records needs the developer's yes in chat (you stop and report; the lead asks).
- Every create is prefixed (`QA-<ticket>-`, or `QA-DATA-` for the lasting dataset) and logged in
  `.claude/qa/create-log.jsonl` at once; cleanup removes only what the log lists.
- Nothing is created before the data map says `Approved: <name>, <date>`.

## CTAL-TTA: test data as a technical test asset
- Derive data from the test conditions, not the other way round: every record traces to a matrix row, a smoke
  journey, a recipe line or a volume.
- Equivalence classes and boundaries live in the data: the page size p gives 0, 1, p, p+1 and 3p+1 rows; a limit L gives
  L-1, L and L+1 (the L+1 create should fail, which is also a test).
- State coverage: one record per state of each status flow (draft, published, archived, deleted, expired) and per
  type in the facts' type list; a new type gets its own records.
- Relationships: a parent with no children, one child and many; a manager with two levels of reports; orphans only when
  the app can produce them.
- Data that breaks layouts: the longest allowed text, a 60-character word, quotes, colon, ampersand, emoji, leading
  and trailing spaces, right-to-left text when the product supports it, and both languages the facts name.
- Time: the far time zones (UTC+13, UTC-10), a date on a month and a year boundary, durations of null, under a minute
  and over five hours.
- Repeatable setup: a seed script is idempotent (it checks what exists by prefix before it creates) and has a dry run
  that prints what it would create.
- Keep a lasting dataset (`QA-DATA-`) for what every ticket needs, and top up per ticket (`QA-<ticket>-`) only for
  what is new; cleanup is on request, never by itself.

## CIPT: privacy in test data
- Data minimisation: only the fields the test needs; optional personal fields stay empty or synthetic.
- No production data on dev, not even "anonymised" copies: masked data still re-identifies people. Synthetic only.
- Files, logs and replies hold counts and ids, never names, emails or free text read from real records.
- Test identities are obviously fake (`example.test` domain, "QA" in the name), so nobody mistakes them for people.
- A need that only real data can meet (history from another system) is met by finding a test user who already has
  it, by count, never by copying it.

## Seed script layout (`.claude/qa/seed/`)
- One Python script per need or group, standard library only (`urllib.request`, `json`, `csv`, `argparse`), run
  with `python .claude/qa/seed/<name>.py [--apply] [--ticket <id>] [--count N] [--host <url>]`.
- On start it reads `.claude/project.json` `qa.data.hosts` and refuses a host that is not listed; the token comes
  from an environment variable the script names (never a file in the repo).
- Without `--apply` it prints what it would create and creates nothing. With `--apply` it refuses `--count` over
  100 unless `--yes-over-100` is given (the lead passes it only after the developer's yes).
- It looks up existing records by prefix first and creates only the missing ones.
- After each create it appends one JSON line to `.claude/qa/create-log.jsonl`: `{"date", "ticket", "need", "host",
  "entity", "id", "name"}`.
- `cleanup.py [--apply] [--ticket <id> | --all] [--keep-lasting]` deletes through the app only the log's records,
  newest first, and marks each line `"removed": "<date>"`.

## Finding data (read-only)
- Count first, then ids: `SELECT COUNT(*) ...`, then `SELECT <id column> ... LIMIT 5`; never select name or email
  columns.
- Pick the find query from the entity's own key and tenant column, so the result is for the dev tenant the testers
  use.
- (SAP) Blend and TalentBox read HANA only with `python .claude/scripts/hana_query.py "SELECT ..."` (one SELECT);
  SuccessFactors data (learning history, org structure) is found on the dev tenant or asked of the developer.

## What goes on the ask list
- Anything only another system or a person can make: SuccessFactors-side setup, an identity-provider user (a far
  time zone, a disabled user), a licence or tenant setting, a screen-only action with no API.
- Each ask says what, where, why (which rows it unblocks) and a recommended way; the rows it blocks stay BLOCKED.
