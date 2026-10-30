# SuccessFactors fields - DeskBook

Field mode (S5), sf-consultant, 2026-10-28. Inputs: `02-spec.md` F14 (R48-R52, AC14.1-14.8), F9/F10 (team, R32),
Integrations; `05-architecture.md` 4.5 and ADR-6; `05-data-model.md` 4.1 (`ofc_offices.sf_location_code`), 4.6
`ppl_employees`, 4.7 `ppl_sync_runs`; `05-integrations.md` section 1; `decisions.md` D1-D5; questions Q11, Q54,
Q60, Q62, Q63, Q77, Q81, Q85.

Fact marks: **[V]** verified, with the source in section 9; **[T]** to verify in the customer tenant (`/odata/v2/$metadata`,
Admin Center > OData API Data Dictionary, one anonymised sample page). Nothing here is written back to SF (R48):
there are no push use cases.

## 0. Summary

| Use case | Spec | Entity (OData v2) | Id stored | My verdict vs 05-integrations.md |
|---|---|---|---|---|
| UC1 Employee copy (id, name, email, active) | F14, AC14.1, AC14.6, AC14.7 | `User` | `userId` | Agree on entity, id and full read. **Change:** filter `status in 't','f'` explicitly instead of no filter (1.3, Q112) |
| UC2 Direct manager and manager status | R50, R52, AC14.4 | `User.manager` (nav) | manager's `userId` | Agree for MVP (today's manager is all we need). Add `NO_MANAGER` handling |
| UC3 Home office | Q63, BK-11 | `User.location` **or** `EmpJob.location` | FOLocation `externalCode` | **Differ:** `User.location` is a text copy whose format is tenant-defined [T]; if it is not the bare code, read `EmpJob.location` through `$expand` in the same call (3) |
| UC4 Leavers | R51, AC14.5 | `User.status` (+ absence) | - | **Differ:** leavers come back as `status='f'` only if asked for; with no filter SF silently leaves them out, so "absent" mixes leavers with scope and permission loss; absent people are counted MISSING and cancel nothing (4, Q128) |
| UC5 Person grouping (concurrent employment, rehire) | Q60, Q85 | `User.personKeyNav` -> `PerPerson.personIdExternal` | `personIdExternal` (extra, optional) | **New:** not in 05-integrations.md (5) |
| UC6 Sync run log | R49, AC14.2 | - (our own `ppl_sync_runs`) | - | Agree |

Top risks: (1) `User.location` is not the code the admin types (Q63/Q77); (2) RBP target population or a
permission change makes people vanish, and absence is read as "left" (the 10 % guard of Q81 is the only brake);
(3) default User reads also return `T` (active external) users who are not employees; (4) concurrent employments
give one person two rows with the same email.

## 1. UC1 Employee copy - `User`

### 1.1 Request

```
GET /odata/v2/User
  ?$select=userId,status,firstName,lastName,email,location,lastModifiedDateTime,
           manager/userId,personKeyNav/personIdExternal
  &$expand=manager,personKeyNav
  &$filter=status in 't','f'
  &$orderby=userId
  &$top=1000&$skip=<n>          (or server paging, see 1.4)
  &$format=json
```

| Item | Choice | Why / rejected alternative | Mark |
|---|---|---|---|
| Module | Platform user (`User`), filled from Employee Central by HRIS sync when the tenant runs EC | One flat entity per employment, already today's values; no effective dating to handle | [V] entity; HRIS sync source [T] (is EC enabled?) |
| Entity | `User` | Rejected `EmpJob` + `PerPersonal` + `PerEmail` as the main read: three effective-dated entities, picklists and email-type lookups for data `User` already holds as of today. Rejected SFAPI `CompoundEmployee` (SOAP, heavier, built for full HR replication) | [V] |
| Effective dating | none on `User`; it shows today's state. No `asOfDate` | DeskBook only needs today (R50: change takes effect from the next sync) | [V] User is not effective-dated |
| `$filter` | `status in 't','f'` | Default read returns only `t` and `T`; inactive users are left out silently. Never use `status ne ...`. Excludes `T`/`F` (external users) and `e`/`d` (Learning/Onboarding-only external suite users), who are not employees (Q109) | [V] codes and default; combining `status in` with other filters [T] |
| `$orderby` | `userId` | Stable order for `$skip` paging (agree with 05-integrations 1.2) | [T] base client accepts it (Q77) |
| Fields | only the 9 above | No photo, phone, locale, time zone, birth date, job title, gender: not needed (02-spec privacy row). `defaultLocale`/`timeZone` rejected: mails are English (R47), office time zone rules | [V] field names standard; lengths [T] |
| `$expand` | `manager`, `personKeyNav` (one level each) | Keeps it one call | nav names [T] in `$metadata` |

