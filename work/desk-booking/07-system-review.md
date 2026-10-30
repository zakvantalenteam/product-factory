# System review (build mode) - DeskBook

Reviewer: system-reviewer. Date: 29 Oct 2026. Product `D:/products/desk-booking` (Backend `com.talenteam.deskbook`, Frontend `src`). Read-only: nothing was built or run here; QA runs the tests. Read: `03-journeys.md`, `04-backlog.csv`, `05-api-notes.md`, `05-architecture.md` (module rule, jobs), `05-openapi.yaml` (Grep and script only), `06-build-log.md`, `07-code-review.md`, `decisions.md`, `questions.md`, the controllers, services, DTOs, migrations, mail templates, route and label files named below.

## Verdict: FAIL (3 MUST)

The parts fit well. All 45 MVP operations in `05-openapi.yaml` have a controller route and a role check, the 47 response records match the contract field for field (checked by script: only `usualDesk`, which is R1, is absent), all enums and states agree between contract, Java and the SPA, every label key the SPA uses exists in all 5 locale files (770 keys each), and the DeskBook paths, query parameters, headers (If-Match, Idempotency-Key) and problem codes of the journeys line up. The three MUSTs are not wrong seams but missing proof or missing built parts: the designed rate limits, no run of the whole system, and the e-mail link entry point.

| # | Finding | Sev | Owner |
|---|---|---|---|
| M1 | Rate limits are designed, contracted and mapped in the SPA, but not built | MUST | backend-developer |
| M2 | No end-to-end proof of any main journey; the database scripts never ran on PostgreSQL | MUST | qa-engineer (test-engineer), devops-engineer for a dev environment |
| M3 | The e-mail links open client routes (`/bookings?focus=...`, `/book`) and the approuter has no fallback for them | MUST (prove on dev, then fix) | devops-engineer |
| S1-S13 | See section 3 | SHOULD | various |

## 1. Journey traces (screen -> API -> controller -> service -> repository -> table, and back)

Legend: OK = fits; the finding number follows when something does not.

### J1 Find and book, including Plan my days (ST-BK-1, 5-8, 11-15; S1, S2, S3, S4)
| Step | Screen / SPA | API (contract path) | Controller -> service | Repository -> table | Fit |
|---|---|---|---|---|---|
| Open S2 | `PlanPage`, `bookingApi.listBookableOffices` | `GET /api/v1/bookable-offices` | `BookingController` -> `BookingQueryService.listBookableOffices` -> `OfficeQueryService` (Caffeine 60 s) | `OfficeRepository` -> `ofc_offices` | OK |
| Pickers, day grid, zone and chips | `DayPickerGrid`, "More choices" | `GET /bookable-offices/{id}/calendar` (`zones[]`, `features[]`, `days[].parts[].reason`, `late`, `lateCheckInMinutes`) | `BookingQueryService.getCalendar` -> `OfficeClockService.assess`/`closedDays`, `PartOfDayRules` | `ClosedDayRepository` -> `ofc_closed_days`; zones and features from the cached desk list (`ofc_zones`, `ofc_features`) | OK. Grid is Mon-Fri only while office settings accept Sat/Sun (S3) |
| Proposal per day | `proposeDesks` (dates comma separated, debounce 400 ms), `DeskProposalRow` | `GET /desk-proposals` | `DeskProposalService.propose` -> `DeskProposalRules.pick` (usual desk, same zone, matches choices, first free) | `BookingRepository` (index-only occupied read, booked dates, 60-day usual desk) -> `bkg_bookings`; desks from cache | OK. SPA ignores `noneReason` (S4) |
| Change a desk | `ChooseDeskDialog`, pages of 50 | `GET /free-desks` (office, date, part, page, size) | `BookingQueryService.listFreeDesks` | cached active desks minus occupied read | OK |
| Book N days | `createBookings`, one Idempotency-Key per press, items `{date, part, deskId, source PROPOSED or CHOSEN}` | `POST /bookings/batch` | `BookingController` -> `BookingBatchService` -> `BookingCommandService.create` per day (own transaction, re-pick up to 2 for PROPOSED) | `BookingRepository.saveAndFlush` -> `bkg_bookings`; `BookingSlotRepository` -> `bkg_booking_slots`; races map by constraint name (`uq_bkg_booking_slots_desk_date_half`, `uq_bkg_bookings_employee_date`, `uq_bkg_bookings_idempotency`) | OK on paper. Constraint-name mapping proven only on H2 (M2). `REQUEST_IN_PROGRESS` is not in the contract (S1) |
| Result S3 | `DonePage`, `BookingResultList` (BOOKED, REPICKED, FAILED + problem) | answer `BookingBatchResult` | `BatchOutcome(date, outcome, booking, problem{code, existingBookingId, reason...})` | - | OK; every refused-day code the service throws is mapped in `booking/lib/errors.ts` except `REQUEST_IN_PROGRESS` and `IDEMPOTENCY_KEY_REUSED` (S1) |
| S1 Today | `TodayPage`, `DayStrip` (14 tiles by `state`), `ReleaseNote`, `TomorrowCard` | `GET /today` | `TodayService` (states BOOKED, BOOKABLE, CLOSED, OUTSIDE_WINDOW built exactly as in the contract; `today` and `timezone` added, Q151) | `BookingRepository`, `OfficeQueryService`, `PeopleService` | OK |
| S4 list and cancel | `MyBookingsPage`, `cancelBooking(id, version)` | `GET /bookings`, `GET /bookings/{id}`, `POST /bookings/{id}/cancel` + If-Match | `BookingService` -> `BookingCommandService.cancel` (slots deactivated in the same transaction) | `bkg_bookings`, `bkg_booking_slots` | OK. Cancel reasons: domain 9 values map to the 5 API values in `CancelReason.apiName()`; labels exist for all 5 |
| Not ready person | `ProfileNotReadyNote`, buttons disabled | `GET /me` -> `profileReady`, `profileNotReadyReason` | `MyProfileService` -> `PeopleService`; `BookingContextFactory.requireReadyEmployee` answers 422 `PROFILE_NOT_READY` | `EmployeeRepository` -> `ppl_employees` | OK |

