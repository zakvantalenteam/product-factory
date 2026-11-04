# API test checklist (MUST)

Read by `qa-engineer` for every new or changed endpoint (task mode `test`, product mode `run`) and by `qa-lead` for
the plan and the sign-off. A FAIL fails Test and goes back to Build with the item id, the request, the expected and the
actual response. Each changed endpoint gets every item a result: PASS, FAIL, N/A (with the reason) or BLOCKED (what is
needed). Run as automated API tests in the project's test folder where the repo has an API test harness; otherwise as
recorded calls against the running app (the developer's app, never one you start), with the requests in the report.

- **AQ1 Contract** The response matches the design or `05-openapi.yaml`: every field, its type and nullability, the
  status codes (200, 201, 204, 400, 401, 403, 404, 409) and the error body shape. An extra or renamed field is a FAIL
  unless the design says so; existing callers in the impact map still get what they read.
- **AQ2 Paging bounds** A list endpoint: the first page, the last page, a page past the end (empty list with the total,
  not an error), size 0 and a negative page (400 or the default), and a size above the maximum (capped on the server,
  RE7). The total is right and stable across pages; the order key is stable (no row on two pages, none skipped).
- **AQ3 Filters and sort** Each filter alone, two together, one that matches nothing, special characters (`%`, `_`,
  `'`, Unicode), a blank value, and every sort field both ways; a filter change with a page number returns page 1's
  rows when the client sends page 1.
- **AQ4 Access** Each role in the access matrix, allowed and denied: no login 401, a role without the right 403,
  another tenant's or another user's record 404 (or 403 as the design says), a manager outside the team denied, and a
  user id or tenant in the request ignored as authority (RE1-RE4).
- **AQ5 Input** Missing required field, too long, wrong type, out of range: 400 with a readable message and nothing
  saved; a stale version 409 where the design uses versions; a repeated create does not make a duplicate.
- **AQ6 Big data** The largest realistic volume for this endpoint (the plan's number, or 10 000 rows when the list
  grows with use): the response stays paged, the payload size is bounded, and there is no query per row (the log or
  the query count).
- **AQ7 Speed budget** The median of 3 calls is under the budget in the spec, else 2 s for a server call (a list at the
  big-data volume included), measured on the running app and reported with the numbers.