### 1.2 Field -> column map (`ppl_employees`)

| SF field (type) | Column | Transform | Odd values | Mark |
|---|---|---|---|---|
| `userId` (Edm.String, key, up to 100) | `user_id` varchar(100) | trim only; keep case as SF sends it; matched to the sign-in id (Q62) | blank: skip, count | [V] key; length [T] |
| `firstName`, `lastName` (Edm.String) | `full_name` varchar(200) | `firstName + ' ' + lastName`, collapse spaces, cut 200 | both blank: `userId` | [V] |
| (option) `defaultFullName` or `displayName` | `full_name` | if the tenant has it and fills it with the preferred-name format, use it instead of the concatenation | | [T] field exists and is filled |
| `email` (Edm.String) | `email` varchar(254) | trim, lower case; HRIS sync puts the primary business email here | blank: skip, `NO_EMAIL` (AC14.7). Never a key: it can change | [V] field; "primary business email" source [T] |
| `status` (Edm.String, 1 char) | `active` boolean | `t` -> true, `f` -> false; any other value -> skip row, count `BAD_STATUS` | | [V] codes |
| `manager/userId` | `manager_user_id` | see 2 | | |
| `location` (Edm.String) | `home_office_code` varchar(50) | see 3 | | |
| `personKeyNav/personIdExternal` | **new** `sf_person_id` varchar(100) null (Q110) | trim | missing (non-EC tenant): null | [T] |
| `lastModifiedDateTime` (Edm.DateTimeOffset) | not stored | used only for the optional delta of 1.4 | | [T] present on User |
| derived | `is_manager`, `source`='SF', `left_at`, `last_synced_at` | as 05-integrations 1.3 | | - |

No picklist or locale lookups are needed on this path: `status` is a fixed code, and DeskBook stores the location
code, not a location name.

### 1.3 Why the explicit status filter (change to 05-integrations 1.2 "Filter: none")

05-integrations treats a missing row as a leaver because it does a full read with no filter. That works only
because SF hides inactive users by default; it also means DeskBook can never tell "left the company" from
"removed from the API user's target population", "user record purged (DRTM)" or "external user". Asking for
`status in 't','f'` gives positive evidence (`f` = deactivated) and keeps absence as a second, separately counted
reason (`MISSING`). It also drops `T` users, which the no-filter read would import and let book.

Volume cost: inactive users accumulate (every leaver since go-live of SF). For a 3,000-person company this is
typically a few thousand more rows, 3-8 pages of 1,000; still inside AC14.1. Above ~20,000 rows, split the read:
active `status in 't'` full, plus `status in 'f' and lastModifiedDateTime ge <last SUCCESS - 3 days>` (filter
combination [T]).

### 1.4 Paging and first load

| Item | Advice | Mark |
|---|---|---|
| Page size | up to 1,000 rows per call is the commonly cited SF ceiling; 200 (05-integrations) is safe and only means more calls (15 for 3,000) | 1,000 ceiling [T] (SAP Community, not SAP Help) |
| Client paging | `$top`/`$skip` with `$orderby=userId` | [V] KBA 2675265 |
| Server paging | alternative: follow `__next` (`$skiptoken`); for long reads `paging=snapshot` with `customPageSize`. A snapshot can expire mid-read ("snapshot lost") and the read must restart from page 1 | [V] KBA 2489065, 2990434 |
| First load | the same full read; no special query. Expect `f` rows on the first run: insert them as inactive with `left_at` = run time, publish no `EmployeeLeft` for people who never had a DeskBook row | - |
| Delta | none in MVP (agree): full read is cheap at this size and is the only way to see disappearance | - |
| Throttling | one sequential reader, honour 429 / `Retry-After` (agree) | [T] tenant limits |

## 2. UC2 Manager - `User.manager`

| Item | Advice | Mark |
|---|---|---|
| Source | `User.manager` navigation, `$select=manager/userId` | [V] nav exists on User |
| Why not `EmpJob.managerId` | `EmpJob.managerId` is the master and is effective-dated; `User.manager` is the HRIS-synced view of today. DeskBook needs only today's manager (R50), so `User` is enough. Switch to `EmpJob.managerId` only if UC3 already expands `EmpJob` (then take both from there, as of today) | [V] |
| No manager | EC uses the literal `NO_MANAGER` on EmpJob; on `User` it shows as null or as a user `NO_MANAGER`. Treat null, blank, `NO_MANAGER` and the person's own `userId` as "no manager" | `NO_MANAGER` on User [T] |
| Inactive manager | `$expand=manager` may return null when the manager is inactive (default active-only rule applied to the expanded user) | [T]; harmless: an inactive manager cannot sign in and R52 counts active reports only |
| Matrix / HR manager | not used. Second managers live in `EmpJobRelationships` (`relationshipType`); out of scope (02-spec: direct manager only) | [V] |
| Manager of managers (R1, Q58 "all levels below") | derive by walking `manager_user_id` in DeskBook; no extra SF field | - |