### J2 Release, no-show, check-in and hold (ST-CI-1, 4-7; ST-NT-2, 3)
| Step | Screen / SPA | API | Controller -> service | Table | Fit |
|---|---|---|---|---|---|
| Check in | `CheckInActions` (S1, S4), `aria-disabled` + reason | `POST /bookings/{id}/check-in` + If-Match | `CheckInController` -> `CheckInService` -> `BookingCommandService.checkIn` (second press returns the same booking) | `bkg_bookings` (version check) | OK. Codes `CHECK_IN_NOT_OPEN` (opensAt), `DEADLINE_PASSED` (deadline), `BOOKING_STATE_CHANGED` (currentStatus) all built and mapped |
| Running late | "Running late, keep until {time}" only when `HOLD` is in `allowedActions` (S15 fix) | `POST /bookings/{id}/hold` | `BookingCommandService.hold` (once, before the deadline, only if it gives more time, else `HOLD_ALREADY_USED` with `deadline`) | `bkg_bookings` | OK |
| Release | none (S1 shows the note next day) | job `ReleaseBookingsJob` every minute | `ReleaseBookingsRunner` -> `BookingCommandService.findDue/release` (batches of 200, 45 s, version check so check-in wins) -> event `BookingReleased` | `bkg_bookings` (NO_SHOW or RELEASED_AFTER_HOLD), slots freed | OK |
| Notice | `releasedToday` on S1; mail | - | `BookingReleasedListener` (same transaction) -> `NotificationOutbox` | `ntf_notifications` (unique tenant + event key) | OK |
| Reminder | mail link `<base>/bookings?focus=<id>[&action=hold]` | job `PreReleaseReminderJob` | `PreReleaseReminderRunner` -> outbox, key `PRE_RELEASE:<booking>:<deadline>` | `ntf_notifications` | Link target matches the SPA route and its `validateSearch` (UUID, `hold|checkin`); the action only moves focus (Q74). Entry point itself is M3; base URL default is S11 |
| Send | - | job `NotificationDispatchJob` | `NotificationDispatchRunner` -> `MailSenderRouter` (default LOG_ONLY) -> `TtCommonMailAdapter` -> base `SendEmail` | `ntf_notifications` status | OK in LIVE mode only (S11, Q176) |

