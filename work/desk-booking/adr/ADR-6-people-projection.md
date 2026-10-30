# ADR-6 DeskBook keeps its own employee projection from SuccessFactors

Status: proposed (S5, 2026-10-28)

## Context
DeskBook needs per person: user id, name, email, direct manager, home office, active (Q11), manager status (R52), leavers (R51), last good copy date (R49), manual records matched by email (Q60). The base user sync (B4.5) fills TTCommon user tables (LXP_USER_DETAILS) through `UserDetailsService`; whether it keeps manager and home office is not confirmed (Q54).

## Options
1. Extend the base user sync and read TTCommon user tables - mixes product rules into platform plumbing; TTCommon fields unknown.
2. Read the TTCommon user tables after the base sync and derive manager and office - depends on fields that may not exist and on the job order.
3. A DeskBook `PeopleSyncJob` reading the SF User API through the base `SuccessFactorsClientService` (B5 connection, B5.9 readiness) into `ppl_employees` and `ppl_sync_runs`.

## Decision
Option 3. Selected fields only; paged 200; upsert by SF user id; records without email skipped and counted; manager status computed after the run; leavers raise `EmployeeLeft`. Hourly schedule that works once per day (nightly copy plus hourly retry in one job). The sign-in identity is matched to `ppl_employees` by user id (Q62).

## Consequences
- DeskBook owns its people rules and can add `addPerson` (R1) without touching the base.
- Two copies of person data in one database (base and DeskBook); retention and anonymisation apply to both (security-architect).
- If the base SF client cannot select manager or location fields, the job needs its own OData call (PP-1/PP-2 grow, Q54).
