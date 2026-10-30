# SuccessFactors review - DeskBook (people sync, Wave 3b)

Review mode (S7), sf-consultant, 2026-10-29. Checked: `05-sf-fields.md`, `05-integrations.md` section 1, `06-build-log.md` "Wave 3b (integration)", and the code in `D:/products/desk-booking/Backend/src/main/java/com/talenteam/deskbook/people/` (job, service, sf, event, domain/Employee) with its tests (88 new, all mock-based). Base client: only its use is visible (`SuccessFactorsClientService.getUserDetails(top, skip, filter)`, `BASE-SPEC.md` B4.5, B5); the TTCommon jar source is not in the repo.

Marks: **[V]** verified (source given), **[T]** verify in the customer's dev tenant (section 5 gives the exact call). Nothing in the build has touched a real SuccessFactors; every SF behaviour below is still unproven until section 5 is run.

## 1. Verdict

**PASS WITH CONDITIONS: 2 MUST, 6 SHOULD.** Entity, id, status filter, field map, `NO_MANAGER` handling, "absent is not a leaver", all-or-nothing apply, retry and 401/403 handling follow `05-sf-fields.md` and are sound. Two code changes are needed before go-live, and the whole read path needs one proof on the dev tenant (section 5, checks C1 to C4 and C10) because the unit tests mock the base client.

| Id | Level | Owner | Where |
|---|---|---|---|
| M1 | MUST | integration-engineer | a missing manager, location or person-id column silently wipes the stored values |
| M2 | MUST | integration-engineer (my design change, data-architect informed) | old `f` users on the first load are stored, listed as NO_EMAIL and fill the 500 cap |
| S1 | SHOULD | integration-engineer | page size is a constant |
| S2 | SHOULD | integration-engineer | drop guard: no floor for small tenants, no alert when it keeps refusing |
| S3 | SHOULD | integration-engineer | `UNMAPPED_LOCATION` count (my Q129 rule 4) is not built |
| S4 | SHOULD | integration-engineer | the first run time is a constant, SF's own sync time is unknown |
| S5 | SHOULD | developer / base owner | `BIZX_USER_API_DATA_MODEL_FIELDS` is shared with the base user sync |
| S6 | SHOULD | integration-engineer | full read of all inactive users every night grows without limit |

## 2. Does the build follow 05-sf-fields.md

| Item of 05-sf-fields | Built | Finding |
|---|---|---|
| UC1 `User`, filter `status in 't','f'`, `$orderby=userId` | `BaseClientPeopleSource.java:36` `"&$filter=status in 't','f'&$orderby=userId"` | Correct syntax: the list form with several codes is used by SF integrations in the field (a SailPoint community example uses `status in 't','f','T','F','e','d'`) and matches KBA 2166571 [V]. Never `ne`: respected. Whether the string survives the base client's URL building (spaces and quotes) is untested [T] C1 |
| Fields `userId,status,firstName,lastName,email,location,manager/userId,personKeyNav/personIdExternal` | `toPerson` `BaseClientPeopleSource.java:63-71` | Right fields. They reach SF only if the base setting `BIZX_USER_API_DATA_MODEL_FIELDS` lists them (Q167, S5) [T] C4, C12 |
| Id `userId` (trim, case kept) | `PeopleMapper.java:56-60` | Right. `personIdExternal` stored as `sf_person_id` (Q110) |
| Name `firstName + ' ' + lastName` | `PeopleMapper.java:73-84` | Right; preferred-name field still a TODO [T] C4 |
| Email trim, lower case, shape check, `NO_EMAIL` | `PeopleMapper.java:86-95`, Store 190-195, 213-222 | Right; the known-person rule (keep last good email) is a good SF-aware choice: HR can blank an email by mistake. See M2 for the `f` side |
| Status `t`/`f` only, `T`/`F`/`e`/`d` skipped `BAD_STATUS` | `PeopleMapper.java:62-66` | Right and defensive: even if the tenant's filter were case-insensitive (so `T` rows came back) the mapper would still refuse them [T] C2 |
| Manager: null, blank, `NO_MANAGER`, own id = none | `PeopleMapper.java:97-103` | Right. A manager outside the copy is kept as an id: right |
| UC4 explicit `f` = leaver, absent = `MISSING`, cancels nothing | Store 156-177, 208-231 | Right (Q128 agreed). Rehire clears the handled mark: right |
| UC5 person grouping | `sf_person_id`, no unique | Right |
| No delta, full read | `fetchAll` Runner 169-183 | Right for now; see S6 for the inactive-user growth |
| Leaver on first load: stored inactive, handled | Store 200-202 | Superseded: see M2 (my design was wrong here) |
| `DESKBOOK_SF_LOCATION_SOURCE` switch | not built (Q169) | Acceptable until the tenant sample; answered in Q169 |
| `UNMAPPED_LOCATION` count (Q129 rule 4) | not built | S3 |
| Readiness gate, 401/403 no retry, 429/5xx retry with `Retry-After`, timeouts | Runner 136, 185-207; `classify` Source 74-93 | Right. `Retry-After` can be seconds or an HTTP date in SF/HTTP generally; the code reads seconds only and falls back to 5/20 s: fine |

