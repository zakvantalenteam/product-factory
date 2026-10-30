# ADR-1 One deployable, modules by package

Status: proposed (S5, 2026-10-28)

## Context
DeskBook has eight business areas (M1-M8), 3,000 users, 500 at peak, two developers. The base (B1, B9) is one Spring Boot WAR with feature packages and one SPA. Some areas need each other in both directions: office setup must know whether bookings exist (close, retire, code lock); the people sync must cancel a leaver's bookings; booking needs offices and people.

## Options
1. Microservices per area - separate deployables and databases.
2. One WAR, modules by package, any class may call any other.
3. One WAR, modules by package with a public service per module, no cross-module repositories or JPA relations, cycles broken by ports (interface declared by the upstream module, implemented downstream) and Spring events.

## Decision
Option 3. Dependency graph in 05-architecture section 3 (time <- office <- booking <- checkin/notification/reports/team; people <- access <- booking). `office` declares `BookingImpactPort`, `booking` implements it. `people` publishes `EmployeeLeft`, `booking` listens in the same transaction. Notifications listen with `@TransactionalEventListener(BEFORE_COMMIT)`.

## Consequences
- One deploy, one transaction for "cancel bookings when a desk is blocked", simple local development on the base.
- Module rules must be checked in review (an ArchUnit-style test is recommended but adds a test dependency; until then the code reviewer checks imports).
- A later split into services is possible along the same boundaries.
