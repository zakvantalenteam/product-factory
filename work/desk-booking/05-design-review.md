# Design review - DeskBook (system-reviewer, design mode)

Stage S5, 2026-10-28. Scope: the MVP of prototype option A "Plan my week" (decisions.md D5), plus the R1 items that
the MVP contract or security rules already carry. Inputs: `02-spec.md`, `03-journeys.md`, `04-stories.md`,
`04-backlog.csv`, `05-architecture.md` + `adr/`, `05-openapi.yaml` (grepped, not read whole), `05-api-notes.md`,
`05-data-model.md`, `05-security.md`, `05-integrations.md`, `05-sf-fields.md`, `05-ui.md`, `05-performance.md`,
`questions.md` Q83-Q127. Nothing else was changed.

**Verdict: not PASS. Ready for G3 after the 14 MVP MUST fixes below** (one of them, M2, waits for the user's answer to
G3 questions 1 and 2). PF-7 is a MUST for R1 and does not block G3.

## 1. Coverage

| Chain | Count | Result | Breaks |
|---|---|---|---|
| MVP stories (backlog, release MVP) -> task | 38 stories, 139 pts | 36 have their own task rows in architecture 5.2 (93 tasks: 27 FE, 44 BE, 22 DB) | ST-BK-13 and ST-BK-14 have no rows of their own; their work sits under ST-BK-8 (S7) |
| MVP story -> operation or job | 38 / 38 | every MVP story reaches an operation (api-notes 1, stories column) or one of the 7 MVP jobs | - |
| Task -> story in the same release | 93 | 4 task rows build R1 stories inside MVP stories | ST-BK-11 rows build the usual-desk card (ST-BK-16, R1) and the two-week strip (ST-BK-15, R1); ST-RP-1 rows build the heat grid (ST-RP-10, R1) (M2) |
| MVP operations: api-notes -> YAML | 45 + 17 base = 62 | 62 operationIds in the YAML, all 45 MVP ids match | - |
| Operation -> access row (05-security 2.1, 2.2a, 2.2) | 45 / 45 | every operation has a row and an `x-roles` value | - |
| Operation -> table(s) (05-data-model 7, 13) | 45 / 45 | office ops -> `ofc_*`; booking ops -> `bkg_*`, `ofc_*`, `ppl_*`; rules -> ConfigService DESKBOOK; profile -> `ppl_employees`; reports -> `bkg_bookings`, `ofc_desks` | - |
| Operation -> screen (05-ui) | 44 / 45 in an MVP screen | 44 are called from S1-S4, S2b, S6, S10-S12, S17, S19 | `createBooking` has no MVP screen: S2/S3 book through `createBookings`; only R1 S5 calls it (S8) |
| Jobs -> story | 7 / 7 | Release, PreReleaseReminder, NotificationDispatch, PeopleSync, three purge jobs (CI-4/5/6, NT-1/2/3, PP-1/2/3, EN-1) | - |
| MVP tables -> used by an operation or job | 12 / 12 | `ofc_offices`, `ofc_floors`, `ofc_zones`, `ofc_desks`, `ofc_features`, `ofc_desk_features`, `ofc_closed_days`, `ppl_employees`, `ppl_sync_runs`, `bkg_bookings`, `bkg_booking_slots`, `ntf_notifications` | `ppl_employees.sf_person_id` from 05-sf-fields is missing (S5) |
| MVP screens -> journey and story | 11 / 11 | S1, S2, S2b, S3, S4, S6, S10, S11, S12, S17, S19 each have stories; journeys J1, J2, J4, J5 and J7 (plan my days) in 02-spec | 03-journeys still describes the pre-A S2 "Book a desk" and S3 dialog (S6) |
| Personal data -> retention | 6 / 6 columns in data model 11 | all have a rule | leavers' name and email wait for the R2 `AnonymiseJob` (Q85 open) (S15) |
| Spec non-functional numbers -> design answer | all | 05-architecture 6.1 and 05-performance 2 give a budget for each | 6 MVP budgets fail as designed today (PF-1 to PF-6) |
| MVP acceptance criteria -> contract field | - | 3 MVP criteria have no field to show | AC18.4 bookable count, AC5.12 hold time, AC19.4 changed desk (M4); option A choices need zone and feature options (M3) |

## 2. Settled disagreements

