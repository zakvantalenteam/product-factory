# Performance build review - DeskBook

Stage S7, performance-engineer, build mode, 2026-10-29. Read-only on code; nothing was run (no server, no Maven, no npm,
no EXPLAIN): every number below is a trace of the code or an estimate and is marked so. Inputs: `05-performance.md`
(budgets, PF-1 to PF-22), `05-architecture.md` 6.1-6.4, `05-data-model.md`, `06-build-log.md`, `questions.md` (Q156, Q176-Q179).
Product root `D:/products/desk-booking`, Backend 197 Java files, migrations V001-V062, `Frontend/dist` as built 29 Oct 03:18.

## 0. Verdict

**At risk, not ready to sign off.** 2 MUST, 14 SHOULD. Nothing found that breaks a read path by itself: every hot read has an
index, nothing walks entities into N+1 (the `Booking` entity has ids only, no relations), every list is paged or bounded,
the L2 cache is off (PF-4 done, `application.properties` line 52), PF-1 and PF-2 are built as designed. The two MUSTs are an
unbounded synchronous job inside an admin request (PB-1) and a mail rate that is only a hope until one real send is timed (PB-2).
Most budgets stay "Not measured": the product has no metrics (PB-9), so server p95 can only come from k6 timings plus
`pg_stat_statements`.

| Budget (05-performance) | Status | Evidence |
|---|---|---|
| Release lag < 5 min, drain 720 in one run (PF-1) | At risk, probably met | loop + 45 s budget built (`ReleaseBookingsRunner`); ~10 statements per release; 720 x 30-50 ms = 22-36 s of the 45 s; next run continues (+60 s), still inside 5 min. Measure in T4 |
| Mail >= 300/min, last reminder by 09:50 (PF-5) | Not measured, at risk | PB-2 |
| Settings change returns < 2 s (admin write) | **Not met** | PB-1: ~15,000 rows in the request |
| `createBookings` 14 days 1.4 s / 10 days 1.0 s (PF-3) | At risk | ~320 statements for 14 days (PB-3) |
| `proposeDesks` 400 ms (PF-2) | Not measured, estimate 40-120 ms | one set read + cached desk list, 6 statements |
| `listFreeDesks` 300 ms | Not measured, estimate 20-60 ms | 3 statements, no per-desk probe |
| `getToday` 250 ms | Not measured, estimate 60-110 ms | 12-17 statements, design said ~4 (PB-4) |
| `listMyBookings` 250 ms | Met by trace (not measured) | window 30 d back to horizon, index range, one count, one select, batched desk/office reads |
| `checkIn`, `holdBooking`, `cancelBooking` 400 ms | Met by trace (not measured) | PK read, one office read, one update (+ slot rows on cancel); est 20-40 ms |
| `getBookingCalendar` 150 ms | Not measured, estimate 15-30 ms | ~5 small reads, not cached (PF-15 cache not built; harmless) |
| `getOccupancyReport` page 0 3 s | Not measured, estimate 0.6-1.5 s | 3 grouped reads over ~150,000 rows (3 months, all offices) |
| Report next pages 300 ms | **Not met by design** | every page recomputes the whole aggregate (PB-6) |
| `exportReport` 31 d 2 s, 93 d 6 s, 30,000 rows 20 s, heap < 50 MB | Not measured, estimate 1 s / 3 s / ok | POI `SXSSFWorkbook(100)` streamed, 100,000-row and 93-day bound checked before the first byte; no concurrency cap (PB-7) |
| People copy < 10 min (AC14.1) | Not measured, estimate 2-4 min | PB-12 for the first load |
| Purge jobs < 5 min | Met by trace | chunks of 1,000, 10 min budget |
| Employee JS <= 250 KB gzip | **Not met** | main chunk 284 KB gzip alone (PB-10) |
| S1 serial calls (PF-16) | **Not met** | three serial round trips (PB-11) |

## 1. Findings