## 3. Findings

### MUST

**M1. A column that SF did not send overwrites the stored value with null - `Employee.java:97-108` with `PeopleMapper.java:120-128`.**
`applySuccessFactors` writes `manager_user_id`, `home_office_code` and `sf_person_id` even when the new value is null, and the "fields missing" check (`checkFetched`) tests only `userId`, `status` and `email`. The `$select` list comes from a base setting that an admin can edit without telling DeskBook (Q167). If `manager/userId`, `location` or `personKeyNav/personIdExternal` is dropped from that list, or the API user loses the field permission (a missing field permission returns null, not an error [V, 05-sf-fields 7]), the next run succeeds with zero managers, no home office, no person id: every manager flag clears (Store 248-259), every Today screen loses the free-desk count, and nothing is reported. The design (05-integrations 1.5) asked to refuse a set when a field is "missing from the response, usually a changed field list"; the build covers three of the six fields.
Fix: in `checkFetched`, with at least 20 active rows (small test tenants are exempt), refuse the run as `FIELDS_MISSING` when no row has a manager, or no row has a location, or (when any known row already has one) no row has a `personIdExternal`. In a real company at least the many non-top people have a manager, so "zero of 20 or more" is never true by data. Add one test per field. No SF fact is needed beyond this.

**M2. First load stores every old leaver and files the ones without an email as `NO_EMAIL` - `PeopleSyncStore.java:190-203`, `PeopleMapper.java:56-70`.**
`status in 't','f'` returns every user ever deactivated in the tenant (a few thousand, in an old tenant tens of thousands). The built apply creates an inactive, "already handled" row for each (Store 200-202) and for those with a blank email (SF does not guarantee an email on a long-gone user, and HR often clears it at termination [T] C14) it counts and lists `NO_EMAIL`. Consequences: (1) the skipped list is capped at 500 (Store 50), so on the first run it fills with old leavers and hides the active people without email that the go-live checklist (05-integrations 1.4 "skipped list reviewed", AC14.7) exists to find; (2) names and emails of people who never used DeskBook are copied, which is more personal data than the product needs (02-spec privacy row); (3) the tables grow by the inactive population for no behaviour. This is my design (05-sf-fields 1.4, "insert them as inactive"); I withdraw it.
Fix: a person who arrives with `f` and has no row is **not stored** and not listed; count them in a new `inactiveNotCopied` figure of the job result text (and not in `skippedNoEmail`). A known person turning `f` is handled as built (leaver). A person who is `f` today and `t` tomorrow (pre-hire, rehire, correction) is then a normal new person, which works. Change the test `theFirstLoadInsertsActivePeopleAndStoresOldLeaversInactiveAndAlreadyHandled` and the build-log line. The drop guard still gets a fair count (it only counts known active rows).

