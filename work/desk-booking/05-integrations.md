# Integrations - DeskBook

Design mode (S5), integration-engineer, 2026-10-28. Inputs: `05-sf-fields.md` (SuccessFactors consultant, the source of truth for SF entities, fields, ids and the status filter; this file follows it, fix M8 of `05-design-review.md`), `05-architecture.md` (ADR-5, ADR-6, 4.4, 4.5, 6.3, 6.5), `02-spec.md` F13, F14, F15 and Integrations, `decisions.md` D1-D4, questions Q53, Q54, Q62-Q64, base B4 (jobs) and B5 (integrations settings).
`05-data-model.md` did not exist when this was written, so target tables are named by business object ("employee record", "sync run", "notification row"); `ppl_employees`, `ppl_sync_runs` and `ntf_notifications` are the prefixes proposed in the architecture. Data-architect decides final names and columns.

Systems in scope: SAP SuccessFactors (in, read only) and the mail service (out). XSUAA sign-in and the Excel export are not designed here.

## 0. Summary

| System | Direction | Job(s) | Schedule | Biggest risk |
|---|---|---|---|---|
| SuccessFactors | in only (R48) | `PeopleSyncJob` (+ admin run-now variant) | hourly invocation, works once per UTC day after 01:00; hourly retry until one run succeeds (R49) | base client may not return manager and location (Q54, Q77); location code vs name (Q63, Q111); people absent from the read (counted `MISSING`, cancel nothing) |
| Mail service | out only | `PreReleaseReminderJob`, `NotificationDispatchJob`, `NotificationPurgeJob` (new) | every minute, every minute, daily | no confirmed sender in the base (Q53, Q64); reminder retry timing contradicts the deadline (Q78) |