### J4 Admin setup (ST-OS-1..9; S10, S11, S12, S19)
| Step | Screen / SPA | API | Controller -> service -> repository | Table | Fit |
|---|---|---|---|---|---|
| Offices list and create | `OfficeListPage`, New office dialog | `GET/POST /offices` (+ floorCount, deskCount, Q145) | `OfficeController` -> `OfficeService` (`requireAdmin` first) -> `OfficeRepository` | `ofc_offices` (DRAFT) | OK; duplicate SF code 409 `DUPLICATE`, mapped |
| Settings | `OfficeSettingsTab`, If-Match | `PUT /offices/{id}/settings` | `OfficeService.updateSettings` -> event `OfficeSettingsChanged` -> `OfficeSettingsListener` (later days only; today keeps the earlier times, V062) | `ofc_offices` incl. `prev_*` columns | OK. Form offers Sat/Sun (S3) |
| Floors, zones | `FloorsTab` | `POST /offices/{id}/floors` (adds zone Main), `PUT /floors/{id}`, `POST .../retire`, zone create/rename/delete | `OfficeController`, `FloorController` -> `FloorService`, `ZoneService` | `ofc_floors`, `ofc_zones` | OK; `FLOOR_RETIRED`, `OFFICE_CLOSED` mapped (wave 3 FE) |
| Desks, features | `DesksTab`, S12 dialog | `GET/POST /desks`, `PUT /desks/{id}`, retire, `desk-features` | `DeskController` -> `DeskService`, `FeatureService` (defaults seeded by `FeatureDefaultsSeeder` on first office create) | `ofc_desks`, `ofc_desk_features`, `ofc_features` | OK. No accessibility flag (Q135, R1) |
| Closed days | Calendar tab | `GET/POST/DELETE /offices/{id}/closed-days` | `ClosedDayService` | `ofc_closed_days` | OK |
| Open / close | Open and Close buttons from `allowedActions` | `POST /offices/{id}/open`, `/close` | `OfficeService.open` (DRAFT only; no check that a desk exists, S8), `close` refused with 422 `HAS_FUTURE_BOOKINGS` + `count` via `BookingImpactAdapter` (real bean; wiring test asserts one `BookingImpactPort`) | `ofc_offices`, count from `bkg_bookings` | OK; refusal is the designed MVP rule (R1 turns it into cancel and tell) |
| Booking rules S19 | Settings tab "Booking rules", If-Match | `GET/PUT /booking-rules` | `BookingRulesService` (ConfigService group DESKBOOK, admin only) | config store | OK; limits 1-60 / 15-240 / 5-120 come from the contract |
| History | history panel | `GET /offices/{id}/history`, `/desks/{id}/history` | audit listener -> `AuditHistory` | `aud_*` | OK; desk feature rows not shown in desk history (Q142, accepted) |

### J5 Report and export (ST-RP-1..4; S17)
| Step | Screen / SPA | API | Controller -> service -> repository | Table | Fit |
|---|---|---|---|---|---|
| Table | `ReportsPage` (office or all, period, stat cards, rows, "All floors" line from `dayTotals`) | `GET /reports/occupancy` (officeId, from, to, page, size, sort) | `ReportController` -> `OccupancyReportService` (`requireAdmin` first) -> `BookingStatsQuery` -> `OccupancyCalculator` | `bkg_bookings`, `ofc_desks`, `ofc_closed_days`, `ofc_offices` (read) | OK. Range 93 days after `from` (94 inclusive) agrees in contract, backend constant and SPA; two documents still say 366 (S5). Module boundary S6 |
| Export | `exportReport`, blob, file name built in the SPA | `GET /reports/occupancy/export` | `OccupancyExportService` (POI streaming, 100,000 rows) | same | OK. `from` and `to` are `required: true` in the contract but optional in the controller; the service must answer 400 (confirm in the QA contract test, S1) |
| Privacy | counts only, no names | - | no person id in any record (`OccupancyRow`, `OccupancyDayTotal`) | - | OK |