### SHOULD

**S1. Page size is `PAGE_SIZE = 200` constant (`PeopleSyncRunner.java:44`).** The base URL always expands three navigations (`personKeyNav`, `manager`, `incumbentOfPositionNav`) and the base read timeout (60 s) cannot be changed from DeskBook. If a page of 200 with three expansions is slow on this tenant (C8) the run fails with `SF_UNREACHABLE` every night and only a release can lower the page size. Make it a DESKBOOK setting (default 200, allowed 50 to 1,000) next to the drop percent. SF facts: `$top` above 1,000 is not honoured [T, SAP Community only]; client paging with `$skip` is verified (KBA 2675265).

**S2. Drop guard (Q170).** `dropTooLarge` (Mapper 135) is a pure percentage. (a) For a tenant under about 100 active people 10 percent is 1 to 9 people, so the normal leaver of one week trips it and the sync is refused until an admin edits a deployment setting; add an absolute floor: refuse only when `wouldStop > max(percent of active, 5)` (and keep the first-load exemption). (b) A refused run repeats every hour for ever, because the comparison is always against the last good copy; nothing alerts after the first night. Add an `addError` line that names the counts and the setting to raise, and make the architecture's "36 hours without SUCCESS" metric (Q82) fire on it. My view on 10 versus 20 to 25 percent is in section 4.

**S3. `UNMAPPED_LOCATION` is not built** (Q129 rule 4, agreed by integration-engineer). Count active people whose location matches no office `sf_location_code` (case-insensitive) in the job result text. It is the only runtime signal that `User.location` is a name and not a code, or that someone remapped the HRIS sync later (KBA 2395169 [V]).

**S4. First run time.** `FIRST_RUN_UTC = 01:00` (`PeopleSyncRunner.java:48`) is independent of when SF refreshes `User` from Employee Central. `User.status` and `User.location` are written by the HRIS sync job, which runs on the tenant's own schedule [V that `User.location` is HRIS-synced: KBA 2395169, 2506989; the job schedule is [T] C13]. If that job runs after 01:00 UTC the nightly copy is one day late (a leaver is cancelled 24 hours later than needed; harmless but visible). Make `FIRST_RUN_UTC` a setting; set it from check C13.

**S5. The base setting is shared.** `BIZX_USER_API_DATA_MODEL_FIELDS` (B5, group SUCCESSFACTORS) also feeds the base user sync (B4.5 `UsersSyncDailyJob`/`FullFetch`), which maps `UserVO` into the base user tables. Add the five DeskBook fields to the existing list; do not replace it. The owner of the base setting must confirm who else reads it (C12).

**S6. Inactive users grow every year.** The nightly full read carries all inactive users (every leaver since SF go-live) although only changes matter. After M2 they are not stored, but they are still fetched and the read still grows (cap 500 pages = 100,000 rows then `TOO_MANY_PAGES`). Not urgent at 3,000 staff. The planned split (05-sf-fields 1.3: `t` in full, `f` only when modified in the last 3 days before the last SUCCESS) needs `lastModifiedDateTime` or `lastModified` on `User`. SF facts: SAP documents both `lastModified` (Edm.DateTime, filter `datetime'...'`) and `lastModifiedDateTime` (Edm.DateTimeOffset, filter `datetimeoffset'...'`) on User and warns that two orderings of the same filter can return different rows [V: help.sap.com "Working with the Edm.DateTime Data Type", "lastModifiedDateTime and $filter", KBA 2920680]. The base's own delta uses `datetime'<now-26h>'` (B4.5). `standards/successfactors.md` says `datetimeoffset` for every entity; that is per field (to correct in the knowledge base by the next field-mode run; this review was told to write no other file). Use the field and literal that the tenant `$metadata` shows (C4). Combining it with `status in` is [T].

