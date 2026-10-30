# ADR-12 Plan my week: desk proposals and several days in one action

Status: proposed (S5, 2026-10-28, after gate GP; revised after the S5 design review, M10 and M11, and after G3 D6 for M2)

## Context
At gate GP the user approved prototype option A (D5): the employee picks the days she comes in, the app proposes the best free desk for each day with a reason, she can change any day, and "Book 3 days" makes three separate bookings (Q90). ST-BK-8 Best desk moves from R1 into the MVP. The R1 design had one call `bookBestDesk` that chose and booked a desk in one step for one day. Option A needs the proposal shown before booking, several days per action, and a clear partial result when a day fails (option A weakness: a proposed desk can be taken between seeing and booking).

## Options
1. Keep `bookBestDesk` and call it once per day from the browser.
2. `proposeDesks` (read, no side effect) + `createBookings` (one request, each day its own booking and transaction, per-day result, re-pick of a taken proposed desk).
3. `proposeDesks` + `createBookings` all-or-nothing (one transaction for all days).

## Decision
Option 2.
- `DeskProposalRules` is pure (no Spring, no DB) in `booking`; `DeskProposalService` feeds it free desks from `OfficeQueryService` and the person's own bookings. Order: usual desk (D6: the desk she booked most in that office in the last 60 days, at least 3 times, a tie goes to the most recent; no usual desk below 3) -> lowest free code in the usual desk's zone -> lowest free code matching the chosen zone/features -> lowest free code in the office. Chosen zone/features filter every step. Reasons: USUAL_DESK, SAME_ZONE, MATCHES_CHOICES, FIRST_FREE. Reserved desks (R1) only for people on the access list.
- `createBookings` handles 1-14 distinct days. Each day runs `BookingCommandService.create` in its own transaction with every rule of `createBooking`. A day whose PROPOSED desk was just taken is proposed again and booked on the next desk (REPICKED); a CHOSEN desk that was taken, or any other refusal, is FAILED with the usual problem code. Booked days stay booked. The `Idempotency-Key` of the request is stored per day as `<key>:<date>`, so a replay returns the same booked days.
- Reads are set-based (PF-2, PF-3). `proposeDesks` reads the occupied desks of all chosen dates in one index-only query on `ix_bkg_bookings_office_date` (office, date in the list, status BOOKED or CHECKED_IN) and takes the office desk list from a Caffeine cache (60 s, evicted on desk, floor or zone change); R63 runs in memory per day. `createBookings` builds one `BookingContext` per request (person, profile, office and OfficeClock, closed days, check-in policy, usual desk, desk list) that each day's `BookingCommandService.create` uses; only the day's inserts and commit repeat. A re-pick re-reads that day's occupied desks only, at most 2 re-picks per day, then FAILED. `createBooking` builds the same context for its one day.
- `createBooking` stays for single bookings (and for R1 manager booking). R1 `createBookingForReport` uses `DeskProposalService` for "the zone where most of the team sits".

## Consequences
- 44 MVP operations (+`proposeDesks`, +`createBookings`), `bookBestDesk` removed; about +5 points as D5 expects.
- D6 (M2): the heat grid `getOccupancyGrid` is R1 with ST-RP-10 (MVP Reports is the occupancy table); the "Your usual desk" card (`getToday.usualDesk`, ST-BK-16) is R1, while the same rule feeds USUAL_DESK proposals in the MVP; the two-week strip (ST-BK-15, MVP) comes from `getToday.nextTwoWeeks`, not from two more calls (PF-12).
- All-or-nothing (option 3) is rejected: one taken day would undo the others and hold locks over 14 inserts; the per-day result is what the prototype shows.
- Proposals are deterministic and explainable; they are not stored (no preferences table, in line with 5.1 item 10).
- Budgets: `proposeDesks` 400 ms for 14 days (expected 30-60 ms); `createBookings` 100 ms per day, 10 days 1.0 s server, inside AC19.10's 2 s. The desk list cache can be up to 60 s stale on another instance; every write re-checks the rules, so a retired desk is refused or re-picked, never booked.
- The first proposal can be stale by the time she books; re-pick handles it and the result says which days moved.