## 3. UC3 Home office - location code

| Item | Advice | Mark |
|---|---|---|
| Wanted value | the FOLocation `externalCode` of the person's current job (Q63: admin types the SF location code on the office, `ofc_offices.sf_location_code`) | - |
| `User.location` | a free-text copy written by HRIS sync from `EmpJob.location`. What it holds (code, name, or "Name (code)") depends on the tenant's HRIS sync mapping, and it can be remapped (SAP KBA 2395169 shows a customer remapping it to geozone) | text copy [V] (KBA 2395169, 2506989); format [T] |
| Preferred if `User.location` is not the bare code | add `empInfo/jobInfoNav/location` to the same call: `$expand=empInfo/jobInfoNav&$select=...,empInfo/jobInfoNav/location`. `EmpJob.location` is the FOLocation `externalCode`, effective-dated; the expanded `jobInfoNav` returns the record valid today by default | nav names `empInfo`, `jobInfoNav` [T]; today-by-default [V] KBA 2638422 |
| Rejected | asking the admin to type a location name or a "Name (code)" string as the office code (05-integrations 1.3 fallback): names are localised and renamed, so the mapping breaks silently | - |
| Transform | trim; compare case-insensitively with `ofc_offices.sf_location_code`; store as received | - |
| Location name for the admin screen (optional, R1) | `FOLocation?$select=externalCode,name&$filter=status eq 'A'` once per run, to show "Pune Tower B" next to the typed code. Not needed for MVP | `FOLocation` fields [V] KB; status values [T] |
| Future transfers | not read: a transfer counts from the day `User`/`EmpJob` shows it (R50 logic applied to office) | - |

## 4. UC4 Leavers and inactive users

| Case | What SF shows | DeskBook action | Mark |
|---|---|---|---|
| Terminated, past end date | `User.status='f'` | `active=false`, `left_at`, `EmployeeLeft` (R51) | [V] status code; timing of the flip after termination [T] |
| Termination keyed with a future end date | user stays `t` until the deactivation date | nothing until it flips; bookings after the last day are cancelled then (bookings are at most 14 days ahead, so exposure is small) | [T] the date SF deactivates (end date or day after) |
| Long leave, sabbatical (`emplStatus` = leave) | `User.status` stays `t` | stays active, can book (no rule in the spec) | [V] status is user-level |
| Absent from the read (not `t`, not `f`) | purged (DRTM), out of target population, changed to external | count as `MISSING` and list (user id only, capped); **not a leaver**: row unchanged, nothing cancelled, nothing marked left (Q128, agrees 05-integrations 1.6, M8). MISSING in 7 consecutive successful runs: admin warning only. A jump over the 10 % guard (Q81) refuses the run as a likely population or permission change | absence cannot be told apart from scope loss [V]; DRTM purge on this tenant [T] |
| Rehire, same employment reactivated | same `userId`, `t` again | active again; old cancellations stay (agree 05-integrations 1.6) | [T] tenant rehire setting |
| Rehire with new employment | new `userId`, same `personIdExternal` | new row; old row stays left; `sf_person_id` links them | [V] KB golden rule 3 |
| Contingent worker | normal `t` user; `EmpEmployment.isContingentWorker=true` | included, can book (Q109) | flag [T] |
| External users `T`/`F`, `e`/`d` | not employees | excluded by the filter | [V] |

## 5. UC5 Concurrent employment and person id