### NOTES (no action)

- Concurrent employment: two `userId`s, one email, one `sf_person_id` is stored; the R1 manual-match refusal when two rows share an email is for ST-PP R1. Nothing to change in the sync [05-sf-fields 5].
- `T`/`F` rows can never become employees: the filter and the mapper both exclude them (two independent guards).
- A leaver is cancelled on the first run that sees `f`. If HR corrects a termination, SF can flip `f` then `t`; the cancellations stay (accepted, 05-integrations 1.6). The exposure is bookings of at most 14 days.
- Long leave, sabbatical and pay-no-work stay `t` in `User.status` in the standard HRIS mapping [T] C9; nobody is cancelled for them.
- Retry on `$skip` paging: a failed page restarts only that page; with `$orderby=userId` the sets stay stable unless a user is created or deactivated in the middle of a read (a row can then be read twice or missed once; the duplicate rule keeps the last row, and a missed row is "missing", which cancels nothing). Acceptable.
- Logs and the job result carry user ids and counts only: confirmed in `PeopleSyncJob.java:63-105` and Runner 148, 198.

## 4. Q170: drop threshold 10 percent or 20 to 25 percent

My view: **keep 10 percent as the default, make it configurable (as built), add the small-tenant floor of S2.** Reasons from the SF side:

- Normal churn is tiny. Annual attrition of 10 to 20 percent is 0.03 to 0.06 percent a day; a 3,000-person company deactivates 1 to 3 people a night, a bad day maybe 30 (1 percent). Even a one-site closure or a divestiture, the rare legitimate case, is a planned event and the admin is told to raise the setting first (Q81).
- The cases the guard exists for are SF-side accidents: a bulk deactivation by an admin or data-load error, a changed target population (typically one legal entity or one population group, 10 to 30 percent of the people), a half-empty page set. A 20 to 25 percent line lets the smaller of these through. Absent people cancel nothing, so the harm of a missed population shrink is small, but a mass false `f` cancels real bookings (no mail, G7) and is the expensive case. 10 percent catches it earlier at no daily cost.
- The guard counts newly `f` plus absent-from-read among active SuccessFactors rows only. Inactive users that SF purges later (DRTM) are already inactive in the copy and are not counted, so a routine purge does not trip it. Rows that turn external (`T`) are counted as absent, which is the intended signal.
- Where 10 percent is wrong is small tenants, not big ones: add the absolute floor (S2a) rather than raising the percentage.
- The security brief's 20 percent (4.6) and 25 percent (item 8) should be corrected to "10 percent, configurable, with a floor of 5 people". That is for security-architect to edit; Q170 stays with them.

## 5. Checks to run on the customer's dev tenant

Run as the same API user and authentication type the product will use (a read as a tenant admin shows more than the role allows). `$format=json` is implied. Use one anonymised page as evidence (Q77).