### People copy (ST-PP-1..5)
`PeopleSyncJob` (hourly; syncs once per UTC day after 01:00; ADHOC type skips the clock) -> `PeopleSyncRunner` -> `BaseClientPeopleSource` (base `SuccessFactorsClientService`, filter `status in 't','f'`) -> `PeopleSyncStore` (one apply transaction, drop guard `DESKBOOK_PEOPLE_MAX_DROP_PERCENT` 10) -> `EmployeeRepository`/`SyncRunRepository` -> `ppl_employees`, `ppl_sync_runs` -> `LeaverHandler` -> `EmployeeLeft` -> `EmployeeLeftListener` (cancels BOOKED bookings from today, reason LEAVER, no mail). Read side: `GET /me` -> `MyProfileService` (roles EMPLOYEE, MANAGER from `is_manager`, ADMIN) -> SPA `requireRole` guards and `ProfileNotReadyNote`; S1 admin banner from `TodayService` (`SyncBanner`, WARNING from 2 days). Fits: field names, reasons `NOT_IN_COPY` and `INACTIVE`, and labels agree. Nothing ran against a real SuccessFactors tenant (Q113, Q167, Q110-112, Q169). The first copy: until it has run no one can book (`PROFILE_NOT_READY`); the hourly job waits for 01:00 UTC, so go-live day needs an admin "Run now" on `/jobs` (Q168 proof) - see S7.

### Notifications
Two MVP mail types (`PRE_RELEASE`, `RELEASED`) agree between `NotificationType`, `MailTemplates` (11 `deskbook.mail.*` keys all present in `messages.properties`, English only), the outbox status set (adds EXPIRED, Q174) and the stories (ST-NT-1..3). No mail goes out for cancellation by a manager or the admin because those actions are R1 (ST-NT-5, ST-NT-6, ST-OS-15): consistent, nothing built half way. The mail strings are the only place a learner-facing hard-coded host appears: `DESKBOOK_APP_BASE_URL` default `https://deskbook.example` (S11).

## 2. Cross-checks

| Check | Result |
|---|---|
| Paths and methods contract vs routes | 45 MVP operations: 28 office, 12 booking, 2 check-in/hold, `me`, 2 reports = all present. `getOccupancyGrid` (R1) has no route, correct. Base shell operations present. Contract tests compare the full path with no prefix stripping since wave 3a. |
| Roles | 33 admin-only and 13 employee-level DeskBook operations in the contract (46 with the R1 grid); each service starts with `requireAdmin()` or `requireEmployee()` (counted per class); `RoleMatrixContractTest` and `BookingRoleMatrixTest` check 401/403 before any collaborator. SPA guards (`/admin`, `/reports`, `/jobs`, `/settings` admin; `_authenticated` needs a role) agree. |
| Fields and enums | Records vs schemas: no difference except R1 `usualDesk`. Enums: status (6), part (3), reasons (5), proposal reasons (4), `noneReason`, batch outcome (3), day `state` (4), office state, deadline kind: equal in contract, Java and SPA. |
| Codes | All codes the booking, check-in, office and report services throw are in the contract except `REQUEST_IN_PROGRESS`; `UNAUTHORIZED` (guard) is `UNAUTHENTICATED` in the contract; `RATE_LIMITED` is contracted and never thrown (M1, S1). |
| Labels | 520 literal label keys and all dynamic families (`status.*`, `part.*`, `booking.reason.*`, `booking.cancelReason.*`, `booking.error.dateNotBookable.*`, `access.*`) exist in en; de, es, fr, en-GB have the same 770 keys (de, es, fr carry English for most of the new keys, known). Mail keys present. |
| Migrations vs data model | `ofc_` 7 tables, `ppl_` 2, `bkg_` 2, `ntf_` 1 as designed (V010, V020, V030, V050, V061, V062; V060 drops the demo tables). Not built and all R1: `acc_access_entries`, `ofc_desk_blocks`, `ppl_sync_issues`, `rpt_search_log`. Deviations are logged as Q140, Q141, Q148, Q171, Q174, Q175. Scripts have only run on H2 (M2). |
| Module boundaries | One break: `reports/service/BookingStatsQuery` injects `BookingRepository` and the office `OfficeRepository`, `DeskRepository`, `ClosedDayRepository`. The architecture rule (05-architecture section 3) says no repository is injected across modules, and lists `BookingStatsQuery` as a public service of `booking` (S6). All other modules go through services and ports (`BookingImpactPort`, `OfficeQueryService`, `PeopleService`, events). |
| FE / BE split | Rules (cut-off, release, late window, hold, usual desk, report totals) live in the backend; the SPA keeps display maths only. Report day totals now come from the server (MUST 5 of the code review fixed). |
| Contract copies | `Backend/.../openapi.yaml` equals `05-openapi.yaml` in schemas and operations but is older in the 400-response detail of 6 operations (`createDesk`, `createFloor`, `createZone`, `getOccupancyReport`, `exportReport`; descriptions) and carries the base theme parts; `deskbook.gen.ts` still has the removed Project and Task types (generated before the demo removal) (S2). |
| Config and deployment | `xs-security.json` has USER and ADMIN templates that the guard reads (`app.security.SecurityRole.USER`); `xs-app.json` routes `/deskbook/api/public/*` anonymous and the rest of `/deskbook/*` through XSUAA to the backend; `manifest.yml` uses placeholders only. Open: M3, S7, S11. `application*.properties` was not opened (secrets rule). |
| Tests per journey | Backend: unit and contract tests for every operation group, 40+ repository tests on H2 with two tenants, a Spring context smoke test (9) incl. the three event hand-overs and rollbacks; Frontend: pure-logic tests (181 then 177), none render a screen. No journey is tested across SPA, API and database (M2). |

