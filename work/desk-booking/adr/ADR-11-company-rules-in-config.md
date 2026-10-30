# ADR-11 Company booking rules in the base ConfigService

Status: proposed (S5, 2026-10-28)

## Context
Company-wide values: booking horizon 14 days (G6), hold length release + 90 minutes (Q49), late-booking check-in 30 minutes (P1), pre-release reminder 15 minutes (P2). The admin edits the horizon (S19). The base stores tenant settings in CONFIGURATION via `ConfigService`, with change history in CONFIGURATION_AUDIT (B5).

## Options
1. A new `bkg_booking_rules` table with one row per tenant.
2. ConfigService keys in a new group `DESKBOOK` registered in the product ConfigurationHelper (B1.17): `DESKBOOK_HORIZON_DAYS`, `DESKBOOK_HOLD_MINUTES`, `DESKBOOK_LATE_CHECKIN_MINUTES`, `DESKBOOK_PRE_RELEASE_REMINDER_MINUTES`.

## Decision
Option 2; `booking` owns the keys, validates them (horizon 1-60) and caches them for 60 s. `getBookingRules` / `updateBookingRules` are `/api/v1` operations with problem details.

## Consequences
- No new table; history comes from CONFIGURATION_AUDIT, not B6 (accepted: these are settings, not business records).
- Values are strings in storage; typed and validated in one service.
- Version for If-Match (Q93): a counter key `DESKBOOK_RULES_VERSION` in the group, returned as `version` and raised by one in the same transaction as every save; stale If-Match gives 409 `CONCURRENT_UPDATE`. Two saves within milliseconds can both pass (accepted: rare, admin-only, audited).
- Changed hold or late check-in minutes apply to new bookings and holds only; a smaller horizon never cancels existing bookings (Q96).
