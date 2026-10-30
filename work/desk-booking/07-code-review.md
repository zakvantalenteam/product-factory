**Overall verdict (S7 re-check, 29 Oct 2026): PASS on code, 0 MUST open, 0 new MUST. Batch 2 MUST 1 and all 5 batch 1 MUSTs are closed. One environment proof stays open for dev, not a code defect: system review M2 (Flyway V001-V062 and the first-booker race on real PostgreSQL). Earlier verdicts below stay as written; the re-check is the last section, "## S7 re-check".**

# Code review - batch 1 (wave 1 BE, wave 1-2 FE)

Reviewer: code-reviewer. Date: 29 Oct 2026. Product `D:/products/desk-booking`. Read-only; nothing was built or run, so test results are taken from the build log (BE 290, FE 164 tests).

Scope read: Backend `common/time`, `office`, `access`, `people`, `common/exception`, `common/web`, V010, V020, the office and access tests; Frontend `features/office|access|booking|checkin|reports`, `lib/api`, `lib/session`, `routes/_authenticated/**`, `components/layout/navConfig.ts`, locale files; Backend `openapi.yaml` against `05-openapi.yaml`. Not read: booking and check-in backend, V030+.

## Verdict: FAIL (5 MUST)

The core is sound: every one of the 28 office operations calls `requireAdmin()` as the first line of the service (checked in all six services), every repository query filters tenant and `deleted_at`, lists are paged (max 100) with batched lookups (no N+1), If-Match is checked before any change, problems are RFC 9457 with stable codes, V010 and V020 match the data model (partial and functional unique indexes, composite FK desk-zone, checks, `settings_effective_from`), and the part-of-day rules are pure and table-tested. The MUSTs are contract drift, one missing test class, one missing label, and one displayed total that can be wrong.

## MUST

| # | Where | Problem | Fix | Owner | DoD |
|---|---|---|---|---|---|
| 1 | `05-openapi.yaml` and `Backend/.../openapi/openapi.yaml` paths (`/offices`, `/desks` ...); `OfficeControllerContractTest.java:132` | Contract paths have no `/api/v1` prefix (servers url is `/deskbook`), the implementation serves `/deskbook/api/v1/...` (Q133). The contract test strips `/api/v1` before comparing, so it hides the mismatch. | Put `/api/v1` on every DeskBook path (the base theme paths in the same file already have it), regenerate `deskbook.gen.ts`, make the test compare full paths. | api-designer (test: backend-developer) | M4 |
| 2 | `05-openapi.yaml` `updateOffice` (responses 200,400,401,403,404,409), `createDesk`/`updateDesk`, `createOffice` | Built answers the contract does not list: `updateOffice` returns 422 `HAS_FUTURE_BOOKINGS` on a timezone change (`OfficeService.java` update); `updateDesk` returns 422 `DESK_FLOOR_LOCKED`; duplicate location code returns 409 `DUPLICATE` (Q143, Q144). | Add 422 to `updateOffice`, list `DESK_FLOOR_LOCKED`, `HAS_FUTURE_BOOKINGS` and the duplicate code on the operations and in 05-ui section 10; keep both contract copies identical (see S10). | api-designer | M4, M6 |
| 3 | `Backend/src/test` (office, access) | No test runs a repository query or proves tenant isolation: all office tests use mocked repositories, so `OfficeRepository.search`, `DeskRepository.search` (cross-root join + count), the JPQL counts and the "another tenant's id gives 404" rule are never executed. | Add a PostgreSQL-backed (Testcontainers or the project's test DB) repository/service test: records of tenant B are invisible to tenant A on every `findLive`, list and count; plus one real unique-violation test (data model section 12 asks for it). | backend-developer | M10, M13 |
| 4 | `Frontend/src/features/checkin/components/TodayDeskCard.tsx:137` | `t('checkin.desk.label')` has no key in any locale (the object `checkin.desk` is empty): the desk code is announced with the raw key text. | Add `checkin.desk.label` to the five locale files. | frontend-developer | M15 |
| 5 | `Frontend/src/features/reports/lib/report.ts` `groupByDay`/`sumRows`, `ReportsPage.tsx:356,486` | The "All floors" line per day is summed in the SPA from the rows loaded so far. With pages of 100 a day split across the page border shows a partial total as if complete, on a report admins act on (Q152). | Contract: `getOccupancyReport` returns per-day totals (`dayTotals[]` or a `floorId: null` row) and the SPA shows those; until then show the last group's total only when `hasNextPage` is false. | api-designer + backend-developer (contract and report lane), frontend-developer (stop-gap) | M1, M5 |

## SHOULD (quality, not blocking)

Backend (backend-developer unless noted)
- S1 `FeatureService.list` writes on a GET (seeds Monitor, Docking station, Standing desk). Two first calls at once hit `uq_ofc_features_name` and one gets 409 `DUPLICATE`. Seed in a first-use step that tolerates the violation, or from `openOffice`/migration.
- S2 `NoBookingsImpactAdapter` (`@Fallback`) answers "no bookings" for every check. Until the booking lane registers its bean, closing an office or retiring a desk/floor ignores bookings. Batch 2 must show the booking bean replaces it (add a Spring wiring test) before any release.
- S3 Close office, retire desk/floor and add closed day count bookings and then write, without a lock; a booking created between the two is not seen. The booking lane must re-check office OPEN, desk and floor active inside its own transaction (booking reviewer to confirm).
- S4 `DeskBody.featureIds` allows 50 items, the contract says 20 and unique. `OfficeService`/`DeskService` use inline fully-qualified `BusinessException` and `HttpStatus`; import them.
- S5 Parent state is not checked: `ZoneService.create` and `DeskService.create` accept a retired floor path where the floor check is missing (zone) and floors/desks can be added to a CLOSED office; `DeskService.retire` of a desk on a retired floor answers 400 `FLOOR_RETIRED` (a desk cannot be retired or fixed there); `FloorService.retire` says it hides the floor's desks but retires none (booking and capacity queries must filter on the floor's `retired_on`).
- S6 Q146: `OfficeClock` reads new times at once although `settingsEffectiveFrom` is tomorrow. Booking lane must use the date-effective times (or store the deadline) so a same-day change cannot move today's release.
- S7 `DeskAccessGuard.tenantId()` reads `session.getCompanyID()`; `AuditContext.tenantId()` (used by people and the entity listener) is the one source. Use it.
- S8 Bean-validation field codes (`NOT_BLANK`, `SIZE`, `PATTERN`) are not in the contract (Q136); list them (api-designer).
- S9 `getDeskHistory` shows DESK rows only; the data model (4.5) says desk feature changes appear in the desk history (Q142). Acceptable for MVP, track it.

