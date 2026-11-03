# Practice pack: verifier

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## CTAL-TA: independent verification of criteria
- Write your check list from the criteria, the approved decisions and the confirmed answers before you open the build log, `test.md` or the builder's notes; compare afterwards, so their list cannot narrow yours.
- Independence is from the builder's conclusions, not from the spec: read what binds the work, never the builder's reading of it.
- Expected results come from the criterion and are written down before you run; never from what the code returns now (that verifies the bug).
- Evidence strength, strongest first: a run you made (command output, a test you ran, a query result); code at `path:line` in the verified revision; a test you read but did not run; anything the builder reported. Only the first two support PASS.
- Structure criteria (a field exists, a route is guarded, a key is in every locale) can pass on `path:line`; behaviour criteria (computes, filters, rejects, sorts) need a run when a cheap one exists, else NOT RUN with steps.
- A green test counts only if it ran (the runner's executed count, not skipped or filtered), asserts the criterion's expected result and exercises the changed code; read the assertion before you cite it.
- Evidence is reproducible and current: command, revision or diff range, inputs and trimmed output; an edit after your run makes it stale, so run again.
- Use your own inputs, not the builder's sample data: values from other partitions and on the boundaries.
- Look for the breaking input: each criterion gets at least one negative case (wrong role, other tenant, invalid value, forbidden transition), not only the case that passes.
- A forbidden action hidden in the UI is not proof: check that the API rejects it too.
- A number in a criterion (time, rows, size) needs a measurement that states data volume, environment and percentile; without one it is NOT RUN, not PASS.
- A vague criterion ("fast", "clear") can neither pass nor fail: NOT RUN, with the question to its owner.
- Map every changed hunk to a criterion and every criterion to evidence; a hunk no criterion explains is reported as scope, never passed silently.
- Many items under one criterion (every endpoint, screen or locale): check all with a script when you can (key-set diff, grep over routes); else every high-risk item (writes, deletes, personal data, money, tenant scope) plus a random sample of the rest, spread over roles, tenants, locales and statuses.
- State the sample in the evidence ("9 of 40: the 6 write operations and 3 random reads"); one failing item fails the criterion, a clean sample passes only what was checked.

## CTAL-TTA: technical evidence without the running app
- Trace each input of a changed operation: controller parameter, validation, service, query (bound parameters, tenant in the WHERE), response DTO (only the fields the role may see).
- List the branches of each changed decision and give each one evidence; a `catch` that returns an empty list or a default fails open and breaks "a failed call is an error".
- Compound conditions (role and tenant and status): check that each condition can change the outcome on its own; a wrong `||` still passes the happy path.
- Cyclomatic complexity of a changed method (decisions + 1) is the number of paths needing evidence; over 10, sample paths by risk and say so.
- Contract against code: every operation in the contract or design has a handler with the same path, method, status codes and required fields, and every handler has an operation.
- Data model against code: migration columns, types, lengths and nullability match the entity and the design; a renamed column is grepped in native queries.
- Renamed or removed names: grep the old name across the repo (callers, views, i18n keys, n8n payloads, tests); the diff alone does not show what it broke.
- Config: every new key exists in every profile or has a code default; no secret value in a committed file.
- Security evidence per new operation: the role check at `path:line`, a tenant-scoped query, encoding of user and LLM text on output; a cheap run with another tenant's id when the app is up.
- Reliability evidence: a timeout and a bounded retry on every new outside call, and the state the user sees when it fails.
- A technical smell (query in a loop, missing index, high complexity) is FAIL only when it breaks a criterion's number or a hard rule; otherwise one LATER line.
- (SAP) Approuter changes: check `xs-app.json` route order and per-route `authenticationType` against the ui5-plainjs pack.
- (SAP) UI5 changes: grep changed views for controls without stable IDs and texts outside the i18n model.

## Traps
- "Tests pass" in a build log, report or comment is a claim; fix: run the named tests or mark NOT RUN.
- A run that reports success with 0 tests executed (filter typo, class not compiled); fix: read the executed count.
- With the app up, `commands.test` runs what the IDE compiled, so "test not found" or old behaviour can be a stale build, not a defect; fix: say so, NOT RUN, ask for an IDE build.
- Verifying against the plan instead of the criterion (a plan step done is not a criterion met); fix: start from the criterion text.
- Sampling the easiest items; fix: draw the random part by a stated rule (every k-th item or a seeded shuffle).
- A screenshot or log from the builder for a live criterion; fix: the main session runs the listed steps and records the result, until then NOT RUN.

## Numbers
- 0 failures in a random sample of n still allows about 3/n of the rest to fail (95% confidence): 0 of 30 leaves about 10%, 0 of 60 about 5%.
- N independent binary conditions: up to 2^N decision-table rules; MC/DC evidence needs at least N+1 cases.
- Boundaries: 2 checks per boundary, 3 where an off-by-one is costly.
- Cyclomatic complexity over 10: more paths than a reading can cover, so run tests or sample by risk.
- UI live checks: text contrast 4.5:1, UI parts 3:1, targets 24x24 CSS px; LCP 2.5 s, INP 200 ms, CLS 0.1 at the 75th percentile.
