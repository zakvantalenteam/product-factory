# Security and privacy - DeskBook

Stage S5 (security-architect), 2026-10-28. Inputs: `05-architecture.md` (operations, ADR-7), `02-spec.md` (roles, F12-F17,
non-functional), `decisions.md` D1-D4, `questions.md` Q1-Q76, `base/BASE-SPEC.md` (B1.14, B1.27, B3.2, B3.4, B5.4, B6, B9.5).

Checked against: `05-openapi.yaml` and `05-data-model.md` did NOT exist when this was written. Operations were checked
against the list in `05-architecture.md` section 5.2, tables against its section 8.2. Re-run section 8 when both files exist.

Binding rules (D1, D2, Q4): an employee sees only their own bookings; a manager sees direct reports (R1, no per-person
no-show count, Q47); reports show counts, never names; Facilities admin never sees who sits where in MVP.

## 1. Roles and scopes

| Role | How it is known | Scope in the base | Who assigns | MVP operations |
|---|---|---|---|---|
| Employee | app role `USER` (`app.security.SecurityRole.USER`, B1.27) from the XSUAA token | role collection "DeskBook User" | IAS group mapped to the role collection (Q69); nobody by hand | own-record operations only |
| Manager | derived at request time: has an active direct report in `ppl_employees` (R52) | none; not a role collection (ADR-7) | follows SuccessFactors nightly | none in MVP (R1 `getTeamWeek` etc.); in MVP a manager is an employee |
| Facilities admin | base `adminAccess` or `superAdminAccess` (`AdminGuard.isAdmin`, B9.5) | role collection "DeskBook Admin" (base admin) | platform admin in BTP cockpit | office, rules, report operations; also an employee for own bookings (A9) |
| System | job identity (`created_by` = job name, B6.2) | no token; runs inside the WAR | - | the 4 MVP jobs; never reachable through HTTP |
| Signed in, no role | token without USER or admin | none | - | `getMyProfile` only; answer `roles: []` drives the "No access" page (AC17.2) |

Rules for the guard (`DeskAccessGuard`, ADR-7):
- `requireEmployee` accepts USER or admin. `requireAdmin` accepts admin only. Every service method calls one of them as its
  first line; a controller-only check is not enough (jobs and listeners call services too).
- The employee identity is the sign-in user id from the token (`UserSessionBean.getLoggedInUserID`), never a field in a request.
- MVP admin = base admin (Q66, answered). Compensating controls: every admin write is an audited entity change (B6) with the
  admin's user id; admin operations are rate limited; R1 introduces a separate Facilities role (option 3 of ADR-7) so that
  platform admins who manage integrations are not automatically Facilities admins.

## 2. Access matrix - 45 MVP operations (42 + 2 from ADR-12 + `exportReport` from D7)

Legend: **A** allowed; **OWN** only records of the caller; **ALL** tenant-wide; **-** denied (403 `FORBIDDEN`); "404" means
a record that is not the caller's answers 404 `RESOURCE_NOT_FOUND`, identical to an unknown id (no existence oracle).
Tenant scoping applies to every row (section 3). "Employee" includes managers in MVP.

### 2.1 Booking, check-in, access, reports (15)

