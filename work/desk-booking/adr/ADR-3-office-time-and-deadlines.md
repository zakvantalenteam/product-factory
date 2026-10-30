# ADR-3 Office-local dates, UTC deadlines, one OfficeClock

Status: proposed (S5, 2026-10-28)

## Context
Every time rule is in the office's own timezone (R9, Q3): release 10:00 and 14:00, midday 13:00, check-in opens 06:00 / 12:00, late bookings get 30 minutes (P1), a hold moves the deadline to release + 90 minutes (P2, Q49), reminders 15 minutes before. Offices span Asia/Kolkata and Europe/Berlin; DST changes (AC3.6). A settings change applies from tomorrow (R10). The release job must find due bookings fast across all offices.

## Options
1. Store local times only and compute "is it due" per office in the job on each run.
2. Store the booking date as the office-local date plus part, and store the computed check-in deadline as a UTC instant on the booking; one `OfficeClock` computes it.

## Decision
Option 2. `common/time/PartOfDayRules` is pure Java (`java.time`, ZoneId from the office) with a 20+ case table including DST gaps (shift forward) and overlaps (earlier offset). `office/OfficeClockService` loads the office settings and calls it. `createBooking` and `holdBooking` store `check_in_deadline` (UTC), `deadline_kind` (NORMAL, LATE, HOLD) and keep the original deadline. When `updateOfficeSettings` changes release times, `booking` recomputes the deadlines of BOOKED bookings dated tomorrow or later in that office (event `OfficeSettingsChanged`); today's bookings keep theirs.

## Consequences
- The release job is one indexed query (`status = BOOKED and check_in_deadline <= now`) for all offices.
- No other module does its own time maths (EN-2 criterion).
- A timezone change of an office with future bookings would shift them; the timezone is editable only while the office has no future bookings (`HAS_FUTURE_BOOKINGS`).
