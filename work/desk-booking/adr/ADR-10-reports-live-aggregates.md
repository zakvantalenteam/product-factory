# ADR-10 Reports as live aggregates; snapshot only if measured

Status: proposed (S5, 2026-10-28)

## Context
Occupancy per office, floor and office-local day with capacity in desk-days, half day 0.5, blocked and retired desks not capacity, no-show rate (R39-R42, Q50); 3 months for all offices under 5 s (AC12.12); about 2 M booking rows after 4 years; numbers unchanged by anonymisation (AC12.13).

## Options
1. Live grouped queries over bookings, plus capacity from desk dates (`bookable_from`, `retired_on`) and blocks.
2. A nightly snapshot table per office, floor and day.

## Decision
Option 1 in MVP through `booking.BookingStatsQuery` and `office` capacity queries; reporting index (tenant_id, office_id, booking_date). Anonymisation nulls the employee only, so counts stay. If the RP-5 load test misses 3 s server time, the snapshot is added as an additive change.

## Consequences
- Always current (today included), no second source of truth; desks need dated active periods (RP-3 DB task).
- 3 months for all offices is about 110,000 bookings - a grouped index scan, well inside budget.