| # | Operation | Employee | Admin | Record rule in words |
|---|---|---|---|---|
| 1 | `listBookableOffices` | A | A | Open offices only (not draft, closed). No person data. |
| 2 | `getBookingCalendar` | A | A | Office must be open; answer is dates, parts and refusal reasons, no person data. |
| 3 | `listFreeDesks` | A | A | Desk code, floor, zone, features, `totalFree`. Never who holds a desk. Reserved desks (R1) are left out and not counted for people not on the access list. Records the search server-side (R1) without the person id. |
| 4 | `createBooking` | OWN | OWN | The booking is made for the caller; body has desk, date, part only. A reserved desk id the caller may not see answers like an unknown desk. `Idempotency-Key` replay only for the same caller. |
| 5 | `getBooking` | OWN | OWN | `employee_id` = caller else 404 (admin included: an admin cannot read another person's booking). |
| 6 | `listMyBookings` | OWN | OWN | Filter is the caller's id, not a parameter. Paged, window upcoming + 30 days. |
| 7 | `cancelBooking` | OWN | OWN | Own booking, status BOOKED only (CHECKED_IN cannot be cancelled); other id 404; stale 409 `BOOKING_STATE_CHANGED`. |
| 8 | `checkIn` | OWN | OWN | Own booking inside the window; server clock only; second press idempotent. |
| 9 | `holdBooking` | OWN | OWN | Own booking, once, before the deadline. |
| 10 | `getToday` | OWN | OWN + sync health | Caller's next bookings, released note, free count at the caller's home office, and `usualDesk` (code, zone; the desk the caller booked most in the last 60 days, at least 3 times; own data only; absent when none; derived at read time, not stored). Admin-only field `syncHealth` (people copy age, failures) must not exist in the employee answer (AC17.4). |
| 11 | `getMyProfile` | OWN | OWN | The only operation open to a signed-in person without a role. Returns the caller's roles, manager flag, profile ready, last copy date. Nothing about anyone else. |
| 12 | `getBookingRules` | - | ALL | Company rules (horizon, hold minutes, late minutes). Employees get the effects through `getBookingCalendar`. |
| 13 | `updateBookingRules` | - | ALL | Allow-listed DESKBOOK keys only, range-checked (horizon 1-60, minutes within limits); writes nothing else in ConfigService. |
| 14 | `getOccupancyReport` | - | ALL | Counts and rates per office, floor, day. No ids, names, desk codes or hours. Range at most 366 days. |
| 45 | `exportReport` | - | ALL | Facilities admin only (D7); counts only, the same row set and the same small-cell rule as `getOccupancyReport` and the screen: no ids, names, desk codes or hours; the file contains no names. Range at most 93 days, at most 100,000 rows; spreadsheet cells starting `= + - @` are prefixed with an apostrophe. Rate limited (section 7). |

### 2.2a Plan my week (ADR-12, prototype option A; 2)

| # | Operation | Employee | Admin | Record rule in words |
|---|---|---|---|---|
| 43 | `proposeDesks` | OWN | OWN | Read only, no side effect. Employee id from the token; request has days (1-14 distinct), part, optional zone and features, no employee field. Answer: per day one free desk (code, floor, zone, features) and a reason code (USUAL_DESK, SAME_ZONE, MATCHES_CHOICES, FIRST_FREE). Never who holds another desk. The usual desk is derived from the caller's own bookings only (section 4.2a). Reserved desks (R1) left out unless the caller is on the access list. |
| 44 | `createBookings` | OWN | OWN | Batch of 1-14 distinct days, each day its own booking and transaction with every rule of `createBooking` (row 4). Booked for the caller only; the body has no employee field. Manager for a direct report (R1): not through this operation in MVP; `createBookingForReport` keeps its book-for rule (`requireManagerOf(employeeId)`, the report gets an email, history names the manager, the answer never lists the report's other bookings, `ALREADY_BOOKED_THAT_DAY` returns no booking id). If R1 adds a report id to the batch, the same check runs for every day, and the proposal reason for a report is never USUAL_DESK (it would show the report's habit to the manager). Per-day result: BOOKED, REPICKED or FAILED with the usual problem code; a FAILED day for a reserved desk reads like an unknown desk. `Idempotency-Key` per section 4.2a. |

### 2.2 Office setup (28; all admin-only)

| # | Operation | Employee | Admin | Record rule in words |
|---|---|---|---|---|
| 15 | `listOffices` | - | ALL | Includes draft and closed offices. |
| 16 | `getOffice` | - | ALL | - |
| 17 | `createOffice` | - | ALL | Name unique ignoring case; timezone from the IANA list. |
| 18 | `updateOffice` | - | ALL | `If-Match` version. |
| 19 | `getOfficeHistory` | - | ALL | Audit rows (B6.9) of the office: who changed which setting. Holds admin ids only; no booking data. |
| 20 | `openOffice` | - | ALL | State machine; invalid transition 422. |
| 21 | `closeOffice` | - | ALL | Refused with future bookings: answer carries the count only, no names or ids (`HAS_FUTURE_BOOKINGS`). |
| 22 | `updateOfficeSettings` | - | ALL | Effective from tomorrow (R10); cross-field rules server-side. |
| 23 | `listFloors` | - | ALL | - |
| 24 | `createFloor` | - | ALL | - |
| 25 | `updateFloor` | - | ALL | - |
| 26 | `retireFloor` | - | ALL | Count-only refusal as row 21. |
| 27 | `listZones` | - | ALL | - |
| 28 | `createZone` | - | ALL | - |
| 29 | `renameZone` | - | ALL | - |
| 30 | `deleteZone` | - | ALL | Refused while desks use it. |
| 31 | `listDesks` | - | ALL | Desk data only; no holder. |
| 32 | `getDesk` | - | ALL | No holder, no booking list. |
| 33 | `createDesk` | - | ALL | Code unique per tenant. |
| 34 | `updateDesk` | - | ALL | Code locked once booked. |
| 35 | `retireDesk` | - | ALL | Count-only refusal. |
| 36 | `getDeskHistory` | - | ALL | Audit rows of the desk entity only; booking rows are never joined in. |
| 37 | `listFeatures` | - | ALL | R1 opens a read-only list to employees for the filter (BK-2). |
| 38 | `createFeature` | - | ALL | - |
| 39 | `deleteFeature` | - | ALL | Refused while desks use it. |
| 40 | `listClosedDays` | - | ALL | Employees see closed days only as reasons in `getBookingCalendar`. |
| 41 | `addClosedDay` | - | ALL | Not in the past; count-only refusal. |
| 42 | `removeClosedDay` | - | ALL | - |

Counts: 45 rows (43 in 2.1 and 2.2, `exportReport` included, + 2 in 2.2a; `getOccupancyGrid` is R1, D6). Employee column: 13 allowed (1-11, `proposeDesks`, `createBookings`), 32 denied. Admin column: 45 allowed (13 own-record, 32 tenant-wide).

### 2.3 R1 operations, grouped (rules to hold the design now)

| Group | Operations | Who | Record rule |
|---|---|---|---|
| Manager views | `getTeamWeek` | manager, delegate | `requireManagerOf(employeeId)` for each report, computed from `ppl_employees` at request time, direct reports only (indirect only in ST-TM-7, view only). No per-person no-show count (D2). |
| Manager acts | `createBookingForReport`, `cancelBookingForReport` | manager, delegate | Only for a direct report; the report gets an email; history records who acted; the answer never shows the report's other bookings. `ALREADY_BOOKED_THAT_DAY` must not return the existing booking id to the manager. |
| Delegation | `getDelegate`, `setDelegate`, `removeDelegate` | the manager for themselves | A manager cannot name a delegate for someone else; delegate rights expire (default 90 days, renewable); history row on every change. |
| Admin on bookings | `getDeskOccupancy`, `adminCancelBooking`, `adminMoveBooking`, `previewDisruption`, block operations | admin | Holder shown only inside cancel/move, reason required and written to history (Q52); Legal confirms for DE/FR first. |
| Access list | `listAccess`, `addAccess`, `removeAccess`, `getAccessHistory` | admin | Possible disability inference (GDPR Art. 9 risk). Admin only; employee id only, no reason field (R54); DPIA and Legal sign-off before go-live. |
| People admin | `getSyncStatus`, `runSyncNow`, `addPerson`, `searchPeople` | admin | `searchPeople` returns max 20 rows, minimum 3 characters, no export. Manual person (Q60) cannot set a manager. |
| Reports | `getOccupancyGrid`, `getSuccessShare` | admin | `getOccupancyGrid` (D6, moved from MVP): counts per office, floor, zone, day (booked, capacity, rate); never an id, name, desk code or hour (D2); zones with fewer than 3 desks, and any zone that holds a reserved desk (R1), are merged into the floor row (small-cell rule, section 4.2a); range at most 31 days (longer periods: `getOccupancyReport` and `exportReport`); 10/min. `getSuccessShare`: aggregate only, no ids or names. |
| Desk by QR / best desk | `checkInByDesk`, `getDeskPage`, `bookBestDesk`, `suggestFreeDesks`, `getBookingPreferences` | employee | Acts only on the caller's own booking; the QR holds the desk URL only (R25); sign-in required. |
| Import / QR sheet | `importDesks`, `getQrSheet` | admin | Upload rules in section 7. |
| Notifications log | `listNotifications` | admin | Recipient shown as user id; email address masked. |

## 3. Tenant isolation

- `tenant_id` comes from `UserSessionBean.getCompanyID()` and is set by `AuditableEntityListener` on insert; it cannot change
  afterwards (B6.2). Nothing in a request may carry a tenant.
- Reads: one central filter (Q71, EclipseLink `@AdditionalCriteria` with the tenant as session property), not a clause written
  per query. Jobs set the tenant explicitly per run; a job without a tenant fails the run instead of reading all tenants.
- Every unique index starts with `tenant_id` (ADR-2 does); caches (calendar 60 s, free desks 1 s) include the tenant in the key.
- DeskBook is one company per deployment in practice, but the base is tenant-aware, so the controls stay.
- A test must prove: with two tenants holding identical desk codes and office names, (1) tenant A never reads or counts tenant B
  rows through any of the 42 operations, (2) a B id requested by A answers 404, (3) a unique constraint does not collide across
  tenants, (4) a job run for A changes nothing of B, (5) cache entries are not shared.

## 4. Threat model (STRIDE)

Control location: AR approuter, BF backend filter/guard, SV service rule, DB database constraint, JOB job design.

### 4.1 Sign-in and session

| STRIDE | Threat | Control | Where |
|---|---|---|---|
| S | Stolen or replayed session cookie | HttpOnly, Secure, SameSite=Lax cookie `_tt_deskbook_jwt_`; token validity 3600 s (B3.4); logout clears | AR (Q68) |
| T | CSRF: hostile page triggers book/cancel (approuter has csrf off, B3.2) | approuter csrfProtection on for POST/PUT/DELETE, or custom-header check; strict CORS list `deskbook.cors.allowed-origins` (B1.9), no wildcard | AR + BF (Q68) |
| E | Role taken from the request or a cached stale role | role only from the token and `getUserRolesCacheInMinutes` cache (B1.27); keep that cache at 5 minutes at most | BF |
| I | Unused base routes: `/webservices/webhook/*` is open without auth (B3.2) | remove from `xs-app.json`; only `/api/public/health` stays public | AR (Q68) |
| D | Login storms at 08:00 | XSUAA/IAS platform; no custom login | platform |
| R | "I never booked that" | every write has `created_by` from the token and an audit row (B6) | SV |

### 4.2 Find and book (J1, `listFreeDesks`, `createBooking`)

| STRIDE | Threat | Control | Where |
|---|---|---|---|
| S | Booking in someone else's name | employee id from the token only; request body has no employee field; closed schemas (`additionalProperties: false`) | BF + contract |
| T | Double booking by two clicks or two people | unique indexes on slots and on employee-day (ADR-2); `Idempotency-Key` scoped to (tenant, employee) with request hash | DB + SV |
| R | Dispute over a lost booking | audit rows and `created_at`; response carries booking id | SV |
| I | Learning who holds a desk (free-desk list, error codes, timing); learning a reserved desk exists | no holder anywhere in the answer; `DESK_JUST_TAKEN` says only "taken"; reserved desk the caller may not see = same answer as unknown desk; R1 cache must not mix reserved visibility (Q72) | SV |
| D | Polling and scripted searching (125 req/s nominal at 500 users, ADR-8); one user filling the horizon with bookings | per-user rate limits (createBooking 10/min, listFreeDesks 30/min, 429 `RATE_LIMITED`); page size max 100; one active booking per day by DB; horizon 1-60 days | BF (Q72) |
| E | Guessing booking ids (IDOR) | UUID ids (B6.1) plus the own-record check; other id = 404 | SV |

### 4.2a Plan my week (`proposeDesks`, `createBookings`, usual desk; ADR-12)

| STRIDE | Threat | Control | Where |
|---|---|---|---|
| S | Batch or proposal for another person | employee id from the token only; closed request schemas (no employee field); R1 report id checked per day with `requireManagerOf` | BF + SV |
| T | Idempotency key reuse: same key with another day list or desk; key `a` colliding with `a:2026-11-02` (stored per day as `<key>:<date>`) | key charset `[A-Za-z0-9_-]`, 16-64 characters, `:` rejected; key scope (tenant, employee); each stored day keeps a hash of its date, part and desk mode; same key with different content answers 422; another employee's identical key does not replay | SV + DB |
| R | Dispute over which days were booked or moved | every day writes its own audit row; result lists BOOKED, REPICKED (old and new desk code) and FAILED per day | SV |
| I | Usual-desk inference: the usual desk is a habit of one person (where she sits, how often she comes) | `usualDesk` and the reason USUAL_DESK exist only in the caller's own answers; computed from the caller's bookings in the last 60 days, not stored, no table; never in a list, report, grid, email, log or URL; a proposal never reveals why another desk is missing (taken, reserved, blocked look the same); R1 report proposals use SAME_ZONE_AS_TEAM, never the report's own habit | SV |
| I | Learning who holds a desk by comparing proposals over days, or by the REPICKED answer | the answer names only the caller's own desks; "taken" is the only reason; proposals are not stored and not cached across people (cache key includes the employee and the reserved-visibility flag, Q72) | SV |
| I | Heat grid cell of one or two desks reveals one person's attendance (worst on a reserved or accessibility desk, R54) | small-cell rule: zones under 3 desks or with a reserved desk merge into the floor row; admin only; counts only (D2); range at most 31 days | SV |
| D | Many days in one request; many requests; a script filling 14 days again and again; polling `proposeDesks` | at most 14 distinct days, over 14 or a repeated date = 422 `VALIDATION_ERROR` before any write; body at most 16 KB; separate per-user counters (section 7): booking-days 30 per minute shared by `createBooking` and `createBookings` (each day counts one), `createBookings` 3 requests per minute, `proposeDesks` 20 per minute, `getOccupancyGrid` 10 per minute; 429 `RATE_LIMITED` with `Retry-After` checked before the batch starts, so a batch is never half-refused by the limit; one active booking per employee-day (DB) and horizon 1-60 days stay the hard cap | BF + DB |
| E | Batch used to book past the horizon or on closed days | each day passes the same calendar rules as `createBooking`; a bad day is FAILED, not skipped silently; no day is accepted that `getBookingCalendar` would refuse | SV |

### 4.3 Check-in, hold, deep links (J1 step 5)

| STRIDE | Threat | Control | Where |
|---|---|---|---|
| S/E | Checking in for a colleague; link in an email that acts without sign-in | email links only open `/bookings?focus=<id>`, sign-in first, own-record check (R25); no signed action links | AR + SV |
| T | Client clock or `action=hold` in the URL forces a state change | server clock only (`Clock` bean); the SPA never runs an action from a URL, the person presses the button (Q74) | SV + FE |
| R | Remote check-in without being there | accepted in MVP (honour-based); QR (R1) raises the bar; not claimed as proof of presence | accepted |
| D | Hold abused to keep a desk | once per booking, deadline + 90 min cap (Q49) | SV |

### 4.4 Release job and reminders (J2)

| STRIDE | Threat | Control | Where |
|---|---|---|---|
| T | Job releases a booking that just checked in | per-booking transaction with version check, check-in wins (AC8.4) | JOB + DB |
| E | Job triggered by a user to release at will | no HTTP trigger; the base job page is admin only and every run is idempotent | JOB |
| R | Who released it | `updated_by` = job name; booking carries reason NO_SHOW or RELEASED_AFTER_HOLD | SV |
| D | Downtime backlog | catch-up by query, batch 200 | JOB |
| I | Personal data in job logs or `addError` text | log booking ids only; failure text carries notification id, never an address (Q76) | JOB |

### 4.5 Notifications (mail integration)

| STRIDE | Threat | Control | Where |
|---|---|---|---|
| S | Phishing that imitates the mail; links built from the request Host header | link host from configuration, not from the request; SPF/DKIM on the sender owned by the mail service | SV + ops |
| T | Admin-entered office or desk names inject markup into mail | HTML-escape every variable in templates; plain-text part; no user text in the subject beyond escaped office name | SV |
| I | Mail names another person or leaks desk of someone else | message holds the recipient's own desk, office, time only (R47); test per template | SV |
| R | Sent twice or lost | unique event key in the outbox (ADR-5); status and attempts in `ntf_notifications` | DB |
| D | Mail outage blocks bookings | booking never waits for mail (R46); breaker after 5 failures | SV |
| E | Mail credentials in code | BTP destination only (Q76) | platform |

### 4.6 People copy from SuccessFactors (integration, in only)

| STRIDE | Threat | Control | Where |
|---|---|---|---|
| S | Fake employee appears | data only from the SF client with base credentials (B5); no manual manager (Q60) | SV |
| T | Bad or empty SF page marks everyone as left and cancels all future bookings (R51) | sanity guard: if the active count falls by more than 20 % against the last good run, or a page is empty, the run FAILS and the last copy stays (R49); admin sees the reason | SV |
| T | A changed manager field grants team-view access (R1) | manager flag derived only from the nightly copy (R52); no override screen | SV |
| I | Copying more than needed | `$select` of the six fields in F14 only; no birth date, pay, phone | SV |
| I | Admin sync page shows who was skipped (AC14.7) | list user ids, not names | SV (Q70) |
| D | Run overlaps or hangs | one RUNNING run (DB unique), timeouts 10 s/60 s (6.5) | DB + SV |
| R | Who changed the people data | sync run row with counts; employee rows audited with job name | SV |

### 4.7 Admin setup and reports

| STRIDE | Threat | Control | Where |
|---|---|---|---|
| E | Platform admin changes offices by accident of role (Q66) | accepted for the pilot; audit on every write; R1 separate Facilities role | BF |
| T | Concurrent edits | `If-Match` version; 409 `CONCURRENT_UPDATE` (B1.14) | SV |
| T | Stored XSS in names; formula injection in the export (MVP, D7) | React escaping, length limits (name 100), no HTML accepted; export prefixing | FE + SV |
| I | Report re-identifies a person (one booking on one floor on one day, plus outside knowledge) | counts only, grain = office/floor/day, never desk or hour, no breakdown by manager or team; accepted residual risk, noted for Legal | SV |
| D | 3-month all-offices report abused | range at most 366 days, 10 requests/min, p95 budget 3 s (6.1) | BF |
| R | Who changed a rule or desk | audit (B6), 24 months (Q70) | SV |

## 5. Data protection

### 5.1 Personal data inventory (from architecture 8.2; data model not yet written)

| Data | Where | Why (purpose) | Who may read | Retention |
|---|---|---|---|---|
| User id, name, email, manager id, home office, active | `ppl_employees` | identify the caller, send mail, derive manager (R1) | the owner via `getMyProfile`; names reach other people only in R1 manager views | while active; leavers: name and email cleared 30 days after leaving, id kept until their bookings are anonymised |
| Employee id on booking, date, part, status, check-in time | `bkg_bookings` | run the service, release, no-show counts, reports | the person (OWN); manager of the person (R1); nobody else | 2 years, then `employee_id` set to null, counts kept (G8, R2 `AnonymiseJob`) |
| Who created or changed a row | `created_by`, `updated_by`, audit tables | accountability (A6) | admin via history endpoints | 24 months; default is 84 (B6.10): set `AUDIT_RETENTION_MONTHS=24` (Q70) |
| Employee id inside audit field values | `aud_change_field` | - | - | must not be stored: mask `bookings.employee_id` in the audit (Q70) |
| Recipient address, type, booking id, result | `ntf_notifications` | send once, retry, show failures | admin job page (ids only) | 90 days |
| Usual desk (ADR-12) | derived at read time from `bkg_bookings` (caller's last 60 days); not stored | pre-fill the best desk for the caller | the caller only (`getToday`, `proposeDesks`) | none of its own; follows the booking retention; part of the person's data export (it is derived from their bookings) |
| Search outcome (R1) | `rpt_search_log` | success share (RP-6) | admin as aggregate | 2 years (Q59); no person id stored |
| Access list (R1) | `acc_access_entries` | who may book reserved desks | admin | while listed; removed entries 12 months in history, then purged (Q75) |
| Delegates (R1) | `tm_manager_delegates` | manager delegation | manager, delegate | until expiry + 12 months history |

No health data, no reasons, no free-text about a person anywhere (R54, AC16.4).

### 5.2 Export, deletion, legal basis

- Data request: the person can see all own bookings through `listMyBookings`; a full export and erasure on request run as a
  documented admin runbook in MVP, because no operation exists (Q75). Erasure sets `employee_id` null and clears the
  employee row, keeping counts.
- Leavers: future bookings cancelled without mail (R51); their rows follow the retention above.
- Germany and France: booking and check-in times show who is in the office on which day. Legal and the works council
  (Germany) or staff representatives (France) must confirm purpose, retention and the manager views before go-live;
  this is a go-live condition, not a build blocker (Q75). The per-person no-show count for managers stays out until then (Q47).
- Encryption: in transit TLS at the approuter and between app and database as the platform gives; at rest the BTP database
  service encryption. No extra column encryption in MVP. SuccessFactors secrets are encrypted by the base and never returned (B5.4).

### 5.3 Never logged, never in a URL

- Never in logs: names, emails, session cookie, JWT, `Authorization` header, SuccessFactors or mail credentials, request
  bodies of the people and access operations, the full `Idempotency-Key`.
- Allowed in logs: request id, booking id, desk id, office id, employee id (pseudonymous), counts, error codes. Log retention
  is the platform default; keep it at 90 days.
- Never in a URL or query string: person ids, names, emails. Paths and queries carry UUIDs, desk codes, dates and filters only.
- 500 answers never carry internals (B9, error envelope); the SPA shows the request id.

## 6. Secrets

| Secret | Lives in | Rotation | Never |
|---|---|---|---|
| XSUAA client credentials | service binding (`VCAP_SERVICES`) of backend and approuter | rebind at least yearly and on any leak | in git, `manifest.yml` values, `xs-security.json` (B3.4) |
| PostgreSQL credentials | service binding | rebind yearly | in `application*.properties` |
| Backend destination (approuter to backend) | destination service, `forwardAuthToken: true` | with the app | - |
| SuccessFactors API user and keys | base ConfigService group SUCCESSFACTORS, encrypted, GET returns "" plus a present flag (B5.4) | admin rotates on the Integrations page yearly | returned to the browser; read by DeskBook code other than through `SuccessFactorsClientService` |
| Mail credentials | BTP mail destination (Q64, Q76) | yearly | application properties |
| Session cookie signing | TTCommon | platform | - |

DeskBook adds no secret of its own in MVP. `manifest.yml` keeps placeholders (B3.5).

## 7. Abuse and input handling

- Rate limits (Q72), per user per instance in memory (Caffeine, no new dependency; approximate across instances is
  acceptable): `createBooking` 10/min; `cancelBooking`, `checkIn`, `holdBooking` 20/min; `listFreeDesks` 30/min (SPA polls 15/min in R1);
  `getOccupancyReport` 10/min; `exportReport` 5/min; `getOccupancyGrid` (R1) 10/min; `proposeDesks` 20/min; `createBookings` 3 requests/min; booking-days 30/min shared by `createBooking` and `createBookings` (each day counts one; the `createBooking` 10/min above is for the single-day call from the R1 flows); admin writes 60/min. Over the limit: 429 `RATE_LIMITED` with `Retry-After`.
- Size: JSON body at most 16 KB; page size at most 100; report range at most 366 days; free text fields at most 100 characters.
- Injection: only JPA parameter binding (no concatenated JPQL or native SQL); sort fields from an allow-list; dates, UUIDs,
  enum values and timezone ids parsed strictly (timezone from the IANA list, `INVALID_TIMEZONE`); search text has `%` and `_` escaped.
- Mass assignment: request DTOs have only the fields of the operation; status, deadline, employee id, tenant and version
  (except via `If-Match`) are never accepted from the client.
- Upload (R1 `importDesks`): `.csv` or `.xlsx` only, at most 2 MB and 2,000 rows, no macros, parsed with a safe library, cells
  read as text, file never stored after parsing.
- Clickjacking and headers: keep `SEND_XFRAMEOPTIONS` on; CSP `default-src 'self'` and `frame-ancestors 'self'` at the
  approuter (Q68).
- No AI feature in this product, so no prompt-injection surface.

## 8. Checks against the contract and model

`05-openapi.yaml` and `05-data-model.md` were not present. Checked against `05-architecture.md`. Mismatches, each in `questions.md`:

| # | Finding | Owner | Question |
|---|---|---|---|
| 1 | Approuter csrf off and an unused open webhook route in the base | base-builder | Q68 |
| 2 | Who assigns USER, whether admin passes `requireEmployee`, `getMyProfile` for roleless people | base-builder | Q69 |
| 3 | Audit default 84 months and `employee_id` in audit values contradict the 2-year promise; sync skip list must hold ids only; slots must carry no employee id | data-architect | Q70 |
| 4 | No single tenant mechanism; idempotency key scope; cache keys | data-architect | Q71 |
| 5 | R1 free-desk cache clashes with per-person reserved desks; no rate limits in the design | solution-architect | Q72 |
| 6 | Contract: `x-roles` on all 42, closed request bodies, `getToday` mixes admin data, count-only refusals, 404 for others' ids, 429 | api-designer | Q73 |
| 7 | Email deep link `action=hold` must not run on load | ux-designer | Q74 |
| 8 | DE/FR sign-off, erasure and data-request path, `AnonymiseJob` only in R2, R1 access list | PO | Q75 |
| 9 | Mail and Actuator secrets and endpoints; no addresses in job errors | developer | Q76 |

Operations with no role: none in the architecture list (all 42 have a row). Tables with personal data and no retention: none
once Q70 and Q75 are accepted; `ppl_employees` leaver clearing and `ntf_notifications` purge are new and must appear in the
data model. Endpoints returning more than the role may see: `getToday` (admin field) and `getMyProfile` (caller only) are the
two to test; no MVP endpoint returns another person's data.
Note: spec F15 and AC15.4 still describe the older manager no-show count; stories moved it to Later (Q47, ST-TM-11); the
spec text needs the revision the requirements-analyst owes (D2).

## 9. Tests the security design requires

1. Role matrix contract test: all 45 operations x {no token, no role, employee, admin} against section 2 (expected 401/403/200).
2. Own-record test: employee B calls `getBooking`, `cancelBooking`, `checkIn`, `holdBooking` with employee A's booking id: 404;
   same for an admin.
3. Closed-body test: `createBooking` with extra fields `employeeId`, `status`, `deadline` is rejected.
4. Employee `getToday` answer has no `syncHealth` key; `listFreeDesks`, report and error bodies contain no name, email or holder.
5. Two-tenant test (section 3).
6. Idempotency: same key and body replays; same key by another employee does not; same key with another body 422.
7. Rate limit returns 429 with `Retry-After` and the limit resets.
8. SuccessFactors guard: a page with 0 rows or a 25 % drop fails the run and cancels nothing.
9. Email templates: names escaped; no other person named; link host from configuration.
10. Log scan in the test run: no `@` addresses, no `Bearer`, no cookie names.
11. CSRF: a POST without the token or header is refused (after Q68).
12. Batch: 15 days, a repeated date, or an extra `employeeId` field is refused before any booking exists; 14 days books 14 or reports each failure.
13. Idempotency of the batch: same key and same days replays the same result; same key with another day or desk = 422; a key containing `:` is refused; another employee's same key does not replay.
14. Rate limit: 31 booking-days in a minute across both booking operations gives 429 with no partial batch.
15. Usual desk: employee B never sees A's usual desk in `getToday`, `proposeDesks` or any error; the key `usualDesk` is absent when the caller has fewer than 3 bookings in 60 days; no `usualDesk` in the admin or grid answers.
16. Grid: a zone with 2 desks and a zone with a reserved desk appear only inside the floor row; no cell carries an id, name or desk code; an employee gets 403.

## Changes after GP (2026-10-28, ADR-12, prototype option A)

- Added `proposeDesks`, `createBookings` to the matrix (2.2a): 45 operations; employee 13, admin 45. Review N2 (2026-10-28): `getOccupancyGrid` moved to the R1 table (2.3, D6); `exportReport` moved from 2.3 into the MVP matrix (2.1, row 45, D7: Facilities admin only, counts only, same small-cell rule as the report, no names in the file); the total stays 45.
- `getToday` gains `usualDesk` (own data, derived, not stored); data inventory (5.1) has a row for it; no new table, no new retention.
- New threat block 4.2a: batch abuse (14-day cap, separate rate counters, limit checked before the batch), idempotency key reuse (charset, no `:`, per-day content hash), usual-desk inference, heat-grid small cells.
- Section 7 rate limits updated; section 9 tests 12-16 added; test 1 now covers 45 operations.
- Still open: the small-cell threshold (3 desks) needs PO agreement (Q114); the grid range (31 days, R1) is closed (Q114a); `05-openapi.yaml` must carry `x-roles` for `proposeDesks`, `createBookings` and `exportReport` and a closed `createBookings` body.
- The R1 "zone where most of the team sits" proposal returns a zone only, direct reports only, no names; recheck when R1 is designed.
