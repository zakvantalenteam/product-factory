# ADR-9 State changes as POST /<resource>/{id}/<action>

Status: proposed (S5, 2026-10-28) - lead to record in decisions.md (api-standards asks for one style per product)

## Context
DeskBook has many non-CRUD state changes with different inputs and rules: check-in, hold, cancel (bookings); open, close (offices); retire (floors, desks). The base demo uses one generic `POST /<resource>/{id}/transition {targetStatus}` (B8.8). api-standards allows `:action` or `/action`, one style per product.

## Options
1. Generic `/transition` with a target status - hides that each action has its own rules, payload and error codes.
2. `POST /<resource>/{id}:<action>` - colon paths are awkward in the approuter route regex and some tooling.
3. `POST /<resource>/{id}/<action>` in kebab-case (`/bookings/{id}/check-in`, `/hold`, `/cancel`, `/offices/{id}/open`, `/close`, `/floors/{id}/retire`, `/desks/{id}/retire`).

## Decision
Option 3; one operationId per action (`checkIn`, `holdBooking`, `cancelBooking`, `openOffice`, `closeOffice`, `retireFloor`, `retireDesk`). Actions take `If-Match`.

## Consequences
- Clear contract and roles per action; differs from the base demo style, which is removed anyway (EN-1).
