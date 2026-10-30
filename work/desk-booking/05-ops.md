# 05-ops - DeskBook operations plan (devops-engineer, 2026-10-29)

Scope: environments, per-environment settings, the job schedules, the first people copy, alerts, and the checks this sandbox could not run.
Files changed for this plan: `approuter/xs-app.json` (SPA fallback, M3), `manifest.yml` (instances, memory, pool, health check). Nothing was deployed, started or built.
Names only below; no host, secret or credential value appears here or in the files.

## 1. What changed in the files

| File | Change | Why |
|---|---|---|
| `approuter/xs-app.json` | 3 routes added before the end, last catch-all replaced: (4) `/assets/**` from `resources`, cached 1 year (hashed names); (5) any other path with a file extension from `resources` (a missing file stays a real 404); (6) any path with no dot and not under `/deskbook`, `/api`, `/webservices` returns `/index.html`, `no-cache`. Query strings are allowed on all three. Routes 1-3 and the `xsuaa` auth of every route are unchanged. | M3 / Q189: `/bookings?focus=...&action=hold`, `/book`, `/admin/...`, `/reports`, `/no-access`, `/forbidden` and a reload on any screen now open the app instead of 404. After sign-in the approuter returns the person to the same URL (proven on dev, check C1). |
| `manifest.yml` backend | `instances: 2`, `memory: 1536M`, HTTP health check on `/deskbook/api/public/health` (timeout 180 s for Flyway), env `SPRING_DATASOURCE_HIKARI_MAXIMUM_POOL_SIZE: 20`. Optional third app `deskbook-jobs` is written as a comment. | PB-8 / Q186. |

Route check (offline, `scratchpad/do7_route_check.py`, applies the regexes in order, path only and path + query): 37 URLs, 0 failures. Client routes and deep links with query strings give `/index.html`; `/assets/*.js|css` and `/favicon.svg` give the file; `/deskbook/api/**`, `/deskbook/api/public/**`, `/deskbook/webservices/**` go to destination `deskbook` (auth as before); bare `/api/**`, `/webservices/**` and `/deskbook` match no route (404), they are not turned into HTML.
Limits of this proof: it proves the regexes, not the approuter. Two things only a run shows: that `target: /index.html` with `localDir` serves the file (standard approuter use), and that the query string survives the XSUAA login redirect (check C1). A client route whose id contains a dot would be treated as a file (404); office ids are UUIDs, so none exists today.

## 2. Environments

| | dev | test | prod |
|---|---|---|---|
| Purpose | developer checks, first real mail and SF timing | load test T1-T12 (sized like prod, 2 instances, same PostgreSQL plan), E1-E10 | users |
| Backend instances / memory | 1 / 1024M is enough for checks, but run T-checks only on test | 2 / 1536M | 2 / 1536M (final value after T6 and T8) |
| PostgreSQL | dev service | same plan as prod; `max_connections` of the plan at least 50 (2 x 20 pool + jobs + admin) | same |
| SuccessFactors | customer dev tenant (checks C1-C16 of 07-sf-review 5) | customer test tenant, or an anonymised copy | production tenant |
| `DESKBOOK_MAIL_MODE` | `LOG_ONLY`; `LIVE` only for the timing test, to a test mailbox | `LIVE` only with test mailboxes (see risk below) | `LIVE` after post-deploy check P6 |
| Who deploys | developer | developer | developer with the customer's BTP admin |

Risk: `LIVE` sends to the e-mail address of every person the people copy loaded. On any space that holds real SuccessFactors people, mail would reach real employees. The product has no allow-list for test recipients (not found in code). Use an anonymised copy or a tenant whose mail addresses are test addresses, or keep `LOG_ONLY`.

## 3. Settings per environment (names only)

### 3.1 Placeholders in `manifest.yml` and `xs-security.json` (set by the developer at `cf push`)

