# ADR-4 Release and reminders as minute jobs with per-booking optimistic updates

Status: proposed (S5, 2026-10-28; revised after the S5 design review, M9)

## Context
Release within 5 minutes after the deadline (R30); a job that was down catches up and releases once with one email (AC8.5); a check-in saved at 09:59:58 wins (AC8.4); two runs change nothing (CI-5). The base job framework is TTCommon (B4): schedule types include MINUTE, ad hoc start latency about 75 s, jobs run on the node role in `allowedNodeRoles`. Audit (B6) is written by the EclipseLink descriptor listener, so bulk JPQL updates would skip it.

## Options
1. Spring `@Scheduled` in every instance - runs N times, outside the job page, no run history.
2. TTCommon job every 5 minutes with one bulk UPDATE - may miss the 5-minute promise and bypasses audit.
3. TTCommon job every minute; select due bookings in batches of 200; release each in its own short transaction through the entity with its version.

## Decision
Option 3 for `ReleaseBookingsJob` (checkin module), and the same pattern for `PreReleaseReminderJob` and `NotificationDispatchJob`. One run loops: it takes the next batch of 200 until none is due or 45 s of the run are used (PF-1), so the first run drains a 10:00 peak of 720 in about 11 s; `NotificationDispatchJob` loops the same way within 50 s and at the configured mail rate (ADR-5). A version conflict means the booking changed (checked in, cancelled, held) and is skipped. Catch-up is the same query. The released event writes an outbox row with a unique event key, so a repeated release cannot send twice.

## Consequences
- Worst case lag about deadline + 60 s + 75 s + ~11 s drain at the 5-year peak, about 2.5 minutes, inside 5 minutes; to be verified in sprint 1 on BTP (risk 1).
- Every release is audited like a user change (changed_by = job name, B6.2).
- 540 (year 1) to 720 (5 years) bookings share the 10:00 deadline when offices share a timezone (05-performance 3.5); one batch per run would need 4 runs and miss R30 by about 15 s, hence the loop.