| Id | Level | Owner | Finding | Fix | Question |
|---|---|---|---|---|---|
| PB-1 | MUST | backend-developer | `OfficeSettingsListener.onSettingsChanged` (`@EventListener @Transactional`, runs inside the admin's save request) loads every future BOOKED booking of the office as entities (`findForRecompute`, no limit) and updates the ones whose deadline moved, in one transaction. Effective date is tomorrow, so ~13 days x ~1,200 = ~15,000 bookings (~72,000 at the 60-day horizon limit). One UPDATE each (`check_in_deadline` is `@NotAudited`): ~15,000 statements, est 30-60 s, 20-100 MB of heap, row locks on every future booking until commit (cancel and create-day writes wait), and a gateway timeout turns a good save into a failed one | recompute after commit in chunks of 500 per transaction (by date), as a job or an async listener; the settings save returns at once; or derive the deadline from the office times when it is read and store nothing | Q180 |
| PB-2 | MUST | backend-developer, devops-engineer | Mail throughput is a guess. Per run: sends = workers x 50 s / seconds per message. The base `SendEmail` opens one SMTP connection per message (Q176); a TLS + AUTH handshake to a hosted mail service is typically 0.8-2 s, not the 0.1 s the runner comment assumes. Default 4 workers: at 0.4 s/mail 600/min (cap), at 1.0 s 200/min, at 1.5 s 133/min. At 133/min the 1,150 reminders of 09:45 (5 years) take 8.6 min (last one ~09:54, after the T-10 target of 09:50) and the 720 release mails of 10:00 queue behind them (~5.4 min more; the 10 min budget holds, the reminder budget does not). Chunking adds a wait for the slowest mail of every 20 | time 10 sequential and 10 parallel real sends on dev (Q176) before go-live; set `DESKBOOK_MAIL_WORKERS` default to 8 (limit 16) so 1 s per mail still gives 480/min; log mails/min and seconds/mail in the job result | Q181 |
| PB-3 | SHOULD | backend-developer | `createBookings` costs ~24 statements per day, ~320 for 14 days: per day it re-reads the office and the desk (review S3: `findOffice` + `findDesk`, and `findDesk` is 3 statements because `desksByIds` always reads desk features), checks the idempotency key and the day, inserts booking + 2 slots + 1 audit log + ~6 audit fields (no JDBC batch writing is set), then `BookingAssembler.toResponse` runs per day: offices + desks + features + rules again (PF-3 asked for "once per request"). At 3 ms per statement: 1.0 s of the 1.4 s budget; at 4-5 ms (app and database in different zones) it is over | (a) `desksByIds` without features for bookings, mail and Today (features only for the free-desk list): saves 2 statements per call everywhere; (b) in the batch, re-check desk and office inside the transaction with one read each, or reuse the context read minutes ago and rely on the FK/check; (c) assemble all days once after the loop; (d) try `eclipselink.jdbc.batch-writing=JDBC` with `batch-writing.size=100` and compare in T1/T3 | Q182 |
| PB-4 | SHOULD | solution-architect | Of the five caches in 05-performance 4 only the active desk list is built. `getToday` reads the home office 2-4 times (`findOpenByLocationCode`, `firstOpenOffice` = select + count, `findOffice`), closed days 3 times, and computes "N of M free tomorrow" on every call (one read of ~1,200 booking rows, PF-9 not built): at P1 ~37 calls/s = ~45,000 rows/s read for one tile. Office, settings, closed days (60 s) and the 5 s count are missing | add the Caffeine caches of 05-performance 4 for office rows, closed days (key office, from, to) and the free count (key office, date, can-see-reserved, 5 s); keep own bookings uncached | Q183 |
| PB-5 | SHOULD | data-architect | The design reads `ix_bkg_bookings_office_date` and `ix_bkg_bookings_employee_date` index-only (3.1, 3.2, 3.7, 4.8) but every repository query adds `deleted_at is null` and `deleted_at` is in neither index (nor partial predicate), so each row is a heap fetch: ~17,000 rows for `proposeDesks` at 14 days, ~1,200 for `listFreeDesks` and the Today tile, ~150,000-600,000 for the 3-month report and the export. Heap is mostly hot (future days, last 90 days), so est +10-30 ms per call, not a budget breaker, but the CPU adds up at 22 proposeDesks/s | additive migration: make `ix_bkg_bookings_office_date`, `ix_bkg_bookings_employee_date` and `ix_bkg_bookings_booked_deadline` partial `WHERE deleted_at IS NULL` (the queries carry that literal, so the planner matches it); check heap fetches in EXPLAIN (below) | Q184 |
| PB-6 | SHOULD | backend-developer | PF-13 not built: `getOccupancyReport` recomputes the whole aggregate (3 reads over ~150,000 rows, 600,000 at 366 days) for every page request. 4,650 rows = 47 pages of 100; "Load more" repeats the full cost each time (est 0.6-1.5 s), the 300 ms budget for next pages is unreachable, and the export does it again after the table | cache the computed `Stats` for 60 s per (tenant, officeId, from, to) in Caffeine and slice pages from it; the export reads the same cache | Q185 |
| PB-7 | SHOULD | backend-developer | PF-22 not built: nothing limits parallel exports (no semaphore, no 429; the only 429 in the code is the SuccessFactors one). 5 admins at month end = 5 aggregates of 150,000 rows plus 5 request threads and 5 SXSSF temp files on a 1 GB node that also serves P1. The same grep finds no per-user rate limit at all (createBookings 3/min, proposeDesks 20/min, `listFreeDesks` 30/min of 05-security); the frontend comment says "limit 20 a minute" but the server does not enforce it | `Semaphore(2)` per instance around prepare+write, `tryAcquire` failing with 429 + `Retry-After`; log rows and ms per export; the per-user limits belong to the security lane (note for security-architect) | Q185 |
| PB-8 | SHOULD | devops-engineer | `manifest.yml`: one backend instance, 1024 MB, no pool setting in the product config (`spring.datasource.hikari.*` absent, so the Spring default of 10 unless the base sets one). The design and T1 assume 2 instances, pool 20, job work on one node. At P1 the busy-connection estimate is ~5-6 of 10 on one instance (each `@Transactional` read holds a connection for 20-60 ms), which leaves no room for the 10:00 burst | `instances: 2`, `maximum-pool-size=20`, and the job node role named; confirm the heap the Java buildpack computes for 1 GB (about 400-500 MB) is enough for 2 exports + 5,500 employees in the sync | Q186 |
| PB-9 | SHOULD | solution-architect | PF-20 not built: no actuator or Micrometer in the poms, `RequestIdFilter` logs no duration, the Caffeine cache has no `recordStats()`. S7 cannot show server p95 per operation, nor the cache hit rate T7 asks for | log method, route template, status and ms per request in `RequestIdFilter` (one line, no query string, no person), `recordStats()` on the desk cache; or add actuator | Q186 |
| PB-10 | SHOULD | frontend-developer | Bundle: `index-BAZ5cMrM.js` 946,752 B raw, **284 KB gzip** (gzip -9), plus CSS 7 KB gzip; `/dashboard` also pulls `route-Dh6Anctm` (20 KB gzip), `dashboard` (3.8 KB) and shared bits: ~315 KB against 250 KB. The entry chunk has MUI (120 `Mui` references) and emotion although the screens use Radix + Tailwind; the admin chunks (`_officeId` 6.8, `jobs` 6.3, `reports` 4.5 KB gzip) are lazy, as designed. `index.html` loads Inter from `fonts.googleapis.com` as a render-blocking stylesheet (a third-party DNS + TLS + request before first paint on 4G, not covered by the 1-year cache) | keep MUI out of the employee entry chunk (lazy-load toast and dialogs that use it, or use the Radix versions), `manualChunks` for vendor, a size check in CI at 250 KB gzip; self-host the Inter subset and `font-display: swap` | Q187 |
| PB-11 | SHOULD | frontend-developer | PF-16 not built: `_authenticated` `beforeLoad` awaits `getCurrentUser`, then `requireRole` awaits `getMyProfile`, and `getToday` is issued only when the dashboard mounts: three serial round trips (est +0.7-1.0 s on 4G, ~120 ms RTT each plus server time) on the screen with the 1.5 s budget | start `getToday` (prefetch) in the same `beforeLoad` as profile and user (`Promise.all`); skeleton until `getToday` | Q187 |
| PB-12 | SHOULD | integration-engineer | `PeopleSyncRunner`: `$skip` paging of 200 with no overall time cap (worst case 35 pages x (3 tries, 5 s + 20 s waits) = ~50 min before the 30 min ABANDONED rule); first load applies ~6,500 employees and their audit rows in one transaction with no JDBC batching (est 40,000-60,000 inserts, 1-3 min); later runs write < 50 rows. Also `user/job` carries the base `UsersSyncDailyJob` and `UsersSyncFullFetchJob`, which page the same SuccessFactors `User` entity again (with photos) | one total deadline for the fetch (for example 8 min, then fail with a code); run the first load once on dev and record time and SF calls; confirm the base user-sync jobs are not scheduled for DeskBook; cursor paging if a tenant passes ~10,000 users | Q188 |
| PB-13 | SHOULD | backend-developer | `getBookingCalendar` and `zonesOfOffice` + `allFeatures` are read per call and `proposeDesks` builds a `HashSet` of feature ids per candidate per day (14 x 1,500 = 21,000 sets per call, ~5 ms CPU, ~10 % of a core at 22 calls/s); `DeskInfo` is immutable, so the set can be built once | precompute `featureIds` in `DeskInfo`; cache zones/features with the desk list | Q183 |
| PB-14 | SHOULD | backend-developer | `ConfigService.getConfigurationMap()` (TTCommon) is called up to 3 times per request (`BookingRulesService.current`) and 4-5 times per dispatch run (`MailSettings`); whether it hits the database is not visible in this repo | confirm it is cached in TTCommon; if not, read the rules once per request/run and cache them 30 s | Q188 |
| PB-15 | SHOULD | solution-architect | `evictDeskCache()` has no caller (Q156): a desk, floor, zone or feature change shows up to 60 s late on each instance. Safe for bookings (the write re-checks), visible for admins who retire a desk and still see it offered. Not a performance risk | accept Q156 for the MVP; wire `evictDeskCache()` to the office write paths (local instance) or delete the dead method | - |
| PB-16 | SHOULD | backend-developer | Notes at no cost: (a) `findIdsBefore` of the slot purge has no index on (tenant, booking_date): a scan + sort of ~250,000 slots per chunk, 3-4 chunks a night, ~0.2 s each, fine; (b) `ReleaseBookingsRunner` filters rows it already tried, so 200 persistent failures would end a run early (only a poison batch); (c) the reminder runner re-reads the same ~1,150 candidates for 15 minutes in a row (3 `IN` reads of 500 keys per run, est 0.3-0.6 s, Q178 accepted) | none now; (b) log a warning when `due` is empty only because of `seen` | - |

No finding for: tenant filter on every query (checked in all 12 repositories), `deleted_at` filters, paging (every list is paged or bounded:
`proposeDesks` and `createBookings` at 14 days, report at 100 rows, My bookings windowed), L2 cache off, outbox existence check before insert,
no transaction open during a mail send (`NotificationStore` is two short transactions per chunk), the connection released before the xlsx is written.

## 2. Hot paths as built (what the load test must confirm)

Statement counts are a trace of the code, to be compared with `pg_stat_statements` `calls` per request in T1.

| Operation | Statements (trace) | Design said | Largest read |
|---|---|---|---|
| `listFreeDesks` | 3 (office, closed days, occupancy) + role check | 3-4 | occupancy of one date: ~1,200 rows, filtered in memory against the cached desk list (no per-desk probe, so no slot anti-join: Q156) |
| `proposeDesks` (14 days) | 6-7 | 5 | occupancy of 14 dates: ~17,000 rows (largest office), `findBookedDates`, `countByDesk` (60 days of her own rows) |
| `getToday` | 12-17 (9 with no booking) | ~4 | occupancy of tomorrow ~1,200 rows (no cache), desks 3 statements per call |
| `createBooking` | ~25 (7 reads before the transaction, 9 inside, 4 for the answer, 5 writes incl. audit) | ~8 | one booking + 2 slots + audit |
| `createBookings` 14 days | ~320 | not stated (budget 100 ms per day, 1.4 s for 14) | per-day transaction as designed |
| `checkIn`, `hold`, `cancel` | 6-11 | 3-4 | PK read, update, audit rows |
| release of one booking | ~10 (read, slots, 2 updates, outbox existence + insert, audit log + fields) | ~8 | one transaction each, 720 at 10:00 |
| reminder run (each minute, window 15 min) | 2-3 pages x (1 candidate read of 500 entities + 1 existence read of 500 keys + 1 insert batch) | chunks of 200 | ~1,150 entities re-read for 15 runs |
| dispatch (per chunk of 20 mails) | claim (per 200) + recipients + facts + offices + desks (3) + 1 record per 20 | - | no DB work on the sender threads (good) |
| report / export | 4 reads (offices, closed days, desks grouped, bookings x2 grouped) | 3 | ~150,000 booking rows grouped, heap fetches (PB-5) |

Caches as built: desk list (Caffeine, 60 s, max 500 keys, per instance, no stats, no eviction on change); JPA L2 off (Met). Not built: office
row, closed days, calendar, free count, report aggregate. Frontend: no polling (R1 not built), `staleTime` 30 s for Today, 60 s for calendar and
offices, 0 for proposals and free desks: matches the design.

## 3. Index check (read every query against V010, V020, V030, V061)

Every query in the 12 repositories has an index that serves its predicate and order. Notes that need the EXPLAIN pass:

| Query | Index | Check |
|---|---|---|
| `findOccupied`, `countForReport`, `countCancelledBeforeDeadlineForReport`, `findForRecompute` | `ix_bkg_bookings_office_date` | heap fetches because of `deleted_at` (PB-5); not partial, so cancelled and released rows of those dates are read and filtered |
| `findDue`, `findReminderCandidates` | `ix_bkg_bookings_booked_deadline` (partial `status = 'BOOKED'`) | the status is a bind value (`status = :status`): confirm the planner picks the partial index (custom plan) and does not switch to a generic plan after 5 executions |
| `findUpcoming`, `findInRange`, `findBookedDates`, `countByDesk`, `findOnDate`, `findForLeaver` | `ix_bkg_bookings_employee_date` | range on (tenant, employee, date); fine; `deleted_at` heap fetch on ~60 rows |
| `findByIdempotencyKey` | `uq_bkg_bookings_idempotency` (partial `key IS NOT NULL`) | `key = :key` implies not null, so it matches |
| `findByBooking` (slots) | `ix_bkg_booking_slots_booking` | fine |
| `findDue` (notifications) | `ix_ntf_notifications_due` (partial PENDING) | `ORDER BY type, next_attempt_at` adds a sort of the due rows (<= ~2,000): fine |
| `findIdsToPurge` | `ix_ntf_notifications_status_created` | three statuses = three ranges + sort: fine |
| `findIdsBefore` (slots) | none (scan) | PB-16 (a) |
| `findLeaverIdsToHandle`, `findAllLive` (employees) | none needed | 5,500 rows, not a request path |
| `findActiveRowsOfOffice` | `ix_ofc_desks_floor_code`, `uq_ofc_floors_office_name` | one read per office per minute; the feature read uses `IN` with up to 1,500 ids: fine for PostgreSQL (limit 32,767 binds) |

EXPLAIN (ANALYZE, BUFFERS) on the seed of 05-performance 5, record plan, rows, buffers and heap fetches: `findOccupied` (1 date and 14 dates),
`findDue` at 720 due, `findReminderCandidates`, `countForReport` (31 and 93 days), `findInRange`, `findForRecompute` (14 and 60 days),
`findActiveRowsOfOffice`. Run each twice, with and without `plan_cache_mode = force_generic_plan`, to see the partial-index risk.

## 4. Jobs

| Job | Built as | Budget | Verdict |
|---|---|---|---|
| `ReleaseBookingsJob` | loop of 200, 45 s, one transaction per booking, version check (check-in wins) | lag < 5 min, p95 < 3 min | At risk, probably met: 720 x ~30-50 ms = 22-36 s; if the database round trip is 5 ms the run ends at the budget and the next minute continues (+60 s) |
| `PreReleaseReminderJob` | window (now, now + 15 min], pages of 500, max 20 pages, unique event key | 1,150 rows within 60 s | Met by trace; re-reads candidates each minute (PB-16 c) |
| `NotificationDispatchJob` | claim 200, 4 workers, 50 s, cap 600/min, lease 5 min, breaker after 5 transient failures | last reminder before T-10 | **PB-2**; reminders sorted first (P before R), recorded per chunk of 20, expired rows never sent late |
| `PeopleSyncJob` | all pages in memory (200 per page, <= 500 pages), apply in one transaction, drop guard | < 10 min | Not measured; memory fine (~6,500 small objects, ~5 MB); PB-12 |
| `BookingSlotPurgeJob`, `NotificationPurgeJob`, `SyncRunPurgeJob` | chunks of 1,000 per transaction, 10 min budget | < 5 min | Met by trace |
| `OfficeSettingsListener` (not a job, but runs in a request) | all future BOOKED rows in one transaction | admin write < 2 s | **PB-1** |

## 5. Frontend bundle (`Frontend/dist`, not rebuilt)

| File | Raw | Gzip -9 |
|---|---|---|
| `assets/index-BAZ5cMrM.js` (entry) | 946,752 | 284,444 |
| `assets/route-Dh6Anctm.js` | 57,745 | 19,979 |
| `assets/book-ERMHcsTJ.js` | 45,718 | 15,126 |
| `assets/_officeId-RrOp_fRS.js` (admin, lazy) | 26,365 | 6,842 |
| `assets/jobs-yL31s_AO.js` (admin, lazy) | 21,809 | 6,257 |
| `assets/reports-S7xntDJf.js` (admin, lazy) | 13,521 | 4,493 |
| `assets/dashboard-BkDv1M2Y.js` | 11,728 | 3,808 |
| `assets/bookings-pTbzLcjF.js` | 7,906 | 2,915 |
| `assets/index-CyP37Hl8.css` | 32,570 | 6,895 |

All other chunks are under 7,000 B raw. Route splitting works (admin, reports, jobs are separate). Entry chunk over budget: PB-10. Dependencies
that explain the size: `@mui/material` 6 + emotion next to Radix + Tailwind, `i18next` + `react-i18next`, `zod`, `react-hook-form`, `lucide-react`,
`@tanstack/react-query` + `react-router`. Check on 4G: 285 KB is ~0.6-1 s on a cold first visit, nothing on later visits (hashed names, 1-year cache at the
approuter, to confirm in the approuter config).

## 6. Load test on dev (what must run before sign-off; scripts to be written by the next round, k6)

The plan of `05-performance.md` 5 (T1-T9) stands; T10 stays R1. Changes after reading the build:

| # | Change or addition | Why |
|---|---|---|
| T1 | read `pg_stat_statements` `calls` per operation and compare with section 2; record connection-pool wait (Hikari) | statement counts are 2-4x the design; pool unset (PB-8) |
| T3 | run `createBookings` 14 days at 3 ms and at 5 ms added latency (a proxy on the database port) | PB-3 depends on round-trip time |
| T4 | 720 due at 10:00, measure `released_at - check_in_deadline`, time of the run, statements per release | PB-1/PF-1 margin of 45 s |
| T5 | first step: 10 sequential and 10 parallel real sends through the base sender on dev, then the 1,150 + 720 run with that real latency, workers 4 and 8 | PB-2: the mail number is Not measured |
| T6 | add "Load more" through 47 pages and 5 exports at once with a heap and thread dump, and a 30,000-row seed (about 320 floors x 93 days) | PB-6, PB-7, NFR export |
| T8 | first full load of 6,500 employees on an empty copy (time, statements, audit rows) and a repeat run | PB-12 |
| **T11 (new)** | change the release time of the largest office with the 14-day horizon full (~15,000 BOOKED rows), under T1 at 50 %: request time, statements, row-lock waits on cancel and create-day | PB-1 |
| **T12 (new)** | page-weight check: first useful content of `/dashboard` on a throttled 4G profile, cold and warm cache, with the Google font blocked and allowed | PB-10, PB-11 |

Metrics needed on the dev space: Hikari pool usage, `pg_stat_statements`, per-request duration (PB-9), heap and threads during T6.

## 7. Open questions

Q180-Q188 in `questions.md` (PB-1 to PB-14). PB-15 and PB-16 need no question (Q156 accepted, the notes are in this file).
