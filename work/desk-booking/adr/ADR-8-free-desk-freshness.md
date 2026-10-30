# ADR-8 Free-desk freshness by polling with a short server cache

Status: proposed (S5, 2026-10-28; applies from R1, ST-BK-3)

## Context
A desk taken by someone else disappears from other lists within 5 seconds (R15, AC4.4); a failed refresh keeps the old list with "Showing data from N seconds ago" (AC4.5). Up to 500 people at once; the backend runs on several instances behind the approuter.

## Options
1. Server-sent events or WebSocket push - needs long-lived connections through the approuter, a broadcast across instances, more moving parts.
2. Polling `listFreeDesks` from the SPA while visible, with a short per-instance cache.

## Decision
Option 2: poll every 4 s while the tab is visible (pause when hidden); server Caffeine cache 1 s per (tenant, office, date, part), evicted locally on any booking change in that office and day. The response carries `asOf` for the stale banner.

## Consequences
- Worst case 5 s across instances; no new infrastructure.
- About 125 requests per second at 500 users on S2, mostly cache hits; covered by the RP-5 load test.