## 3. Findings

### MUST
| # | Where | Problem | Owner | Fix |
|---|---|---|---|---|
| M1 | 05-security section 1 and 7 (tests 7 and 14), `05-openapi.yaml` 429 `RATE_LIMITED`, `Backend/src/main` (no rate limiter anywhere), Q147 | The design requires per-user limits (createBooking 10 per minute, listFreeDesks 30 per minute, 31 booking-days per minute across both booking operations with no partial batch, admin writes 60 per minute) and the contract lists 429. The build has none: a script can fill the horizon or poll without limit. The SPA already maps 429. Code review 07 said it must exist before release. | backend-developer (decision Q147 is open with solution-architect) | Build the in-memory per-user limiter as in 05-security 4 (Caffeine, no new dependency), answer 429 `RATE_LIMITED` with `Retry-After`, add security tests 7 and 14. |
| M2 | DoD M13; build log "Not proven"; Q158, Q165, Q168 | No end-to-end proof of any main journey (J1, J2, J4, J5) and the system never ran as a whole: Flyway V001-V062 never executed on PostgreSQL (V002 partitions and PL/pgSQL cannot run on H2; the tests rebuild the DDL by hand in `H2Schema`); the first-booker-wins rules depend on PostgreSQL constraint names in the exception text; the TTCommon beans, security filters, approuter login and the SPA against a live backend were not run (also 10-base-check "Full-stack runtime"); the screens have no component test. | qa-engineer (test-engineer); devops-engineer for a dev PostgreSQL | Run V001-V062 on PostgreSQL; add two-session race tests (same desk, same person and day, same key); one scripted journey per J1, J2 (check-in and release with the job), J4, J5 on the dev stack; component tests need jsdom and Testing Library (code review S17). |
| M3 | `approuter/xs-app.json` (no route that returns `index.html` for client routes; the last route serves `localDir` as is); `MailTemplates` (`<base>/bookings?focus=...&action=hold`, `<base>/book`); 10-base-check (dist copied by hand into `approuter/resources`) | Both mails open client-side routes of the SPA. The approuter serves files from `resources` and has no fallback, so a direct open or a reload of `/bookings` or `/book` very likely answers 404 instead of the app, which breaks the one-tap keep-my-desk link of the reminder. Not proven either way (nothing ran, `resources` is empty in the repo). | devops-engineer | Open `<approuter>/bookings` directly on dev. If 404, add the approuter fallback for non-file paths (or build the mail link to a path that is served), and record it in the deploy plan. |

