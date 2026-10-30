# 08 Audit - desk-booking (DeskBook)

## Re-audit 2026-10-29

Verdict: **PASS WITH CONDITIONS** (updated 29 Oct 10:57 after the theme fix). No team FAIL is left: every MUST is PASS
or a DEV CONDITION. Conditions: B7 (the user runs Redocly lint, npm audit and OWASP dependency-check; the team fixes
findings) and B9 (dev-stack proofs C1, C3, C6, C8, C9, C10) of `09-deploy-plan.md`. The first pass of this re-audit
found one FAIL (theme body), and the lead fixed it (M4 and M12 rows).

Evidence is fresh (my own reads, 29 Oct, S8 re-check): `Backend/target/surefire-reports` has 72 suites, 749 tests,
0 failures, 0 errors, 0 skipped, written 29 Oct 05:41-05:42; no file in `Backend/src` is newer than those reports.
Frontend 215 vitest tests are taken from `07-test-report.md:24` (no result file to read; not re-run, per brief).

| Item | New status | Evidence (path:line, tests) | Owner / deploy-plan item |
|---|---|---|---|
| M1 acceptance criteria met and shown | DEV CONDITION | D10-2 moved the 4 R1 criteria: `04-stories.md:70,216,248,643,885-886`; Q200 answered (`questions.md:221`). `07-test-report.md:9`: 166 MVP criteria, 150 PASS, 0 FAIL, 16 NOT RUN; BK-8.3 PASS (`:62`). The 16 NOT RUN need a server, browser, PostgreSQL, SF or approuter (`:13`) | qa-engineer, performance-engineer, developer with sf-consultant: `09-deploy-plan.md` B9 (C9 journeys + 8 screen states, C10 load, C1 sign-in, C8 SF) |
| M4 matches 05-openapi.yaml, lint zero errors | PASS (b) + DEV CONDITION (a) | **Re-check 10:57, theme fixed:** `UpdateThemeRequest.java:10` `@ClosedBody`; served `Backend/src/main/resources/openapi/openapi.yaml:8225` `UpdateThemeRequest` now `additionalProperties: false` (05-openapi `ThemeUpdate` already closed, `:8108`); `ClosedRequestBodiesTest.java:88` 15th case updateTheme, skip only the multipart logo (`:166`), `assertEquals(15, ...)` (`:187`), open-theme test removed. Surefire 10:57: `ClosedRequestBodiesTest` 4/4; 72 suites, 748 tests, 0 failures; no `src` file newer. **First pass (kept):** (b) fixed for all 14 DeskBook bodies and the locale body: `ClosedBodyConfig.java:26-43` (handler on the app mapper), `GlobalExceptionHandler.java:113-118` (400 VALIDATION_ERROR, UNKNOWN_FIELD), `@ClosedBody` on `BookingRequests.java:22-40`, `OfficeRequests.java:32-74`, `UpdateLocalePreferencesRequest.java:8`; tests `ClosedRequestBodiesTest` (5/5, completeness check `:153-183` asserts 14 schemas) and `ShellControllerContractTest.updateLocalePreferencesRefusesAnUnknownFieldAndMalformedJsonWith400` (`:225-233`). **Still open:** `ThemeUpdate` is closed in the contract (`05-openapi.yaml:8108` `additionalProperties: false`) but `UpdateThemeRequest.java:8` has no `@ClosedBody`, so `PUT /api/v1/theme` accepts and ignores unknown fields. The test excludes theme (`ClosedRequestBodiesTest.java:162`) and asserts the open behaviour with a wrong comment (`:187-191` "not closed in the contract either"). (a) lint: user runs Redocly per D10-3 | (b) done (lead, re-checked 10:57). (a) the user: B7 |
| M7 schema = 05-data-model | PASS | `05-data-model.md` now has V050 `leaver_handled_at` (`:209`), V062 `prev_*` columns and check (`:119-120,128`), V061 SKIPPED/EXPIRED (`:45,293`); Q173, Q174 answered (`questions.md:194-195`). V063 (`V063__booking_partial_indexes.sql:7-17`) matches the design text at `05-data-model.md:267,431` column for column (3 partial indexes, same INCLUDE lists, same WHERE). The document still labels V063 "planned / NOT yet built" (`:9,267,431,480`): LATER 27 | - |
| M12 server-side validation, encoded output, no critical CVE | PASS (a) + DEV CONDITION (b) | (a) theme body now closed at runtime and tested; evidence as in M4 (re-check 10:57). (b) no CVE scan result yet; the user runs `npm audit` and OWASP dependency-check per D10-3 | (a) done. (b) the user runs, devops-engineer reads, developers fix: B7 |
| M13 unit, contract per operation, e2e per main journey | DEV CONDITION | (a) closed: `ShellControllerContractTest` covers all 16 shell operations, 20/20 pass (`:151` route set = 16, `:166` each in the contract with an operationId, one test per operation `:192-343`, request-id header `:350`). (c) closed: `DeskBookBatchRaceTest` 5/5 in the surefire XML; 10 loop runs PASS (`07-test-report.md:357-371`). (b) still no HTTP-to-SPA journey test and the race only on H2 | qa-engineer with the developer: B9 (C9 journeys E1-E10, C6 PostgreSQL race) |
| M2, M3, M5, M6, M8, M9, M10, M11, M14, M15, M16 | PASS (unchanged) | Spot re-checks: no hex or rgb in `features`/`components`/`lib`, no `outline: none` (M15); `PageParams.java:22,30` max 100 (M8); `application.properties:55` request id (M16); 69 questions open, none marked blocker (M2). Dev proofs as before: M3 browser states and M10 cookies in B9 (C9, C1); M9 Flyway on PostgreSQL in B9 (C3) | - |