Frontend (frontend-developer unless noted)
- S10 Two contract copies now differ (`OfficeSummary` counts optional in Backend yaml, required in factory file); `deskbook.gen.ts` comes from the factory file, `generate-api` from the Backend file (Q137). Keep one source and drop the other generated file.
- S11 `/jobs` and `/settings` have no `requireRole('ADMIN')` route guard (the pages have their own in-page check, so no data leaks); use S6 forbidden for the same behaviour as `/admin` and `/reports`.
- S12 S2 grid is Mon-Fri only (05-ui) while office settings allow Saturday and Sunday as working days: a Saturday-working office cannot be booked in the UI. ux-designer to decide: limit settings to Mon-Fri for the MVP, or draw weekend columns when the office works them.
- S13 `getBooking(search.focus)` puts a URL value into the path without `encodeURIComponent` or a UUID check (`MyBookingsPage.tsx:144`); low risk (GET, same origin) but validate in `validateSearch`.
- S14 No label for `DUPLICATE`, `DESK_FLOOR_LOCKED`, `IF_MATCH_REQUIRED`, `validation.NOT_BLANK|SIZE|PATTERN`: the user sees the server's English text (`features/office/lib/errors.ts`).
- S15 `deskCardView` hides Hold and Check-in reasons from the browser clock (`nowMs`); with a skewed clock the button state differs from the server. Display is fine, but let `allowedActions` decide when the server lists the action.
- S16 Prettier was run over base and wave-1 files (build log); keep unrelated formatting out of the next diff so reviews stay small.
- S17 Component tests are impossible with the current vitest setup (environment node). Add jsdom and Testing Library before the test stage so the screens' states (M3) and the main journeys have a test (test-engineer).

## Open questions Q133-Q154 answered by the developers with their fallback

| Q | Verdict | Note |
|---|---|---|
| 133 | MUST | Contract paths without `/api/v1`: fix the contract (MUST 1); the FE call path is right. |
| 134 | Acceptable | Superseded by Q145. |
| 135 | Acceptable | Accessibility flag is R1 (reserved desks, ST accessibility list); no MVP story asks for it. |
| 136 | Acceptable | Fallback works; list the codes (S8). |
| 137 | Acceptable | Merge done; keep one contract source (S10). |
| 138 | Acceptable | Contract wins; fix the 05-ui text (ux-designer). |
| 139 | Acceptable | CLOSED is final (D6 item 4, Q84); fix the contract wording. |
| 140 | Acceptable | Column exists in V010 and the contract. |
| 141 | Acceptable | 200 chars; update data model 4.5. |
| 142 | Acceptable | MVP; see S9. |
| 143 | MUST | Built codes missing in the contract (MUST 2). |
| 144 | Acceptable | `DUPLICATE` works; name `SF_LOCATION_TAKEN` in the contract as part of MUST 2 or keep `DUPLICATE` and list it. |
| 145 | Acceptable | Make both fields required in the factory file (S10). |
| 146 | Acceptable | Only with S6 handed to the booking lane. |
| 147 | Acceptable | Admin write rate limit and `requireManagerOf` belong to later lanes; the rate limit must exist before release (05-security section 1 and 7). |
| 148 | Acceptable | Update data model section 12 numbering. |
| 149 | Acceptable | Inclusive horizon matches `PartOfDayRules.isWithinHorizon` and the FE "opens on"; confirm in 05-api-notes. |
| 150 | Acceptable | Late note after booking (S3 page) meets AC5.12; the S2 note is extra. |
| 151 | Acceptable | `nextTwoWeeks` starts today at the home office. A person with no home office or a closed office has no "today"; add `today` and `timezone` to `TodayView` when the contract is next touched. |
| 152 | MUST | Partial totals can be shown (MUST 5); fallback is right only with day totals from the server or the stop-gap. |
| 153 | Acceptable | Text without the time is correct; add `deadline` to the problems later. |
| 154 | Acceptable | Pages of 50 bound the DOM at 500 desks; free count later. |

## Definition of Done (this batch)

| Item | Result |
|---|---|
| M1 acceptance criteria | Checked for ST-OS-1..8, ST-EN-2, ST-PP-5 BE and the FE screens: met, except MUST 5 (S17 totals). |
| M2 no open blocker question | Not applicable to code review; none of Q133-Q154 is marked blocker. |
| M3 empty, loading, error, no-permission | Checked: present on all office, booking, reports screens; S6 pages exist; `/jobs` and `/settings` use in-page checks (S11). |
| M4 contract match | MUST 1 and 2. Operations, methods, request limits and If-Match otherwise match (29 routes). |
| M5 split | Checked: rules live in the backend; display-only date maths in the SPA (S12, S15, MUST 5). |
| M6 problem details | Checked: stable codes, no stack traces; 500 text is fixed. |
| M7 schema vs data model | Checked: V010 and V020 match 05-data-model, audit columns and version on every table; `MigrationMappingTest` ties entities to scripts. |
| M8 paged, no N+1 | Checked: all lists paged, grouped counts, four lookups per desk page. |
| M9 migration with rollback note | Checked: rollback note in both scripts. |
| M10 authorization and tenant isolation | Authorization checked (guard first in every service, 401/403 tested for all 28 ops). Tenant isolation untested: MUST 3. |
| M11 secrets, personal data | Checked: no log statements in the new code; employee name, email and person id are `@AuditMasked`; `getMyProfile` returns only the caller. |
| M12 input validation | Checked: closed schemas (`ignoreUnknown=false`), patterns, sizes, IANA timezone, allow-listed sort. Minor S4. |
| M13 tests | BE and FE unit and contract tests exist; DB-level and E2E missing (MUST 3, S17). |
| M14 conventions | Checked: B9 layout and naming followed; small functions. |
| M15 text, tokens, focus | One missing key (MUST 4). No fixed colours or shadows found in the reviewed folders; en-GB/de/es/fr carry English text for the new keys (known). |
| M16 request id, jobs | Request id filter and `traceId` in problems present; background job not in this batch. |


