# Code review checklist (core)

The `code-reviewer` agent applies this list to every code change. It adds to the hard rules in `AGENTS.md` and
the `.claude/rules/*.md` file for each changed path; it does not repeat them, so check those first. A project
adds its own path-triggered sections (its framework, widgets, workflows, descriptors) in
`.claude/review/checklist.md`; those use their own ids and are read the same way. Examples in brackets are
examples, not requirements.

## Which focus reads which section

A focused pass (`code-reviewer` with focus `rules`, `bugs` or `security`) reads only its items in the sections
whose path trigger matches a changed file. Focus `all` reads every section in the review pack. Every section and
item stays in force; each item belongs to one focus. A section's path trigger is its `Paths:` line (a project
section: the backticked globs after " - " in its heading); a backticked `@Marker` matches the changed text.

| Section | rules | bugs | security |
|---|---|---|---|
| Always | AL8, AL9, AL10 | AL3, AL5, AL6, AL7 | AL1, AL2, AL4 |
| Backend | BE8, BE9, BE11, BE12 | BE1, BE2, BE3, BE7, BE10, BE13, BE14 | BE4, BE5, BE6 |
| REST and API | RE12 | RE6, RE7, RE13 | RE1-RE5, RE8-RE11 |
| Data access | DA14, DA16, DA18 | DA3-DA9, DA11-DA13, DA15, DA17, DA19 | DA1, DA2, DA10, DA20 |
| Jobs and schedulers | JB8 | JB1-JB7, JB9 | - |
| Integrations | - | IN2, IN3, IN4, IN7, IN9, IN10, IN11 | IN1, IN5, IN6, IN8 |
| LLM calls | LL14, LL15, LL16 | LL3, LL4, LL5, LL7, LL10, LL11, LL13, LL17 | LL1, LL2, LL6, LL8, LL9, LL12 |
| Frontend pages | PG7, PG11, PG13, PG14, PG17, PG19, PG20 | PG4, PG5, PG6, PG12, PG15, PG16, PG18, PG21, PG22 | PG1, PG2, PG3, PG8, PG9, PG10 |
| Labels and i18n | LB1-LB7 | - | - |
| Config and dependencies | CF4, CF5, CF7, CF8 | CF2, CF6, CF9, CF10 | CF1, CF3 |
| Live checks for Verify | the lines for your items | the lines for your items | the lines for your items |

The extra passes also read:
- `ux-designer (ui)`: PG5, PG7, PG10, PG11, PG13, PG19, LB1-LB3.
- `performance-engineer (speed)`: AL6, BE3, BE4, BE10, RE7, DA3, DA4, DA12, DA13, DA15, IN9, LL13, LL17, JB4, JB5, PG16.
- `sf-expert (sf)`: AL4, AL6, BE3, BE12, RE10, IN1-IN10, JB1-JB7 where SuccessFactors is called.
- `sf-skills-expert (sf-skills)`: the same ids where job profiles, roles, competencies or skills are read or written.
- `ai-engineer (ai)`: AL4, AL6, RE9, LL1-LL17, JB6.
- `n8n-expert (n8n)`: LL1-LL17 where a node calls a model, IN1-IN10 where a workflow calls out, plus the repo's own
  n8n ids named in `.claude/experts/n8n.md`.

## How to use

1. Read the review pack (`python ${CLAUDE_PLUGIN_ROOT}/scripts/review_pack.py <id>` writes `<work>/<id>/review-pack.md`): it
   holds "Always" plus every section whose path trigger matches a changed file, core and project. Without a pack:
   `git diff --stat`, then read those sections only.
2. Every item is MUST or SHOULD. One failed MUST makes the verdict FAIL and sends the change back. SHOULD items
   go in the SHOULD list and do not block.
3. Proof rule: each finding cites `path:line`, quotes the exact line, and gives a failure scenario (input or
   state, then the wrong result). No proof, no MUST: downgrade it to SHOULD or drop it.