| # | Disagreement | Recommended answer | Who changes what |
|---|---|---|---|
| 1 | Grid range 31 days (architecture 8.1, YAML) vs 62 days (05-security 2.2a, row 45, Q114; 05-ui S17) (Q114, Q121a) | **31 days.** It matches Q95's answer and the YAML, keeps the answer near 160 KB (PF-14), and a month is the Facilities view. Longer ranges use the paged table and the R1 export | security-architect and ux-designer (M6, M7) |
| 2 | `getOccupancyGrid` MVP in ADR-12, YAML `x-release: MVP` and the task split vs ST-RP-10 in R1 | **Product owner decides (G3 question 2). Recommended: R1, as sized.** The MVP S17 shows B's table (ST-RP-1 to ST-RP-3 are met by it). The operation stays in the YAML with `x-release: R1`, MVP operations become 44 | solution-architect, api-designer, story-sizer after the answer (M2) |
| 3 | Proposal without a desk: architecture 8.1 `desk ... \| null` vs YAML omits `desk` and `reason` and sets `noneReason` (Q121b) | **Absent, not null** (the file rule; the YAML is already right) | solution-architect fixes 05-architecture 8.1 (S2) |
| 4 | QR scan checks in at once (Q91, answered) vs no action ever runs from a URL (Q74, open) (Q118) | **One exception:** the R1 desk page runs `checkInByDesk` on load only when the signed-in caller has her own booking on exactly that desk, today, inside the check-in window; the server decides; the URL carries the desk code only. Email links and every other route never act. Close Q74 with this wording | security-architect (S3) |
| 5 | Two-week strip in R1 (ST-BK-15) although it is step 1 of option A's journey (Q120) | **Product owner decides (G3 question 1). Recommended: move ST-BK-15 into the MVP (+3 pts, MVP 142),** served by `getToday` (14 days, own data, PF-12) instead of two more calls; ST-BK-16 usual-desk card stays R1 | story-sizer, solution-architect, api-designer after the answer (M2) |
| 6 | Employee zone and feature options missing: S2 has Zone and Must-have chips, `proposeDesks` takes `zoneId`/`featureIds`, but `listZones`/`listFeatures` are admin-only (Q115) | Add `zones[]` (id, name, floorName) and `features[]` (id, name) of the office to `BookingCalendar`; no person data, same cache | api-designer (M3) |
| 7 | Display fields missing (Q116) | MVP criteria need three now: `TomorrowFree.bookableDesks` (AC18.4), `Booking.holdUntil` (AC5.12), `previousDeskCode` on REPICKED (AC19.4, Q117). `CalendarDay.parts[].freeDesks` and `features` on Booking/UsualDesk can follow (SHOULD) | api-designer (M4, S11) |
| 8 | Idempotency key: YAML `format: uuid` (36), 05-security 16-64 `[A-Za-z0-9_-]` without `:`, data model `varchar(80)` sized for 64 + `:` + date | No runtime break (36 + 11 = 47 fits 80). **Keep the UUID** (05-ui 0.2 sends only UUIDs): YAML adds a UUID `pattern` and `maxLength: 36`; 05-security 4.2a says "UUID, 36 characters, so no `:`"; the column stays `varchar(80)` | api-designer, security-architect (S1) |
| 9 | 05-integrations vs 05-sf-fields: status filter, location code, `sf_person_id` | **Follow 05-sf-fields.** Filter `status in 't','f'`; a leaver is an explicit `f`; an absent person is counted as MISSING, cancels nothing, and stays under the 10 percent guard; `T`/`F`/`e`/`d` users are not copied (Q112). Location: compare case-insensitively, store as received, read `EmpJob.location` in the same call if the tenant sample is not the bare code (Q111, Q77). Add nullable `sf_person_id` (Q110) | integration-engineer (M8, S4), data-architect (S5) |
| 10 | 7 performance MUSTs (05-performance 6) | Accepted as written, with one change to PF-6: in the MVP `listFreeDesks` records nothing, because `rpt_search_log` is R1 | owners as in M9-M14 and PF-7 |
| 11 | Spec still on pre-D2 rules: AC4.7, AC5.7, R14, R20, R28, AC8.7 (cut-off G16), F8 (no hold, no RELEASED_AFTER_HOLD), F13 (no 15-minute reminder) | Rewrite to D2/P1-P2 as 04-stories states it: today is bookable until the part ends, a late booking must be checked in within 30 minutes, a 15-minute reminder, one Running late hold. Q100 is moot after this: she can book again until the part ends | requirements-analyst (M1) |