Process checks, changed:
- G0, G1, G2: **PASS**. D10-1 (`decisions.md:14`, by user, chat "Accept all 3") confirms D1-D4 as the user's own.
- Skipped stages recorded: still **FAIL** (not a MUST). No line in `decisions.md` or `status.md` records the S2
  sf-consultant fit-mode skip (`02-sf-fit.md` missing). Lead: one decision line.
- Questions: 69 open (was 82), 144 answered, each open item tracked with an owner; none is a blocker. Still to close or
  defer before G4 (lead).
- S7 reports current: **PASS**. `07-test-report.md` re-issued 29 Oct 10:49 (749 / 215, BK-8.3 PASS, batch race).

What changed since the first audit:
1. M4b/M12a: closed bodies are now enforced on the application's real ObjectMapper for the 14 DeskBook bodies and the
   locale body (opt-in `@ClosedBody`, not the global switch), with tests through the Spring-configured mapper. The
   theme body was left open in the first pass; at 10:57 the lead closed it (code, served contract, 15th test case): PASS.
2. M7: `05-data-model.md` updated to V050, V061, V062; Q173, Q174 answered. V063 built and matches the design.
3. M13: 16 shell operations have contract tests; the batch race has its result (5 tests, 10 runs, all PASS on H2).
4. M1: D10-2 moved 4 R1 criteria out of the MVP; 166 criteria, 0 FAIL; Q200 answered.
5. D10-3: lint and CVE scans are the user's, so M4a and M12b are DEV CONDITIONs (B7), not FAILs.
6. Tests: backend 714 -> 749, frontend 215; all pass.

New LATER items:
27. `05-data-model.md:9,267,431,480` still say V063 is planned / not built; data-architect to mark it built.
28. `09-deploy-plan.md` B8 still lists the 5 first-audit MUSTs; devops-engineer to cut it to the theme item (and
    drop it once fixed).
29. Error envelopes differ: the shell test reads `$.error.fieldErrors` (`ShellControllerContractTest.java:233`), the
    DeskBook tests `$.errors` (`ClosedRequestBodiesTest.java:130`); both follow their contract today, but one shape
    would be simpler (with LATER 5).

---

# First audit (29 Oct 2026, kept as written)


Auditor: audit-expert (independent, not part of the build). Date: 29 Oct 2026. Product root `D:/products/desk-booking`.
Read-only on code: no git, no server, no build. Evidence is my own sampling of code, tests and recorded results; helper
scripts in the session scratchpad (`au_*.py`). Baseline: Definition of Done M1-M16 (no extra MUST in `decisions.md`).

## Verdict: FAIL

5 MUSTs fail on items the team can close here (M1, M4, M7, M12, M13). Every other MUST passes in code, and some of them
still need a proof on dev (see "Dev conditions"). After the 5 team items are closed the verdict can become
PASS WITH DEV CONDITIONS. Two process checks also fail (G0-G2 not in the user's words; S2 sf-fit stage skipped with no
record).