| Placeholder / key | Meaning | Notes |
|---|---|---|
| `<backend-host>` | route host of the backend | |
| `<postgres-service>`, `<destination-service>`, `<xsuaa-service>` | service instance names in the space | never the dev names in prod |
| `<approuter-host>` | public host of the approuter | also in `xs-security.json` `redirect-uris` (`https://<approuter-host>/login/callback`) |
| `<approuter-host-suffix>` | part of `TENANT_HOST_PATTERN` | |
| `<backend-url>` | destination URL of `deskbook` | must end with the context path: `https://<backend-host-and-domain>/deskbook`. The routes send `/deskbook/api/v1/x` as `api/v1/x` to this URL and the WAR has `server.servlet.context-path=/deskbook`. Prove on dev with `GET <approuter>/deskbook/api/public/health` (check C2) |
| `<tenant-mode>` | xsuaa tenant mode | `xs-security.json` |
| `companyID` | tenant id the base reads | per environment; local runs use `-DcompanyID=local` |
| `SEND_XFRAMEOPTIONS` (both apps) | frame option | per customer |
| `allowedNodeRoles` | node role(s) that run jobs | see 5, Q206 |
| `IAS_XSUAA_XCHANGE_ENABLED`, `spring_profiles_active`, `databaseType`, `disableSchemaValidation`, `logoutEnabled` | fixed | keep as in the file |
| `SPRING_DATASOURCE_HIKARI_MAXIMUM_POOL_SIZE` | 20 | set; start-up log must show 20 (check C4) |

Role collections (BTP cockpit, per subaccount): "DeskBook User" (template USER) and "DeskBook Admin" (template ADMIN). Map the customer's IAS group to "DeskBook User" so nobody is assigned by hand (Q69); at least two named admins to "DeskBook Admin" before go-live.

### 3.2 Product settings (ConfigService group `DESKBOOK`, rows of the TTCommon CONFIGURATION table, not environment variables)

These are read through `ConfigService.getConfigurationMap()`. They are not manifest env, so `cf set-env` does nothing for them. How a row is entered on a new environment: section 11.1 (admin call to `POST /webservices/storeConfiguration`).

| Key | Default in code | Set per environment |
|---|---|---|
| `DESKBOOK_MAIL_MODE` | `LOG_ONLY` | yes (table in 2) |
| `DESKBOOK_APP_BASE_URL` | placeholder `https://deskbook.example` | yes: `https://<approuter-host>`, no trailing path. While it is unset the reminder link points to a dead address (Q196) |
| `DESKBOOK_MAIL_WORKERS` | 10 (1-16) | set 8 on test and prod until the real mail timing is known (PB-2, Q181) |
| `DESKBOOK_MAIL_MAX_PER_MINUTE` | 600 | keep; raise only if timing allows |
| `DESKBOOK_PRE_RELEASE_LEAD_MINUTES` | 15 (5-60) | keep |
| `DESKBOOK_HORIZON_DAYS`, `DESKBOOK_HOLD_MINUTES`, `DESKBOOK_LATE_CHECK_IN_MINUTES` | 14, 90, 30 | keep; admins change them on the rules screen |
| `DESKBOOK_RULES_VERSION` | counter | never set by hand |
| `DESKBOOK_PEOPLE_MAX_DROP_PERCENT` | 10 | keep; raise only for a planned large leaver run |
| `AUDIT_RETENTION_MONTHS` (base) | 84 | per customer policy |

### 3.3 SuccessFactors (Settings > Integrations > SuccessFactors, stored encrypted by the base)

Keys: `BIZX_COMPANY_ID`, `BIZX_API_USER_ID`, `BIZX_BASE_URL`, `BIZX_API_URL`, `BIZX_IDP_CLIENT_ID` (secret), `BIZX_IDP_PRIVATE_KEY` (secret), `SF_CONTENT_LOCALE`, `SUCCESSFACTORS_INTEGRATION_STATUS`. The validator also demands `LMS_BASE_URL`, `LMS_ADMIN_ID`, `LMS_TENANT_ID` and `LMS_OAUTH_SECRET`, although DeskBook has no LMS: the form cannot be saved without them (Q205). The secrets are typed by the customer's admin in the screen; they are never in a file, a ticket or a chat. "Test connection" must end SUCCESS before the people job is allowed to run (`requireSuccessFactorsReadyForSync`).

### 3.4 Mail credentials (location only)