| # | Call | Expected result | Decides |
|---|---|---|---|
| C1 | `GET /odata/v2/User?$top=3&$select=userId,status,firstName,lastName,email,location,manager/userId,personKeyNav/personIdExternal&$expand=manager,personKeyNav&$filter=status in 't','f'&$orderby=userId` and, from the DeskBook dev log of one run (base client debug log of the URL), the exact URL the base built | HTTP 200, 3 rows, each with the 8 fields; `manager` an object with `userId` or null; `personKeyNav` with `personIdExternal`. The base-built URL has the filter spaces and quotes encoded (`%20`, `%27`), has one `$select`, one `$expand`, one `$filter`, and the same 200 result | Q167: base client works, setting content, URL encoding, `status in` together with `$orderby` and `$expand` (05-sf-fields 8 item 4). If 400: add the failing piece to a second `PeopleSource` |
| C2 | `GET /odata/v2/User/$count?$filter=status eq 't'`, then the same with `'T'`, `'f'`, `'F'`, `'e'`, `'d'`; then `.../User/$count?$filter=status in 't','f'` | Counts: `t` about the headcount; `f` the leavers; `T`/`F`/`e`/`d` small or zero. `in 't','f'` equals count(`t`) + count(`f`). Count(`T`) different from count(`t`) | case sensitivity of the filter (if count(`T`) equals count(`t`) the filter is case-insensitive and `T` rows reach the mapper as `BAD_STATUS`: harmless, but inform the PO); size of the read (S6) |
| C3 | `GET /odata/v2/User?$select=userId&$filter=status in 't','f'&$orderby=userId&$top=200&$skip=0`, then `$skip=200`, `400`, ... to the end | No `userId` twice, none missing against `$count` of C2, last page shorter than 200, each page under 10 s (record the time of the slowest) | paging with `$orderby`, S1 page size |
| C4 | `GET /odata/v2/$metadata` (save it; look at `EntityType Name="User"` and `EmpEmployment`) | `User`: `userId` MaxLength, `email`, `location`, `status`, `manager` and `personKeyNav` as NavigationProperty, `lastModifiedDateTime` and/or `lastModified`; note whether `defaultFullName`, `displayName`, `personIdExternal` exist as plain properties of `User`; `empInfo`, `incumbentOfPositionNav`; on `EmpEmployment` `jobInfoNav`. `PerPerson.personIdExternal` present | field lengths against 100/200/254/50 columns; the names used by Q167/Q169/S6; preferred-name field |
| C5 | `GET /odata/v2/User?$select=userId,location&$filter=status eq 't'&$top=20` and `GET /odata/v2/FOLocation?$select=externalCode,name,status&$top=20` | `User.location` equals `FOLocation.externalCode` (bare code) for the same people, or it equals the name or "Name (code)" | Q111/Q169: the location source |
| C6 | `GET /odata/v2/EmpJob?$select=userId,location,managerId,emplStatus,startDate,endDate&$filter=userId eq '<id of one test employee>'&fromDate=<today>&toDate=<today>` | exactly one record (the one valid today) with `location` the FOLocation code, `managerId` equal to `User.manager.userId` of C1 for that person | EMPJOB option for Q169; manager source agrees |
| C7 | `GET /odata/v2/User('<top manager id>')?$select=userId,manager/userId&$expand=manager`, and `GET /odata/v2/EmpJob?$select=userId,managerId&$filter=managerId eq 'NO_MANAGER'&$top=3` | manager is null or the literal `NO_MANAGER`; the second call shows whether `NO_MANAGER` exists as a value. Both forms are already treated as "no manager" by the code | confirms nothing breaks; records the tenant's form |
| C8 | Time one full read with the base client's URL (C1 shape, `$top=200`) over all pages, and one page without `incumbentOfPositionNav` if you can call SF directly | each page under 10 s; whole read under 3 minutes (AC14.1: 10 minutes). If one page takes over 30 s, S1 is a must | page size, whether the base's three expansions are affordable |
| C9 | Pick (a) a terminated employee, (b) an employee with a future-dated termination, (c) a future-dated hire, (d) someone on long leave. For each: `GET /odata/v2/User('<id>')?$select=userId,status` and `GET /odata/v2/EmpJob?$select=userId,emplStatus,endDate&$filter=userId eq '<id>'&fromDate=<today>&toDate=<today>` | (a) `f`; (b) `t` until the end date passes, then `f` at the next HRIS sync; (c) record whether it is `t` or `f` before the start date; (d) `t`. Note on which day after the end date `f` appears | when a leaver is seen (04 UC4 timing), pre-hire behaviour (a pre-hire `f` is not stored after M2 and appears as a new person when `t`), leave handling |
| C10 | As the API user: `GET /odata/v2/User?$select=userId&$filter=status eq 'f'&$top=1` and `User/$count?$filter=status eq 'f'`; compare with the tenant admin's count of inactive users | one row returned and the counts agree. 0 rows when the tenant has leavers = the role's target population excludes inactive users | Q113: without it leavers are invisible and every leaver becomes `MISSING` |
| C11 | Read the same 20 `userId`s (C1 shape) as the API user and as an admin | no field is null for the API user where the admin has a value (email, location, manager, personKeyNav); if there is, the RBP field permission or target population is missing | section 7 of 05-sf-fields, M1 scenario |
| C12 | In the product: Settings > Integrations > SuccessFactors, read `BIZX_USER_API_DATA_MODEL_FIELDS` (a developer, not pasted into chat if it holds more than field names); ask the base owner which jobs read it | the list contains `userId,status,firstName,lastName,email,location,manager/userId,personKeyNav/personIdExternal` plus whatever the base needs; no other job breaks when it is extended | Q167, S5 |
| C13 | Admin Center > Job Monitor (or Scheduled Job Manager): last start times of the HRIS Sync / "Employee Central to User" sync job over the last 7 days | one run per night at a fixed time; note it in UTC | S4: `FIRST_RUN_UTC` at least 1 hour after it finishes |
| C14 | `GET /odata/v2/User/$count?$filter=status eq 't' and email eq null`, and `...$filter=status eq 'f' and email eq null` | `t` and no email: 0 or a short list of known cases; `f` and no email: possibly many. (Combining filters on `User` is itself a check, 05-sf-fields 8 item 4; if it fails, count in a script from pages.) | M2 size; the real size of AC14.7 noise |
| C15 | `GET /odata/v2/PerPerson?$select=personIdExternal,employmentNav/userId&$expand=employmentNav&$top=200` (or the `User` pages of C1 grouped by `personKeyNav/personIdExternal` in a script) | count persons with two or more `userId`s; also whether `personIdExternal` equals `userId` for most users | concurrent employment in use, size of Q60/Q85 cases |
| C16 | Is Employee Central enabled on the tenant at all: `GET /odata/v2/EmpJob?$top=1&$select=userId` | 200 with a row; 404 or "entity not found" = no EC, so `personKeyNav`/`empInfo` may be empty and `User.location` is typed by HR | Q169 option B is not possible without EC |