## 3. Findings

### MUST (14 for the MVP, 1 for R1)

| Id | Where | Problem | Owner | Fix |
|---|---|---|---|---|
| M1 | 02-spec F4 R14, AC4.7; F5 R20, AC5.7; F8 R28, AC8.7; F13 R45 | Spec still refuses same-day bookings after the cut-off (G16) and has no 15-minute reminder or Running late hold, which contradicts D2, ST-BK-7, ST-CI-6, ST-CI-7, ST-NT-2 and the contract (`PART_ENDED`, `holdBooking`, `deadlineKind`) | requirements-analyst | D2 revision of those rules and criteria (disagreement 11); also AC19.8 "beyond 14 days" -> "beyond the booking horizon"; mark Q100 answered by D2 |
| M2 | 05-architecture 5.2 (ST-BK-11 rows "usual desk card and two-week strip", ST-RP-1 heat-grid rows), ADR-12, YAML `getOccupancyGrid` `x-release: MVP`, 05-security 2.2a | The design builds three R1 stories (ST-BK-15, ST-BK-16, ST-RP-10, 10 pts) inside MVP stories, so MVP points and the build plan disagree with the approved backlog | solution-architect (with story-sizer and api-designer) | After G3 questions 1-2: move the task rows to the stories and releases the user picks; set `x-release` and the operation count (45 or 44); story-sizer updates the points |
| M3 | YAML `BookingCalendar`; 05-ui S2 | No employee operation returns zone and feature options, so the S2 controls and the reason MATCHES_CHOICES (ST-BK-8) cannot work | api-designer | Add `zones[]` and `features[]` to `BookingCalendar` (disagreement 6); security-architect confirms the row stays "no person data" |
| M4 | YAML `TomorrowFree`, `Booking`, per-day result of `createBookings` | Three MVP criteria have no field: AC18.4 "40 of 57 desks free" (no bookable count), AC5.12 "keeps the desk until the hold time" (no `holdUntil`), AC19.4 "says which desk changed" (no `previousDeskCode`) | api-designer | Add `bookableDesks`, `holdUntil` (absent when no hold is possible), `previousDeskCode` as read-only fields |
| M5 | YAML `/reports/occupancy/grid` | The small-cell rule of 05-security row 45 and 4.2a (zones with fewer than 3 desks, or holding a reserved desk, merged into a floor row) is not in the contract; 05-ui S17 already shows the merged row. Without it a cell can show one person's attendance (D2) | api-designer | Write the rule in the description and the merged-row shape (`zoneId` absent, `merged: true`, floor name) |
| M6 | 05-security 2.2a, row 45, 4.2a, "Still open" line; Q114 | Grid range 62 days vs 31 in the YAML and architecture | security-architect | Change to 31 days (disagreement 1); close Q114 with 31 and the 3-desk threshold |
| M7 | 05-ui S17 (line ~401) | The screen offers 62 days; the YAML refuses more than 31 with VALIDATION_ERROR | ux-designer | Range picker capped at 31 days, with a hint to use the table for longer ranges |
| M8 | 05-integrations 1.2 "Filter: none", 1.3 status, 1.6 leavers | A full read without a filter never returns leavers as `f`; absence (scope or permission change) is treated as leaving and cancels bookings; external `T` users are copied and can book | integration-engineer | Adopt 05-sf-fields 1.3 (disagreement 9); data-architect adds the MISSING count to `ppl_sync_runs` |
| M9 | 05-architecture 4.3, 6.3 (PF-1, Q122) | Release job takes one batch of 200 per run; the last of 720 is released about 5 min 15 s late (R30 is 5 min) | solution-architect | Loop batches in one run until none is due or 45 s are used |
| M10 | ADR-12, architecture 5.2 ST-BK-8 (PF-2, Q123) | `proposeDesks` runs one free-desk query per day, 14 days break its 400 ms budget | solution-architect | One set read of occupied desks on `ix_bkg_bookings_office_date` + cached desk list, R63 in memory |
| M11 | ADR-12 (PF-3, Q123) | `createBookings` at 150 ms a day leaves under 0.5 s of AC19.10's 2 s for 10 days | solution-architect | 100 ms a day; read employee, profile, clock, closed days and desk list once per request; at most 2 re-picks |
| M12 | 05-architecture 6.2 (PF-4, Q124) | EclipseLink shared cache on by default; with 2+ instances `getToday` shows stale status and actions | solution-architect | Shared cache off for `bkg_*`, `ppl_*`, `ntf_*` (or globally); confirm the base default |
| M13 | 05-integrations 2.4, Q53, Q64 (PF-5, Q125) | Mail sender not chosen; a mailbox sender at ~30 a minute sends 09:45 reminders after the release | solution-architect (sender choice: G3 question 6) | Require at least 300 mails a minute; prove in load test T5 |
| M14 | YAML `listFreeDesks` description (PF-6, Q126) | Every call "records the search outcome": a write inside a read on every poll and page; the table it writes (`rpt_search_log`) is R1 | api-designer | MVP: records nothing. R1: record user-started searches only (page 0, SPA `trigger` value), asynchronously, outside the request transaction |
| PF-7 (R1) | 05-ui S2b polling (ST-BK-3) | Polling every loaded page is 45 calls a minute, over the 30-a-minute limit | ux-designer | Poll page 0 only; drop rows that are gone on the next scroll or on Choose. Before R1 build, not G3 |