4. Judge only what the diff and the code around it show. If the answer needs the running app, raise no finding:
   copy the matching line from "Live checks for Verify" into the review file.
5. Cite the item id (for example `RE3`) in each finding.
6. If a guard or test the item asks for already exists elsewhere, name it with `path:line` and pass the item.
7. Product mode: each MUST also names the Definition-of-Done item (M1-M16) it breaks; see the map at the end.

## Severity mapping

| Severity | Grade | Note |
|---|---|---|
| CRITICAL (security hole, data loss, cross-user leak, secret committed) | MUST | FAIL |
| HIGH (production incident, broken contract, expensive rework) | MUST | FAIL |
| MEDIUM (real defect or design debt) | SHOULD | MUST when it breaks an acceptance criterion, a hard rule, privacy, or fails at runtime or deploy |
| LOW (naming, dead code, small inconsistency) | SHOULD | Only when it helps this change; skip style nits |
| NEEDS-VERIFICATION (unprovable from the diff) | none | Not a finding: list it under Live checks for Verify or as a question for the developer |

## Always - every change

Also apply the hard rules in `AGENTS.md`.

- **AL1 MUST** The diff adds no secret, token, key, password, connection string or real personal data in any file: code, config, exports, fixtures, test data, docs.
- **AL2 MUST** User and tenant identity come from the authenticated session or token, never from a request parameter, body, header, client field or model output the caller controls.
- **AL3 MUST** No empty `catch`, no `catch` that turns a failed read into an empty or "no data" result, no debug print or stack-trace print in new code.
- **AL4 MUST** Logs and console output at INFO and above never print prompts, answers, tokens, keys, e-mail, other people's ids or full request bodies.
- **AL5 MUST** A changed contract keeps today's callers working: endpoint request or response, event or tool schema, message payload, response envelope. A removed, renamed or narrowed field is fixed in every caller in the same change.
- **AL6 MUST** Every new outbound call (HTTP, workflow, model, tool, file transfer) has a connect and a read timeout, a bounded retry and a failure result the user can read: no endless spinner.
- **AL7 MUST** The change works with more than one app instance: no new local file write, static map or in-process counter that another instance must see (turn state, locks, quota, dedupe).
- **AL8 SHOULD** New branch logic, a new query or a bug fix has a test run that covers it: an updated existing test, or a scratch test noted in `status.md`. A committed test file is required only when the project says so.
- **AL9 SHOULD** No IDE, OS or build artefacts, debug leftovers, commented-out code, unused imports or types, or changed line endings in the diff.
- **AL10 SHOULD** A new helper does not copy an existing one (escape, date format, URL check, row mapper): reuse the shared one.

## Backend - server code (for example `src/main/**`, `server/**`)

Paths: `**/*.java`, `**/*.kt`, `**/*.scala`, `**/*.go`, `**/*.cs`, `**/*.rb`, `**/*.php`, `**/*.py`, `server/**`, `backend/**`, `api/**`

Also apply the `.claude/rules/*.md` file for backend paths when it exists.