Decisions taken in this design (each is small and reversible; the ones that need an owner are in section 6):
1. People copy is a full read every run (no delta). 3,000 people is about 15 pages; a delta cannot see people who disappeared.
2. The whole run is fetched into memory first, then applied in one database transaction. A failure in the fetch changes nothing, so "the last good copy stays" (R49) is literally true.
3. Leaver cancellation is a catch-up step that runs on every invocation, not only on the day's sync.
4. A run in which more than 10 percent of the active people would stop being active (newly `f` plus missing from the read) is refused as suspect data (the "file is bad" case of R49).
5. Mail goes through a `MailSender` port with a `LOG_ONLY` mode, so UAT and demos never mail real people.
6. A leaver is an explicit status `f`. A person who is absent from the read is counted separately (`MISSING`) and cancels nothing (M8).
7. The read asks for `status in 't','f'`: external users are not copied (pending the product owner's G3 answer 5); the SF person id is stored.

## 1. SuccessFactors (people copy)

### 1.1 What is exchanged

Direction: SuccessFactors to DeskBook only. Nothing is written back (R48). Entity: the SuccessFactors `User` record per person (OData v2), with its manager and person key expanded in the same call, and the current job record only when the location needs it (1.3). DeskBook keeps its own employee projection (ADR-6), not the base user tables.

| Business object | Fields | Used by |
|---|---|---|
| Employee record | user id, name, email, status (active or not), direct manager user id, location code, SF person id | sign-in match (Q62), `createBooking` checks (`PROFILE_NOT_READY`, `EMPLOYEE_INACTIVE`), manager derivation (R52), team views (R1), home office (BK-11), emails (recipient only) |
| Sync run | start, end, trigger, status, counts, skipped list, error code | `/jobs` result text now, S18 tab in R1 (ST-PP-6), `PROFILE_NOT_READY.lastCopyAt` |

### 1.2 External API

| Item | Design |
|---|---|
| Connection | Base B5 SuccessFactors card (BIZX_* keys in group SUCCESSFACTORS, secrets encrypted). DeskBook reads no secret and stores none. |
| Client | Base `SuccessFactorsClientService.getUserDetails(top=200, skip, filter)` for auth, URL and paging, as base B4.5 does. |
| Entity and version | OData v2 `User` entity of the tenant API URL (BIZX_API_URL). |
| Paging | `$top=200`, `$skip` steps of 200, until a page has fewer than 200 rows. Ask for `$orderby=userId` so that `$skip` paging cannot repeat or lose a row between pages (to confirm the base client allows it, Q77). 200 per page is kept although 1,000 is the commonly cited ceiling (05-sf-fields 1.4): more calls, less risk. Guard: stop at 500 pages (100,000 rows) and fail the run. |
| Fields asked | `userId, status, firstName, lastName, email, location, manager (userId only), personKeyNav (personIdExternal only)` with `$expand=manager,personKeyNav` (05-sf-fields 1.1). When `DESKBOOK_SF_LOCATION_SOURCE=EMPJOB` (1.3) also `$expand=empInfo/jobInfoNav` and `empInfo/jobInfoNav/location`. `lastModifiedDateTime` only if the delta of 1.8 is ever built. Only these; no photo, phone, job code, birth date or any field DeskBook does not need. |
| Filter | `$filter=status in 't','f'` (05-sf-fields 1.1, 1.3). `t` is an active employee, `f` a deactivated one, so a leaver is an explicit `f`. External users (`T`, `F`, and `e`, `d`) are not read, so they are not copied and cannot book (Q109, pending the product owner's G3 answer 5). Never `status ne ...`. The API user's role must include inactive users in its target population (05-sf-fields 7, Q113); without that no `f` row comes back. That `status in` works together with `$orderby` and `$expand` is checked on the tenant (05-sf-fields 8 item 4). |
| Auth | whatever the base client does with the B5 settings; DeskBook adds nothing. |
| Readiness gate | first line of every run: `IntegrationConfigService.requireSuccessFactorsReadyForSync()` (B5.9): 409 `SUCCESSFACTORS_UNTESTED` unless the last Test connection was SUCCESS, 409 `SUCCESSFACTORS_NOT_CONFIGURED` when the company id is blank. Both fail the run with that code as the reason. |
| Limits | SuccessFactors throttles per tenant and per API user. One sequential reader, about 15 to 45 calls a run (inactive users add pages), no parallel pages. HTTP 429 or 503 is retried honouring `Retry-After` if present. |

Gap to close in build (Q77): B4.5 describes the base client mapping into the base user tables; it is not confirmed that `getUserDetails` can return the manager and location, nor that it accepts `$select` and `$orderby`. If it cannot, `PeopleSfReader` in the `people` module makes its own OData GET with the same base URL and the same authentication object from the base client (no second credential), and that is the "PP-1 and PP-2 grow by about 3 points" case of Q54. Needs one anonymised sample payload from the tenant either way. The same applies to the `status in` filter and the two `$expand`s (05-sf-fields 8 items 3 and 4).

### 1.3 Field mapping (external field to our record)

Column names are proposals; data-architect owns them.

| SuccessFactors field | Our field (employee record) | Transform | Null or odd values |
|---|---|---|---|
| `userId` | user id (natural key per tenant, unique) | trim; kept exactly as received; matched to the sign-in user id exactly (Q62), case compared as the base compares it | blank: skip, count as "no user id", list |
| `firstName`, `lastName` | display name | `firstName + " " + lastName`, trim, collapse spaces, cut at 200 | both blank: name = user id |
| `email` | email | trim, lower case; must match a simple `x@y.z` shape | blank or invalid: skip the record, count and list it with reason `NO_EMAIL` (AC14.7, ST-PP-1). Existing record with the same user id keeps its last good email and is not skipped for a bad new value (reason `BAD_EMAIL` logged, counted) |
| `status` | active flag | `t` is active, `f` is inactive; any other value skips the row, counted `BAD_STATUS` and listed (05-sf-fields 1.2) | status absent from the response for every row: the run is refused as bad data (1.5). With the filter only `t` and `f` normally arrive. A row that arrives `f` and never had an active DeskBook row (first load, old leavers) is stored inactive with no event (1.6) |
| `manager.userId` | manager user id (text, no cross-table link) | trim; equal to the person's own user id becomes empty | empty: no manager. Manager not in the copy (for example inactive or outside scope): kept as is; derived manager status only counts active people |
| `location`, or `empInfo/jobInfoNav/location` | SuccessFactors location code (FOLocation `externalCode`) | trim, upper case for comparison. Source by config `DESKBOOK_SF_LOCATION_SOURCE`: `USER` (default) or `EMPJOB`, set after the tenant check, because `User.location` is a text copy whose format the tenant sets (05-sf-fields 3, Q111). `EMPJOB` returns the job record valid today | empty: no home office. Value not matching any office's SF location code: kept, no home office, Today shows no free-desk count (Q63) |
| `personKeyNav/personIdExternal` | SF person id (`sf_person_id`, nullable, not unique; Q110) | trim | missing (tenant without Employee Central): empty. Never a key: booking is by the sign-in user id (Q62). Two SF rows with one person id (concurrent employment, rehire) are one person for R2 anonymisation; the R1 email match refuses when two SF rows share an email (05-sf-fields 5) |
| derived | manager flag (R52) | true when at least one active employee has this person as manager; computed in the same transaction after all upserts | cleared when the last active report goes |
| derived | source | `SUCCESSFACTORS` for all rows from this job; `MANUAL` is reserved for R1 `addPerson` (Q60) | - |
| derived | last seen run | id of the run that saw this row | used for the missing-person rule |

Home office is not stored as an office id. The raw location code is stored and the office is found at read time through `OfficeQueryService` by the office's SF location code. When the admin later types the code on an office, the mapping works at once, without waiting for a sync.

Check to settle with the tenant sample (Q77, Q111): if `User.location` is the bare FOLocation code nothing changes. If it is a name or "Name (code)", set `DESKBOOK_SF_LOCATION_SOURCE=EMPJOB` and the same call returns the code from the job record (no second call, no change for the admin). The admin never types a location name as the office code: names are localised and renamed, so the mapping would break silently (05-sf-fields 3). If Employee Central is not enabled the `EmpJob` path does not exist and `User.location` as typed by HR is used.

### 1.4 Sync design

| Item | Design |
|---|---|
| Job | `com.talenteam...people.job.PeopleSyncJob` on TTCommon `BaseJob` (B4.1), registered in the FE job registry under `inbound` (B4.9). |
| Schedule | HOURLY (`jobFrequency` `1:0:0`, B4.11). Each invocation: (a) stale-run recovery, (b) leaver catch-up (1.6), (c) sync only if no SUCCESS run exists for the current UTC date and UTC time is 01:00 or later. Otherwise it ends at once with `addInfo("People copy already done today")`. This gives the nightly copy and the hourly retry from one job (ADR-6). Cost: 24 result rows a day on `/jobs`, 23 of them "already done". |
| First run after 01:00 UTC | about 06:30 India, 02:00 Central Europe, 21:00 the evening before in US Eastern. |
| Run kinds | `SCHEDULED` and `ADMIN`. An admin run (Run now on `/jobs`, B4.2 `createAdhocJob`) must not be blocked by "already done today". Preferred design: a second job class `PeopleSyncRunNowJob` sharing one `PeopleSyncRunner`, like the base pair UsersSyncDailyJob and UsersSyncFullFetchJob. If TTCommon lets a job know it is ad hoc, one class is enough (Q79). |
| Batch size | page 200 from SuccessFactors; database apply in chunks of 500 inside one transaction. |
| Checkpoint | none needed: a run is all or nothing. |
| Idempotency | upsert by (tenant, user id). Re-running the same data changes nothing: a row is written only when a mapped value differs (compare before write), so no audit noise and no version bumps. |
| Overlap (AC14.8) | a sync run row with status RUNNING is unique per tenant (database constraint, data-architect). A second invocation finds it and ends with a note. A RUNNING row older than 30 minutes is a crash leftover: mark it ABANDONED and continue. |
| Fetch then apply | 1 insert RUNNING row (own transaction). 2 gate B5.9. 3 read all pages into memory (3,000 rows is about 1.5 MB; 100,000 rows cap is about 50 MB). 4 sanity checks (1.5). 5 one transaction: upsert, mark last seen run, derive manager flags, mark people newly `f` as inactive with "leaver not yet handled", count (not change) people absent from the read, write counts. 6 update the run row to SUCCESS with counts (own transaction). No database transaction is open while waiting for SuccessFactors. |
| Conflict rule | SuccessFactors wins for every field of a `SUCCESSFACTORS` row. A `MANUAL` row (R1) is never marked left by absence; when a SuccessFactors row with the same email appears, the rows are merged into the SuccessFactors one (Q60) and the manual source disappears. |
| Run counts | fetched, new, changed, unchanged, inactive (newly `f`), missing (absent from the read, nothing changed), left handled, skipped (by reason, including `BAD_STATUS`), manager flags changed. Skipped list keeps user id and reason only, no names or emails, capped at 500 entries. |
| First load at go-live | Checklist for the admin before go-live: (1) base Settings > Integrations > SuccessFactors saved and Test connection SUCCESS; (2) offices created with their SF location codes (Q63); (3) Run now on `/jobs`; (4) read the counts: new equals the expected headcount, missing is 0 and inactive shows the old leavers that arrive as `f` (stored inactive, no `EmployeeLeft`, they never had a DeskBook row; the previous active count is 0, so the drop check is skipped), skipped list reviewed. Until then every booking gets `PROFILE_NOT_READY`. |
| Re-run by an admin | Run now on `/jobs` (base B4.13, no new screen). Safe at any time because of idempotency and the overlap rule. |

### 1.5 Bad data checks (the "file is bad" case, R49)

A fetched set is refused, the run ends FAILED, and nothing in the database changes when:
- zero rows came back, or zero rows are active;
- every row lacks `status`, `email`, or `userId` (field missing from the response, usually a changed field list);
- the people who would stop being active, newly `f` plus active `SUCCESSFACTORS` rows absent from the read, are more than 10 percent of the active `SUCCESSFACTORS` rows of the last good copy (config `DESKBOOK_PEOPLE_MAX_DROP_PERCENT`, default 10, ConfigService group DESKBOOK, ADR-11). This stops a half-empty answer, or a target-population or permission change, from flipping hundreds of people: absent people are only counted and cancel nothing, but they still count toward the guard so the admin sees the problem. A real large layoff needs the admin to raise the setting first (Q81).

The reason is written to the run row and to the job result with `addError`, as a code (`EMPTY_RESPONSE`, `FIELDS_MISSING`, `DROP_TOO_LARGE`, `SF_UNREACHABLE`, `SF_AUTH`, plus the two B5.9 codes), never a raw response body.

### 1.6 Leavers (R51, AC14.5)

- A person is a leaver only when the run saw them with status `f` (explicit evidence) and the row is `SUCCESSFACTORS`. A person who is absent from the read is not a leaver: they are counted `MISSING` and listed (user id only, capped at 500), their row stays as it was, nothing is cancelled and nothing is marked left. Absence also comes from a target-population or permission change, a purged record (DRTM) or a user turned external; none of these is leaving (05-sf-fields 1.3, 4; M8).
- A real leaver who is purged from SF stays active until SF shows `f` or an admin acts; this is accepted, the MISSING count and list make it visible (question to sf-consultant).
- A person who arrives as `f` and never had an active DeskBook row (first load, old leavers) is stored inactive and publishes no `EmployeeLeft`.
- The sync only marks the person inactive and records "leaver not yet handled". It does not cancel bookings itself (module boundary).
- Handling is a catch-up step of every invocation, also on days when the sync is skipped: for each person inactive and not yet handled, `people` publishes `EmployeeLeft(id)`; the `booking` listener cancels future bookings in the same transaction, sends no email (G7) and `people` marks the person handled in that transaction. One person per transaction: a poison person (cancel fails) is logged with `addError`, counted in the run result text, and retried by the next hourly invocation without blocking the others.
- A person who becomes active again is just active again; bookings cancelled earlier stay cancelled.
- Booking `EMPLOYEE_INACTIVE` (AC5.9) takes effect as soon as the flag is written, before the cancellation finishes.

### 1.7 Failure behaviour

| Case | Handling | Admin sees | Employee sees |
|---|---|---|---|
| Connect timeout | 10 s per call | run FAILED `SF_UNREACHABLE` | nothing, copy is intact |
| Read timeout | 60 s per page | same | same |
| 5xx, 429, network reset | retry the page twice, waits 5 s then 20 s (honour `Retry-After`, max 60 s); then run FAILED | same | same |
| 401 or 403 | no retry; FAILED `SF_AUTH`; message tells the admin to open Settings > Integrations and Test connection | `/jobs` result and base ConnectionBanner (B4.13) | same |
| Gate B5.9 fails | no call made; FAILED with the 409 code | same | `PROFILE_NOT_READY` for people not yet copied |
| Bad data | 1.5 | FAILED with code and counts | same |
| Crash mid-run | RUNNING row recovered after 30 minutes, nothing was applied | nothing special | same |
| Poison record | skipped and listed (bad email) or counted (leaver cancel failed); the run still succeeds | skipped list (R1 S18); `/jobs` text | same |
| Down all day | hourly invocations keep trying; after 36 hours without a SUCCESS run a metric alert fires (Q82); after 2 days the R1 banner (AC14.3) | banner, S18 | employees with a record keep working; new hires see "Your profile is not ready yet" with the last copy date |

No circuit breaker is needed: at most 24 invocations a day, each ends fast when the first page fails.

Test connection: the base owns it (B5.8, `SuccessFactorsClientService.testConnection()`). DeskBook adds no second test. The job does not reset `SUCCESSFACTORS_LAST_TEST_STATUS`; a credential that expires after a good test shows up as a FAILED `SF_AUTH` run, not as an untested connection. Open point in section 6 (Q80): MVP has no DeskBook screen showing "People data last updated <date>" (R49), because ST-PP-6 is R1.

### 1.8 Volume and cost

| Item | Estimate |
|---|---|
| Rows per run | 3,000 active now plus the inactive users SF keeps (a few thousand more, 05-sf-fields 1.3); design limit 100,000 |
| Remote calls | 15 to 45 per run, sequential, about 2 to 4 s each, so 30 s to 3 minutes |
| Apply | read 3,000 rows by user id once, write only changed rows (normally under 50 a night); about 5 s |
| Total | 1 to 4 minutes against the 10 minute criterion (AC14.1) |
| Memory | about 1.5 MB per run |
| Database | one indexed read of the active people, a few dozen writes, one sync run row (plus up to 24 on an outage day). Keep sync run rows for 1 year, purged by the same new purge job as notifications (6.3 gap). |
| Scale trigger | above about 20,000 people add the base pattern: daily delta with `lastModifiedDateTime` and a weekly full read; first step (05-sf-fields 1.3): read `t` in full and `f` only when modified in the last 3 days before the last SUCCESS (filter combination to verify). Not needed now. |

### 1.9 Secrets, config, privacy

- SuccessFactors credentials: base B5 only (BIZX_IDP_PRIVATE_KEY and the others, encrypted, never returned by GET, B5.4). DeskBook code has no property for them.
- DeskBook keys in ConfigService group DESKBOOK: `DESKBOOK_PEOPLE_MAX_DROP_PERCENT` (10) and `DESKBOOK_SF_LOCATION_SOURCE` (`USER`, or `EMPJOB`). Nothing else is needed.
- Logs and job results carry user ids and counts, never names, emails, manager ids with names, or response bodies. SuccessFactors error text is mapped to the codes above before it is logged.
- The employee record is personal data: name, email, manager, SF person id. Retention and anonymisation are for security-architect and data-architect; this job never deletes employee rows (leavers stay inactive so old bookings keep a valid owner until the R2 anonymise job).

## 2. Mail service

### 2.1 What is exchanged

Direction: out only. DeskBook sends; it receives nothing (no bounce reading, no inbound mail). Messages (F13, English in release 1, R47):

| Type key | Release | Trigger | Recipient | Valid until |
|---|---|---|---|---|
| `PRE_RELEASE` (NT-2) | MVP | `PreReleaseReminderJob`, 15 minutes before the deadline (`DESKBOOK_PRE_RELEASE_LEAD_MINUTES`, 20 in the fallback of 2.4) | booker | the booking deadline |
| `RELEASED` (NT-3) | MVP | `BookingReleased` event | booker | 1 hour after creation (R46 window) |
| `EVENING` (NT-4) | R1 | job at 18:00 office time, evening before | booker | 18:00 + 1 hour |
| `BOOKED_FOR_YOU`, `CANCELLED_BY_MANAGER` (NT-6) | R1 | `BookingCreatedForOther`, manager cancel | the employee | 1 hour |
| `CANCELLED_BY_ADMIN` (NT-5) | R1 | block, closure, move | the employee | 1 hour |
| `NO_SHOW_REMINDER` (NT-7) | Later | third release of the month (R53) | the employee | 1 hour |

A message never names another employee (R47). Leaver cancellations send no mail (G7). Employees without a usable email or who are inactive at send time get no mail (status `SKIPPED`, reason recorded, not an error).

### 2.2 Port and adapters

```
MailSender.send(MailMessage m) -> MailResult
MailMessage { messageId (derived from the event key), toAddress, subject, textBody, htmlBody }
MailResult  { OK | TRANSIENT_FAILURE(reason code) | PERMANENT_FAILURE(reason code) }
```
The port lives in `notification`; nothing else imports an adapter. Adapters, in order of preference (Q64, recommended answer accepted by D4):
1. `TtCommonMailAdapter`, if TTCommon exposes a mail sender. Not confirmed anywhere in `BASE-SPEC.md`, which lists only EMAIL* tables (B1 table list). To be confirmed from the TTCommon jar before NT-1 starts; this is the cheapest case.
2. `SmtpMailAdapter` over `spring-boot-starter-mail` with the connection taken from a BTP destination named `deskbook-mail` (or the mail service in the customer's landscape). New dependency, needs a D6 card from solution-architect.
3. `LogOnlyMailAdapter` selected by `DESKBOOK_MAIL_MODE=LOG_ONLY`: logs the outbox row id and type, marks it SENT with the note "not sent". Default on every profile except production, so demos and UAT mail nobody.

Config in ConfigService group DESKBOOK (non-secret only): `DESKBOOK_MAIL_MODE` (LIVE or LOG_ONLY), `DESKBOOK_MAIL_MAX_PER_MINUTE`, `DESKBOOK_PRE_RELEASE_LEAD_MINUTES`, `DESKBOOK_MAIL_FROM_ADDRESS`, `DESKBOOK_MAIL_FROM_NAME`, `DESKBOOK_APP_BASE_URL` (public approuter URL for links). SMTP host, user and password live in the destination or TTCommon, never in DeskBook config, never logged. These keys are set by deployment in MVP; the base B5 screens have no mail card (adding one is a base change, not requested).

### 2.3 Sending design

| Item | Design |
|---|---|
| Enqueue | `notification` listeners write the outbox row in the booking's transaction (ADR-5), unique per (tenant, event key). Event keys: `PRE_RELEASE:<bookingId>:<deadline epoch>`, `RELEASED:<bookingId>`, `EVENING:<bookingId>`, and so on. The unique key is what makes AC13.7 (no duplicate when the job runs twice) true. |
| Dispatch | `NotificationDispatchJob` every minute. Takes due rows (PENDING with next attempt due), oldest deadline first, in batches of 200 repeated until none is due, the 50 second time budget is used, or the sender's rate limit (`DESKBOOK_MAIL_MAX_PER_MINUTE`, 2.4) is reached, then stops. Send in up to 4 parallel workers (config), 10 s send timeout, 5 s connect timeout. |
| Claim | before sending, set the row to SENDING with attempts + 1 and a version check, in its own short transaction; after the answer set SENT or schedule the retry. A SENDING row older than 5 minutes (crash during send) goes back to PENDING once. |
| Delivery guarantee | at least once. A crash between the mail server accepting and DeskBook saving SENT can send one duplicate; accepted (narrow window, harmless messages). The Message-ID header is derived from the event key. |
| Recipient | resolved from the employee record at send time (ADR-5), never copied into the outbox. |
| Content | text and HTML from `messages.properties` in `en`, built in the backend. Links go to `DESKBOOK_APP_BASE_URL` plus the booking id; they never carry a token and do not sign anyone in (R25, security brief). No tracking pixels. Transactional mail, no unsubscribe link. |
| Retry | transient failure: retry at +20, +40, +60 minutes, then FAILED (R46, ADR-5). The booking is never touched (R46). Overall age limit 1 hour from creation: older rows become FAILED whatever the attempt count. |
| Permanent failure | invalid or rejected recipient (SMTP 5xx class, malformed address): FAILED at once, no retry, reason code kept. |
| Skipped | no email on file, employee inactive (except types that still apply), or the type's valid-until time has passed: `SKIPPED` or `EXPIRED`, reason recorded. |
| Circuit breaker | 5 consecutive transient failures stop the batch and open the breaker for 5 minutes (in memory on the job node; a restart resets it). While open, due rows are not attempted and do not use up attempts. This replaces the "next run tries again every minute" wording of 6.5, which would burn 50 s of every minute during an outage. |
| Alert | each FAILED row: `addError` in the dispatch job result (visible on `/jobs`) with row id, type and reason code, no address. Metric `deskbook.mail.failed` (needs the Actuator dependency, Q67). |
| Purge | SENT, SKIPPED, EXPIRED rows after 90 days, FAILED after 1 year, by a new daily `NotificationPurgeJob` (gap in 6.3, Q83). |

Conflict in the existing design, to be settled (Q78): `PRE_RELEASE` is due 15 minutes before the deadline, so the +20 minute retry would arrive after the booking was released and say "check in" for a desk that is gone. Recommended: for `PRE_RELEASE` only, retry at +2 and +5 minutes while the deadline has not passed, then mark EXPIRED (not FAILED, because a late reminder has no value). The other types keep +20/+40/+60.

### 2.4 Volume

| Item | Estimate |
|---|---|
| MVP mails a day | about 450,000 bookings a year is roughly 1,800 a working day; reminders to bookings not yet checked in about 700, releases (no-shows) about 180 at an assumed 10 percent, so about 900 a day |
| Peak | all bookings of an office share a deadline: about 860 reminders (year 1) to 1,150 (5 years) in the same minute at 09:45, and 540 to 720 release mails at 10:00 (Q125, 05-performance PF-5) |
| Capacity | the sender must take at least 300 mails a minute (5 a second); 4 workers at 0.3 s a mail can do about 800 a minute, so DeskBook is not the limit. At 300 a minute 1,150 reminders take under 4 minutes (the last at about 09:49) and 720 release mails about 2.5 minutes |
| Database | one outbox insert per event, three updates per sent mail (SENDING, SENT, version); about 1,000 rows a day, 90,000 retained |

**Requirement on the sender (the product owner confirms at G3, answer 6):** at least 300 mails a minute, sustained for 5 minutes, from a mail API or relay, not a personal mailbox. A mailbox-limited sender at about 30 a minute would send the last of 860 reminders about 29 minutes after 09:45, after the 10:00 release. The chosen sender is proven in load test T5 with 1,150 mails in a burst (section 4). The sender domain also needs SPF and DKIM for the sending host so reminders are not filed as spam (customer IT task before pilot).

**Fallback if the customer's mail service cannot take 300 a minute:**
1. Set `DESKBOOK_MAIL_MAX_PER_MINUTE` to the service's real limit: the dispatch job paces itself, so nothing fails and no attempt is used up.
2. Spread the burst: set `DESKBOOK_PRE_RELEASE_LEAD_MINUTES` from 15 to 20, so `PreReleaseReminderJob` creates the reminders at 09:40 and they are sent paced, oldest deadline first, until the deadline. The NT-2 text names the deadline time (not "in 15 minutes"), so an early reminder is still correct.
3. A reminder not sent by its deadline becomes EXPIRED (Q78); the booking is never touched.
4. Limit of the fallback: 1,150 reminders between 09:40 and 10:00 need about 60 a minute. Below that some people get no reminder, so the product owner is told at G3 which limit the customer's service has, not in production.

Other assumption to confirm: the relay allows 4 parallel connections.

### 2.5 What the user sees when mail is down

Employees see nothing in the app; bookings, check-in and release behave as normal (R46, AC13.6). The reminder missing means a person may be released without warning, which is the intended price of keeping the booking path independent. Admin sees FAILED mail only on `/jobs` in MVP; the R1 notification log page (ADR-5) lists them with reasons. Test of the mail path without a log page: `LIVE` mode on a test tenant with a test mailbox; "Send test email to me" on the R1 log page is recommended but not designed here.

## 3. Jobs registered by this design

| Job | Section on `/jobs` | Schedule | New or changed vs 6.3 |
|---|---|---|---|
| `PeopleSyncJob` | inbound | HOURLY, once per UTC day after 01:00 | as 6.3, plus stale-run recovery and leaver catch-up |
| `PeopleSyncRunNowJob` (or same class if TTCommon allows, Q79) | inbound | RUN_NOW only, not scheduled | new |
| `PreReleaseReminderJob` | outbound | MINUTE | as 6.3 |
| `NotificationDispatchJob` | outbound | MINUTE | as 6.3, breaker, batch loop and rate limit added |
| `NotificationPurgeJob` | maintenance | DAILY 02:00 UTC | new (Q83) |

## 4. Verification that needs a real system (for S6 and S7)

Unit tests use recorded sample payloads and a fake `MailSender`; no live calls in tests. These need the real systems:
1. One real User API page from the pilot tenant: field names, `status` values, manager and location shape, `$orderby` and `$select` acceptance (Q77).
2. Test connection SUCCESS and a first full run with the real headcount: run time, row counts, skipped list.
3. A forced 401 (wrong key) and a forced timeout on a test tenant to see the admin messages.
4. A real SMTP or BTP mail send to a test mailbox: from address, links, spam placement, and 1,150 messages in a burst at the 300 a minute requirement of 2.4 (load test T5).
5. TTCommon scheduler precision for the MINUTE jobs (architecture risk 1) with the dispatch job running 50 s batches.

## 5. Handover

- solution-architect: replace the 6.5 mail row (breaker wording), add `NotificationPurgeJob` and the people-sync run-now variant to 6.3, record the PRE_RELEASE retry rule in ADR-5, add a D6 card for the SMTP starter if TTCommon has no sender (Q64, Q67).
- data-architect: employee record needs manager user id, SF location code, active flag, manager flag, source, last seen run, leaver-handled marker, plus SF person id (`sf_person_id`, nullable, not unique, Q110), a unique "one RUNNING sync run per tenant" constraint, and on the sync run row `inactive_count` (newly `f`) and `missing_count` (absent from the read) next to the left count (M8); outbox needs status SENDING and the reason code, plus the unique event key; purge windows in 1.8 and 2.3.
- api-designer: `PROFILE_NOT_READY` carries `lastCopyAt` from the last SUCCESS run.
- security-architect: no secret handled by DeskBook; log rules in 1.9 and 2.3; links carry no token.
- base-builder: Q77, Q79, and the TTCommon mail service question behind Q53 and Q64.

## 6. Open questions raised (also in questions.md)

Q77 SF field shape and client capability; Q128 and Q129 to sf-consultant (absent people, location source); Q78 PRE_RELEASE retry; Q79 ad hoc job variant; Q80 MVP visibility of "People data last updated" (R49); Q81 mass-leaver threshold; Q82 who receives the alerts; Q83 purge job.