### SHOULD

| Id | Where | Problem | Owner | Fix |
|---|---|---|---|---|
| S1 | YAML `IdempotencyKey`, 05-security 4.2a, data model 4.8 | Three different key rules (no break today) | api-designer, security-architect | Disagreement 8 |
| S2 | 05-architecture 8.1 (line ~580) | `desk ... \| null` contradicts the absent-not-null rule and the YAML | solution-architect | Disagreement 3 |
| S3 | 05-security 4.3, Q74, Q118 | QR auto check-in vs no action from a URL (R1) | security-architect | Disagreement 4; settle before the R1 build |
| S4 | 05-integrations 1.3 `location` | Upper-case compare and "admin types the name" vs 05-sf-fields 3 (case-insensitive, `EmpJob.location` fallback) | integration-engineer | Follow 05-sf-fields after the Q77 tenant sample |
| S5 | 05-data-model 4.6 | `sf_person_id` (Q110) missing | data-architect | Nullable `varchar(100)`, index (tenant_id, sf_person_id), in the MVP migration (additive, avoids a backfill later) |
| S6 | 03-journeys screen inventory S2, S3 | Still the pre-A "Book a desk" list with filters and a confirmation dialog | ux-designer | Align with 05-ui (S2 Plan my days, S2b, S3 result page) and point to spec J7 |
| S7 | 05-architecture 5.2 | ST-BK-13 and ST-BK-14 (MVP, 7 pts) have no task rows; their work is filed under ST-BK-8 | solution-architect | Re-key the multi-day rows to ST-BK-13 and the picker rows to ST-BK-14 |
| S8 | 05-architecture 5.2 FE rows ST-BK-5, ST-BK-6, ST-BK-7, ST-PP-4 | FE tasks name `createBooking` for S3; 05-ui S3 and S2 use `createBookings` | solution-architect | Point the FE rows at `createBookings`; `createBooking` stays as the single-day command (ADR-12) whose screen caller is R1 S5 and R1 S8 |
| S9 | 02-spec AC5.12; 05-ui `HowCheckInNote` | The MVP box would tell people to scan a desk QR, which is R1 (ST-CI-2) | requirements-analyst, ux-designer | MVP text without the QR line; add it with ST-CI-2 |
| S10 | 02-spec AC19.3, AC19.12; YAML `listFreeDesks` | "Grouped by zone ... and filters" but the zone and feature filters on `listFreeDesks` are R1 (ST-BK-2) | api-designer | Add the optional `floorId`, `zoneId`, `featureIds` now (additive, same query) and sort by floor, zone, code with per-zone counts on page 0 (PF-8) |
| S11 | YAML `CalendarDay`, `Booking`, `UsualDesk` | Prototype display fields "12 free" per day and desk features (Q116 a, c) | api-designer | `parts[].freeDesks` (cached like `listFreeDesks`), `features` as FeatureRef[] |
| S12 | YAML `UsualDesk` description; Q97 | "At least 3 bookings in 60 days" (AC18.3, data model, security test 15) is not in the contract | api-designer | Add it; close Q97 after G3 question 3 |
| S13 | questions.md | Answered in effect but still open: Q98, Q99, Q117 (covered by the YAML), Q100 (moot after D2), Q102-Q108 (D2 list Q39-Q44, stories TM-3, TM-4, OS-2, OS-4, OS-14, PP-7, EN-3), Q121 a-c (settled here) | lead | Mark answered with the source |
| S14 | 05-ui 9 S12 desk dialog | Shows the accessibility flag in the MVP; `ofc_desks.reserved` is R1 (ST-PP-10) | ux-designer | Hide in the MVP |
| S15 | 05-data-model 11, Q85 | Leavers' name and email stay until the R2 `AnonymiseJob`; no date for the pilot | security-architect, data-architect | Confirm with Legal that the pilot may keep them until R2, or add leaver anonymisation to the MVP `SyncRunPurgeJob` |
| S16 | Q86, YAML `updateDesk` | Floor change after the first booking not settled | solution-architect | Floor locked like the code (`DESK_FLOOR_LOCKED`), zone may change |
| S17 | Q87 | Audit retention 24 months and trimmed booking audit not confirmed | base-builder | Accept as recommended |
| S18 | 05-performance 6 PF-8 to PF-21 | 14 SHOULDs | owners named there | As written there |