- **BE1 MUST** A value from outside (a remote response, a JSON config row, a nullable column, an optional) is null-checked or defaulted before use; an optional is unwrapped only after a check.
- **BE2 MUST** A declarative transaction, async or cache boundary (for example Spring `@Transactional`, `@Async`, `@Cacheable`) sits on a public service method called from another component: not on a controller, not self-invoked, so the proxy applies.
- **BE3 MUST** No remote call (HTTP, workflow, model), file I/O or e-mail while a transaction is open or a connection is held. Scenario: a slow remote holds a pooled connection and the pool runs dry.
- **BE4 MUST** A cache or memoised value is keyed by everything that scopes the data (user, role, language, tenant). A key without the user can serve one person's answer to another.
- **BE5 MUST** A thread-local or static holder of user or tenant context is cleared in `finally`; code on async, executor or scheduler threads does not read the request or session context.
- **BE6 MUST** A key or secret is compared in constant time, never logged, and never returned in full to the browser or in an error body.
- **BE7 MUST** "Today", "this week", "overdue", "upcoming" and due dates use the user's time zone explicitly; no zone-less "now" in user-facing logic.
- **BE8 SHOULD** New classes use constructor injection; no new field injection; no reliance on circular references or bean overriding.
- **BE9 SHOULD** A controller stays thin and does not call a repository; rules live in the service. A module does not import another module's internals.
- **BE10 SHOULD** A new cache has a size bound and a time limit.
- **BE11 SHOULD** An exception message carries the operation and id; the error is logged once at the boundary, with the request id, not at every layer.
- **BE12 SHOULD** Vendor payload shapes (a SaaS API, a message queue, JSON from a workflow) are mapped to own types at the edge and do not leak into controller responses.
- **BE13 SHOULD** Counts, percentages, money and quota math do not use floating point where exactness matters; integer division and rounding are checked.
- **BE14 MUST** A date or time is compared and filtered as an instant (UTC, the event's end for 'upcoming'), never as a local date or a formatted string. Scenario: an event that ends tonight in the user's zone is dropped from "upcoming" because the server date has already moved on.

## REST and API - controllers, resources, route handlers

Paths: `*Controller*`, `*Resource.*`, `*Endpoint*`, `*Handler.*`, `*Router*`, `**/routes/**`, `**/api/**`, `**/controllers/**`, `@RestController`, `@RequestMapping`

- **RE1 MUST** A new or changed endpoint has a guard that fits its caller: login session, permission annotation, or a machine key for callbacks. Name the guard in the review. With no guard it is public: it must be public on purpose and return non-sensitive data only.
- **RE2 MUST** Admin-only endpoints (configuration, policies, monitoring, debug, integration settings) check the admin role on the server. Hiding the button is not the check.
- **RE3 MUST** Callback, webhook and machine-to-machine endpoints fail closed with 401 or 403 on a missing or wrong key.
- **RE4 MUST** The acting user is the session user. A `userId`, person id or e-mail in the path, query or body is ignored or rejected, unless the endpoint is a manager or delegate endpoint that checks the relationship. Scenario: a user changes the id and reads another person's plan.
- **RE5 MUST** A request body binds to a DTO or named fields, not to a persistence entity or a free map copied into one (mass assignment).
- **RE6 MUST** Input is validated (required, type, range, enum, length) and a bad value returns 400 with a plain message. No 500 for an expected condition; no stack trace, SQL, class name or key in a response.
- **RE7 MUST** A list endpoint enforces a maximum page size on the server; a caller cannot ask for all rows.
- **RE8 MUST** A write endpoint (assign, enrol, submit, approve, accept) re-checks permission on the server, starts from an explicit user action, and is idempotent: a replay or double click creates no duplicate.
- **RE9 MUST** A new endpoint that starts a switchable or costly feature (an AI call, an export, a bulk job) honours the feature switch, usage policy and quota gates its siblings apply, on the server. A refusal names the scope that refused.
- **RE10 MUST** A response carries only fields the caller's role may see: no e-mail, phone, internal ids, other people's ids, tokens or raw model output.
- **RE11 MUST** A new upload path checks content type, size and file name (path traversal).
- **RE12 SHOULD** Errors follow the module's shape (or the API standard's problem-details shape) with the right status (400, 403, 404, 409), not 200 with an error text.
- **RE13 SHOULD** Long work (import, sync, scan) does not run on the request thread; the endpoint starts it and reports status.

## Data access - repositories, DAOs, query classes, entities, migrations

Paths: `*Repository*`, `*Dao*`, `*Query*`, `*Entity*`, `**/entity/**`, `**/entities/**`, `**/models/**`, `**/migrations/**`, `**/db/**`, `*.sql`, `@Entity`, `@Query`

Also apply the hard rules in `AGENTS.md` about the database.

