# ADR-2 Double booking prevented by booking slots with partial unique indexes

Status: proposed (S5, 2026-10-28)

## Context
A desk holds one person per half day (A16); a full-day booking occupies morning and afternoon (R13); one active booking per employee per day (R17); first request wins (R18, AC5.3) and a double click books once (AC5.4). 500 people book at Monday 08:00. Application-level "check then insert" races.

## Options
1. Check in the service, then insert - races between two requests.
2. Pessimistic lock on the desk row (`SELECT ... FOR UPDATE`) - serialises bookings per desk; works, but every path that frees or takes a desk must lock the same way.
3. PostgreSQL exclusion constraint on a range per desk - precise, but needs `btree_gist` and DDL patterns that EclipseLink does not model.
4. A slot table: one row per booking and half day (`MORNING`, `AFTERNOON`) with `active`; partial unique index (tenant_id, desk_id, booking_date, half) WHERE active; plus partial unique index on bookings (tenant_id, employee_id, booking_date) WHERE status IN (BOOKED, CHECKED_IN).

## Decision
Option 4. `createBooking` inserts the booking and its 1-2 slots in one transaction; the database refuses the loser. The backend maps the constraint name to `DESK_JUST_TAKEN` or `ALREADY_BOOKED_THAT_DAY` (the base handler alone would answer `DUPLICATE`). Release, cancel and (later) leave early set the slots inactive in the same transaction. An `Idempotency-Key` on create returns the first result on a replay.

## Consequences
- Correct under any concurrency and any number of instances, no locks held.
- Slots are derived data: opted out of audit with a reason; data-architect owns the exact DDL (Flyway).
- Constraint names become part of the code contract; a test against PostgreSQL (not mocks) is required.
- The free-desk query is an anti-join on slots - indexed and cheap.