## 4. Questions for the user at G3

Only what the product owner can decide. Each has the recommended answer.

1. **Two-week strip on Today (ST-BK-15, Q120): MVP or R1?** Recommended: MVP (+3 pts, MVP 142), because it is step 1 of the approved option A journey; the usual-desk card (ST-BK-16) stays R1.
2. **Heat grid on Reports (ST-RP-10): MVP or R1?** Recommended: R1 as sized; the MVP report shows the occupancy table. When it comes, zones with fewer than 3 desks or with a reserved desk are merged into their floor row, so no cell shows one person.
3. **What is a person's "usual desk" (Q97)?** Recommended: the desk she booked most in the last 60 days, at least 3 times; a tie goes to the most recent.
4. **Can a closed office be reopened (Q84)?** Recommended: no in the MVP; closed is final, and a reopened office is created as a new office.
5. **Who may book (Q109)?** Recommended: employees and contingent workers; external users are not copied from SuccessFactors.
6. **Mail sender (Q125, Q53, Q64):** Recommended: the customer provides a mail API or relay that takes at least 300 mails a minute (not a personal mailbox); we prove it in the load test.

## Re-review after fixes

Re-review pass, 2026-10-28, after the owners' fixes and decisions D6 (G3 answers 1-6) and D7 (ST-RP-4 `exportReport` R1 -> MVP, MVP 147 points). Line numbers are from the files as they stand now.

### MUST status

| Id | Status | Evidence |
|---|---|---|
| M1 | FIXED | 02-spec R14 (l.88), AC4.7 (l.97), R20 (l.109), AC5.7 (l.117), R28 (l.162), AC8.7 (l.173), R45 (l.266), AC19.8 "beyond the booking horizon" (l.358), "Changes for D2" (l.531-541); questions.md Q100 `[answered]` (l.110) |
| M2 | STILL OPEN | D6 half done: 05-architecture 5.2 item 14 (l.307-310), ST-BK-15 rows (l.343-344), 5.3 ST-BK-16 and ST-RP-10 R1 (l.425, l.450); YAML `getOccupancyGrid` `x-release: R1` (l.4168); 04-backlog MVP sums to 147. Not done: D7 in 05-architecture and the 05-security matrix (see N1, N2) |
| M3 | FIXED | YAML `BookingCalendar` `zones` and `features`, both required (l.6279-6299) |
| M4 | FIXED | YAML `TomorrowFree.bookableDesks` (l.6847, required l.6856), `holdUntil` (l.6460), `previousDeskCode` (l.6666) |
| M5 | FIXED | YAML `getOccupancyGrid` description, small-cell rule (l.4165) and merged-row examples `merged: true` (l.4219, l.4253) |
| M6 | FIXED (one leftover in N2) | 05-security row 45 "Range at most 31 days" (l.61), 4.2a (l.160), "Still open" line (l.334); questions.md Q114 has the answer (l.126) but is still tagged `[open]` (l.125) |
| M7 | FIXED | 05-ui S17 range picker capped at 31 days, `reports.heat.tooLong` (l.430-432, label l.773) |
| M8 | FIXED | 05-integrations 1.2 filter `status in 't','f'` (l.44), 1.3 status (l.60), 1.6 MISSING cancels nothing (l.21, l.101-104), external users not read (l.22); 05-data-model `missing_count` (l.214, V011 l.410); 05-sf-fields 4 "Absent from the read ... not a leaver" |
| M9 | FIXED | 05-architecture 4.3 loop of batches until none due or 45 s (l.213, l.226), job table (l.515) |
| M10 | FIXED | 05-architecture one set read on `ix_bkg_bookings_office_date` (l.178, budget l.484); ADR-12 (l.17) |
| M11 | FIXED | 05-architecture 100 ms a day, shared reads once (`BookingContext`), at most 2 re-picks (l.181-182, l.485); ADR-12 (l.25) |
| M12 | FIXED | 05-architecture 6.2 `eclipselink.cache.shared.default=false` with fallback (l.500-505) |
| M13 | FIXED | 05-integrations 2.4 at least 300 mails a minute, fallback, load test (l.202-207, l.235); 05-architecture (l.547-551); D6 answer 6 |
| M14 | FIXED | YAML `listFreeDesks` "A read that records nothing in the MVP (the search log is R1)" (l.2674); no `rpt_search_log` in the YAML |