Host, user, password and the From address are not in this repo and not in `application*.properties`: they are the TTCommon base mail settings of the environment (Q177, `SendEmail`; one fixed From address, Q176). The settings are read from a BTP destination named `BlendMailBox` with the properties `mail.smtp.host`, `mail.user`, `mail.password` (section 11.2); the From address is fixed in the TTCommon jar. Nothing about mail goes into `manifest.yml`.

## 4. The 7 DeskBook jobs and how they are entered

Entered on `/jobs` (admin only), per job: Schedule dialog, then Save, then the enable switch. A job with no schedule never runs: the registry carries no schedule and no migration seeds one, so every new environment needs this step. Times are UTC. Job names are the class names (what the screen and the endpoints use).

| # | Job (class) | Schedule | Dialog entry | Needed before |
|---|---|---|---|---|
| 1 | `com.talenteam.deskbook.checkin.job.ReleaseBookingsJob` | every minute | MINUTE, see below | first booking is due |
| 2 | `com.talenteam.deskbook.notification.job.PreReleaseReminderJob` | every minute | MINUTE | mail LIVE |
| 3 | `com.talenteam.deskbook.notification.job.NotificationDispatchJob` | every minute | MINUTE | mail LIVE |
| 4 | `com.talenteam.deskbook.people.job.PeopleSyncJob` | hourly (works once per UTC day after 01:00, retries hourly until it succeeds) | Hourly, every 1 hour (`1:0:0`) | go-live day: run now (section 6) |
| 5 | `com.talenteam.deskbook.notification.job.NotificationPurgeJob` | daily 02:00 | Daily, 02:00 | after go-live week |
| 6 | `com.talenteam.deskbook.booking.job.BookingSlotPurgeJob` | daily 02:30 | Daily, 02:30 | after go-live week |
| 7 | `com.talenteam.deskbook.people.job.SyncRunPurgeJob` | daily 03:00 | Daily, 03:00 | after go-live week |

Problem for 1-3: the schedule dialog of the base offers only Hourly, Daily, Weekly, Monthly (`ScheduleJobDialog.tsx`, `scheduleSchema.ts`); "Every minute" (`MINUTE`) exists in the display code and in the TTCommon types but cannot be chosen. Until the dialog is fixed (Q203), an admin enters the three minute jobs by calling the TTCommon endpoint the dialog uses, as the signed-in admin (browser console on the approuter host, or an admin token): `POST /deskbook/webservices/updateHourlyJobFrequency` with form fields `jobName`, `enabled=true`, `jobSchedulingType=MINUTE`, `JobSchedulingType=MINUTE`, `jobType=RECURRING` (`jobFrequency` may be needed: confirm the accepted value on dev, check C5). Then `POST /deskbook/webservices/updateEnableOrDisableJob` (`jobName`, `isEnable=true`). Check the row on `/jobs`: schedule label "Every minute", next run filled.

Do not schedule: `SampleHeartbeatJob`, `UsersSyncDailyJob`, `UsersSyncFullFetchJob` (they read the same SuccessFactors users again with photos, PB-12, Q196). Base `AuditPartitionMaintenanceJob`: Monthly, day 1, 01:00; without it no new audit partition exists after the 3 created at start.
After 2 failed or missing runs the person on call looks at `/jobs` > Results; there is no mail alert yet (section 7).

## 5. Instances, pool, jobs on two instances (PB-8)

- Pool: 20 per instance x 2 = 40; the PostgreSQL plan limit must be at least 50. Whether the TTCommon data source honours the Spring setting is not visible in this repo; the start-up log (HikariPool line) shows the real value (check C4). Fallback if it does not: a TTCommon property, then ask the developer.
- Heap: 1536M gives about 900 MB of heap with the Java buildpack calculator, against about 400-500 MB at 1024M. This is a start value; T6 (5 exports, heap and thread dump) and T8 (6,500 employees) decide.
- Jobs: all 7 are idempotent by design (status plus version check, unique event keys, claim rows), so both instances may carry the scheduler. Whether TTCommon then runs each minute job twice, or elects one node through `CLUSTER_STATUS` and `allowedNodeRoles`, is not visible here (Q206). If it needs one job node, enable the optional third app `deskbook-jobs` in `manifest.yml` (one instance, no route) and give the two apps different `allowedNodeRoles`. That also removes the pool sharing of PF-18.
- Approuter: one instance of 256M, as in the base. It holds the sign-in sessions in memory; a second instance needs sticky routing, so it stays at one until a load or availability test asks for more.