- **DA1 MUST** A new query or row on user- or tenant-scoped data filters or stamps the user and tenant like its sibling repository. Scenario: a lookup by turn id alone returns another user's turn.
- **DA2 MUST** No string-built SQL or query text with a user-, admin- or model-controlled part. Table, column and sort names come from a fixed set; values are bound.
- **DA3 MUST** Every new read is bounded: page or limit. No find-all, unpaginated list method or `SELECT *` over a table that grows (events, logs, history, cards, memory).
- **DA4 MUST** No N+1: no query per row or per id in a loop, no lazy association walked while mapping a list. Use a join fetch, a batch fetch or an IN-list.
- **DA5 MUST** A check-then-act on a shared row (quota reserve and release, counters, fingerprints, acceptance records) is atomic: one conditional update, a version column or a unique constraint. Scenario: two parallel requests both pass the check and exceed the quota.
- **DA6 MUST** Writes that must succeed together run in one service-level transaction. A failure at step N leaves no half state, and a hold or reservation is released on every failure path.
- **DA7 MUST** An entity or schema change is safe for an upgraded database: a new column is nullable or backfilled by the project's upgrade mechanism; no rename, drop or type narrowing of an existing column or table in one step (expand, then contract).
- **DA8 MUST** A uniqueness the code relies on (one acceptance per user and version, one card per fingerprint and user) is a database constraint and includes the scope columns. Otherwise two threads create duplicates.
- **DA9 MUST** A text column that stores model or user text (answer, remark, prompt, snapshot) has a length or large-object type that fits. Scenario: a 5,000-character answer on a shorter column fails the insert.
- **DA10 MUST** A new table or column holding personal data or captured model content is covered by the retention job and leaver erasure, is not logged, and is not shown to a lower role.
- **DA11 MUST** Each manual connection, statement and result set is closed (try-with-resources or the language's equivalent).
- **DA12 SHOULD** Columns a new query filters or sorts on, in a growing table, have an index: name the index and its column order. MUST when the query runs per request on an unbounded table and the scenario is shown.
- **DA13 SHOULD** Predicates are sargable: no function around an indexed column, no leading-wildcard LIKE.
- **DA14 SHOULD** A read-only service method is marked read-only where the framework supports it.
- **DA15 SHOULD** A new eager association is justified or lazy; bulk writes are batched, not single statements in a loop.
- **DA16 SHOULD** A new mutable admin setting or policy records who changed it and when.
- **DA17 MUST** A committed migration script is never edited: the change is a new forward script with the next free number, re-runnable (guarded create and alter), backward compatible while the old build still runs, and with a rollback note. No locking rewrite of a large table: no in-place type change, no volatile default on a big table; data migrations are batched.
- **DA18 SHOULD** Every new foreign key has an index and an explicit delete policy; per-tenant uniqueness includes the tenant column; types fit (timestamps with zone, exact numerics, no dates or JSON in text columns); the entity mapping matches the script.
- **DA19 MUST** Search and filter input is trimmed, separators in multi-id fields are handled, and LIKE wildcards (`%`, `_`) and quotes are escaped or bound as parameters. Scenario: a search for `50%` or ` abc ` returns every row or none.
- **DA20 MUST** Every query that reads or changes a user-owned record is scoped to the caller (user, team or tenant) in the query itself, not filtered after the read. Scenario: a second user of the same role opens the first user's record by id.

## Jobs and schedulers - scheduled jobs, upgrade hooks, executors

Paths: `*Job.*`, `*Scheduler*`, `*Executor*`, `*Worker*`, `**/jobs/**`, `@Scheduled`, `@UpgradeJob`, `@Async`

- **JB1 MUST** Only one instance runs the job per schedule: a node-role condition or an atomic lock row. Scenario: two instances start at midnight and write every record twice.
- **JB2 MUST** The job is idempotent: a re-run or a retry after a crash creates no duplicate rows or cards (fingerprint, upsert, unique constraint).
- **JB3 MUST** Partial failure is defined: one record's failure is caught and logged with job name and id and does not abort the batch (or aborts on purpose), and the next run resumes or retries.
- **JB4 MUST** Work is batched: no whole-table or whole-user-list load into memory, and no transaction held across the whole run.
- **JB5 MUST** An executor or thread pool in the diff has a fixed size and a bounded queue; no thread per item and no unbounded cached pool.
- **JB6 MUST** When an outside system or the model provider is down, the job uses fallback text or skips with a logged reason: no tight retry loop, no empty or placeholder record. It respects the feature kill switch.
- **JB7 MUST** An upgrade or startup hook is safe on every startup (a second run changes nothing), makes no remote call, and fails soft when an outside system is unreachable.
- **JB8 SHOULD** The job logs start, end, counts and failures with its name, and no personal data in those lines.
- **JB9 MUST** A job keeps its own state per run: no shared field, static or cache that two jobs running at the same time (or Run Now beside the schedule) can overwrite; every run writes an end state, and a mail or notification job sends once per user and period.

## Integrations and imports - outside APIs, file transfer, storage, spreadsheet or document import and export

Paths: `*Client.*`, `*Connector*`, `*Integration*`, `*Import*`, `*Export*`, `*Sync*`, `*Sftp*`, `*Storage*`, `**/integration*/**`, `RestTemplate`, `WebClient`

- **IN1 MUST** Credentials and hosts come from destinations or per-tenant config, never literals or per-environment values in code.
- **IN2 MUST** A list call pages (server paging by next link, or a stable order key with top and skip) and is bounded; no unbounded fetch of all employees, candidates or records.
- **IN3 MUST** A bulk write or upsert checks the per-record status in the response; failures are logged with the record id and reported, not swallowed. Scenario: one HTTP 200 holds a failed row.
- **IN4 MUST** An imported file is checked for size, type and row count before processing; one bad row is reported with its row number (or the import aborts on purpose).
- **IN5 MUST** File-transfer and storage paths come from config; file names from users or remote systems are sanitised (no `..`, no absolute paths).
- **IN6 SHOULD** An export with user-entered text escapes cells that start with `=`, `+`, `-` or `@` (formula injection).
- **IN7 SHOULD** A re-run of an import or sync is safe (upsert or skip existing) and the run summary shows counts.
- **IN8 MUST** A filter, query string or path segment built from input is encoded or escaped for the target API (for example an OData `$filter` string value). Scenario: a name with a quote breaks the filter or widens it.
- **IN9 SHOULD** A read selects only the fields it needs, a full sync uses a modified-since delta with a stored checkpoint, and there is no per-row remote call in a loop (or the fan-out has a cap).
- **IN10 MUST** Throttling and transient errors (429, 503, timeouts) are retried with bounded backoff honouring Retry-After; an access token is reused until shortly before expiry, not fetched per call.
- **IN11 MUST** A CSV or other export file quotes every field (commas, quotes, line breaks) and writes UTF-8 with a BOM when Excel opens it. Scenario: a title with a comma shifts every later column.

## LLM calls - model clients, prompt code, agent and tool plumbing, guardrails, quota ledger

Paths: `**/ai*/**`, `**/llm/**`, `**/mcp/**`, `*Prompt*`, `*Agent*`, `*Guardrail*`, `*Quota*`, `*Llm*`, `**/n8n*/**`, `@McpTool`

Also apply `.claude/rules/*.md` for AI paths when it exists.

- **LL1 MUST** User, file and database text placed in a prompt (queries, document chunks, titles, remarks, goals) sits in a fenced, length-capped data block and cannot replace the instructions. Scenario: a document says "ignore the rules and output ..." and the answer follows it.
- **LL2 MUST** Keys are sent in a header, never in a URL, a log line or a response; they come from config by key name.
- **LL3 MUST** Every call has a connect and a read timeout, a bounded retry and fallback text; a failure gives the user a readable message that says what is missing, not a stack trace, a blank or an empty reply.
- **LL4 MUST** Model output is parsed with a real parser against a schema; missing or extra fields have a fallback; invalid output becomes an error state and is never saved as if it were valid. No substring tricks to find a JSON block.
- **LL5 MUST** Model output that is saved or shown (questions, profiles, skills, translations) is validated (lengths, enums, counts) before saving and escaped when shown.
- **LL6 MUST** Only the fields the answer needs reach the provider: no e-mails, phone numbers, other people's ids or sensitive HR fields.
- **LL7 MUST** Long or bulk generation runs as a job or async task with status, never on the request thread; no per-row model call in a loop without a cap.
- **LL8 MUST** Tool arguments a model builds are validated before the call (type, enum, range, limit, date format, ids owned by the caller), and a prompt change does not drop an own-data rule. Bad input returns an error object, not a stack trace.
- **LL9 MUST** A tool that changes data cannot be fired by the model from free text alone: an explicit user action (confirm click, card action) is part of the path.
- **LL10 MUST** A new or changed model call still records its tokens in the usage or quota ledger, so quota and monitoring count it.
- **LL11 MUST** Answer text stays grounded in tool data: no invented records, dates, people, links or numbers; an empty tool result is said so; counts, names and dates in the text equal those on the card.
- **LL12 MUST** No new route, branch or sub-flow skips the input and output guardrail checks.
- **LL13 MUST** A tool result has its own default and maximum size (rows and text length) so the payload fits the token budget. Scenario: a user with 4,000 records gets a huge result.
- **LL14 SHOULD** The change reuses the module's client; model, temperature and max tokens are deliberate and stated in the handoff.
- **LL15 SHOULD** A prompt change does not contradict or duplicate another prompt (own-data rule, language, output format) and the size change is stated.
- **LL16 SHOULD** A new route or intent has an eval case (intent by role); replies follow the user's language; the offline eval result is quoted.
- **LL17 SHOULD** Independent model or tool calls run in parallel, not in series; the first words of an answer are streamed.

## Frontend pages - templates, scripts, components, styles, admin screens

Paths: `*.html`, `*.js`, `*.jsx`, `*.ts`, `*.tsx`, `*.vue`, `*.svelte`, `*.css`, `*.scss`, `*.view.xml`, `**/static/**`, `**/templates/**`, `manifest.json`

Also apply the `.claude/rules/*.md` file for frontend paths when it exists.

- **PG1 MUST** Every dynamic HTML insertion that includes data (`innerHTML`, `insertAdjacentHTML`, `document.write`, `dangerouslySetInnerHTML`, an HTML template string) is escaped or sanitised with the page's helper. Scenario: a title `<img src=x onerror=...>` runs script.
- **PG2 MUST** A URL from data is checked (http or https only; no `javascript:`, no `data:`) before it goes into `href`, `src` or `window.open`; a new window uses `noopener`.
- **PG3 MUST** A server template uses its escaping output for data; raw output only for fixed trusted markup.
- **PG4 MUST** New or changed rendering reads every response field defensively (missing, null, wrong type, empty list) and shows a readable fallback.
- **PG5 MUST** Each new or changed screen part has loading, empty, error and no-permission states. A failed call shows a message with retry or close and clears the busy state on both paths; an empty list never stands for a failed read.
- **PG6 MUST** An action shows progress and outcome, disables its control while it runs (no double submit), and stays retryable after a failure.
- **PG7 MUST** Interactive elements are real buttons or links, or have role, tab index and a key handler; icon-only controls have an accessible name; dialogs trap focus, close on Escape and return focus; inputs have labels.
- **PG8 MUST** The page sends no user id or tenant as authority, and puts no personal data, answers, scores or tokens in URLs, local storage or console output.
- **PG9 MUST** A control that starts an admin action (save, delete, enable, run, test connection) calls an endpoint that checks the admin role on the server (RE2). Hiding or disabling the button is not protection.
- **PG10 MUST** A secret field uses a password input and is never filled with the stored value on load; a test-connection result never echoes a key or a raw error body.
- **PG11 SHOULD** Text keeps AA contrast on the tenant colour; the layout works at 200% zoom and a narrow phone width where the page is used on phones.
- **PG12 SHOULD** A new stream, timer or window listener is closed or removed when the view closes; a reconnect does not repeat streamed text.
- **PG13 SHOULD** Dates and numbers follow the page language (`Intl`), not a fixed locale; widths tolerate long German and Finnish labels.
- **PG14 SHOULD** No renderer or helper is copied across screens; reuse the shared one.
- **PG15 SHOULD** Fields are validated before save with the limits the server enforces (required, range, URL, length), and a server rejection is shown, not lost.
- **PG16 SHOULD** A big table is paged or capped on the server; rows do not each trigger a request.
- **PG17 SHOULD** A destructive action (delete, reset, disable, re-run) asks for confirmation.
- **PG18 MUST** A changed view, template or declarative markup file is well formed: a duplicate attribute or an unclosed tag can silently drop the rest of the view.
- **PG19 SHOULD** Colours, spacing and font sizes come from the theme tokens, no fixed hex; the focus ring shows for keyboard use only.
- **PG20 MUST** No business rule or authorisation lives only in the frontend; the backend enforces it (`${CLAUDE_PLUGIN_ROOT}/reference/standards/fe-be-split.md`).
- **PG21 MUST** When one renderer of a shared element (card, row, chip, status, date) is changed, its siblings are changed too or listed with the reason they stay (the context pack's parity list). Scenario: the list card shows the new field and the widget card of the same item does not.
- **PG22 SHOULD** A popup, dialog or panel resets its state on open (not only on close); an action removes its overlay in a finally path.

## Labels and i18n - label files, locale files, message bundles

Paths: `**/i18n/**`, `**/locales/**`, `**/lang/**`, `messages*.properties`, `i18n*.properties`, `*.po`

Also apply the project's labels rule (`AGENTS.md` or `.claude/rules/*.md`).

- **LB1 MUST** Every key the diff reads exists in the file that code reads from. A missing key shows the raw key.
- **LB2 MUST** Placeholders in a label match the arguments the code passes, and the quote style fits how that label group is read.
- **LB3 MUST** End-user text in templates, scripts and server responses (labels, errors, empty states, `aria-label`, toasts) comes from a key, not a literal.
- **LB4 SHOULD** Admin-facing text in views and controllers also comes from a key.
- **LB5 SHOULD** Locale-sensitive output (dates, numbers, plurals) is not built by joining label fragments.
- **LB6 SHOULD** Where the project keeps several locale files, a new key follows the project's translation rule (all files at once, or the release pass) and placeholders match the English value. MUST when a locale test fails.
- **LB7 SHOULD** Master data shown to the user (type, status, category, skill names) goes through the translation lookup and falls back to the stored value when a translation is missing.

## Config and dependencies - properties, constants, build files, deploy and security descriptors, pipeline

Paths: `*.properties`, `*.yml`, `*.yaml`, `*.toml`, `pom.xml`, `build.gradle*`, `package.json`, `requirements*.txt`, `Dockerfile`, `Jenkinsfile`, `.github/workflows/**`, `*Constants*`, `xs-security*.json`, `.env*`

Also apply the project's config and deploy rule when it exists.

- **CF1 MUST** A new secret-bearing property (key, token, password, client secret) has no real value or default in a committed file; it is read from the environment, a destination or the credential store.
- **CF2 MUST** A new property or flag has a safe default and the app still starts under every profile the project runs. A missing required value fails with a clear startup message, not a null error on the first request.
- **CF3 MUST** A change to CORS, CSRF, gateway routes or security matchers adds no wildcard origin with credentials, no route with authentication turned off and no weaker XSS rule without a stated reason; streaming and write endpoints stay covered.
- **CF4 MUST** No per-environment value (host, tenant id, destination name, URL) is hard-coded in a committed default or a constants file.
- **CF5 SHOULD** A new feature switch is read at request time and defaults to a safe state, so it turns off without a restart.
- **CF6 SHOULD** A reader of a config document uses a cache whose staleness fits the setting; an enforcement setting (guardrails, quota, kill switch) is effective right after an admin saves it.
- **CF7 SHOULD** A new role, scope or destination is added everywhere it is declared (deploy descriptor, security descriptor, role grants through the upgrade mechanism) in the same change.
- **CF8 SHOULD** A new dependency has a one-line reason, crosses no major version, and stays compatible with the platform runtime; a known critical CVE is a MUST.
- **CF9 SHOULD** The public health endpoint stays public and does no database call.
- **CF10 SHOULD** Pool sizes stay sane for instance count times pool size against the database's connection limit; the right pool is configured for the profile.

## Live checks for Verify

Not findings. List the ones the change touches in the review file for the Verify stage (`live-check` skill,
`verifier`).

- Guards: call each new or changed endpoint with no login, as a user without the role, as another team's manager and as an admin; 401 or 403 where the guard says so (RE1-RE4, PG9).
- Callback and machine endpoints with no key, a wrong key and the right key (RE3).
- Cross-user: a user passes another person's id to the endpoint and to a tool; a non-manager calls a team endpoint (RE4, LL8).
- One full turn or action with the outside system up, then down or slow: the result matches the card, a clear message on failure, no spinner, holds released (AL6, DA6, LL3, LL11).
- Parallel requests and a double click on an action: no duplicate rows, quota totals correct (RE8, DA5, JB2).
- Startup after an entity or schema change: validation passes on the existing database, the upgrade step ran, and a second start changes nothing (DA7, DA17, JB7).
- Two app instances or a second run of a job: one run only, no duplicates (AL7, JB1, JB2).
- Query time and plan on realistic volume for new heavy queries, and the size of a result for a user with many records (DA3, DA12, LL13).
- An XSS payload in a title, remark and answer text across every screen that shows it (PG1-PG3).
- Keyboard-only walk-through, a screen reader on streamed text, a narrow frame, 200% zoom, a long German label (PG7, PG11, PG13).
- Admin Save then reload: the value persisted, the secret masked, the effect visible without waiting for a cache (PG10, CF6).
- Kill switch on, then the feature refuses cleanly; off again without a restart (RE9, CF5, JB6).
- The served asset is the new file (the project's app status command with its asset option); browser console and network are clean.
- Prompt-injection sample in a title or comment: treated as data or refused (LL1, LL12).
- The outside system's execution log holds no personal data, and token rows appear for every model call (LL6, LL10).

## Definition of Done map (product mode)

Use it to name the item a MUST breaks. An item with no row (M1, M2) is judged from the stories and `questions.md`.

| DoD item | Checklist ids |
|---|---|
| M3 states | PG5 |
| M4 contract | AL5, RE12 |
| M5 FE/BE split | BE9, PG20 |
| M6 errors | RE6, RE12, AL3 |
| M7 schema as designed | DA1, DA8, DA16, DA18 |
| M8 paged, no N+1 | DA3, DA4, RE7 |
| M9 migrations | DA7, DA17 |
| M10 authorisation, tenant isolation | AL2, RE1, RE2, RE4, RE8, RE10, DA1 |
| M11 secrets and personal data | AL1, AL4, PG8, CF1, DA10 |
| M12 validation, encoding, CVEs | RE5, RE6, DA2, PG1-PG3, CF8 |
| M13 tests | AL8 |
| M14 lint and conventions | AL9, AL10, BE8-BE11 |
| M15 i18n, theme, focus | LB1-LB3, PG7, PG11, PG19 |
| M16 request id, job status | BE11, JB8 |