---

## Batch 2 (wave 2-3 backend, fix re-check)

Reviewer: code-reviewer. Date: 29 Oct 2026. Product `D:/products/desk-booking`. Read-only; nothing was built or run (a QA agent runs the tests), so test results are taken from the build log (BE 611, FE 177 tests, 0 failures).

Scope read in full: every guard and authorization path (`DeskAccessGuard`, `BookingService`, `BookingQueryService`, `BookingBatchService`, `DeskProposalService`, `TodayService`, `BookingRulesService`, `CheckInService`, `OccupancyReportService`, `OccupancyExportService`, both controllers of booking, check-in, reports) and every repository query of booking, notification, people sync runs, employee, desk, zone, closed day, plus V030, V050, V060, V061, V062. Read fully: `BookingCommandService`, release job and runner, `EmployeeLeftListener`, `OfficeSettingsListener`, `OfficeClock`, `Office.applySettings`, the people sync (runner, store, source, job, leaver handler), the notification module (dispatch runner, policy, store, outbox, reminder runner, templates, adapters, jobs), the three purge jobs. Sampled: `OccupancyCalculator`, `BookingAssembler`, `BookingStatsQuery`, tests by name (72 test files), frontend guards, locale keys, job registry, contract diff (script `cr2_contract_diff.py` in the scratchpad compares both contract copies structurally). Not read line by line: `PartOfDayRules` (wave 1), `DeskProposalRules`, the frontend screens of wave 3.

## Verdict: FAIL (1 MUST)