Fixed 13 of 14 (M6 with one leftover); M2 still open.

### What the fixes changed

| Check | Result | Evidence |
|---|---|---|
| `exportReport` in the contract | OK | YAML `GET /reports/occupancy/export`, `x-release: MVP`, ST-RP-4, counts only, 100,000 rows, 93 days (l.4097-4106); 05-api-notes (l.6, l.58) |
| `exportReport` access row | MISSING | 05-security has it only in 2.3 "R1 operations" (l.108); 2.1/2.2a MVP matrix has no row (N2) |
| `exportReport` story | OK | 04-stories ST-RP-4 MVP (l.1037, D7 note l.70); 04-backlog `ST-RP-4,...,MVP` |
| `exportReport` screen | MISSING | 05-ui S17 "Export to Excel (R1; hidden in MVP)" (l.399, l.406, l.418) (N3) |
| `exportReport` budget | WRONG RELEASE | 05-performance "exportReport (R1)" (l.79); 05-architecture budget "(R1, 30,000 rows)" (l.488) (N1, N4) |
| `getToday.nextTwoWeeks` (MVP) | YAML and architecture OK; 05-ui MISSING | YAML (l.3493, l.3532, l.6903); 05-architecture (l.308, l.344, l.632-634); 05-ui still "DayStrip (R1, ST-BK-15)", next 8 working days from `listMyBookings` + `getBookingCalendar` (l.11, l.68, l.80-81, l.98) (N3); 05-performance S1 "R1 strip adds listMyBookings + getBookingCalendar" (l.51), `getToday` budget without the 14 days (l.68) (N4) |
| `getOccupancyGrid` R1 everywhere | NO | R1 in YAML (l.4168), api-notes (l.117), architecture (l.414, l.450, l.486), 05-ui (l.76, l.400); still MVP in 05-security 2.2a row 45 under "45 MVP operations (42 + 3)" (l.30, l.55-61, l.330) (N2); 05-performance S17 MVP budget calls it with no release mark (l.57, l.77) (N4) |
| MVP points 147 | OK | 04-stories totals (l.33, l.35, l.1399); 04-backlog sums MVP 147, R1 125, R2 26, Later 15, 85 stories. Leftover: 04-stories "Not in the MVP: ... next-two-weeks strip, ... Excel export" (l.1392) (N5) |
| MVP operations 45 | NO | YAML 45 + 17 base (info l.8; 62 MVP-tagged operations counted); api-notes 45 (l.6); 05-architecture still "44 MVP" (l.470) and "MVP operations 44" (l.634) (N1); 05-security says 45 but counts the grid and not the export (N2) |
| Architecture task split | NO | 5.2 has rows for 37 of the 40 MVP stories in 04-backlog: ST-RP-4 missing (still R1 in 5.3, l.447) (N1); ST-BK-13, ST-BK-14 missing is S7, still open; heading "5.2 MVP (34 stories)" (l.315) |
| 05-integrations vs 05-sf-fields (Q128, Q129) | AGREE | Same rules: filter `t`,`f`, MISSING counted and never cancels, 10 percent guard over newly `f` plus missing (integrations l.19, l.95; sf-fields 4); `DESKBOOK_SF_LOCATION_SOURCE` USER/EMPJOB, no detection, FIELDS_MISSING on EMPJOB without the nav (integrations l.62, l.70, l.142; sf-fields 3; Q128, Q129 `[answered]` l.144-145). Two stale sentences, see S19, S20 |