## 6. First people copy and go-live order

Nobody can book until `ppl_employees` is filled: the hourly job waits for 01:00 UTC, so on go-live day it is started by hand.
Who: a DeskBook admin of the customer (role collection "DeskBook Admin"), with the deploying developer watching the log. How: `/jobs` > PeopleSyncJob > Run now (job type ADHOC, Q168), then Results until SUCCESS. Expected: 1-3 minutes, about 6,500 employees, an `ppl_sync_runs` row with the counts; the number must match `GET .../User/$count?$filter=status eq 't'` of 07-sf-review C2. If the drop guard refuses (`DESKBOOK_PEOPLE_MAX_DROP_PERCENT`) on a first load there is nothing to drop; on a later run read the message before raising it.

Order (the full runbook with rollback is `09-deploy-plan.md`, S9):
1. Services in the space: PostgreSQL, XSUAA (from `approuter/xs-security.json`), destination. TTCommon platform tables (`CONFIGURATION`, `JOB_SCHEDULER`, `JOB_RESULT`, `CLUSTER_STATUS`, `EMAIL*`, ... see `db/README.md`) must exist before the backend starts: they come from the TTCommon DDL, not from Flyway (Q207).
2. Backend: `mvn -pl Backend clean package -DskipTests`, then `cf push` for `deskbook-backend`. Flyway applies V001-V062+ at start-up. Wait for the health check.
3. Frontend into the approuter: `mvn -pl Frontend package` (or `npm run build` in `Frontend`), then copy `Frontend/dist/*` into `approuter/resources/` (no step does this today, Q204). `approuter/resources/*` is git-ignored except `.gitkeep`; never commit it.
4. Approuter: `cf push` for `deskbook-approuter` (the `destinations` env carries `<backend-url>`).
5. BTP cockpit: role collections and IAS group mapping (3.1).
6. Config rows (3.2), then Settings > Integrations > SuccessFactors and Test connection (3.3), mail settings of the TTCommon base (3.4).
7. Jobs 1-7 on `/jobs` (4), then run PeopleSyncJob now.
8. Post-deploy checks P1-P7 below, then open the first office.

Post-deploy checks (a person with an admin login, about 20 minutes): P1 `GET <approuter>/deskbook/api/public/health` answers without sign-in. P2 open `<approuter>/bookings?focus=<any uuid>&action=hold` in a fresh browser: sign-in, then the app (no 404). P3 `/jobs` lists the 7 jobs with a schedule and a next run. P4 PeopleSyncJob SUCCESS with the expected count. P5 one office with one desk, a booking by a test user, check-in works. P6 set `DESKBOOK_MAIL_MODE=LIVE` for a test address only and see one reminder mail arrive with a working link (the link host equals `DESKBOOK_APP_BASE_URL`). P7 a booking with a due release time is released by `ReleaseBookingsJob` within 3 minutes and shows a `RELEASED` audit row.

## 7. Alerts and monitoring

What the base offers today: `GET /deskbook/api/public/health` (public, used by the health check); a request id on every log line (`%5p [%X{requestId}]`); the job results on `/jobs`; Cloud Foundry platform numbers (instance count, CPU, memory, restarts) and the gorouter access log in the BTP cockpit or logging service. Not there: Actuator, Micrometer, request duration in the log, cache statistics (PB-9). Adding any of them is a pom change, and Micrometer is a new dependency: Q67 says yes but needs a D6 card from the solution-architect; I added no dependency and no config for it. Config-only help for test: raise the log level of the Hikari pool logger on the test space (`cf set-env`, not in the manifest) to see pool active/waiting counts every 30 s during T1 and T6.

Alert recipients: not known (Q82 stays open). Needed names before the pilot: (a) who gets "no good people copy for 36 hours" (the banner exists in the app, the mail does not), (b) who looks at FAILED mail rows and a stuck release job, (c) who is paged if the health check fails and the instances restart. Proposal for the customer: one IT mailbox plus BTP Alert Notification on the CF application events (crash, restart) and a weekly look at `/jobs`.