The wave 2-3 backend is in good shape. Every booking, check-in, report and rules operation calls the guard as the first line of its service; own-record reads use `findOwn` (another person's id is 404, admin included); every query filters tenant and `deleted_at`; lists are paged or bounded; uniqueness lives in the database (ADR-2 indexes in V030) and is mapped by constraint name; the release job is versioned so check-in wins; the outbox is written in the release transaction with a unique event key; mail addresses and bodies are never logged; the people sync fetches first, applies in one transaction, refuses a bad set (drop guard) and keeps the last good copy. All five batch 1 MUSTs are closed. One design requirement is not built at all: the abuse limits of 05-security section 7 (rate limits answering 429).

## MUST

| # | Where | Problem | Fix | Owner | DoD |
|---|---|---|---|---|---|
| 1 | no code in `booking`, `checkin`, `reports`, `office` controllers or a filter; `05-openapi.yaml` lists 429 on `createBooking`, `createBookings`, `checkIn`, `listFreeDesks`, `proposeDesks`; `BookingService.requireKey` (line 40-45) | 05-security section 7 and tests 7, 13, 14 are not built: no per-user rate limit (createBooking 10/min, cancel/checkIn/hold 20/min, listFreeDesks 30/min, proposeDesks 20/min, createBookings 3/min and 30 booking-days/min, getOccupancyReport 10/min, exportReport 5/min, admin writes 60/min), so `429 RATE_LIMITED` with `Retry-After` can never be answered (grep for `RATE_LIMITED` finds only the contract); no 16 KB body limit; an Idempotency-Key may contain `:` (test 13 asks to refuse it), so a single-day key `K:2026-11-03` can replay a batch day booked with key `K` (same person only). Batch 1 (Q147) already said this must exist before release. | Add one in-memory per-user limiter (Caffeine, as 05-security 7 says) called from the services right after the guard, answering `RATE_LIMITED` 429 + `Retry-After`; check the batch day budget before the first booking so there is no partial batch; set the body size limit; allow-list the key (`[A-Za-z0-9_-]{1,64}`); add tests 7, 13, 14. | backend-developer (test: test-engineer) | M12, M4 |

## SHOULD (quality and release risks, not blocking)

Backend (backend-developer unless noted)
- B2-S1 `BookingCommandService.hold` (line 254) and `BookingAssembler.holdAvailable` accept and offer "Running late" for a booking dated days ahead (no window check, only "before the deadline"); the once-only hold is then spent and the day itself has none. The design text allows it (05-security row 9), the intent (ST-CI-7, "on my way") does not. Require `now >= checkInOpensAt` (the check-in window). Product-owner to confirm.
- B2-S2 A double submit with the same Idempotency-Key at the same moment answers 409 `ALREADY_BOOKED_THAT_DAY` (the employee-day index fires before the idempotency index, `translate` line 321), not the first booking; `REQUEST_IN_PROGRESS` is then rarely reached and is not in the contract. On either violation re-read by key and replay.
- B2-S3 The double-booking guarantee (V030 partial unique indexes, constraint-name mapping) and the Flyway run itself have never run on PostgreSQL: the H2 mode rebuilds 12 indexes as key columns and skips V002 (Q158, Q165). Add one Testcontainers class (two parallel creates, two bookings one day, V001-V062 applied) in CI before release (test-engineer).
- B2-S4 `OfficeSettingsListener` (`findForRecompute`) loads every BOOKED booking of the office from the effective day inside the admin's request, up to about 60,000 entities (500 desks x 60 days x 2). Chunk it or use a bulk JPQL update that sets the deadline.
- B2-S5 `ReleaseBookingsRunner`: the same 200 oldest due rows are re-read each loop; if 200 poison bookings fail every minute, newer due bookings starve. Page past the `seen` rows.
- B2-S6 `TtCommonMailAdapter.classify(null)` counts as sent: the base `SendEmail.sendMail` returns `e.getMessage()`, which is null for an exception without a message, and success is `""`. Treat null as a transient failure.
- B2-S7 Go-live switches (devops-engineer with backend-developer): default `DESKBOOK_MAIL_MODE` LOG_ONLY marks rows SENT and nobody is mailed; `DESKBOOK_APP_BASE_URL` falls back to `https://deskbook.example` silently, so LIVE mails would carry dead links. Add a warning line in the dispatch job result when the mode is LOG_ONLY or the URL is the placeholder, and put both, plus the seven job schedules (ReleaseBookings and the two mail jobs MINUTE, PeopleSync HOURLY, three purges DAILY) in the release checklist; nothing schedules them.
- B2-S8 The first LIVE send is unproven (base sender has no timeouts, one SMTP connection per mail, Q176): measure one send on dev and the circuit breaker before the switch.
- B2-S9 Report: no small-cell rule exists, so a floor with 1-2 desks shows one person's attendance (05-security threat on heat grids, row 45 says "same small-cell rule", Q114 open); the xlsx cells are string-typed (not evaluated) but the apostrophe prefix of row 45 is not done. Product-owner to set the threshold, security-architect to restate row 45 as built or backend-developer to add the prefix.
- B2-S10 `OfficeQueryService.evictDeskCache` has no caller although its comment says desk, floor and zone changes call it (Q156); a new or retired desk shows for up to 60 s per node. Call it after commit in the three services, or fix the comment.
- B2-S11 `PeopleSyncRunner.fetchAll` stops at the first page shorter than 200; if SuccessFactors caps a page lower than `$top`, the read ends early and only the 10 percent drop guard protects. End on an empty page. Check on the tenant sample (Q167; integration-engineer).
- B2-S12 `OccupancyCalculator` uses the office's current working days for every past day, ignoring the earlier times of V062; a working-day change shifts old capacity. Small; use `previousDayTimes` for dates before `settingsEffectiveFrom`.
- B2-S13 Tests (test-engineer): own-record tests exist for cancel only; add `checkIn`, `hold`, `getBooking` of another person (05-security test 2), a role matrix row for `exportReport` rate limit, and the Spring wiring is only a smoke test. Component tests and one end-to-end test per main journey (batch 1 S17, M13) are still missing; they are the test stage's job.
- B2-S14 Contract (api-designer, backend-developer): the Backend `openapi.yaml` differs again from `05-openapi.yaml`: five operations (`createDesk`, `createFloor`, `createZone`, `getOccupancyReport`, `exportReport`) lack the named 400 answers with the OFFICE_CLOSED, FLOOR_RETIRED, EXPORT_TOO_LARGE descriptions and examples (status and schemas are equal, checked by `cr2_contract_diff.py`); the codes `REQUEST_IN_PROGRESS`, `CONFIGURATION_NOT_SAVED` and `INVALID_SORT` are in no contract copy. Copy the factory file in the build step (one source) and list the three codes.
- B2-S15 Docs to update (data-architect): 05-data-model 4.10 (V061: EXPIRED, SKIPPED, `booking_id`, `last_error_code`), 4.2 (V062 four `prev_*` columns), 4.6 (V050 `leaver_handled_at`), ADR note that V004 stays (Q173). `README.md` of the product still lists the `projects` package.
- B2-S16 Mail is at-least-once: a crash between the send and the outcome write repeats the mail after the 5 minute lease (documented in 05-integrations 2.3); accepted.

Frontend (frontend-developer unless noted)
- B2-S17 Batch 1 S12 (weekend columns, ux-designer decision) and S17 (jsdom and Testing Library) are open; Prettier changed line endings of `AppToast.tsx`, `RouterLinks.tsx`, `TestConnectionResultDialog.tsx` (build log), keep unrelated changes out of the diff; the label group `dashboard.*` is unused.
- B2-S18 `deskCardView` offers Running late for any BOOKED booking with `holdAvailable`; follows B2-S1 once the server limits it, check S4 rows then.

## Batch 1 MUST re-check

| Batch 1 | Closed? | Evidence |
|---|---|---|
| 1 contract paths without `/api/v1` | Closed | Both contract copies have 46 paths under `/api/v1` (test: `ContractFile`, four contract tests compare the full path, no prefix stripping); `deskbook.gen.ts` regenerated from the Backend copy; FE `contract.test.ts` checks every API call against the generated path keys. Residual copy drift: B2-S14. |
| 2 built answers missing in the contract | Closed | `05-openapi.yaml` and the Backend copy list 422 on `updateOffice` and `updateDesk`, `DUPLICATE` 409, `DESK_FLOOR_LOCKED`, `HAS_FUTURE_BOOKINGS`, plus the wave 3 codes (FLOOR_RETIRED, OFFICE_CLOSED, EXPORT_TOO_LARGE, RANGE_TOO_LONG, NOT_FOUND); the FE maps them. |
| 3 no repository or tenant isolation test | Closed, with a limit | 46 repository tests (office 21, people 5, booking 14, stats 6) run every query for two tenants with identical names and dates on H2 in PostgreSQL mode, plus real unique violations; mutation check reported. The limit (no real PostgreSQL, no concurrency) is B2-S3. |
| 4 `checkin.desk.label` missing | Closed | Present in en, en-GB, de, es, fr; the locale parity test covers it. |
| 5 report totals summed in the SPA | Closed | `OccupancyReportService` returns `dayTotals` (server, whole filter, all floors) and the export uses the same load; `report.ts` `groupByDay(rows, dayTotals)` shows them, `sumRows` is gone. |

Batch 1 SHOULD status: S1 closed (`FeatureDefaultsSeeder`, own transaction, race tolerant); S2 closed (adapter deleted, `BookingImpactWiringTest`, `BookingImpactAdapter` is the only port); S3 mostly closed (`create` re-reads office open and desk bookable inside its transaction; closing an office still reads the count and writes without a lock, a small write-skew window remains); S4 closed (`@Size(max = 20)`, DUPLICATE); S5 closed (FLOOR_RETIRED, OFFICE_CLOSED); S6 closed (V062, `OfficeClock.timesOn`, tests with mutation check; `applySettings` keeps the oldest earlier times on a second same-day change, checked); S7 open (Q163, accepted); S8 open (field codes still not in the contract, B2-S14); S9 tracked; S10 partly (one generated file now, copies drift again); S11, S13, S14, S15 closed; S12, S17 open; S16 mostly.

## Developers' fallback answers Q155-Q179

| Q | Verdict | Note |
|---|---|---|
| 155 | Acceptable | Registered; the schedule is entered by hand (B2-S7). |
| 156 | Acceptable | Cache plus one occupied read is fine; booking write re-checks the desk. Eviction never called (B2-S10). |
| 157 | Acceptable | Status and the database version decide; matches AC8.4 and the tests. |
| 158 | Acceptable | Only if B2-S3 is done before release. |
| 159 | Acceptable | Answered and in the contract. |
| 160 | Acceptable | Answered and in the contract. |
| 161 | Acceptable | Product-owner to confirm; calculator-only change. |
| 162 | Acceptable | Fresh deployments only; note for upgrade of existing tenants. |
| 163 | Acceptable | Same value in production; do with the test base sweep. |
| 164 | Acceptable | Superseded by V062 (done). |
| 165 | Acceptable | Honest scope statement; see B2-S3. |
| 166 | Acceptable | Good catch; `Notification.bookingId` already has the converter; add to the backend checklist. |
| 167 | Acceptable | Needs the tenant sample; second `PeopleSource` is ready as a plan (B2-S11). |
| 168 | Acceptable | Run now needs one live proof on dev. |
| 169 | Acceptable | No code until the sample. |
| 170 | Acceptable | Keep 10 percent; fix 05-security text. |
| 171 | Acceptable | Decide with S18. |
| 172 | Acceptable | Closed; the five class names exist exactly as registered. |
| 173 | Acceptable | Right call (never change an applied script). |
| 174 | Acceptable | Update the data model (B2-S15). |
| 175 | Acceptable | Update the data model; length 60 fits the 56 characters needed. |
| 176 | Acceptable | Measure on dev (B2-S8). |
| 177 | Acceptable | Placeholders only; see B2-S7. |
| 178 | Acceptable | Fine at today's volume. |
| 179 | Acceptable | Q78 as recommended. |

No Q155-Q179 answer is a MUST.

## Definition of Done (batch 2)

| Item | Result |
|---|---|
| M1 acceptance criteria | Checked by sampling against ST-BK-1,5-12,15, ST-CI-1,4-7, ST-PP-1-4, ST-NT-1-3, ST-RP-1-4, ST-OS-9, ST-EN-1: met in code and tests; two notes (B2-S1 hold window, B2-S2 double submit). |
| M2 no open blocker question | None of Q155-Q179 is marked blocker. |
| M3 states | Not re-reviewed screen by screen; wave 3 frontend only touched error labels and the job registry; `/jobs`, `/settings` now guarded (batch 1 S11 closed). |
| M4 contract match | Operations, methods, statuses and schemas match (14 booking routes, 2 report routes, 28 office routes tested against the contract). Not met: 429 never answered (MUST 1); copy drift and three unlisted codes (B2-S14). |
| M5 split | Checked: rules in the backend (window, deadline, hold, drop guard, totals); the FE uses `allowedActions`, `holdAvailable`, `dayTotals`; MUST 5 of batch 1 closed. |
| M6 problem details | Checked: stable codes with `currentStatus`, `opensAt`, `deadline`, `existingBookingId`; job results carry codes only. `CONFIGURATION_NOT_SAVED` and `REQUEST_IN_PROGRESS` unlisted (B2-S14). |
| M7 schema vs data model | Checked: V030 matches 4.8 and 4.9 (checks, FKs, three ADR-2 indexes); V050, V061, V062 are recorded deviations (B2-S15); audit opt-outs for slots, outbox and runs are documented; V060 drops the demo tables. |
| M8 paged, no N+1 | Checked: free desks, bookings, reports, mail dispatch (batched lookups), reminder (pages of 500). Not bounded: `findForRecompute` (B2-S4), `findAllLive` of the people copy (designed, 5,500 rows, job only). |
| M9 migration with rollback note | Checked: V030, V050, V060, V061, V062 each carry a rollback note; no applied script was changed. |
| M10 authorization and tenant isolation | Checked: guard first in every service; own-record 404; admin-only rules and reports; employee `getToday` has no banner key (NON_NULL). Tenant isolation now tested (batch 1 MUST 3 closed). Own-record tests for check-in and hold: B2-S13. |
| M11 secrets, personal data | Checked: no secrets (placeholders, `<set-in-env>`); no address, name or body in logs, `MailMessage.toString` hides the address, the sync never logs the exception; only user ids appear in two log lines and the job result. |
| M12 input validation | Not met: MUST 1 (rate limit, body size, key charset). Otherwise checked: closed bodies, sizes, date and range checks, allow-listed sort, escaped mail HTML. |
| M13 tests | 611 BE and 177 FE tests reported passing (not run here); rules, services, repositories, jobs, contract tests exist; real PostgreSQL, component and end-to-end tests missing (B2-S3, B2-S13), they belong to the test stage. |
| M14 conventions | Checked: B9 layout and naming, ports and adapters, small classes; minor items B2-S17. |
| M15 text, tokens, focus | Checked: English key set complete, `deskbook.mail.*` in `messages.properties`, no fixed colours in the changed folders; de, es, fr carry English for some new keys (known). |
| M16 request id, jobs | Checked: all seven jobs record counts and errors and set FAILED on an exception; request id in problems; jobs have no guard by design (the scheduler is admin-run). |


## S7 re-check

Reviewer: code-reviewer. Date: 29 Oct 2026. Product `D:/products/desk-booking`. Read-only: nothing was built or run (a QA agent runs Maven); test counts are the build log's (714 backend, 215 frontend). Read for this check: `common/ratelimit/*`, `common/web/RequestBodyLimitFilter`, `GlobalExceptionHandler`, `DeskAccessGuard`, every `guard.require*` call site, `BookingService`, `BookingBatchService`, `BookingCommandService`, `CheckInService`, `OfficeSettingsListener`, `DeadlineRecomputeStore` and its two queries, `RecomputeExecutorConfig`, `MailSettings`, `NotificationDispatchRunner`, `approuter/xs-app.json` (regexes run with `rc_routes.py`), `PeopleMapper`, `PeopleSyncRunner`, `PeopleSyncStore`, `Employee.applySuccessFactors`, `DeskProposalRules`, `DeskProposalService`, the booking contract (factory file and Backend copy), and the frontend `plan.ts`, `DeskProposalRow.tsx`, `PlanPage.tsx`, `en.json`. All paths below are under `Backend/src/main/java/com/talenteam/deskbook/` unless they start with `approuter/`, `Frontend/` or `Backend/src/test`.

### Verdict per item

| Item | Source | Verdict | Evidence |
|---|---|---|---|
| Rate limits: per-user limits, 429 `RATE_LIMITED` + `Retry-After` | 07-code-review Batch 2 MUST 1 | CLOSED | `common/ratelimit/RateRule.java:9-19` has all 11 rules with the 05-security numbers (create 10, cancel/check-in/hold 20, free desks 30, propose 20, batch 3, booking-days 30, report 10, export 5, admin write 60). Counted right after the role check in `access/service/DeskAccessGuard.java:80-103` (`requireEmployee(rule)`, `requireAdminWrite()`, `requireAdmin(rule)`, `charge`). Call sites: `BookingService.java:94` (createBooking 10 + 1 day), `:148` cancel, `CheckInService.java:48,53,60` check-in and hold, `BookingQueryService.java:120`, `DeskProposalService.java:79`, `OccupancyReportService.java:64`, `OccupancyExportService.java:58`, and all 19 office-setup and rules writes use `requireAdminWrite()`. Batch: `BookingBatchService.java:84-85` charges 1 request and N booking-days before the first day is booked; `RateLimiter.hit` (lines 73-105) checks every charge first and counts none unless all fit, so no partial batch and a refused call counts nothing. 429 with the `Retry-After` header and the `retryAfter` member: `GlobalExceptionHandler.java:72-76`. Contract lists `429` on 29 operations (`Backend/src/main/resources/openapi/openapi.yaml`). Tests: `RateLimiterTest` (8), `RateLimitAndBodyLimitHttpTest` (4), `DeskAccessGuardTest` +3. |
| 16 KB body limit | Batch 2 MUST 1 | CLOSED | `common/web/RequestBodyLimitFilter.java:44-62`: POST/PUT/PATCH under `/api/v1/`, refused by Content-Length and again while the stream is read (counting wrapper, lines 112-170, so chunked bodies and a lying header are cut); multipart excluded; answer 400 `PAYLOAD_TOO_LARGE` (the contract has no 413, Q209). The read-time exception is mapped in `GlobalExceptionHandler.java:107-113` through the cause chain. Runs after `RequestIdFilter` (`HIGHEST_PRECEDENCE` against `+10`), so `traceId` is present. Tests: exactly 16 KB passes, one byte more is refused, no Content-Length is cut off. |
| Idempotency-Key pattern | Batch 2 MUST 1 | CLOSED | `BookingService.java:72` `KEY_PATTERN = [A-Za-z0-9_-]{1,64}`, checked in `requireKey` (lines 84-87) before any rate charge or write, 400 `INVALID_FORMAT`. A `:` can no longer be in a key, so the batch day key `key:date` (`BookingBatchService.java:95`) cannot equal a single-day key: the replay hole is shut. The 16-character minimum of 05-security 4.2a is not applied (Q210, known deviation, not a defect: the key is scoped to the person). |
| PB-1 settings recompute off the request | 07-performance PB-1 | CLOSED | `booking/listener/OfficeSettingsListener.java:55-56` is `@Async("deskbookRecomputeExecutor")` + `@TransactionalEventListener(AFTER_COMMIT, fallbackExecution = true)`; `OfficeService.updateSettings` (`office/service/OfficeService.java:206`) only publishes the event and returns. One thread, queue 50, `CallerRuns` when full (`RecomputeExecutorConfig.java:18-25`): bounded, never lost. Work is one date at a time in pages of 500, each page its own `REQUIRES_NEW` transaction (`DeadlineRecomputeStore.java:51-72`), so a cancel or create waits for at most 500 rows; 3 tries per page, ERROR log with the office id. Tenant is set on the async thread (`:58-72`) and `AuditContext.tenantId()` falls back to `TenantHelper`, so `clockFor` and the two queries (both filter tenant and `deleted_at`, `BookingRepository.java:98-107`) work. Accepted risk: no stored pending marker (Q211). See SHOULD N1. |
| PB-2 mail at least 300 a minute | 07-performance PB-2 | CLOSED (design); real figure still to be timed on dev | `notification/service/MailSettings.java:23,49-51`: 10 workers by default (limit 16), cap 600 a minute, so workers x 50 s / seconds per mail = 333 a minute at 1.5 s, 500 at 1.0 s; `MailSettingsTest.java:34-35` asserts that at 1.5 s the default still gives 300. `NotificationDispatchRunner.java:124-157` runs a fixed pool, chunks of workers x 5, reads the clock between chunks, and logs mails a minute and seconds per mail on every run (also in the job result). Null from the base sender is a transient failure; LIVE mode with the placeholder base URL sends nothing (`:136-141`). The measurement of Q176 (10 sequential and 10 parallel real sends) is a dev test step, not a code defect. See SHOULD N2. |
| System M1 rate limits | 07-system-review M1 | CLOSED | Same evidence as the first row. The SPA already maps `RATE_LIMITED`; the contract now lists 429 and the `TooManyRequests` response. |
| System M2 journey and PostgreSQL proof | 07-system-review M2 | OPEN for dev (no code defect) | Nothing in this repo has run on PostgreSQL: no Testcontainers or embedded PostgreSQL in `Backend/pom.xml` or `Backend/src/test`. Offline proof that exists: `DeskBookAcceptanceFlowTest` (24 tests, services end to end with two tenants), `DeskBookBatchRaceTest` (5), `SpringContextSmokeTest` (10, real beans and the TTCommon stubs), 40+ repository tests, all on H2 in PostgreSQL mode with V010-V062 rebuilt by `H2Schema` (pinned by `H2SchemaTest`). The pre-audit deadlock work added real evidence: the race test failed 5 of 10 runs, the cause was proven, and it passes 10 of 10 after the fix. What offline proof cannot show: V002 partitions and PL/pgSQL, the partial unique indexes as written in SQL (the tests use generated key columns), and the constraint names in a real PostgreSQL exception text (`BookingCommandService.translate` matches by name, plus now by SQLState). Needed on dev: run Flyway V001-V062; two-session races (same desk, same person and day, same key); one scripted run each of J1, J2, J4, J5. Owner qa-engineer and devops-engineer. |
| System M3 approuter fallback | 07-system-review M3 | CLOSED (regexes proven offline; two checks need dev) | `approuter/xs-app.json` routes 4-6: `/assets/**` from `resources`, any path with a file extension from `resources` (a missing file stays 404), and route 6 `^/(?!(?:deskbook|api|webservices)(?:[/?]|$))[^.?]*(?:\?.*)?$` answers `/index.html` with no-cache. I ran all routes in order against 14 URLs (`rc_routes.py`): `/bookings?focus=<uuid>&action=hold`, `/book`, `/`, `/admin/offices`, `/no-access` and `/reports?from=2026.10.01` give `index.html`; `/assets/index-abc.js` and `/favicon.svg` give the file; `/bookings/missing.png` stays a file 404; `/deskbook/api/v1/me` and `/deskbook/api/public/health` reach the destination; `/api/x` and `/deskbook` match nothing. Vite `base` is the default `/`, so asset URLs match route 4. Still to see on dev (check C1 of 05-ops): that `localDir` with target `/index.html` serves the file, and that the query string survives the XSUAA login redirect. |
| SF M1 missing fields never wipe stored values; `FIELDS_MISSING` | 07-sf-review M1 | CLOSED | `people/service/PeopleMapper.java:125-163`: with 20 or more active rows, `FIELDS_MISSING` when no row has a manager or none a location (`:152`), and the person id the same way. The person id check needs the stored copy and is in `PeopleSyncStore.java:186-190` (only when a known SF person has one, so a tenant without Employee Central is not refused forever); the runner calls `checkFetched(rows, false)` (`PeopleSyncRunner.java:144`) so the id is not checked twice. Nothing is written before either refusal. Below 20 active rows the guard does not refuse, but `Employee.applySuccessFactors` (`people/domain/Employee.java:97-126`) with the three `*Present` flags from `PeopleMapper.fieldsPresent` (`PeopleSyncStore.java:142,241-242`) keeps the stored value of a field no row carries, while a field the read does carry is written as is (a removed manager is still removed). Tests: one per field in `PeopleMapperTest`, five in `PeopleSyncStoreTest`, two in `PeopleSyncRunnerTest`, each guard mutation-checked by the developer. |
| SF M2 inactive users with no row not stored | 07-sf-review M2 | CLOSED | `PeopleSyncStore.java:203-209`: a person that arrives `f` and has no row is only counted (`inactiveNotCopied`), not inserted, not in `skippedNoEmail`, not in the 500-entry skipped list; the job text carries "old leavers not copied N". A known person turning `f` is still a leaver (`:244-249`), and a pre-hire `f` that later becomes `t` is inserted as a new person (`:210-221`). The drop guard is unaffected (it counts only known active SF rows, `:166-185`). |
| AC19.5 NO_MATCH alternatives, backend | 07-test-report FAIL ST-BK-8 c3 | CLOSED | `booking/service/DeskProposalService.java:106-118` answers `NO_MATCH` when desks are free but none fits (`NOTHING_FREE` only when nothing is free), and `noMatch` (`:143-168`) fills `alternatives` from the pure `booking/rules/DeskProposalRules.alternatives` (`:128-178`): usual desk, nearest zone, other zone, without one feature, then any free desk when nothing else, one desk per zone or dropped feature, never the same desk twice, at most 3, never empty while a desk is free. Contract: `DeskProposal.noneReason` NO_MATCH, `alternatives` 1-3, `DeskAlternative` with `reason` and `missingFeature` in both the factory file (line 6954-6995) and the Backend copy (6909-6950). Tests: `DeskProposalRulesTest` +5, `BookingBatchAndProposalTest` +10. |
| AC19.5 NO_MATCH alternatives, frontend | 07-test-report FAIL ST-BK-8 c3 | CLOSED | `Frontend/src/features/booking/lib/plan.ts:171-180` keeps up to 3 alternatives for NO_MATCH only; `noneTextKey` gives one text per reason (`:183-196`); `DeskProposalRow.tsx:92-130` lists each with code, reason and place and a Choose button (40 px target, aria label); a tap sets her choice (`plan.ts pickAlternative`, `PlanPage.tsx:463-464`), `planRows` shows it as `YOUR_CHOICE`, and `toBatchItems` sends it as `CHOSEN`, so the server does not re-pick it. Labels `booking.plan.noMatch` and `booking.alt.*` exist (`en.json:782,823-827`); `plan.test.ts` covers it. |
| Pre-audit deadlock: ordering | 06-build-log "Pre-audit fixes" 3 | CLOSED | `booking/service/BookingCommandService.java:121-133`: the booking row is saved and flushed, then one slot per half, always morning first, flushed one by one (`PartOfDay.halves()` is `List.of(MORNING, AFTERNOON)` for a full day, `common/time/PartOfDay.java:11-13`). With one fixed order, two people on the same desk can only wait on the same first row, never on each other, so the second gets the unique violation (`DESK_JUST_TAKEN`). I also walked the other lock orders: same person twice waits on the booking row before any slot; cancel and release both lock the booking row first. No cycle found. |
| Pre-audit deadlock: SQLState mapping to 409 | 06-build-log "Pre-audit fixes" 3 | CLOSED | `BookingCommandService.java:286-309` `translate`: constraint names in the cause chain win first (slot unique gives `DESK_JUST_TAKEN`, employee-day gives `ALREADY_BOOKED_THAT_DAY`, idempotency gives `REQUEST_IN_PROGRESS`); then any `SQLException` in the chain with SQLState `55P03`, `40P01`, `50200` or `40001` (`:48-49`) gives the retryable 409 `REQUEST_IN_PROGRESS` (already in the contract for createBooking); anything else is rethrown untouched. The `catch (RuntimeException)` at `:131` wraps both inserts, and the batch day handler (`BookingBatchService.java:114-131`) turns it into that day's failure or the first booking via `replayOf`. Test `aLockTimeoutBecomesTheRetryable409AndAUniqueViolationStillWins` checks the four states, the precedence and the rethrow. |
| Pre-audit deadlock: `createBookings` shares the fixed path | 06-build-log "Pre-audit fixes" open item | CLOSED | `BookingBatchService` has no `@Transactional`; each day calls `commands.create(...)` (`:113`), the same method with its own transaction and the same ordered inserts. Days are sorted by date (`:86`), and a day never holds locks across days, so two concurrent batches cannot form a cycle between days. A concurrency test for `createBatch` is still welcome (test-engineer, SHOULD N3). |

### Fix rounds: new findings

I read the changed files, guards and queries of "Fix round S7" (frontend, backend, integration) and "Pre-audit fixes" for new defects. No new MUST. Checked and fine: every new or changed query filters tenant and `deleted_at`; the stats cache key and the desk cache key both start with the tenant; the new guards keep the guard first and the limiter second; the body-limit filter is limited to `/api/v1`; no secret, address or body is logged (the rate limiter logs one startup line; `DESKBOOK_*` keys are listed by name only); the contract copies were replaced as a whole and the theme paths kept; hold now needs the open check-in window in both the service (`BookingCommandService.java:216-221`) and the "Running late" offer (`BookingAssembler.java:66-72`), so the button and the rule agree, and the contract says so (422 `CHECK_IN_NOT_OPEN`).

SHOULD (quality, not blocking; owner backend-developer unless noted):
- N1 `DeadlineRecomputeStore.recomputeChunk` pages by offset over `status = BOOKED` (`BookingRepository.java:104-107`, `PageRequest.of(page, CHUNK)`). A booking cancelled between two pages of the same date shifts the rest up, and one row can be skipped and keep its old deadline. Only offices with more than 500 bookings on a date, and a cancel during the few seconds of the run; the fix is keyset paging (`id > lastId`, same order) instead of an offset. The ERROR-log and "save again" repair does not help because nobody sees the skipped row.
- N2 `NotificationDispatchRunner.sendChunk` waits with `futures.get()` and no timeout (`:336`). If the base SMTP call hangs (the base jar's socket timeout was not checked here), the run overruns its 50 s budget and the minute job stays busy. Use `get(timeout)` per chunk and treat a timeout as a transient failure. Devops to confirm the base mail timeouts on dev (Q176).
- N3 Rate limits count per instance; `manifest.yml:8` runs 2 backend instances while the limiter's start log and Javadoc say "one instance today". The design accepts approximate limits (05-security 7), but the effective ceiling is up to twice the table (for example 60 booking-days a minute). Correct the log line, and say it in 05-ops. Also add the concurrency test for `createBatch` named above (test-engineer).
- N4 Still open from before and not part of this re-check: batch 2 SHOULDs B2-S5 and PB-7 (export semaphore) were not touched, PB-3 not done (Q182), `Employee.markLeftAlreadyHandled` is now unused (dead code, `people/domain/Employee.java`).

### Definition of Done after the re-check

| DoD item | State |
|---|---|
| M4 contract match | Met: 429 on the 29 operations, NO_MATCH and `alternatives`, key pattern, `CHECK_IN_NOT_OPEN`, `PAYLOAD_TOO_LARGE` are in both contract copies; the Backend copy equals the factory file apart from the kept base theme parts. Unlisted codes still tracked in Q209. |
| M10 authorization, tenant isolation | Met (guard first, then limiter; tenant on every new query and cache key). |
| M12 input validation | Met: rate limits, 16 KB body limit and key allow-list are built and tested. |
| M13 tests | Met for rules and services (714 backend, 215 frontend reported passing, not run here). Real PostgreSQL, component and end-to-end tests are still system review M2, owned by the test stage. |
| M16 request id, jobs | Met (request id on the new 400 and 429 problems; recompute and mail runs log counts and rates). |
