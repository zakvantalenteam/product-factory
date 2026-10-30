# ADR-7 Roles: employee by app role, Facilities admin by base admin, manager from data

Status: proposed (S5, 2026-10-28)

## Context
Roles: Employee, Manager (anyone with an active direct report, R52), Facilities admin, System. The base offers `adminAccess || superAdminAccess` (AdminGuard, B9.5), app roles USER/ADMIN/SUPER_ADMIN (B1.27) and menu permissions through TTCommon `PermissionChecker`. A signed-in person without a DeskBook role sees "No access" (AC17.2).

## Options
1. Three role collections in XSUAA including Manager - manager lists drift from SuccessFactors.
2. Employee = app role USER; Facilities admin = base admin; Manager derived from `ppl_employees` at request time.
3. As 2, with a separate Facilities admin role through a TTCommon menu permission.

## Decision
Option 2 for MVP; option 3 is the R1 refinement if Q66 is answered that way. `access.DeskAccessGuard` offers `requireEmployee`, `requireAdmin`, `requireManagerOf(employeeId)` (R1), `canSeeReserved` (R1); every service method calls it; `getMyProfile` returns the same facts to the SPA for menus.

## Consequences
- Manager rights follow the nightly copy automatically (AC14.4).
- Platform admins are Facilities admins in MVP (they also see integrations); acceptable for one pilot office.
- Delegates (R1) are checked through `team` data inside `requireManagerOf`.