- One person with two employments has two `User` rows (two `userId`s, one `personIdExternal`). The person signs in
  with one of them [T: which one, in this tenant's IAS/IdP mapping]. DeskBook books by the sign-in `userId` (Q62),
  so the other row exists but is never used to book; it can still show in a second manager's team view, which is
  correct (that manager is her manager in that employment).
- Both rows may carry the same email. The R1 manual-record match by email (Q60) must refuse or ask when two `SF`
  rows share the email, not pick one.
- Do not use `EmpEmployment.isPrimary` to pick the main employment: SAP calls it an obsolete legacy field with no
  meaning for concurrent employment [V KBA 2816104]. If a "main employment" is ever needed, read the primary
  employment indicator described in KBA 2326735 [T].
- Global assignments: host and home assignments also appear as separate users [T]; same handling.
- Store `personIdExternal` as `sf_person_id` (nullable, no unique) so data-architect and R2 anonymisation (Q85) can
  treat a person as one (Q110). Cost: one `$expand`, one column.

## 6. Data model notes for data-architect

- `ppl_employees.sf_person_id` varchar(100) null, index `(tenant_id, sf_person_id)` (Q110).
- `ppl_sync_runs`: add `inactive_count` (explicit `f`) next to `left_count`, or split `left_count` into
  `left_inactive_count` and `left_missing_count`, so the admin can tell real leavers from vanished rows (1.3).
- 05-integrations 1.3 also asks for a "last seen run" and a "leaver handled" marker; `05-data-model.md` 4.6 has
  `last_synced_at` and `left_at` only. Not an SF question; flagged so it is not lost.
- `user_id` length 100 matches `User.userId` [T confirm in `$metadata`].

## 7. RBP permissions for the API user (read only, Q113)

Prefer RBP with a scoped role over OData admin mode: admin mode overrides RBP and returns everything, which is more
than DeskBook may hold [V SAP KBA on OData admin mode; KBA 2316798].

| Permission (Admin Center > Manage Permission Roles) | Why | Mark |
|---|---|---|
| Manage Integration Tools > Allow Admin to Access OData API through Basic Authentication | only if the base B5 connection still uses basic auth; not needed for OAuth SAML bearer / X.509 | label [T]; auth type is base B5 |
| General User Permission > User Login, and User Search | API user must read `User` | [T] labels |
| Employee Data (User Info / HR Information): First Name, Last Name, Email, Manager, Location: View | the `$select` fields; missing field permission returns null, not an error | [T] labels per tenant data model |
| Employee Central Effective Dated Entities > Job Information: Location (and Manager): View | only if UC3 uses `EmpJob` | [T] |
| Employee Central API > Employee Central Foundation OData API (read-only) | only for the optional `FOLocation` read | [V] permission exists (search: SAP KBA + partner guides); [T] label |
| Do **not** grant Employee Central HRIS OData API (read-only) for this user | it switches reads to admin mode and bypasses RBP | [V] SAP KBA (admin mode) |
| Target population: all employees, **including inactive users** (the "include inactive" option of the granted population) | without it `status in 't','f'` returns no `f` rows and leavers look missing | [T] option label |
| Field-level restriction caveat | field-level RBP may not hide restricted fields from an API user in admin-like setups; review the role, do not rely on it | [V] KBA 2635970 |

## 8. Verify in the customer tenant (one session with the customer SF admin, before ST-PP-1 build ends)

1. Run the 1.1 request on the pilot tenant; attach one anonymised page (extends Q77).
2. `User.location` content: bare FOLocation `externalCode`, name, or "Name (code)"? Decides UC3 (Q111).
3. `$metadata`: nav names `manager`, `personKeyNav`, `empInfo`, `jobInfoNav`; field lengths of `userId`, `email`, `location`; presence of `defaultFullName`/`displayName` and `lastModifiedDateTime` on `User`.
4. `status in 't','f'` accepted together with `$orderby` and `$expand` (one community report says combining User status filters failed in Integration Center).
5. How "no manager" appears on `User.manager` (null or `NO_MANAGER`).
6. When `status` flips to `f` after a termination (end date or next day) and how rehire is configured.
7. Whether EC is enabled at all (if not, `User` is maintained by user import, `personKeyNav`/`EmpJob` do not exist, and UC3 must use `User.location` as typed by HR).
8. Concurrent employment / global assignment in use? Which `userId` the IdP maps the login to.
9. Auth type of the B5 connection (OAuth SAML bearer or X.509 vs basic) and the API user's permission role per section 7.
10. Count of `t` vs `f` vs `T` users, to size the read and confirm `T` users are not employees.
11. Is a DRTM purge of inactive users scheduled, and after how many months? Decides how often a real leaver ends as MISSING (Q128).
12. Location source switch `DESKBOOK_SF_LOCATION_SOURCE` (USER or EMPJOB) is set from item 2 and item 7 (Q129); also count active users whose location matches no office code.

## 9. Sources

- SAP KBA 2166571 "How to query inactive users on User entity - OData API" (full text behind SAP for Me; status
  codes, default active-only read, `status in` syntax and the "never `ne`" rule confirmed from SAP KBA snippets via
  web search, 2026-10-28).
- SAP KBA 2638422 (EC effective-dated entities return the latest active record by default); KBA 2148752 (use
  `fromDate`/`toDate` for past and future slices).
- SAP KBA 2675265 (`$top`/`$skip`), 2489065 (`$skiptoken`, `__next`), 2990434 (snapshot lost, restart paging).
- SAP KBA 2816104 (`EmpEmployment.isPrimary` obsolete for concurrent employment), 2326735 (primary vs secondary
  employment via API).
- SAP KBA 2395169 and 2506989 (User location is HRIS-synced from job information and can be remapped).
- SAP KBA 2316798 (restricting OData API access to EC entities), 2635970 (field-level RBP and API users); SAP KBA on
  OData admin mode vs RBP (search 2026-10-28).
- `standards/successfactors.md` (knowledge base), updated with the facts above.
