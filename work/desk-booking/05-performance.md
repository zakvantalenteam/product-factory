# Performance design review - DeskBook

Stage S5, performance-engineer, design mode, 2026-10-28. Design as it stands after gate GP (decisions D5: option A
"Plan my week", ST-BK-8 in the MVP, Change picker = option B's zone list, occupancy table under the heat grid).
Inputs: `02-spec.md` Non-functional + F4/F7/F8/F14/F18/F19, `05-architecture.md` 4 and 6, `05-openapi.yaml`
(operation ids, limits), `05-api-notes.md`, `05-data-model.md` 4.4/4.8/4.9/7/9, `05-integrations.md` 1.8/2.4,
`05-sf-fields.md`, `05-ui.md` S1/S2/S2b/S4/S17, `05-security.md` rate limits, `04-stories.md`.

Numbers marked (P) are proposed here; the spec has none for them. Everything else traces to a spec line.

## 0. Scope update after D6 and D7 (fix of N4, re-review 2026-10-28)

Budgets, hot paths and the load-test plan below follow decisions D6 (G3 answers 1-6) and D7 (`exportReport` R1 -> MVP,
MVP 147 points). Marks used in this file: **(MVP, moved in)** = was R1, now MVP; **(R1, moved out)** = was MVP, now R1.

| Item | Was | Now | Where changed in this file |
|---|---|---|---|
| `getToday.nextTwoWeeks` (14-day strip, ST-BK-15) | R1 (extra calls `listMyBookings` + `getBookingCalendar`) | **MVP, moved in**; part of the `getToday` answer, no extra call | S1 row, `getToday` row, 3.1, PF-12, T1 |
| `getToday.usualDesk` and "usual desk free next working day" | MVP | **R1, moved out** | `getToday` row, 3.1, PF-17 note, T10 |
| `getOccupancyGrid` (S17 heat grid, query 17) | MVP | **R1, moved out** | S17 row, grid row, 3.7, PF-14, T6 -> T10 |
| `exportReport` (xlsx, same filter as `getOccupancyReport`, ST-RP-4) | R1 | **MVP, moved in** (budget, size limit, test) | S17 export row, operations row, 3.7, P7, T6, PF-22 |

MVP operations on the hot path change from "grid" to "export"; the MVP load targets (150 req/s, P1) do not change.

## 1. Load model

### 1.1 Volumes used (year 1 and 5 years)

| Item | Year 1 | 5 years | Source |
|---|---|---|---|
| Employees in the copy | 3,000 active (+ a few thousand inactive in the SF read) | 5,500 | spec NFR, data model 9, sf-fields |
| Offices / desks | 8 / 3,000 (largest office 1,500) | 12 / 4,000 | data model 9 |
| Bookings per average working day | 1,800 | 1,800-2,400 | A13, data model 9 |
| Bookings on a peak day (Mon/Tue, 80 % of desks) (P) | 2,400 | 3,200 | assumption here |
| Share with the 10:00 release (morning + full day) (P) | 90 % = 2,160 | 2,880 | assumption here |
| No-show rate for sizing (P) | 25 % (spec example 16.7 %) | 25 % | AC12.1 |
| `bkg_bookings` rows | 450,000 | 2.25 M | data model 9 |
| `bkg_booking_slots` live rows (90-day purge) | ~170,000 | ~170,000 | data model 9 (says ~100,000; 90/365 x 675,000 is ~170,000, no impact) |
| Zones in the largest office (P) | 40 | 40 | data model 9 (150 zones / 12 offices, largest x3) |

Worst case for every job number below: all offices share one timezone (the Indian offices do), so their 06:00,
09:45 and 10:00 events fall in the same minute.

### 1.2 Peak scenarios

| Scenario | When | Users | Requests | Writes |
|---|---|---|---|---|
| P1 Monday rush (spec "500 at once", Q10) | Mon 08:00-08:15 | 500 active, think time 5 s | ~100 req/s; design 150 req/s (+50 %) | createBookings ~5 req/s (avg 3 days = 15 bookings/s), createBooking ~3 req/s, cancel ~1 req/s |
| P2 Check-in burst | 08:45-09:15 office time | 1,620 check-ins before 10:00 (Y1), 2,160 (Y5); 40 % in this 30 min = 650 / 865 | 0.36 check-ins/s average, 1.1/s (Y1) and 1.4/s (Y5) in the peak minute, ~4/s peak second; each visit ~6 API calls (shell, getCurrentUser, getMyProfile, getToday, checkIn, getToday refetch) -> ~9 req/s on top of P1 | checkIn 1-4/s, one row update + 2 slot rows untouched + audit |
| P3 Reminder spike | 09:45 | 40 % of 10:00 bookings not checked in yet: 860 (Y1), 1,150 (Y5) | half open the mail within 5 min: ~430 visits, 1.5 req/s | 860-1,150 outbox rows in one job run; holds ~20 % of them |
| P4 Release | 10:00 | 540 (Y1) / 720 (Y5) bookings released in the same minute | 30 % of the released come back within 15 min: 160-215 users on today's free list, 0.3 req/s | 540-720 booking updates + 1,080-1,440 slot updates + 540-720 outbox rows + audit |
| P5 R1 polling (ST-BK-3) | any busy time | 300 of 500 users keep a free list open | +75 req/s polls (architecture 6.2 states 125 req/s if all 500 poll) | none (see PF-6: no search-log row per poll) |
| P6 People copy | 01:00 UTC (06:30 IST), hourly retries | 1 job | 30-40 SF pages of 200 (3,000 active + inactive) | under 50 changed rows a night; one apply transaction |
| P7 Report export (ST-RP-4, MVP, moved in) (P) | office hours, month end and review weeks | 2-3 admins at a time, 5 at the month end | 1 request each; answer is a file of 100 KB (31 days) to ~2 MB (cap) | none; reads the same aggregate as the report, no cache of its own |

Design targets: MVP 150 req/s sustained over 15 minutes, R1 250 req/s (P1 + P5), with every budget in section 2 met.
Exports (P7) are outside the 150 req/s: at most 2 run at once per instance (PF-22) and they must not move the P1 numbers.
At an average 3 statements per request plus the session row, the database sees about 600 statements/s and about
20 write transactions/s at P1; the job burst at 10:00 adds about 50 short transactions/s for 10-15 s.

## 2. Budgets

### 2.1 Screens (phone 360 px on 4G, ~120 ms RTT, assets already cached; company sign-in redirect not included)

| Screen | First useful content | Fully usable | Source | Calls on load (05-ui) |
|---|---|---|---|---|
| S1 Today `/dashboard` | 1.5 s (P) | 2.0 s at 500 users | AC18.7, NFR | `getCurrentUser`, `getMyProfile`, `getToday` in parallel (+ base `getLabels`, `getTheme` cached); the 14-day strip is in the `getToday` answer (`nextTwoWeeks`, MVP, D6): no `listMyBookings` or `getBookingCalendar` call on load (PF-12 done). `usualDesk` is R1 |
| S2 Plan my days `/book` | 1.0 s picker (P) | proposals 1.2 s after the last tick (400 ms debounce + `proposeDesks`) (P) | NFR 2 s | `listBookableOffices`, `getBookingCalendar` (cached), `proposeDesks` per tick change |
| S2b Change a desk | 1.5 s first 50 rows (P) | 2.0 s with 500 desks; next page 1.0 s | AC4.10 | `listFreeDesks` page 0, then next pages on scroll |
| S3 Booked (result) | - | 1.0 s for 3 days, 2.0 s for 10 days, 2.5 s for 14 days (P) | AC19.10, A14 | `createBookings` once |
| S4 My bookings | 1.5 s (P) | 2.0 s; a new booking shows within 1 s | AC5.11 | `listMyBookings` page 0 |
| Check-in / hold / cancel action | - | 1.0 s for 95 % | A14 | `checkIn`, `holdBooking`, `cancelBooking` + `getToday` refetch |
| S17 Occupancy, 3 months all offices | stat cards 3.5 s (P) | table 5.0 s | AC12.12 | `listOffices`, `getOccupancyReport` page 0. Heat grid `getOccupancyGrid` is **R1, moved out** (budget in 2.2, test T10) |
| S17 Export to Excel (ST-RP-4, MVP, moved in) | - | file saved within 5 s for a 31-day filter, within 10 s for the 93-day contract maximum (P); never over 30 s (AC12.8) | AC12.8, D7 | one `exportReport` call with the filter of the table; button busy state until the file arrives |
| Admin set-up lists | 1.5 s | 2.0 s | NFR | paged lists, size max 100 |
| SPA shell | initial JS for employee routes at most 250 KB gzip (P); admin, reports and grid code lazy-loaded | | NFR devices | static files from the approuter, hashed names, cached 1 year; `index.html` no-cache |

Time split for S1 (target): HTML 150 ms + JS parse 300 ms + three parallel API calls (250 ms server + ~300 ms network)
+ render 100 ms = about 1.1-1.3 s. A cold first visit adds the bundle download (~1 s on 4G).

### 2.2 Operations (server time p95 at the design peak, 5-year rows)

| Operation | p95 | Rows touched (5 y) | Payload (JSON, before gzip) | Change against architecture 6.1 |
|---|---|---|---|---|
| `getToday` (MVP: bookings, released today, `nextTwoWeeks`, "N of M free tomorrow") | 250 ms (target 150 ms) | ≤ 3 bookings + ≤ 14 own index entries for the strip (index-only, desk code from the cached desk list, closed days from the cached calendar) + one count of the next working day (~1,500 index entries, or cache hit). R1 adds `usualDesk`: ~60 own index entries + one slot probe | ~5-6 KB raw (strip 14 x ~120 B), ~1.5 KB gzip; was ~3 KB | strip added (D6); `usualDesk` moved to R1; count cached (PF-9) |
| `listMyBookings` | 250 ms | ≤ 20 per page (index range, employee, date) | ~12 KB per 20 rows | same |
| `listFreeDesks` page of 50 | 300 ms MVP; 50 ms on an R1 cache hit | 1,500 desks probed against the slot index, sort by code, 50 returned | ~13 KB per 50 (~2-3 KB gzip) | same; R1 cache key adds reserved visibility (PF-10) |
| `proposeDesks` 14 days | 400 ms | one set read of occupied desks for the 14 dates (~20,000 index entries in the largest office) + cached desk list | ~5 KB | must be set-based (PF-2) |
| `createBookings` | 100 ms per day: 3 days 300 ms, 10 days 1.0 s, 14 days 1.4 s | per day: 1 booking + 2 slots + audit rows, own transaction | request ≤ 16 KB, answer ~8 KB for 14 | was 150 ms/day: 10 days = 1.5 s server leaves too little of AC19.10's 2 s (PF-3) |
| `createBooking` | 400 ms (target 100 ms) | 1 booking + 1-2 slots | ~1 KB | same |
| `checkIn`, `holdBooking`, `cancelBooking` | 400 ms (target 60 ms) | 1 booking update (version) (+ slots on cancel) | ~1 KB | same |
| `getBookingCalendar`, `listBookableOffices` | 150 ms (20 ms on cache hit) | office row + closed days in 14 days | ~2 KB | TTL must not outlive the end of today's part (PF-15) |
| `getOccupancyReport` 3 months all offices | 3 s page 0; 300 ms next pages | ~150,000 index entries (366-day max: ~600,000) | ~20 KB per 100 rows | aggregate once per filter (PF-13) |
| `getOccupancyGrid` one office, 31 days (**R1, moved out** by D6; budget kept for R1) | 1 s | ~37,000 index entries of one office + ≤ 1,500 desks | ~160 KB raw for 40 zones x 31 days (~15-20 KB gzip); 62 days doubles it | compact cells (PF-14) |
| Admin reads / writes | 400 ms | paged, ≤ 100 | ≤ 30 KB | same |
| `exportReport` (xlsx; **MVP, moved in** by D7; counts only, same filter as `getOccupancyReport`) | 31-day filter, all offices (~1,550 rows, ~50,000 index entries): 2 s server, file ~100 KB, saved within 5 s. 93-day contract maximum (~4,650 rows, ~150,000 entries): 6 s server, file ~300 KB. Ceiling 20 s for 30,000 rows (AC12.8 allows 30 s) | same aggregate as the report (cache hit if the table was just viewed: +0.5 s to write) + rows written one by one with a small row window | xlsx 100 KB-2 MB, never held in memory whole (heap under 50 MB per export). **Size limit**: 100,000 rows and 93 days as in the contract; over that the call is refused, not cut (PF-22) | new in the MVP; was "R1" |
| `getTeamWeek` (R1) | 500 ms | 40 reports x 7 days | ~10 KB | same |

### 2.3 Jobs

| Job | Budget | Peak work | Check |
|---|---|---|---|
| `ReleaseBookingsJob` (every minute) | every due booking released within 5 min of its deadline (R30); target max lag 3 min, one run drains the 10:00 peak in under 30 s (P) | 540 (Y1) / 720 (Y5) at 10:00, ~15 ms each = 8-11 s | only if one run loops over batches (PF-1) |
| `PreReleaseReminderJob` | 860 / 1,150 outbox rows enqueued within 60 s of T-15 (P) | chunked inserts of 200 | partial deadline index |
| `NotificationDispatchJob` | last reminder of the 09:45 spike sent by 09:50 (T-10) (P); release mails within 10 min | 860-1,150 mails in the reminder minute; 540-720 at 10:00 | needs 4 mails/s sustained (PF-5, PF-11) |
| `PeopleSyncJob` | under 10 min (AC14.1); target 3 min | 30-40 SF pages x 1-3 s, apply ~5 s | fine (section 4.7) |
| Purge jobs (3) | under 5 min each, chunks of 1,000, night UTC | ~2,700 slots, ~3,600 outbox rows a day | fine |

## 3. Hot paths: query, index, rows, payload, caching, what breaks first

### 3.1 Today on load (`getToday`, AC18.7) - MVP carries the 14-day strip, `usualDesk` is R1
- Queries (MVP): (a) next 3 own bookings: `ix_bkg_bookings_employee_date` range from today, LIMIT 3, join-fetch
  desk/floor/zone names for those 3 rows only; (b) released today: same index, date = today; (c) the strip
  `nextTwoWeeks` (D6, moved in): same index, employee and booking_date from today to today + 13, status, office and
  desk_id from the INCLUDE, at most 14 rows (one per day, `uq_bkg_bookings_employee_date`), index-only; desk code from
  the cached office desk list, no join per row; closed days and non-working days for the 14 dates from the cached
  office calendar (`OfficeClock`, PF-15); (d) "N of M free tomorrow": M = bookable desks of the office (desk list,
  cacheable), N = M minus desks with an active booking on that date.
- R1, not built in the MVP (moved out): `usualDesk` (query 16: same index, last 60 days, office filter and status from
  the INCLUDE, group by desk, at most ~60 entries, index-only) and the probe "usual desk free on the next working day"
  (one probe of `uq_bkg_booking_slots_desk_date_half`). When R1 adds them they cost ~60 index entries and one probe;
  the 250 ms budget holds.
- Index check: (a)-(c) served by `ix_bkg_bookings_employee_date` INCLUDE (desk_id, office_id, status). OK.
  (d) is best read from `ix_bkg_bookings_office_date` INCLUDE (desk_id, part, status) WHERE status IN (BOOKED,
  CHECKED_IN), index-only, ~1,500 entries in the largest office. OK with the existing index.
- Payload: the strip is 14 cells x ~120 B (date, status, part, office, desk code, closed flag) = ~2 KB, so `getToday`
  grows from ~3 KB to ~5-6 KB raw (about 1.5 KB gzip). No extra round trip: this is what PF-12 asked for (two calls
  less on 4G at 08:00).
- Caching: (a)-(c) no cache (own data, AC5.11; the strip must show a booking made 1 s ago). The calendar and desk list
  it reads are cached (section 4). (d) is the same for everyone of the office: cache 5 s per (tenant, office, date,
  can-see-reserved) (PF-9). At P1 that turns ~25 count queries/s into ~2 per 5 s.
- What breaks first: nothing at 5-year volume; the risk is the client side (three serial calls on 4G = +0.7 s).
  The parallel load of S1 is a UI rule (PF-16).

### 3.2 `proposeDesks` (up to 14 days)
- Rule R63 needs, per day, the set of free desks of the office and her usual desk/zone/floor. The architecture says
  "one free-desk query per day". At 14 days and 1,500 desks that is 14 anti-joins of 20-50 ms each, 0.3-0.7 s: over the
  400 ms budget at P1 and rate-limited at 20/min, so a slow call cannot be hidden by retries.
- Design (PF-2): one query for all dates on `ix_bkg_bookings_office_date` (office, booking_date = ANY(:dates),
  status IN (BOOKED, CHECKED_IN)) returning (desk_id, booking_date, part), index-only, at most ~20,000 entries; the
  office desk list (id, code, zone, floor, features, bookable_from, retired_on; ≤ 1,500 rows) from a cache evicted on
  any desk/floor/zone change; usual desk from query 16 once. R63 runs in memory per day, lowest code first.
  Expected 30-60 ms.
- Payload: ≤ 14 proposals x ~350 B = ~5 KB.
- What breaks first: the per-day loop as the largest office grows; with the set-based read nothing does before 10,000 desks.

### 3.3 `createBookings` (batch of 14 days)
- Per day (query 4/18): idempotency check on `uq_bkg_bookings_idempotency` (key `<key>:<date>`), insert booking (unique
  `uq_bkg_bookings_employee_date`), insert 1-2 slots (unique `uq_bkg_booking_slots_desk_date_half`), audit change log
  (B6), commit. ~20-40 ms per day on PostgreSQL including the commit flush. Fourteen commits are fine.
- Must not repeat per day (PF-3): employee and profile lookup, office row and `OfficeClock` (working days, closed days,
  horizon), check-in policy, usual desk and desk list for a re-pick. Read once per request.
- Re-pick (R66): on `DESK_JUST_TAKEN` re-run R63 for that day only, with a fresh read of that day's occupied desks
  (one index-only query), then one retry insert. At most 2 re-picks per day, then FAILED (bounded).
- Contention: two people re-picking the same zone collide on the lowest free code (R63 is deterministic). At P1 with
  ~15 bookings/s across 3,000 desks the collision rate is low (< 2 %); the bound above keeps it from looping.
- Budget: 100 ms per day p95, so 10 days = 1.0 s server and the 2 s of AC19.10 holds on 4G.
- Rate limits (05-security): 3 requests/min and 30 booking-days/min per user; a 14-day batch plus a few singles fits.

### 3.4 `listFreeDesks` (S2b Change picker, AC4.10)
- Query 2: floors of the office (`uq_ofc_floors_office_name`), desks of those floors (`ix_ofc_desks_floor_code`)
  with bookable_from/retired_on, NOT EXISTS active slot (`uq_bkg_booking_slots_desk_date_half`, one probe per desk),
  ORDER BY code, OFFSET/LIMIT 50, plus `totalFree` over the same set; features batched by `uq_ofc_desk_features_desk_feature`
  (no N+1). 1,500 probes ~ 20-40 ms. Index check OK. Offset paging is fine at ≤ 1,500 rows.
- Grouping by zone (option B list): the page is sorted by code, so zone groups split across pages and "Floor 3 · n free"
  cannot be counted from the loaded pages. Sort by floor, zone, code and return per-zone free counts (≤ 40) with page 0
  (PF-8).
- Caching: MVP none. R1 (ADR-8) 1 s per (tenant, office, date, part) must add reserved visibility to the key (PF-10).
- Search log (RP-6): the YAML says every call records the search outcome. With R1 polling that is ~75 rows/s
  (~270,000 an hour) and a write in a read path; data model 9 sized `rpt_search_log` at 2 M a year, which only
  holds if polls and next pages are not logged (PF-6).
- R1 polling: if the SPA refetches every loaded page of the infinite list every 4 s, three loaded pages are
  45 calls/min, over the 30/min `listFreeDesks` limit, so a user who only watches gets 429 (PF-7).
- What breaks first: the poll volume (P5), not the query.

### 3.5 Release job at 10:00 (`ReleaseBookingsJob`, query 6)
- `findDue(now)`: `ix_bkg_bookings_booked_deadline` (tenant, check_in_deadline) WHERE status = 'BOOKED', ORDER BY
  deadline LIMIT 200: a range scan on a partial index of ~20,000 entries. OK.
- Per booking: update booking with version, deactivate 1-2 slots (`ix_bkg_booking_slots_booking`), outbox insert
  (`uq_ntf_notifications_event`), audit rows; ~15 ms in its own transaction.
- Volume: 540 (Y1) / 720 (Y5) due in the same minute. The design takes one batch of 200 per run: 720 needs 4 runs, so
  the last booking is released at deadline + up to 60 s schedule + ~75 s start latency + 3 more minutes = ~5 min 15 s,
  over R30's 5 minutes. A run must loop over batches until none is due or a 45 s budget (PF-1): then 720 x 15 ms =
  ~11 s in the first run.
- Race with check-in at 09:59:58 (AC8.4): the version check makes the release skip; no lock is held across the batch.
- What breaks first: the single-batch rule, then the scheduler's start latency (architecture risk 1).

### 3.6 Reminders and mail around 09:45-10:05 (`PreReleaseReminderJob`, `NotificationDispatchJob`)
- 860 (Y1) / 1,150 (Y5) reminders fall in the same minute. Dispatch takes 200 rows per run with a 50 s budget and 4
  workers at ~0.3 s per mail: ~13 mails/s possible, but capped at 200 a run, so 1,150 need 6 runs and the last
  reminder leaves at ~09:51. Let a run take further batches while its 50 s budget lasts (PF-11): 2 runs.
- The mail sender is still open (Q53, Q64). An Exchange Online mailbox over SMTP is limited to about 30 messages a
  minute, which would send the last of 860 reminders ~29 minutes after 09:45, after the release, and delay the 10:00
  release mails by another 18 minutes. The chosen sender must take at least 300 mails/min (PF-5).
- Enqueue: insert reminders in chunks of 200 per transaction so the reminder job does not hold one long transaction.

### 3.7 Occupancy report, export (MVP) and grid (R1) (S17)
- Report (query 9): `ix_bkg_bookings_office_date` INCLUDE (floor_id, desk_id, part, status, original_deadline,
  cancelled_at), group by office, floor, date. 3 months all offices ~150,000 entries; 366 days ~600,000. Index-only
  only where the visibility map is set: the last days are updated all the time (status), so recent pages need heap
  fetches until autovacuum runs (PF-17). Capacity: desk intervals (≤ 4,000 rows) x days x closed days; compute per floor
  in memory from one desk read, not by joining a generated day series to every desk (PF-13).
- Paging at 100 rows with totals over the whole filter (Q95) means page 2..n recompute the full aggregate unless it is
  kept: cache the computed rows and totals per (tenant, filter) for 60 s and slice pages from it (PF-13). 92 days x
  50 floors = 4,600 rows, 46 pages.
- Export (`exportReport`, ST-RP-4, MVP since D7, moved in): the same filter and the same aggregate as the report, so the
  same cost: 31 days all offices ~50,000 index entries (~1,550 rows), 93 days ~150,000 entries (~4,650 rows). Plan:
  (1) take the rows from the report aggregate cache of PF-13 when the same filter is in it, else compute once;
  (2) release the database connection, then write the xlsx row by row with a small row window and stream it, so a slow
  client download never holds a connection and heap stays under 50 MB; (3) counts only, no names (D7). Budget: server
  2 s for 31 days, 6 s for 93 days, ceiling 20 s for 30,000 rows (AC12.8: under 30 s). Size limit: the contract's
  100,000 rows and 93 days; a filter over that is refused with the contract's error, never silently cut. At most 2
  exports run at once per instance (PF-22). Payload: ~100 KB (31 days) to ~2 MB (30,000 rows x ~12 columns).
- Grid (query 17, **R1, moved out of the MVP by D6**; kept here for R1): one office, ≤ 31 days: ~37,000 entries of
  `ix_bkg_bookings_office_date` (INCLUDE desk_id) joined to that office's desks (≤ 1,500) as one grouped SQL statement
  (hash join), never an entity walk booking -> desk -> zone (EclipseLink N+1 risk). Capacity per zone and day from the
  same cached desk list. ~50-150 ms.
- Grid payload (R1): 40 zones x 31 days = 1,240 cells x ~130 B (a 36-char zone uuid and a date in every cell) = ~160 KB
  raw; at 62 days (05-ui says 62, the YAML 31, Q121a) ~320 KB. Send cells as arrays indexed by zone and day position
  (~60 KB at 31 days) and keep gzip on (PF-14).

### 3.8 People copy (SF full read, `PeopleSyncJob`)
- Full read each run (no delta, 05-integrations 1). `User` with `$select` 8 fields and `$expand=manager,personKeyNav`,
  `$top=200`, `$orderby=userId`, sequential: 3,000 active plus inactive history = 30-40 calls x 1-3 s = 1-2 min;
  ~4 MB in memory; apply in one transaction in chunks of 500, writing only changed rows (normally < 50) so audit
  stays small. Well inside AC14.1 (10 min). Index check: `uq_ppl_employees_user` for the match, `ix_ppl_employees_manager`
  for the manager status update (one set-based statement).
- Timing: 01:00 UTC is 06:30 IST, before check-in opens in India; an hourly retry after a failure can land in the 08:30-10:30
  IST rush. Its database load (~5 s of writes, no long locks under MVCC) is small enough to allow that; no change needed.
- What breaks first: SF throttling and page latency above ~20,000 users (scale trigger in 05-integrations 1.8). Page size
  1,000 (sf-fields) would cut the call count by 5 when needed.

## 4. Caching summary

| Data | Where | Key | TTL / eviction | Why safe |
|---|---|---|---|---|
| Office row, settings, closed days, calendar | backend Caffeine | (tenant, office) | 60 s and on `OfficeSettingsChanged`; for today never past the end of the current part (PF-15) | rules re-checked on write |
| Office desk list (id, code, floor, zone, features, dates) | backend Caffeine | (tenant, office) | evict on any desk/floor/zone/feature change, 5 min max | used by proposeDesks, the `getToday` strip, capacity (grid: R1); free state is never cached here |
| "N of M free tomorrow" | backend Caffeine | (tenant, office, date, can-see-reserved) | 5 s | not personal; spec allows 5 s freshness |
| Free-desk page (R1) | backend Caffeine | (tenant, office, date, part, can-see-reserved, page) | 1 s + local eviction (ADR-8) | freshness 5 s across instances |
| Report aggregate (report pages and `exportReport`) | backend Caffeine | (tenant, filter) | 60 s | counts only; the export reuses it when the same filter was just viewed |
| Labels, theme, locales | HTTP | locale + version | ETag + `Cache-Control: max-age` | static per release |
| SPA assets | approuter / browser | hashed file name | 1 year immutable; `index.html` no-cache | standard |
| JPA second-level cache | EclipseLink | - | off for booking and people entities (PF-4) | several instances |

No cache on own bookings (`getToday` bookings part, `listMyBookings`, `getBooking`): AC5.11 needs them fresh.

## 5. Load-test plan for S7 (k6, scripts in `work/desk-booking/perf/`)

Environment: a test space sized like production (2 backend instances, the same PostgreSQL plan, approuter in front, a
mail stub, an SF stub). The developer starts it; the scripts only call it. Server metrics from Micrometer if Q67 is
accepted, otherwise from k6 timings plus `pg_stat_statements`.

Seed (one script, synthetic, no real names): 8 offices in two timezones (6 in IST to make the shared-minute case),
3,000 desks (one office 1,500, 40 zones), 3,500 active + 3,000 inactive employees, 2.25 M historic bookings over 5 years,
the next 14 days filled to 80 %, slots for the last 90 days, autovacuum run once (then a second run without it).

| # | Scenario | Shape | Pass |
|---|---|---|---|
| T1 | Monday rush (P1) | ramp to 500 VUs in 2 min, hold 15 min, think 3-8 s; mix: getToday 25 % (with `nextTwoWeeks`, no `usualDesk`), profile/user 15 %, proposeDesks 15 %, listFreeDesks 20 %, createBookings 5 %, createBooking 3 %, checkIn 7 %, listMyBookings 5 %, cancel 2 %, calendar/offices 3 % | each op meets 2.2 p95; errors < 0.1 %; S1 composite < 2 s; DB CPU < 60 % |
| T2 | Check-in burst (P2) | 865 check-ins in 30 min with a 3x peak minute, on top of T1 at 50 % | checkIn p95 < 400 ms; no 409 except the intended races |
| T3 | Last-desk race | 50 VUs book the same desk in the same second; 100 VUs send 14-day batches over overlapping desks; each press sent twice with the same key | exactly one booking per desk-half and per employee-day; REPICKED/FAILED per day as R65-R66; createBookings 14 days p95 < 1.4 s |
| T4 | Release at 10:00 (P4) | 720 BOOKED due at 10:00 IST; 100 check-ins between 09:59:30 and 10:00:30; 200 VUs on Today | max release lag (released_at - deadline) < 5 min, p95 < 3 min; AC8.4 race keeps the check-in; request p95 unchanged |
| T5 | Reminders and mail (P3) | 1,150 reminders due 09:45; mail stub 0.3 s per mail; second run with the stub throttled to 30/min | last reminder sent before T-10 with the real sender rate; the throttled run shows the PF-5 failure |
| T6 | Reports and export (MVP) | 10 admins: 3-month all-offices report + 5 pages; then `exportReport` for the 31-day and the 93-day all-offices filter, 5 at once (P7), alone and on top of T1 at 50 % | page 0 < 3 s, next pages < 300 ms; export 31 days < 2 s server and < 5 s to the saved file, 93 days < 6 s server; a filter over 93 days or 100,000 rows is refused, not cut; 2 running per instance, the rest answered 429 with Retry-After; heap per export < 50 MB; T1 request p95 unchanged; file sizes logged |
| T7 | R1 polling soak (P5) | 300 VUs poll `listFreeDesks` every 4 s for 30 min, some with 3 loaded pages, across 2 instances | cache hit rate > 80 %; zero 429 for a watching user; a taken desk disappears within 5 s |
| T8 | People copy during load | SF stub with 6,500 rows, 200 per page, 1.5 s per page, run during T1 | finishes < 10 min; T1 p95 unchanged |
| T9 | Soak | 2 h at 50 % of T1 (with a 93-day export every 10 min) | no growth in heap, connections or response time |
| T10 | R1 only (moved out of the MVP): heat grid and usual desk | grid one office 31 and 62 days, 10 admins; `getToday` with `usualDesk` at T1 load | grid < 1 s, payload logged; `getToday` p95 still < 250 ms with `usualDesk`; run when R1 is built, not at the MVP S7 |

Query checks before T1: `EXPLAIN (ANALYZE, BUFFERS)` on queries 2, 5, 6, 9, the 14-day strip read of 3.1 (MVP) and the PF-2 set read (queries 16 and 17 are R1: at R1 time) against the
seed; record plan, buffers and heap fetches per query in `07-performance.md`.

## 6. Findings

| Id | Level | Owner | Finding | Fix |
|---|---|---|---|---|
| PF-1 | MUST | solution-architect | `ReleaseBookingsJob` takes one batch of 200 per run; 720 due at 10:00 need 4 runs and the last is released ~5 min 15 s after the deadline (R30 is 5 min) | loop batches inside one run until none due or a 45 s budget; keep per-booking transactions (Q122) |
| PF-2 | MUST | solution-architect | `proposeDesks` runs one free-desk query per day: 14 x 20-50 ms breaks its 400 ms budget | one set read of occupied desks for all dates on `ix_bkg_bookings_office_date` + cached office desk list; R63 in memory (Q123) |
| PF-3 | MUST | solution-architect | `createBookings` at 150 ms/day makes 10 days 1.5 s server, leaving < 0.5 s of AC19.10's 2 s for network and render | budget 100 ms/day; read employee, profile, OfficeClock, closed days, desk list once per request; re-pick re-reads only that day, at most 2 times (Q123) |
| PF-4 | MUST | solution-architect | EclipseLink's shared (L2) cache is on by default; with 2+ instances a check-in, cancel or release done on one instance is not seen by reads on another (stale `getToday`, wrong allowed actions, freshness > 5 s) | shared cache off for `bkg_*`, `ppl_*`, `ntf_*` entities (or globally), confirm the base default (Q124) |
| PF-5 | MUST | solution-architect (with PO for the sender choice) | mail sender not chosen (Q53, Q64); a mailbox-based SMTP sender at ~30/min sends the 09:45 reminders up to 29 min late, after the release | the sender must take ≥ 300 mails/min (1,150 reminders + 720 release mails at 5 years); test in T5 (Q125) |
| PF-6 | MUST | api-designer | `listFreeDesks` "records the search outcome" on every call; with R1 polls and scroll pages that is ~270,000 rows an hour and a write in a read path | record only user-started searches (page 0, not refetch or next page; for example a `trigger` query value the SPA sets), asynchronously, outside the request transaction (Q126) |
| PF-7 | MUST (R1) | ux-designer | R1 polling with an infinite list refetches every loaded page: 3 pages x 15/min = 45/min, over the 30/min limit, so a watching user gets 429 | poll page 0 (count, `asOf`) only and drop rows that are gone from loaded pages on the next scroll or on Choose (Q127) |
| PF-8 | SHOULD | api-designer | S2b groups by zone with "Floor n · m free" but pages are sorted by code; zone groups split across pages and counts need all 500 rows | sort by floor, zone, code; add per-zone free counts (≤ 40) to page 0 |
| PF-9 | SHOULD | solution-architect | the "N of M free tomorrow" count is the same for the whole office but runs for every `getToday` (~25/s at P1) | compute from `ix_bkg_bookings_office_date`, cache 5 s per (office, date, can-see-reserved) |
| PF-10 | SHOULD (R1) | solution-architect | R1 1 s free-desk cache key has no reserved-visibility part (also 05-security row 5) | add can-see-reserved to the key; two variants per office/date/part |
| PF-11 | SHOULD | solution-architect | dispatch caps a run at 200 rows although its 50 s budget fits ~600 | keep taking batches while the budget lasts; enqueue reminders in chunks of 200 |
| PF-12 | SHOULD - DONE by D6 (strip is MVP) | api-designer | the day strip would add `listMyBookings` + `getBookingCalendar` to S1 (two more calls on 4G at 08:00) | decided: `getToday.nextTwoWeeks` carries the 14-day strip (bounded, own data); budget in 2.2 and 3.1; keep it out of S1's call list (links to Q120) |
| PF-13 | SHOULD | solution-architect | report pages recompute the full aggregate for totals; capacity per desk per day is costly if done as a generated series join | cache rows + totals per filter for 60 s and slice pages; capacity per floor in memory from one desk read |
| PF-14 | SHOULD (R1, grid moved out) | api-designer | grid cells repeat a zone uuid and a date: ~160 KB at 31 days, ~320 KB at 62 days | cells as arrays by zone and day position; gzip on at the approuter; settle 31 vs 62 days (Q121a) |
| PF-15 | SHOULD | solution-architect | `getBookingCalendar` 60 s cache can still show today's part as bookable up to 60 s after it ended | TTL never past the next part end of the office (the write path refuses anyway, so this is display only) |
| PF-16 | SHOULD | ux-designer | S1 at 08:00 on 4G: serial `getCurrentUser` -> `getMyProfile` -> `getToday` costs ~0.7 s more than parallel | start the three calls together; skeleton until `getToday`; employee JS ≤ 250 KB gzip, admin/reports lazy |
| PF-17 | SHOULD | data-architect | report and usual-desk queries rely on index-only scans, but status updates on recent `bkg_bookings` rows clear the visibility map; status in INCLUDEs and partial predicates also makes every status update a non-HOT update across all 8 indexes (fine at ~7,000 updates a day) | table autovacuum settings for `bkg_bookings` and `bkg_booking_slots` (vacuum scale factor 0.02, analyze 0.01); check heap fetches in the S7 EXPLAIN pass |
| PF-18 | SHOULD | solution-architect | the job node also serves requests; at 10:00 release, reminder and 4 dispatch workers take connections from the same pool | cap job connections (≤ 6) or keep the job node out of the request route; pool 20 per instance |
| PF-19 | SHOULD | solution-architect | sessions in SPRING_SESSION mean a read and a last-access update per request (~150 writes/s at P1) | confirm the backend needs a session behind the approuter JWT; if yes, measure it in T1 |
| PF-20 | SHOULD | solution-architect | budgets can only be proven server-side with metrics; without Q67 S7 reports server p95 as Not measured | accept Q67 (Micrometer) or log request time per operation in the access log |
| PF-21 | SHOULD | data-architect | in the MVP no job completes CHECKED_IN bookings (`CompleteBookingsJob` is R1), so their slots stay active until the 90-day purge and the "active" partial indexes hold 90 days, not 14 | accept for MVP (bounded by the purge) or move the complete step into the release job; note only |
| PF-22 | SHOULD | solution-architect | `exportReport` (MVP since D7) builds an xlsx for up to 93 days x all offices (cap 100,000 rows) in one request; several exports at once, or a slow client download, would hold a database connection and heap on the same nodes that serve P1 | read the aggregate first (reuse the PF-13 cache), release the connection, then stream with a row-window writer (heap < 50 MB per export); at most 2 exports running per instance (a third gets 429 with Retry-After); over 93 days or 100,000 rows is refused, not truncated; log rows and ms per export; test in T6 |

No finding for the data model's index set (the 14-day strip read in 3.1 uses the same employee/date index; queries 16 and 17 are R1 now): every hot query in section 3 has an index that serves it (queries 2, 4, 5,
6, 9, 16, 17, 18 and the PF-2 set read on `ix_bkg_bookings_office_date`). No partitioning is needed for `bkg_bookings`
within 5 years (2.25 M rows), as data model 9 says.

## 7. Open questions

Q122-Q127 in `questions.md` (PF-1 to PF-7). Q121a (grid range 31 vs 62 days) already open; PF-14 depends on it and is
now an R1 matter. PF-22 (export concurrency) needs no new question: the 2-per-instance cap is a proposed (P) number the
architect may change. The export range stays as the contract says (93 days, 100,000 rows); the design size is 31 days.