## 8. What this sandbox could not prove (developer checklist, in this order)

| # | Check | Source | Pass when |
|---|---|---|---|
| C1 | Open `<approuter>/bookings?focus=<uuid>&action=hold`, `/book`, `/admin/offices`, reload on `/reports`, signed out and signed in | M3, Q189 | app opens, query string kept after the login redirect, `/assets/*.js` answers 200 with `immutable` |
| C2 | Health and one API call through the approuter: `/deskbook/api/public/health`, `/deskbook/api/v1/today` | 1, 3.1 | 200; proves `<backend-url>` with the context path and the `$1` target without a leading slash (as in the base) |
| C3 | Flyway V001-V062+ on a clean PostgreSQL, and on a copy that already has V004 (demo module) | Q192, db/README | all applied, no error, `disableSchemaValidation: false` start-up passes; V002 audit partitions exist |
| C4 | Start-up log shows pool size 20; second instance starts and serves | PB-8 | HikariPool line, both instances healthy |
| C5 | Jobs 1-3 entered with `MINUTE`: accepted value of `jobFrequency`, next run filled, runs every minute for 10 minutes; whether a run happens twice with 2 instances | 4, 5, Q206 | one run per minute per job in `JOB_RESULT` |
| C6 | PostgreSQL race test: two parallel creates of the same desk and half, two bookings of one person on one day, same Idempotency-Key twice | Q158, Q165 | exactly one wins; the loser gets `DESK_JUST_TAKEN`, `ALREADY_BOOKED_THAT_DAY`, or the replayed answer (Testcontainers needs Docker in CI) |
| C7 | Real SMTP timing: 10 sequential and 10 parallel sends through the base sender, then T5 with that latency, workers 4 and 8 | PB-2, Q176, Q181, T5 | mails/min and seconds/mail recorded; 1,150 reminders done before T-10 |
| C8 | SuccessFactors tenant checks C1-C16 as the API user | 07-sf-review 5 | each "Expected result" met; the sample saved anonymised (Q77) |
| C9 | E2E journeys E1-E10 on the dev stack with a real PostgreSQL | 07-test-plan, Q192 | each step passes; results go into 07-test-report.md |
| C10 | Load tests T1, T3, T4, T5, T6, T8, T11, T12 (and T2, T7, T9 as in 05-performance 5) on the test space | 07-performance 6 | budgets of 07-performance 0; also the first people copy time (T8, AC14.1) and release lag (T4) |
| C11 | Post-deploy P1-P7 (section 6) on the test space, then again on prod | 6 | all pass |
| C12 | Backup and restore of the PostgreSQL plan: take a backup, restore to a scratch instance, run Flyway `info` | role file S5 | restore works; the customer names the retention |

## 9. Open items for the developer

1. Enter the three minute jobs by endpoint until the dialog has "Every minute" (Q203).
2. Copy step for `Frontend/dist` into `approuter/resources` (Q204).
3. SuccessFactors form demands LMS fields (Q205).
4. Node role and double runs on 2 instances (Q206).
5. How config rows and TTCommon tables and mail keys are set on a new environment (Q207).
6. Alert recipients (Q82), mail timing (Q176, Q181), allow-list or anonymised data for LIVE mail on test.

## 10. Scans the user runs before go-live (D10-3)

They need the network, so they were not run in the sandbox. Run them from the product root and put the results in `08-audit.md` (M4a, M12b). No critical CVE may stay open.

- Contract lint, on both copies: `npx @redocly/cli@1.25.0 lint Backend/src/main/resources/openapi/openapi.yaml` and on `work/desk-booking/05-openapi.yaml`
- Frontend packages: `npm audit --omit=dev` in `Frontend` and in `approuter`
- Backend dependencies: `mvn -pl Backend org.owasp:dependency-check-maven:check` (downloads the NVD feed on the first run)

## Config keys listed in DeskBookConfigurationHelper.DESKBOOK_KEYS (pre-audit fix, 29 Oct)