Run order for one session: C4 first (names), then C1, C2, C10, C11, C5, C8, C12, then the rest.

## 6. Open items for the product (not code)

1. Real sign-in id vs `userId` (Q62, 05-sf-fields 8 item 8): not checkable from the sync; needs the IdP mapping on the dev tenant.
2. The drop setting and the first-run time are deployment keys; the admin runbook (ST-PP-6 / go-live checklist) should say how to raise `DESKBOOK_PEOPLE_MAX_DROP_PERCENT` before a planned large leave-off and lower it again.
3. After M1 and M2 are fixed, rerun the 88 people tests, and add: manager/location/person-id all null with 20+ rows; first-load `f` rows not stored and not listed.

## 7. Sources

- SAP KBA 2166571 (query inactive users on User, `status in`, default active-only read); SailPoint community post showing `status in 't','f','T','F','e','d'` on `User` (community, supports the syntax only).
- SAP KBA 2395169, 2506989 (User.location HRIS-synced, tenant-mapped); KBA 2638422, 2148752 (effective-dated default and `fromDate`/`toDate`); KBA 2675265, 2489065, 2990434 (paging).
- help.sap.com SuccessFactors OData API Reference Guide: "lastModifiedDateTime and $filter", "Working with the Edm.DateTime Data Type", "Working with the Edm.DateTimeOffset Data Type"; KBA 2920680 (lastModifiedDateTime range filtering).
- `D:/product-factory/base/BASE-SPEC.md` B4.5, B5 (base client use, setting names); the TTCommon jar itself was not available to read.
- `standards/successfactors.md` (not changed in this review; two facts to add later: `status in` several codes, `User` has both `lastModified` and `lastModifiedDateTime`).