Context checked: nothing ran on a server, PostgreSQL, SuccessFactors or SMTP (confirmed: 05-ops 8, 10-base-check 5,
07-test-report G2-G4). Backend tests ran on H2 in PostgreSQL mode: `Backend/target/surefire-reports` has 68 suites,
714 tests, 0 failures, 0 errors, 0 skipped, all written 29 Oct 05:12 (my count, `au_surefire.py`). Frontend: 215
vitest tests in node are recorded in `06-build-log.md:176`; there is no result file to check them against.
`07-test-report.md` is older than the S7 fixes (637/201 tests, BK-8.3 FAIL) and needs the QA re-run.

Depends on the runs going on now: the code-reviewer re-check of the S7 MUSTs (rate limits, body limit, key format:
M4, M10, M12) and the QA batch race test (M13; the create-batch insert-order deadlock in the build log "Pre-audit
fixes, Open").

## MUST list (frozen)

| Item | Result | Evidence (path:line) | Owner if FAIL |
|---|---|---|---|
| M1 acceptance criteria met and shown | **FAIL** | BK-8.3 (the one FAIL in 07-test-report) is now fixed: `DeskProposalService.java:143-167` gives NO_MATCH with `alternatives`, `DeskProposalRules.java:128`, 20 backend tests and 6 frontend tests name them. Still failing: 4 MVP criteria describe features that are not in the MVP build (reserved desk ST-BK-8 c6 and ST-RP-3 c3, blocked desk ST-RP-3 c1, booking made by a manager ST-BK-10 c2; `questions.md:221` Q200 open). They are neither met nor moved out of the MVP. The 8 screen-state criteria (E4) and 5 load or sign-in criteria are dev conditions (below). | story-sizer moves the 4 criteria to R1, PO confirms (or build them) |
| M2 no open blocker in questions.md | PASS | 211 items: 129 answered, 82 open, 0 marked blocker (`au_questions.py`); 02-gaps G1/G2 and critic P1-P10 settled by D2 | - |
| M3 empty, loading, error, no-permission on every screen | PASS (in code) | `TodayPage.tsx:123-124` skeleton and error, `:219` empty; `MyBookingsPage.tsx:258-274` loading, error, empty with Book a desk; no-permission comes from the route gates `routes/_authenticated/route.tsx:11`, `admin/route.tsx:6`, `reports.tsx:7` sending people to forbidden or no-access. 14 page files scanned (`au_states.py`). No test draws them (no component tests); a browser check on dev is part of C9 | - |
| M4 matches 05-openapi.yaml, lint zero errors | **FAIL** | Routes: all 45 MVP DeskBook operations have a handler (`au_ops.py`); the only route outside the contract is the base Azure OpenAI controller. 429 is now built on 29 operations: 19 `requireAdminWrite()`, `BookingService.java:94`, `BookingBatchService.java:84-85`, `CheckInService.java:48,53,59-60`. Fails: (a) lint was not run on the final contract (`05-api-notes.md:253`: "lint is not run"); (b) the contract closes 85 schemas (`additionalProperties: false`), but the running app accepts and ignores unknown fields. Spring Boot's default mapper turns FAIL_ON_UNKNOWN_PROPERTIES off. No `spring.jackson.*` key is set (`application.properties`), there is no ObjectMapper bean in the product, and TTCommon `CustomWebMvcConfigurer` only removes duplicate converters. `@JsonIgnoreProperties(ignoreUnknown = false)` (`OfficeRequests.java:32`) does not switch failing on. The test that passes builds its own `new ObjectMapper()` (`BookingControllerContractTest.java:90`, so `:283` gets 400), which the app does not use | (a) api-designer; (b) backend-developer: `spring.jackson.deserialization.fail-on-unknown-properties=true` (check the base shell bodies too) plus one test through the Spring-configured converter |
| M5 tasks on the right side, no rule only in the frontend | PASS | Release, deadline, hold window, proposals and day totals are in the backend (`BookingCommandService`, `DeskProposalService`, `OccupancyReportService` `dayTotals`). The frontend does display date maths only (`MyBookingsPage.tsx:156`, `PlanPage.tsx:90`); `TimeMathPlacementTest` | - |
| M6 problem details, stable codes, no internals | PASS | `GlobalExceptionHandler.java:200-216` (generic INTERNAL_ERROR, the exception is only logged), `:224-229` (DUPLICATE without the constraint name), `:106-116`, `:240-252` (traceId = request id) | - |
| M7 schema = 05-data-model, tenant, audit, version, FKs, history | **FAIL** | All 11 product tables in V010-V061 have tenant_id, created/updated at/by and version, with FKs as designed (`au_tables.py`). History: `@AuditedEntity` on 10 entities, opt-outs with reasons (`BookingSlot.java:23`, `Notification.java:27`, `SyncRun.java:21`), checked by `AuditedEntityCoverageTest`. Fails: the built schema no longer matches `05-data-model.md`: V050 `leaver_handled_at` (0 hits in 05-data-model), V062 `prev_*` columns (0 hits), and V061 statuses EXPIRED/SKIPPED with `booking_id` (Q174 open) | data-architect: update 4.2, 4.6, 4.10 and answer Q173/Q174 |
| M8 lists paged and bounded, no N+1 | PASS | `PageParams.java:22,30` (size 1-100); the settings recompute now goes by date in pages of 500 (`BookingRepository.java:100-106`, `DeadlineRecomputeStore`); batched lookups (code review batch 2, M8) | - |
| M9 migrations with rollback note | PASS | V010, V020, V030, V050, V060, V061 and V062 each carry a rollback note (`au_tables.py`); no applied script edited (V004 kept, dropped by V060). The base V001-V003 have no note (LATER). A Flyway run on PostgreSQL is a dev condition (C3) | - |
| M10 backend authorization per operation and per record, tenant isolation tested | PASS (in code; dev proof C9) | 45 of 45 DeskBook handlers call the guard first in their service (`au_guard.py`; `DeskAccessGuard.java:52-98`); own records only: `BookingRepository.java:28-32`, `BookingCommandService.java:270-272` (another person's id gives 404); 62 of 62 repository JPQL queries filter on tenant (`au_tenant.py`); tenant tests `BookingRepositoriesTest.java:48-62` (TENANT_A/B) plus office, people and stats tests. The CSRF control promised in Q68 is not built (LATER, before G4) | - |
| M11 no secrets, no personal data in URLs or logs | PASS | Secret keys are placeholders (`application-local.properties:14`, `application-test.properties:13`; manifest `<set-in-env>`); no hard-coded key found; no name, e-mail or address in DeskBook log lines (scan); URLs carry ids only (`/bookings?focus=<uuid>`) | - |
| M12 server-side validation, output encoded, no critical CVE | **FAIL** | Built: rate limits `RateLimiter.java:72-95`, 16 KB body limit `RequestBodyLimitFilter.java:37,56`, key format `BookingService.java:78-88`, bean validation on all 14 DeskBook bodies (`BookingRequests.java:21-31`), escaped mail HTML `MailTemplates.java:80`. Fails: (a) closed bodies are not enforced at runtime (same cause as M4b); (b) no dependency CVE scan is recorded anywhere (no `npm audit`, OWASP or OSV result in any document). Not verified, so not shown | (a) backend-developer; (b) devops-engineer (needs network: CI or dev) |
| M13 unit, contract per operation, e2e per main journey, all pass | **FAIL** | Unit and service tests for rules and services: yes, 714 pass. Contract tests for the 45 DeskBook operations: yes (`OfficeControllerContractTest.java:69-78`, Booking, Report, `RoleMatrixContractTest`). Fails: (a) the 16 base shell operations in 05-openapi (`getCurrentUser`; 4 under `/api/i18n`; 4 under `/api/integrations`; 7 under `/api/v1/theme`; only `getHealth` is tested) have no backend contract or API test (paths found in no test except `ThemeServiceTest`, the service, and `RateLimitAndBodyLimitHttpTest`); (b) no end-to-end test per main journey: `DeskBookAcceptanceFlowTest` is service level on H2, with no HTTP, filters, approuter or SPA (dev condition C9); (c) the batch race result is not in yet (QA running) | (a) qa-engineer; (b) dev; (c) qa-engineer, result pending |
| M14 no lint or type errors, base conventions | PASS (by record) | eslint 0 errors, `tsc -b` clean, build OK (`06-build-log.md:176`); B9 layout sampled (modules with controller/service/repository/domain/dto, ports and adapters). Not re-run by me (no builds) | - |
| M15 i18n complete, theme tokens, focus visible | PASS | No hex or rgb in `features`, `components`, `lib` (scan); 19 `focus-visible` uses, no `outline: none`; key parity and screen-text tests (`qa/screenTexts.test.ts`); mail texts in `messages.properties` | - |
| M16 request id in logs, jobs record status and errors | PASS | `application.properties:55` `[%X{requestId:-}]`, `RequestIdFilter.java:26-36`; `ReleaseBookingsJob.java:35-44` (counts, addError, FAILED); the same pattern in the 7 DeskBook jobs (code review batch 2, M16) | - |

## Process checks

| Check | Result | Evidence |
|---|---|---|
| G0 plan agreed by the user | **FAIL** | `status.md` G0 "demo: lead accepts all recommended answers"; D1 "by lead (simulated user)". Not the user's words |
| G1 product owner answers | **FAIL** | D2 "by lead (simulated PO)" |
| G2 scope and MVP | **FAIL** | D3 "by lead (simulated user)"; D4 likewise. Later user decisions (D5 "Approve A", D6, D7 "Export in MVP", D8) build on this scope but never ratify G0-G2. Fix: one line from the user in decisions.md ratifying D1-D4 |
| GP prototype | PASS | D5 by user ("Approve A") |
| G3 design approved | PASS | D8; `answers/G3.json` by "user (tracker)", "approve", 28 Oct 18:16 UTC |
| No code before G3 except the S1 base | PASS (mtime evidence) | Earliest file in the DeskBook modules (office, booking, checkin, people, notification, reports, access, both FE and BE) is dated 29 Oct 01:21, after G3 (28 Oct 23:46 local). Base files come from S1. This is last-modified time only (no git) |
| Questions answered or tracked | PARTIAL | 82 open, each with an owner and a recommended answer (tracked), but not answered or explicitly deferred. The lead must close or defer them in one pass before G4. Q68 is marked answered ("handled in S6"), but its S6 work was not done (LATER 1) |
| Skipped stages recorded in decisions.md | **FAIL** | S2 `sf-consultant` fit mode (`02-sf-fit.md`) is missing and there is no decision line for it (05-sf-fields field mode and 07-sf-review exist). `status.md` size "not set" (intake says L) |
| S7 reports current | PARTIAL | 07-code-review, 07-system-review, 07-performance and 07-sf-review MUSTs are fixed in code (rate limits, SPA fallback route `approuter/xs-app.json` last route, async recompute, people M1/M2 `PeopleMapper.java:27,119,152-170`), but no S7 report records the re-check yet; 07-test-report is older than the fixes |

## Dev conditions (can only be closed on dev or by people outside the team)

| # | What | Owner |
|---|---|---|
| D-1 | Flyway V001-V062 on a clean PostgreSQL and on one that has V004 (05-ops C3) | devops-engineer |
| D-2 | PostgreSQL race: same desk and half, two bookings on one day, same key twice, and the batch (C6; Testcontainers needs Docker) | qa-engineer / test-engineer |
| D-3 | E2E journeys E1-E10 on the dev stack, including the 8 E4 screen-state criteria and the M3 states in a browser (C9); results into 07-test-report | qa-engineer with the developer |
| D-4 | Approuter: deep links from mails and reloads (`/bookings?focus=...&action=hold`, `/book`), sign-in redirect, cookie flags HttpOnly/Secure/SameSite (C1, Q68) | devops-engineer |
| D-5 | Dependency CVE scan, backend and frontend (M12b), if it cannot run in the sandbox | devops-engineer |
| D-6 | Load tests T1-T12 and the 5 load or sign-in criteria (BK-1.4, BK-9.2, PP-1.1, RP-4.1, BK-5.5/PP-5.1) (C10) | performance-engineer |
| D-7 | Real SMTP timing and LIVE switch: `DESKBOOK_MAIL_MODE`, `DESKBOOK_APP_BASE_URL`, worker count (C7, Q176, Q181); customer mail service to confirm 300 a minute (D6-6) | devops-engineer, integration-engineer; customer mail admin |
| D-8 | SuccessFactors tenant checks C1-C16 as the API user; API user role and population (Q113, Q110-Q112, Q169) | developer with sf-consultant; customer SF admin |
| D-9 | Job schedules on a new environment: minute jobs, node role, double runs on 2 instances (Q203, Q206, Q207) | devops-engineer |
| D-10 | Legal and works-council sign-off for DE and FR before the pilot, plus an erasure runbook (Q75) | PO with customer Legal / works council |
| D-11 | Alert recipients: no good people copy for 36 h, FAILED mails, health (Q82) | customer operations (developer to collect) |
| D-12 | Small-cell threshold for the occupancy report and export (Q114, code review B2-S9) and pilot desk count (Q193) | PO |

## LATER backlog (not MUST)

1. Before G4, security-architect: the CSRF control in Q68 / 05-security row 134 / test 11 is not built (`xs-app.json` csrfProtection false on `^/deskbook/(.*)$`, no X-CSRF-Token in `http.ts`, no CSP, the webhook route is still there). Every DeskBook write needs a JSON body, If-Match or Idempotency-Key, so the browser preflight blocks a cross-site call (`au_csrf.py`). Accept this in writing or build the control.
2. Base `testConnection` POSTs (SuccessFactors, Azure OpenAI) have no preflight trigger; low impact, same decision as item 1.
3. Base leftovers: `AzureOpenAiConnectionController`, `UsersSyncDailyJob`/`UsersSyncFullFetchJob`; D9-3 one-pass drop of unused TTCommon jars not done (system review S10).
4. Base migrations V001-V003 have no rollback note.
5. The TTCommon filter's 401 is not problem details; `UNAUTHORIZED` vs `UNAUTHENTICATED` vocabulary (system review S1).
6. `GlobalExceptionHandler.java:189` logs the whole DataIntegrityViolationException (SQL values may reach the log).
7. `Backend/.../openapi.yaml` is a merged copy of 05-openapi.yaml; keep one generator step so they do not drift again (B2-S14).
8. Rate limits count per instance; with more than one instance each counts for itself (accepted in 05-security 7, logged at start).
9. Batch create: check other multi-row inserts for the opposite-order lock pattern (build log, pre-audit "Open").
10. Settings recompute has no stored pending marker (Q211).
11. PB-3 batch booking statement count (Q182); PB-5 release loop re-reads the same 200 rows (B2-S5); PB-7 export concurrency cap.
12. People sync `fetchAll` ends on a short page (B2-S11); `UNMAPPED_LOCATION` count, nightly inactive read (07-sf-review S3, S6); 36 h no-SUCCESS metric (Q82).
13. `OccupancyCalculator` uses today's working days for past days (B2-S12).
14. Office closing count-then-write window (batch 1 S3); an office can open with no desk (system review S8, Q105).
15. Frontend component tests (jsdom + Testing Library, batch 1 S17 / G1 of the test report).
16. Entry chunk 204 KB gzip after PB-10; self-host the Inter font subset; CI size check.
17. de, es, fr and en-GB carry English text for many keys: translate in the release pass.
18. 05-security 4.6 and 8 item 8 to say "10 percent, configurable, floor of 5"; other document number drift (system review S5).
19. Product `README.md` still lists the `projects` package (B2-S15).
20. `07-test-report.md` to be re-issued after the QA re-run (counts, BK-8.3).
21. Running-late hold and alternatives: the contract line for 422 CHECK_IN_NOT_OPEN on hold is done; the PO to confirm the hold-window rule (B2-S1).
22. Admin "last updated" line for the people copy (Q80) and "Run sync now" (Q107): PO.
23. Same-day afternoon end time (Q130), report row rules (Q161), reminder expiry (Q179): PO short answers.
24. Stray temp folders `D:/tmp_fx7`, `D:/tmp_fx7s`, `D:/tmp_npm_install.log` to delete.
25. `Frontend/dist` copy into `approuter/resources` has no build step (Q204).
26. Mail is at-least-once after a crash (accepted, 05-integrations 2.3).

## What closes the FAIL

1. backend-developer: enforce closed bodies (M4b, M12a) and add one Spring-converter test.
2. api-designer: lint the final 05-openapi.yaml, zero errors (M4a).
3. data-architect: bring 05-data-model in line with V050, V061, V062; close Q173, Q174 (M7).
4. story-sizer with the PO: move the 4 unbuilt criteria of Q200 out of the MVP, or build them (M1).
5. qa-engineer: contract or API tests for the 16 base shell operations; record the batch race result; re-issue 07-test-report (M13).
6. Lead: user ratifies D1-D4 (G0-G2); record the S2 sf-fit skip; close or defer the 82 open questions.