All 12 DESKBOOK_* keys used in the backend are now in the list (ConfigService group `DESKBOOK`). Added in this round, missing from section 3.2 before: `DESKBOOK_PEOPLE_PAGE_SIZE` (50-1,000, default 200; keep) and `DESKBOOK_PEOPLE_FIRST_RUN_UTC` (HH:mm UTC, default 01:00; keep). Also added to the list although they were only in the table: `DESKBOOK_MAIL_MODE`, `DESKBOOK_MAIL_MAX_PER_MINUTE`, `DESKBOOK_MAIL_WORKERS`, `DESKBOOK_PRE_RELEASE_LEAD_MINUTES`, `DESKBOOK_APP_BASE_URL`. Already listed: `DESKBOOK_HORIZON_DAYS`, `DESKBOOK_HOLD_MINUTES`, `DESKBOOK_LATE_CHECK_IN_MINUTES`, `DESKBOOK_RULES_VERSION`, `DESKBOOK_PEOPLE_MAX_DROP_PERCENT`. `DESKBOOK_MAIL_MAX_PER_MINUTE` has no row in 3.2 (default 600; keep).

## 11. New environment: config rows, mail keys, platform tables (B5, Q207)

Answered on 29 Oct from the product code and the TTCommon 2.0.0 jars (class and constant names only; no value of any
`application*.properties` was read or printed). Nothing was run against a live environment, so every answer says what is
proven by code and what the developer must still try on dev.