### SHOULD (quality, not blocking; to the LATER backlog if the DoD says so)
| # | Where | Problem | Owner | Fix |
|---|---|---|---|---|
| S1 | `DeskAccessGuard` (401 `UNAUTHORIZED`), `BookingCommandService` (`REQUEST_IN_PROGRESS` 409), `OccupancyReport*` params | Code vocabulary: contract says `UNAUTHENTICATED`, the guard says `UNAUTHORIZED`; `REQUEST_IN_PROGRESS` is not in the contract or the SPA error map; `from` and `to` are required in the contract and optional in the controller; the 401 of the TTCommon filter is not problem-details. | api-designer (contract), backend-developer | One vocabulary: add `REQUEST_IN_PROGRESS` and `IDEMPOTENCY_KEY_REUSED` text to the SPA map, make the guard and contract agree, make `from`/`to` `required = true` or test the 400. |
| S2 | `Backend/.../openapi.yaml`, `deskbook.gen.ts` | Contract copies drift (see section 2); generated types still carry Project and Task. | backend-developer, frontend-developer | Re-copy `05-openapi.yaml` into Backend (keep base parts), run `npm run generate-api` once more, expect no diff after that. |
| S3 | `OfficeSettingsTab` (working days include SATURDAY and SUNDAY), `DayPickerGrid` (Mon-Fri), 05-ui | An admin can set Saturday as a working day, but nobody can book it, and the report counts its capacity. Code review S12 still open. | ux-designer (decision), frontend-developer | MVP: limit the settings form to Mon-Fri, or draw weekend columns when the office works them. |
| S4 | `DeskProposalRow`, `lib/plan.ts` | `noneReason` ALREADY_BOOKED and DATE_NOT_BOOKABLE are shown as "No free desk at {office}". Rare (the grid does not offer such days) but wrong text after a clock edge. | frontend-developer | Show a text per `noneReason`. |
| S5 | 05-ui (reports.error.range 366, line 435), 05-performance (366-day maximum), 05-security 4.6 (drop guard 20 and 25 percent), 05-data-model 4.5 (reason 100), 4.10, section 12, 05-ui INVALID_RELEASE_TIMES | Documents say different numbers from the contract and the build (93 days; 10 percent; 200; statuses with EXPIRED; V0xx numbering). | ux-designer, performance-engineer, security-architect, data-architect | Update each document once (Q138, Q141, Q148, Q170, Q174 already name them). |
| S6 | `reports/service/BookingStatsQuery` | Reports inject another module's repositories (see section 2). | solution-architect (decision), backend-developer | Accept by an ADR note ("reports reads, never writes") or move the query into `booking` and `office` behind their query services. |
| S7 | `05-ops.md` is missing (listed in AGENTS.md S5); `registry has no schedule` (build log wave 3 FE); `PeopleSyncJob` once per day | No devops plan: nobody has written how the 7 jobs get their schedules (release job, reminder and dispatch every minute, people hourly, 3 purges daily) on a new environment, who runs the first people copy on go-live day, and where `DESKBOOK_*` settings and the node role (`allowedNodeRoles`) are set. A missed schedule means no release and no reminder, silently. | devops-engineer | Write `05-ops.md`/`09-deploy-plan.md` with a go-live runbook (schedules, first "Run now", checks). |
| S8 | `OfficeService.open` | An office can be opened with no floor and no desk, so employees see an open office with nothing to book (A1 step 5 says "when ready"). | backend-developer (PO decides) | Refuse with a clear code or warn when no active desk exists. |
| S9 | 04-backlog ST-OS-13, 14, 15 (R1) | MVP admin has no bulk desk import, no QR sheet and no admin cancel; closing an office or retiring a desk with future bookings is refused for up to 14 days. A pilot office with several hundred desks is typed one by one. | PO | Confirm the pilot desk count (Q193); pull ST-OS-13 into the MVP if more than about 100. |
| S10 | `user/job/UsersSyncDailyJob`, `UsersSyncFullFetchJob`, `jobRegistry.ts`; `integration/openai/controller/AzureOpenAiConnectionController` | Base leftovers: two TTCommon user-sync jobs (a second SuccessFactors pull of the same people into base tables DeskBook does not read) and an Azure OpenAI admin controller that is not in the contract or the product. | backend-developer | Decision D9-3 says drop unused base parts in one pass: remove or hide them, or add them to the contract. |
| S11 | `MailSettings` (default mode LOG_ONLY; base URL default `https://deskbook.example`), Q176, Q177 | Until `DESKBOOK_MAIL_MODE=LIVE` is set, every mail is logged and marked SENT; in LIVE mode with the base URL unset the links point to the placeholder. Nothing refuses or warns. | backend-developer, devops-engineer | In LIVE mode refuse to send (and log an error) while the base URL is the placeholder; list both keys in the runbook. |
| S12 | Q163, Q156 | `DeskAccessGuard.tenantId()` reads the session while the rest uses `AuditContext.tenantId()`; desk cache has no eviction (60 s). Equal in a single-tenant deployment. | backend-developer | Use one source; keep the 60 s as documented. |
| S13 | 05-ui S18, ST-PP-6, Q80 | Admin sees the people copy only as a warning banner on S1 (from 2 days) and on `/jobs`; the "last updated" line R49 promised is not shown while healthy. | PO | Accept, or add the one line (Q80 recommended). |