### New MUST

| Id | Where | Problem | Owner | Fix |
|---|---|---|---|---|
| N1 | 05-architecture 5.2, 5.3 (l.447), operations line (l.470), 8.1 (l.634), budget table (l.488), heading (l.315) | D7 not applied: ST-RP-4 is still an R1 row, the MVP build plan has no export task, MVP operations say 44, the export budget says R1 | solution-architect | Move ST-RP-4 to 5.2 with BE (`exportReport`, streamed .xlsx of the `getOccupancyReport` rows, 100,000-row and 93-day bounds, formula-cell prefix) and FE (Export button on S17) rows; operations 45 MVP + 30 R1 + 5 R2 + 3 Later; budget row MVP; heading to the real MVP story count (40) |
| N2 | 05-security 2 header (l.30), 2.2a row 45 (l.61), 2.3 Reports (l.108), changes (l.330, l.334); questions.md Q114 (l.125) | The MVP matrix still holds `getOccupancyGrid` (R1 since D6) and lacks `exportReport` (MVP since D7); Q114 still `[open]` though D6 answer 2 accepted the 3-desk merge | security-architect | Move row 45 to 2.3 (keep the small-cell and 31-day rules); add an MVP row for `exportReport` in 2.1 (admin, all offices or one, counts only, same row set as `getOccupancyReport`, `= + - @` cells prefixed, rate limit); keep the count at 45; mark Q114 answered (31 days, 3 desks, D6) |
| N3 | 05-ui S1 (l.11, l.68, l.80-81, l.98, l.150), S17 (l.399, l.406, l.418), Q120 note (l.822) | Two-week strip still R1 and built from `listMyBookings` + `getBookingCalendar` over 8 working days; the Export button is hidden in the MVP | ux-designer | S1 DayStrip in the MVP from `getToday.nextTwoWeeks` (14 office-local days, states BOOKED, BOOKABLE, CLOSED, OUTSIDE_WINDOW, no extra call); S17 Export button in the MVP calling `exportReport` with the table filter, with loading, too-large and error states |
| N4 | 05-performance S1 (l.51), `getToday` (l.68), S17 (l.57), grid (l.77), export (l.79) | Budgets still follow the pre-D6/D7 scope | performance-engineer | `getToday` budget includes `nextTwoWeeks` (own bookings for 14 days + closed days); S1 without the R1 calls; S17 MVP budget = cards + table + export, grid marked R1; `exportReport` MVP, 20 s for 30,000 rows, in a load test |
| N5 | 04-stories MVP scope line (l.1392) | "Not in the MVP" still lists the next-two-weeks strip and the Excel export | story-sizer | Remove both from that line |

### New SHOULD

| Id | Where | Problem | Owner | Fix |
|---|---|---|---|---|
| S19 | 05-sf-fields 1.3 (l.73) | Still says 05-integrations treats a missing row as a leaver | sf-consultant | Past tense: "05-integrations used to ..."; now agreed (Q128) |
| S20 | 05-integrations (l.22) | "pending the product owner's G3 answer 5" though D6 answered it | integration-engineer | Cite D6 answer 5 (employees and contingent workers, no external users) |
| S21 | 05-data-model `left_at` (l.196) | "inactive or missing" starts the retention clock, but a missing person is not a leaver (M8, Q128) | data-architect | `left_at` only when status `f` is seen |
| S22 | YAML `getOccupancyGrid` `x-stories` | Lists ST-RP-1 (MVP) next to ST-RP-10 | api-designer | ST-RP-10 only |

S1-S18 not re-checked except S7 (still open: ST-BK-13 and ST-BK-14 have no rows in 05-architecture 5.2).

### Verdict