| | Question | Answer | Status |
|---|---|---|---|
| (a) | How a `DESKBOOK` config row is entered | Nobody seeds it: no migration inserts into `CONFIGURATION` (`db/migration` has no such insert) and there is no DeskBook screen for the mail keys or the base URL. Use the TTCommon endpoint `POST /webservices/storeConfiguration` (admin, flat key/value map) or, as a fallback, SQL on the `CONFIGURATION` table. | CONFIRMED (endpoint, by bytecode); SQL column names NEEDS DEVELOPER CHECK |
| (b) | The TTCommon mail key names | They are not ConfigService keys. Mail comes from a BTP destination named `BlendMailBox`; the properties read are `mail.smtp.host`, `mail.user`, `mail.password`. The From address is a fixed constant in `SendEmail`, not a setting. | CONFIRMED (names, by bytecode); destination content NEEDS DEVELOPER CHECK on dev |
| (c) | Do the TTCommon platform tables exist before the backend starts, and who creates them | Not created by Flyway and not by any script in this repo. The TTCommon jars carry no SQL or DDL file. Whoever starts the backend with DDL execution on (TTCommon's own switch) creates them; otherwise a DBA must. No PostgreSQL DDL for them exists anywhere in the product or the factory. | NEEDS DEVELOPER CHECK |

### 11.1 (a) Entering a DESKBOOK row

Evidence:
- `Backend/src/main/java/com/talenteam/deskbook/notification/service/MailSettings.java` lines 34-39, 60-67, 70-72: reads `configService.getConfigurationMap()` (the whole map, every group) and falls back to a default when the key is missing (`LOG_ONLY`, placeholder URL `https://deskbook.example`, 10 workers). The class comment says "set by deployment; there is no admin screen in the MVP".
- `configuration/service/DeskBookConfigurationHelper.java`: the group `DESKBOOK` is only a read filter (`getIntegrationKeys`). Writing is not filtered by group.
- `TTCommon-Core-2.0.0.jar`, class `com.talenteam.common.controller.ConfigurationRestController`: `/webservices/getConfiguration`, `/webservices/storeConfiguration` (a map, and a multipart variant), `/webservices/importConfiguration`, `/webservices/getValueOfConfigId`, `/admin/saveAdditionalSettings`. The map variant checks `UserSessionBean.getAdminAccess()` or the permission `navConfiguration`, calls `ConfigService.storeConfiguration(userId, map)` and then clears every cache, so a new value is live without a restart.
- `ConfigService.storeConfiguration` writes one `Configuration` row per key (`setConfigID`, `setConfig`, `setCompanyID` from `TenantHelper.getTenantID()`); keys listed by the helper as encrypted are encrypted, the DeskBook mail keys are not (they are non-secret). The product itself writes the three rules keys this way (`BookingRulesService.java:74`).

Steps for the dev team (after the first start, before the first live mail):
1. Sign in to the new environment through the approuter as an admin of the tenant (the request must carry the admin session; there is no anonymous or technical-user route).
2. Send one `POST /webservices/storeConfiguration` through the approuter with the flat map `{"DESKBOOK_APP_BASE_URL": "https://<approuter-host>", "DESKBOOK_MAIL_WORKERS": "8"}`. Leave `DESKBOOK_MAIL_MODE` unset (the default is `LOG_ONLY`) until the mail check in 11.2 passed, then store `{"DESKBOOK_MAIL_MODE": "LIVE"}`.
3. Check with `GET /webservices/getConfiguration` (or `getValueOfConfigId` for one key) that the values are there, and read the log line of the next `NotificationDispatchJob` run (it refuses to send in LIVE mode while the base URL is unset: `NotificationDispatchRunner.java:138`).
4. Fallback if the endpoint cannot be called (no admin session yet): SQL by the DBA on the TTCommon `CONFIGURATION` table, one row per key with the tenant id, key and value. The column names are the entity's and are not visible in this repo: read them from the table of the dev database first (NEEDS DEVELOPER CHECK). Run `ConfigService` cache eviction by restarting one instance, because SQL does not clear the cache.

NEEDS DEVELOPER CHECK on dev: the exact request format of `storeConfiguration` (body or form parameters) and the response `Success`; the jar shows the method signature, not the HTTP binding.

Two inconsistencies found while checking (fixed in 3.2 where it is text; the code one is for the backend developer):
- Section 3.2 said `DESKBOOK_MAIL_WORKERS` defaults to 4. The code default is 10 (`MailSettings.DEFAULT_WORKERS`, range 1-16). Corrected in 3.2.
- `DeskBookConfigurationHelper.DESKBOOK_KEYS` lists only 5 keys (horizon, hold minutes, late check-in minutes, rules version, people max drop percent), but the block below ("All 12 DESKBOOK_* keys ... are now in the list") says 12. `Constants.java` defines 12. Reads through `getConfigurationMap()` are not affected, but a `getConfiguration` call by group name would not return the other seven. Raised to the backend developer in Q207 (below).

### 11.2 (b) Mail key names

Evidence (`TTCommon-Core-2.0.0.jar`, `javap -constants` and `-c`):
- `com.talenteam.common.email.SendEmail`: `sendMail(EmailContentDTO)` (the method `TtCommonMailAdapter.java:55` calls) builds its session from the bean `mailSettings` (a `java.util.Properties`) and reads `mail.smtp.host`, `mail.user`, `mail.password` from it. The From address is `private static final String from = "donotreply@blendlxp.com"`; the method never reads a From value from configuration.
- `com.talenteam.common.btp.configuration.CFDestinationConfiguration` (profile `cloud`): `mailSettings()` reads the destination named `BlendMailBox` through the SAP Cloud SDK `DestinationAccessor`; on failure it logs "Problem Reading Destination".
- `com.talenteam.common.btp.configuration.LocalDestinationConfiguration` (profile `local`): fills the same properties from `EnvConfiguration` (`mail.smtp.auth`, `mail.smtp.host`, `mail.smtp.port`, `mail.smtp.starttls.enable`, `mail.transport.protocol`, `mail.user`, `mail.password`).
- `com.talenteam.common.notification.EmailJob` reads the ConfigService key `NOTIFICATION_FROM_EMAIL_ID` (plus `NOTIFICATION_SEND_PER_DAY`, `NOTIFICATION_EMAIL_SKIP_SEND`): that is the TTCommon e-mail queue job, not the path DeskBook uses, so it does not set the DeskBook From address.

What this changes in the runbook:
- Mail credentials live in a BTP destination, not in a config row and not in `manifest.yml`. Step for the customer BTP admin: create a destination named exactly `BlendMailBox` (Type MAIL) in the destination service instance bound to the backend, with the additional properties `mail.smtp.host`, `mail.user`, `mail.password` (and the port and TLS properties of the customer's mail server). The password is typed in the cockpit only.
- The From address cannot be set per environment. It is `donotreply@blendlxp.com` in the jar. DeskBook mail therefore reaches learners and employees from a Blend address. This is a business point for the product owner (Q176 accepted "one fixed From address", but not that it carries the Blend name); changing it needs a TTCommon release. Raised in Q207.
- The destination must exist before `DESKBOOK_MAIL_MODE` is set to `LIVE`. In `LOG_ONLY` no destination is needed.

NEEDS DEVELOPER CHECK on dev (one test): store `DESKBOOK_MAIL_MODE=LIVE` for a tenant that has one test user, trigger one notification, confirm one mail arrives and that no "Problem Reading Destination" line is in the log. The jar proves which property names are read; it does not prove the destination of the customer carries them.

### 11.3 (c) TTCommon platform tables

Evidence:
- `Backend/src/main/resources/db/README.md`, section "TTCommon platform tables are not created here": the base migrations never create, alter or drop `CONFIGURATION`, `JOB_SCHEDULER`, `JOB_RESULT`, `CLUSTER_STATUS`, `EMAIL*` and the others; "provisioned from the TTCommon DDL before DeskBook runs". `Backend/pom.xml` has `flyway-core` and `flyway-database-postgresql` only; `db/migration` V001 to V063 contain no platform table.
- `application.properties` (key names only): `disableDDLExecution`, `spring.flyway.enabled`, `spring.flyway.locations`, `spring.flyway.baseline-on-migrate`, `spring.flyway.baseline-version`. The comment above them states that TTCommon creates tables only when it is not told to skip DDL (`disableDDLExecution`); the README says the product sets it to skip.
- `TTCommon-*-2.0.0.jar` (all of them): no `.sql`, `.jdbc` or DDL resource. `com.talenteam.common.persistance.DDLDAO` is an empty DAO subclass. `com.talenteam.common.helper.SchemaValidation` only validates `@Column` and `@Table` against the database at start ("Schema Validation - STARTED / FINISHED") and reads `db/fullTextIndex.csv`; it creates nothing.
- Factory search (`base/BASE-SPEC.md` lines 116-117, 365, product tests): the base spec repeats "provisioned from the TTCommon DDL"; no PostgreSQL DDL for these tables exists in the product, the tests (`RepositoryTestConfig` sets `eclipselink.ddl-generation` to `none` and only maps DeskBook entities) or the factory. The Blend repo's `createDDL.jdbc` is generated for SAP HANA, not PostgreSQL.

Conclusion: the tables are created by TTCommon's EclipseLink entities when DDL execution is on, or by a DBA script nobody has written. A new PostgreSQL schema therefore starts with no platform tables unless the dev team decides how they get there. This is the one fact that can stop a first deployment: the backend fails at the first `ConfigService` read, and at start `SchemaValidation` stops the deployment when a mapped table is missing.

Steps for the dev team (decide once, then the runbook uses it for every environment):
1. On the existing dev database, list the platform tables that exist (`\dt` in psql) and compare with the list in `db/README.md`. Say who created them and how (answers "who").
2. If the answer is "the first start with DDL on": on an empty scratch PostgreSQL schema start the backend once with `disableDDLExecution=false` (name from `application.properties`; supply it as a JVM or environment override, never by editing the committed value), let TTCommon create the tables, stop, and export them with `pg_dump --schema-only` limited to the platform table names. Keep that file as `db/platform/ttcommon-2.0.0-postgres.sql` outside `db/migration` (Flyway must not run it) and give it to the DBA.
3. If the answer is "a DBA script exists": add it to the repo under the same path and state its version (TTCommon 2.0.0) in `db/README.md`.
4. Add a check to 09-deploy-plan step 0: `SELECT count(*)` of the platform table names must equal the list before the first backend start (the existing C-check for tables, extended with the script path).
5. After a TTCommon version change repeat step 2 and compare with the stored script; a difference is a new migration for the DBA.

Order on a new environment, with the three answers in place: platform tables (DBA script, 11.3) -> `cf push` backend (Flyway creates the DeskBook tables, V001 to V063) -> destination `BlendMailBox` exists (11.2) -> admin signs in and stores the `DESKBOOK` rows (11.1) -> mail check -> `DESKBOOK_MAIL_MODE=LIVE`.