## 4. Open questions that still block go-live

`questions.md` has 69 `[open]` entries. By build state most are answered in the code or the contract already (list in the last paragraph). Blocking go-live (G4):

| Questions | What | Owner |
|---|---|---|
| Q75 | Legal and works-council sign-off for DE and FR before the pilot; erasure and data-request runbook for the MVP (AnonymiseJob R2 before Oct 2028) | PO |
| Q113, Q167, Q110, Q111, Q112, Q169 | SuccessFactors proof on the customer tenant: API user role and target population (incl. inactive), `User.location` format for the home office, nav names, leaver visibility with the `t,f` filter, one anonymised page and `$metadata`, one live "Run now" (Q168) | developer with sf-consultant and integration-engineer |
| Q176, Q177, Q76, Q82 | Mail: one real send measured on dev (fixed From address, 300 per minute target, D6 item 6 customer mail service), per-environment `DESKBOOK_MAIL_MODE=LIVE`, `DESKBOOK_APP_BASE_URL`, worker count; where mail credentials and actuator endpoints live; who receives alerts (no good copy for 36 hours, FAILED mails) | devops-engineer, developer, integration-engineer |
| Q147 | Admin write rate limit and the other limits (M1) | solution-architect, backend-developer |
| Q158, Q165 | PostgreSQL race and migration proof (M2) | test-engineer, qa-engineer |
| Q189, Q190, Q191, Q192, Q193 | New, from this review (M3, S7, M1, M2, S9) | see `questions.md` |
| Q180-Q188 | Written meanwhile by performance-engineer from 07-performance (PB-1 and PB-2 are marked MUST there; read that report for which of the nine block) | performance-engineer, backend-developer, devops-engineer |

Not blocking go-live but still `[open]` and needing a short PO answer: Q80, Q81 (10 percent drop guard, built), Q114 and Q131 (small-cell number, R1 grid and export), Q130, Q161, Q179. Not blocking (R1 or later): Q72, Q101, Q103-Q107, Q118, Q126, Q127, Q99. Answered by the build and ready to close (the lead decides): Q70 (promise dates Oct 2028, tracked in Q75), Q71, Q73, Q74, Q78, Q85, Q86, Q98, Q115-Q117, Q119, Q121, Q132, Q135, Q136, Q138, Q140-Q142, Q146, Q148, Q149, Q154, Q156, Q157, Q162-Q164, Q166, Q170-Q175, Q178.

## 5. Definition of Done view (this review only)
| Item | Result |
|---|---|
| M2 no open blocker question | No question is marked blocker; the table above lists the ones that need an answer before G4. |
| M4 contract match | Operations, methods, schemas, enums match; codes differ in three places (S1) and RATE_LIMITED is not produced (M1). |
| M10 authorization per operation | Met in code; rate limits missing (M1). |
| M13 one end-to-end test per main journey | Not met (M2). |
| M3, M5, M6, M8, M9, M15 | Met for what could be read (code review 07 and this trace). |