G3: NOT PASS. Open: M2 and new MUSTs N1-N5, all from D6/D7 not reaching 05-architecture, 05-security, 05-ui, 05-performance and one line of 04-stories. The contract (YAML, api-notes), the backlog and the integrations pair are consistent. When N1-N5 are fixed, M2 closes with them and G3 passes without another product decision.


## Final re-check (G3)

Final re-check, 2026-10-28, of M2 and N1-N5 after the owners' fixes (D6, D7). Grep only at the named spots; line numbers are from the files as they stand now.

| Item | Verdict | Evidence |
|---|---|---|
| M2 | FIXED | D6 and D7 now in every document: 05-architecture 5.2 item 14 (l.307), ST-BK-15 rows (l.343-344), ST-RP-10 R1 in 5.3 (l.425-ff); 05-security matrix 45 MVP with `exportReport` (l.30, l.54, l.96) and grid in 2.3 as R1 (l.108); YAML `getOccupancyGrid` `x-release: R1` (l.4168), `exportReport` `x-release: MVP` (l.4105); 04-stories MVP 147 (l.68, l.70, l.1382) |
| N1 | FIXED | 05-architecture 5.2 holds ST-RP-4 FE row (l.406) and BE row `exportReport` (l.407, 100,000 rows); 5.3 has no ST-RP-4 row; "MVP operations: 45" (l.413); "45 MVP + 30 R1 + 5 R2 + 3 Later = 83" (l.471); budget row "exportReport (MVP, D7; 30,000 rows)" 20 s (l.489); 8.1 "MVP operations 45 (exportReport is MVP, D7)" (l.635); no "44 MVP" left. Leftover: heading l.315 (see 1) |
| N2 | FIXED | 05-security 2 header "45 MVP operations (42 + 2 + exportReport from D7)" (l.30); row 45 `exportReport` in the MVP matrix: admin only, counts only, same small-cell rule, `= + - @` prefixed, 93 days, 100,000 rows, rate limit (l.54, rate 5/min l.273); `getOccupancyGrid` only in 2.3 R1 (l.108) and as "(R1)" in the rate list (l.273); counts line 45 rows (l.96); changes note (l.330). Q114 split: Q114a `[answered]` (questions.md l.126); Q114 kept `[open]` for the number 3 only (see 2) |
| N3 | FIXED | 05-ui S1 DayStrip "MVP, ST-BK-15" from `getToday.nextTwoWeeks`, 14 days, no second call (l.68, l.89-90, l.99); story line (l.11, l.80); no "R1 strip" or "8 working days" text left. S17 button "Export to Excel" MVP with `exportReport` (l.405, l.411, l.431) and an Export section with Ready, Disabled empty, Disabled too long (93 days), Exporting, Done, Error states (l.441-452), labels (l.779-783); no "hidden in MVP" text for the export |
| N4 | FIXED | 05-performance: D6/D7 change table (l.13-21); S1 budget with `nextTwoWeeks` in the `getToday` answer, no `listMyBookings`/`getBookingCalendar` (l.67); `getToday` row with the 14-day strip (l.85); S17 table budget with grid "R1, moved out" (l.73); S17 export row MVP, 5 s for 31 days, 10 s for 93 days (l.74); `exportReport` row MVP, 93 days, ceiling 20 s for 30,000 rows (l.96); load test T6 for 31 and 93 days (l.265); grid budget marked R1 (l.94) |
| N5 | FIXED | 04-stories scope line now: "The next-two-weeks strip (ST-BK-15, D6) and the Excel export (ST-RP-4, D7) are in the MVP" (l.1392); both removed from the "Not in the MVP" list |

### Minor leftovers (not MUST)

1. 05-architecture l.315 heading still "5.2 MVP (34 stories)"; the MVP has 40 stories (04-stories l.1382). Also S7 still open: ST-BK-13 and ST-BK-14 have no rows in 5.2. Owner: solution-architect.
2. questions.md l.125 Q114 is still `[open]` for the small-cell number 3; D6 answer 2 accepted the merge, so the PO only needs to confirm the number. 05-security l.334 says the same. Not a gate blocker. Owner: security-architect / PO.
3. S19-S22 from the earlier review were not re-checked here (05-sf-fields 1.3 wording, 05-integrations l.22 wording, 05-data-model `left_at`, YAML `getOccupancyGrid` `x-stories` listing ST-RP-1).

G3: PASS
