# Practice pack: qa-engineer

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## CTAL-TA: technique per risk and criterion
- Input ranges and formats: domain testing (partitions plus boundaries); one invalid value per test, because two invalid values in one test hide each other (masking).
- 2-value boundary analysis (the boundary and its nearest neighbour across it) for ordinary limits; 3-value (both neighbours) where an off-by-one or `==` slip is costly: money, quotas, date cut-offs.
- Combined rules: decision table, one column per feasible rule; collapse to "don't care" only when that condition truly has no effect on the rule, then test every remaining column.
- Statuses: state transition table; every valid transition (0-switch), every invalid one the API can receive even if the UI hides it, and transition pairs (1-switch) for loops such as reopen.
- Data lifecycle: CRUD matrix per entity and role, a read after every write to prove what was stored, and a delete checked in every list and search that shows the entity.
- Many independent options (filters, settings, locale and browser): pairwise covers every pair of values; add the risky full combinations by hand.
- No exact expected result (search ranking, recommendations, LLM output): metamorphic relations, for example adding a filter never adds results, reordering input keeps the result set, the same query with a fixed seed gives the same top results.
- Journeys: scenario tests for the main flow, each alternative flow and each exception flow (outside system down, permission removed mid-journey).
- New or unknown areas: an exploratory session with a charter (target, resources, information sought), a time box and notes; each finding becomes a scripted regression test.
- Risk level = likelihood (new or complex code, many callers, defect history in `lessons.md`) x impact (users affected, money, personal data, legal); it sets technique, depth and order, and the report states the residual risk.
- Review every criterion for testability before writing tests: a measurable expected result, limits stated, no vague words ("fast", "easy"); ask the owner for numbers instead of guessing.
- Error guessing from a defect list: past escapes in `lessons.md` and the classic ones (null, empty, duplicate, concurrent edit, time zone) become test ideas for every similar change.
- Defect report: steps, data, expected, actual, environment, severity (impact) apart from priority (urgency), and the root cause once known.

## CTAL-TTA: white-box, static and technical quality
- Coverage strength: statement < branch < MC/DC < multiple condition; 100% branch gives 100% statement, not the reverse (an `if` with no `else` hides an untested false branch).
- MC/DC on compound access and eligibility predicates (role and tenant and status): each condition shown to flip the outcome on its own; Java `&&` and `||` short-circuit, so count only feasible combinations.
- Use branch coverage of the changed lines (JaCoCo, Vitest coverage) to find untested branches, never as a pass gate.
- Mutation testing (PIT for Java, Stryker for TypeScript) on rule-heavy classes: a surviving mutant (changed operator or boundary still passes) is a missing assertion.
- Static analysis before running: data-flow anomalies (defined and never used, used before defined), unreachable code, unchecked nulls; cyclomatic complexity (decisions + 1) is the minimum test count for basis path coverage.
- Dynamic analysis: memory growth across repeated runs (Java heap after GC; detached DOM nodes after opening and closing a widget many times), thread contention, slow statements in the SQL log.
- Security per new operation: another tenant's id (404, or the status the contract states), a role below the needed one (403), injection text in every free-text field, markup and script in data shown back (LLM output included), modifying calls without the CSRF token.
- Reliability: fault injection on every outside call (timeout, 500, slow, malformed body); retries stay bounded, a retried POST creates nothing twice, the user sees the error state.
- API tests: responses validated against the OpenAPI schema; missing required and unknown fields, wrong types, oversize bodies, page size above the maximum, errors in problem-details format.
- Performance test type by risk: load (expected peak), stress (beyond it, fails gracefully), spike, endurance (hours, for leaks); budgets and scenarios belong to performance-engineer.
- Technical review checklist: a timeout on every remote call, pool sizes, transaction boundaries, cache invalidation, shared state under concurrency.

## CTAL-TAE: automation architecture and flakiness
- Layers: test definition (cases named by `AC` id in business words), execution (the runner), adaptation (API clients, page objects, drivers); a UI change touches only the adaptation layer.
- Page objects own locators and waits, tests hold none; locate by role and accessible name, then a test id or stable ID; never CSS paths, translated text or generated IDs.
- Approach by need: data-driven when the same steps run over many data rows; keyword-driven when non-coders write cases; plain scripts for a few cases; capture and replay only for a throwaway spike.
- Test data: each test creates what it needs through the API (not the UI) with unique names and removes it; no test relies on a record another test changes.
- Wait on a condition (Testing Library `findBy` and `waitFor`, a polling assertion), never a fixed sleep.
- Flaky test (passes and fails on the same code): out of the gating suite at once, logged with an owner and a date, cause fixed (timing, shared state, order, clock, time zone, network); rerun-until-green hides real defects.
- Order independence: run suites in random order now and then (JUnit `MethodOrderer.Random`, Vitest `sequence.shuffle`) to expose hidden coupling.
- Environment: repository tests on the production database engine where the repo supports it (an in-memory database hides dialect and locking differences); outside systems stubbed at the HTTP boundary with recorded payloads.
- Pipeline: a fast gating suite (unit and API) on every change, end-to-end journeys after merge or nightly; each failure carries the `AC` id, logs, request and response, and a screenshot for UI.
- Verify the automation: see each new test fail once (break the expected value or the code) before trusting it; check the executed count equals the planned count, so skipped and not-found tests show.
- Metrics that steer: pass, fail, skipped and not-run per run, flaky rate, suite duration trend, defects caught by automation versus escaped, time spent fixing tests; not "percent automated".
- Treat test code as product code: reviewed, no duplicates, helpers refactored when one locator change touches more than one file.
- (SAP) QUnit for formatters and models, OPA5 with stubbed responses for in-app flows, wdi5 for end to end in the launchpad (it waits for UI5 to be idle); selectors by stable ID plus view name, never generated `__xmlview` IDs.

## Traps
- Expected result copied from today's output for new behaviour copies the bug; fix: expected from the criterion, written before the run (characterization tests are the deliberate exception).
- Mocking the repository in a service test leaves the query and its tenant filter untested; fix: a repository slice test (`@DataJpaTest`) for each new query.
- Asserting mock call counts or private state breaks on refactor and proves nothing to the user; fix: assert the returned or shown result.
- Boundaries tested in the UI while the API accepts more; fix: test the API boundary as well.
- Characterization output with timestamps, random ids or unordered sets differs every run; fix: fixed clock, sorted output, masked ids.
- Green in CI (UTC, English) and red on a laptop (Europe/Berlin, German); fix: date and text tests with a set time zone and locale, including a DST change day.

## Numbers
- Boundary analysis: 2 tests per boundary (2-value) or 3 (3-value); a min..max range gives 4 or 6.
- N independent binary conditions: up to 2^N decision-table rules or multiple-condition tests; MC/DC needs at least N+1.
- Pairwise: 4 options with 3 values each are 81 combinations but 9 tests cover every pair.
- Cyclomatic complexity over 10 in a changed method: cover every basis path or ask for a split.
- Exploratory sessions: 60-120 min, one charter each.
