# Practice pack: qa-lead

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## CTAL-TM: risk, plan, criteria, triage and metrics
- Score every product risk likelihood (1-3) x impact (1-3): 1-2 low, 3-4 medium, 6-9 high. Likelihood grows with new or complex code, many callers, a past escape in `lessons.md`; impact with users hit, money, personal data, legal, no way back.
- Risk sets depth: high = several test types, the largest data volume, every role, an exploratory charter; medium = API or UI check plus the main alternative flow; low = one happy check, never zero.
- Risk sets order: run high-risk rows first, so a stop for lack of time cuts the low rows, not the high ones.
- Test matrix: one row per criterion x type x role x volume that matters; do not build the full cross product. Cut a row only with a stated reason (same code path, same risk) and list it under `## Not tested`.
- Pick the type by the risk it finds: logic -> unit; contract, access, paging bounds -> API; look and keyboard -> UI; a path across screens or roles -> E2E; unknown area -> exploratory; speed -> performance-engineer's budget; leaks and injection -> security.
- Pick who runs by what changed: UI change -> `ui-qa-expert`; journey, status flow or notification -> `e2e-qa-expert`; endpoint -> `qa-engineer`; each left-out expert gets a one-line reason.
- Entry criteria: build compiles, unit suite green, served asset is the new code, test data and test users exist. If one is missing, the verdict is BLOCKED, not a lowered bar.
- Exit criteria are fixed in the plan: every Must row PASS, every checklist MUST PASS or N/A with a reason, no open FAIL, each BLOCKED resolved or accepted by the developer.
- Test data plan per volume: empty, one, exactly a page, a page plus one, 3+ pages, the real maximum; source named (dev data, app screens on a dev tenant, fixtures); never production copies; list what to ask the developer for.
- Estimate in tool calls: a unit or API row 2-4, a UI row per screen part about 10, a journey 8-15 per role, an exploratory charter about 8; add 20% for retests after a fix; if the total passes the budget, cut low-risk rows first and say so.
- Defect triage: severity (impact) apart from priority (urgency); each FAIL has an id, an owner agent, the re-run list; duplicates merged; a SHOULD goes to the LATER list, not into the verdict.
- Verdict rules: `SIGNED OFF` only if every exit criterion is met; `NOT SIGNED OFF` for any Must or checklist MUST that is FAIL or NOT RUN; `BLOCKED` when the app or data is missing. Only the developer accepts a risk, in their own words with a date. Never reword a FAIL into a PASS.
- Metrics that steer: criteria covered (rows run / rows planned, per criterion), open MUSTs, NOT RUN and BLOCKED counts, escaped defects (found after sign-off, each one becomes a `lessons.md` line and a new matrix row), retest fail rate. Not "number of tests".

## CTAL-AT: whole-team quality in agile
- Shift left: at Design the plan already exists. Review each criterion for testability before build: a measurable result, stated limits, no vague words ("fast", "easy"); ask the owner for numbers.
- Three amigos style review: business view (what the user needs), build view (how it is made), test view (what could go wrong). Run it as a short criteria pass; each open question becomes a line for the developer, not a guess.
- Criteria as examples: Given/When/Then with real values (a 21st row, a manager outside the team); an example that cannot fail is not a criterion.
- Testing quadrants: Q1 unit and component (technology, supports the team) = `qa-engineer`; Q2 functional examples and journeys (business, supports the team) = criteria and E2E; Q3 exploratory, usability, acceptance (business, critiques the product) = `e2e-qa-expert`, `ui-qa-expert`; Q4 speed, security, reliability (technology, critiques the product) = specialists. A plan with a quadrant empty must say why.
- Test pyramid: many unit, fewer API, few UI and journey rows; a new UI-only row needs a reason why a lower level cannot check it.
- Definition of done for a change: criteria met, unit and API tests in the test folder, UI MUST items PASS, no open FAIL, `lessons.md` updated, sign-off written. A change is not done while a Must row is NOT RUN.
- Regression risk: every change touches the areas in `.claude/smoke.md`; add the smoke rows of each area in the impact map.
- Retrospective habit: each escaped defect or reopened FAIL gets a cause (missing row, wrong volume, vague criterion) and a plan fix.

## C_STC: Cloud ALM test management
- (SAP) Test cases in Cloud ALM are linked to the requirement or user story they prove; the matrix `Criterion` column keeps the same id so the link is one to one.
- (SAP) Group cases into a test plan per release or feature; a test plan holds the test cases, their owners and the test system; the matrix `Owner` column maps to the tester.
- (SAP) Test execution: each run records a result (passed, failed, not run) and evidence; a failed case creates a defect linked to the case; the sign-off table reports the same states.
- (SAP) Process-based end-to-end scenarios follow the business process across apps and roles (SuccessFactors, the BTP app, the launchpad); the journey rows of `e2e-qa-expert` map to one scenario each.
- (SAP) Role collections from `xs-security.json` each get a row: allowed and denied; the approuter session and the launchpad tile get one row each when the app is a Fiori app.
- (SAP) Test only in the dev or test tenant the developer names; manual test data in SuccessFactors stays in the test instance.

## Traps
- A plan written after the build copies the code, not the criteria; fix: matrix rows come from criteria and the impact map.
- "All rows PASS" with the list tested on 5 rows; fix: a volume column and BLOCKED for missing volumes.
- Exit criteria lowered at sign-off because time ran out; fix: BLOCKED or NOT SIGNED OFF, and the developer decides.
- The sign-off counts tests, not risks; fix: report high-risk rows first and what was not tested.

## Numbers
- Risk score 6-9 = high; at least 3 types and the largest volume for each high row.
- Volumes: 0, 1, page, page + 1, 3+ pages, real maximum.
- Retest allowance: +20% of the calls; exploratory charter: 60-120 min or about 8 calls.
