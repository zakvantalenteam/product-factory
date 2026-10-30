# 09-deploy-plan - DeskBook MVP on SAP BTP Cloud Foundry (devops-engineer, S9, 2026-10-29)

Scope: the release runbook for the first deploy of DeskBook (backend `deskbook-backend`, approuter `deskbook-approuter`, PostgreSQL, XSUAA, destination). Nothing here was run: I never run `cf`, deploy or build commands. The user and the dev team run every command below.
Names only: no host, secret or credential value appears in this file. Where a value is needed it is written `<set-in-env>` or a `<placeholder>` from `manifest.yml`.

Verdict for go-live today: NOT READY. The audit (08-audit.md) is FAIL with 5 team MUSTs open, and 14 conditions in section 2 are open. The plan below is what to do once they are closed.

## 1. Order

Files checked: `manifest.yml` (backend 2 instances, 1536M, HTTP health check `/deskbook/api/public/health`, timeout 180 s, pool 20; approuter 1 instance, 256M), `approuter/xs-app.json` (6 routes, SPA fallback last), `approuter/xs-security.json` (scopes Callback, USER, ADMIN; role templates USER, ADMIN), `Backend/src/main/resources/db/migration` (12 scripts: V001, V002, V003, V004, V010, V020, V030, V050, V060, V061, V062, V063).

| Step | What | Who | Done when |
|---|---|---|---|
| 0 | Space ready: PostgreSQL, XSUAA (from `approuter/xs-security.json`), destination service exist. TTCommon platform tables (`CONFIGURATION`, `JOB_SCHEDULER`, `JOB_RESULT`, `CLUSTER_STATUS`, `EMAIL*`) exist; they come from the TTCommon DDL, not Flyway; who creates them on PostgreSQL is still open (05-ops 11.3, Q207 c). The destination `BlendMailBox` must exist before `DESKBOOK_MAIL_MODE=LIVE` (05-ops 11.2). PostgreSQL plan allows at least 50 connections (2 x 20 pool + jobs). A backup of the database is taken (check C12). | dev team, customer BTP admin | services listed in the space; backup id noted |
| 1 | Build the WAR: `mvn -pl Backend clean package -DskipTests`. `Backend/releases/deskbook.war` does not exist today (the manifest path points to it). | dev team | WAR file present |
| 2 | Database: Flyway migrations V001 to V063 run on PostgreSQL. They are applied by the backend at its start-up, in order (the numbering has gaps, which Flyway allows). No separate migration command exists; step 3 is the migration. First run on a clean database, and one run on a copy that already has V004 (the demo tables, dropped by V060): check C3. | dev team | start-up log shows V063 as the last applied version, no error, `disableSchemaValidation: false` start-up passes |
| 3 | Backend: `cf push deskbook-backend` with the placeholders filled (see 3.1 of 05-ops.md). Both instances start; wait for the health check (up to 180 s, Flyway runs here). Start-up log shows pool 20 (C4). | dev team | `cf app deskbook-backend` shows 2/2 running |
| 4 | Frontend into the approuter: build `Frontend` (`npm run build`), then copy `Frontend/dist/*` into `approuter/resources/`. No step does this today (Q204); `Frontend/dist` exists but `approuter/resources` holds only `.gitkeep`. Never commit the copied files. | dev team | `approuter/resources/index.html` and `assets/` exist before the push |
| 5 | Approuter: `cf push deskbook-approuter` (`destinations` env carries `<backend-url>` = `https://<backend-host-and-domain>/deskbook`, with the context path). | dev team | app running; `GET <approuter>/deskbook/api/public/health` answers 200 |
| 6 | BTP cockpit: role collections "DeskBook User" (template USER) and "DeskBook Admin" (template ADMIN); map the customer's IAS group to "DeskBook User"; at least 2 named admins in "DeskBook Admin". | customer BTP admin | a test user of each role can sign in |
| 7 | Config rows (group `DESKBOOK`): `DESKBOOK_APP_BASE_URL=https://<approuter-host>`, `DESKBOOK_MAIL_WORKERS=8`, `DESKBOOK_MAIL_MODE=LOG_ONLY` for now. Settings > Integrations > SuccessFactors, Test connection to SUCCESS; mail settings of the TTCommon base. How a row is entered is open (Q207). | dev team, customer SF admin | Test connection SUCCESS |
| 8 | Jobs on `/jobs` (7 jobs, schedules per 05-ops.md section 4), plus base `AuditPartitionMaintenanceJob` monthly. Do not schedule `SampleHeartbeatJob`, `UsersSyncDailyJob`, `UsersSyncFullFetchJob`. The 3 minute jobs need the endpoint workaround until Q203 is fixed. | DeskBook admin of the customer, dev team watching | each job shows a schedule and a next run |
| 9 | First people copy: `/jobs` > PeopleSyncJob > Run now until SUCCESS (1-3 min, about 6,500 employees). Nobody can book before this. | DeskBook admin, dev team watching | `ppl_sync_runs` row with counts matching the SuccessFactors count |
| 10 | Smoke checks (section 3), then open the first office. | dev team, PO | all S1-S9 pass |
| 11 | Switch `DESKBOOK_MAIL_MODE=LIVE` only after S9 and only after the conditions in section 2 (item 6). | dev team with customer mail admin | one real reminder arrives with a working link |

Environment order: dev, then test (same size as prod: 2 instances, 1536M, same PostgreSQL plan; the load tests T1-T12 run here), then prod. Each environment repeats steps 0-10.

## 2. Before deploy (conditions, each with an owner)

"Blocks" = prod must not go live while it is open. All items are open on 29 Oct 2026.

| # | Condition | Source | Owner | Blocks |
|---|---|---|---|---|
| B1 | Closed 2026-10-29 (D12): `npm run build:approuter` in `Frontend` builds the SPA and copies `Frontend/dist` into `approuter/resources` (`scripts/copy-to-approuter.mjs`); run it before every approuter push. | 06-build-log B1, Q204 | dev team runs it at deploy | no |
| B2 | Q206: with `instances: 2` the 3 minute jobs may run twice each minute (TTCommon scheduler and `allowedNodeRoles` not visible here). Jobs are idempotent by design, so the risk is double work, not wrong data. Prove on dev (check C5: one `JOB_RESULT` row per minute per job). If it needs one job node, enable the optional third app `deskbook-jobs` in `manifest.yml` and set different `allowedNodeRoles`. | 05-ops 5, Q206, audit D-9 | backend-developer, devops-engineer proves with the dev team | yes |
| B3 | Q203: the base schedule dialog cannot set "every minute" (Hourly, Daily, Weekly, Monthly only). Until it is fixed, an admin enters ReleaseBookingsJob, PreReleaseReminderJob and NotificationDispatchJob through `POST /deskbook/webservices/updateHourlyJobFrequency` (`jobSchedulingType=MINUTE`, `jobType=RECURRING`) and `updateEnableOrDisableJob`. Accepted `jobFrequency` value is proven on dev (C5). Without these 3 schedules nothing is released and no mail is sent. | 05-ops 4, Q203, audit D-9 | frontend-developer (dialog); dev team (workaround on every environment) | yes |
| B4 | Closed 2026-10-29 (D12): the SuccessFactors form saves without the 4 LMS fields (validator, dialog hides the LMS card); a save against a live SuccessFactors tenant is still to be shown on dev (B9). | 06-build-log B4, Q205 | - | no |
| B5 | Q207, PARTLY ANSWERED 29 Oct (05-ops 11). (a) config rows: entered by an admin call to `POST /webservices/storeConfiguration` (no seed, no screen); to try on dev. (b) mail: not config keys but the BTP destination `BlendMailBox` with `mail.smtp.host`, `mail.user`, `mail.password`; the From address is fixed in the jar as a Blend address (product owner to accept); one test mail on dev. (c) STILL OPEN: nothing in the repo creates the TTCommon platform tables on PostgreSQL; the developer says who creates them and a DBA script is stored (05-ops 11.3). | 05-ops 3.2, 3.4, 11, Q207 | developer (prove (a), (b) on dev; answer (c)), devops-engineer (runbook done) | yes, until (c) is answered |
| B6 | The `DESKBOOK_MAIL_MODE=LIVE` switch. Default is `LOG_ONLY`. `LIVE` mails the address of every person in the people copy; there is no test-recipient allow-list. Switch to `LIVE` only when: (a) SMTP timing is measured (C7, Q176, Q181) and the customer mail service confirms 300 mails a minute (D6-6); (b) `DESKBOOK_APP_BASE_URL` is set (else reminder links point to a dead address, Q196); (c) the space holds an anonymised copy or test addresses, or it is prod after smoke check S9. On dev and test keep `LOG_ONLY`. | 05-ops 2, audit D-7, Q177 | devops-engineer, integration-engineer; customer mail admin | yes (for LIVE only; LOG_ONLY may deploy) |
| B7 | D10 item 3: the user runs the three scans and the team fixes findings before go-live. Redocly lint on the final `05-openapi.yaml` (audit M4a: not run on the final contract; 05-api-notes.md line 4 records a clean run of `npx @redocly/cli@1.25.0 lint` on an earlier version); `npm audit` in `Frontend` and `Frontend/approuter` (`approuter/package.json`); OWASP dependency-check on `Backend` (needs network and the NVD feed). D10 says the commands are in 05-ops.md, but that file has none; proposed commands for the user to run: `npx @redocly/cli@1.25.0 lint 05-openapi.yaml`, `npm audit --omit=dev` (both package folders), `mvn -pl Backend org.owasp:dependency-check-maven:check`. Results go into `08-audit.md` (M12b). No critical CVE may remain open. | decisions D10-3, audit M4a, M12b, D-5 | the user runs; devops-engineer reads the results; backend and frontend developers fix | yes |
| B8 | Closed 2026-10-29: the re-audit (08-audit.md, top section) is PASS WITH CONDITIONS; all team MUSTs pass (M1 criteria moved to R1 by D10-2, M4/M12a closed bodies incl. the theme body, M7 data model, M13 base operation tests). What remains is B7 and B9. | 08-audit.md re-audit | - | no |
| B9 | Proofs only a real stack can give (nothing ran on PostgreSQL, SuccessFactors or SMTP): C3 Flyway on clean and V004 databases; C6 PostgreSQL race tests (same desk and half, two bookings on one day, same Idempotency-Key, batch); C8 SuccessFactors checks C1-C16 as the API user; C9 end-to-end journeys E1-E10 plus the 8 screen-state criteria; C10 load tests T1, T3-T6, T8, T11, T12 against the budgets, which fix the final memory value; C1 deep links and the query string surviving the sign-in redirect; cookie flags HttpOnly, Secure, SameSite. | 05-ops 8, audit D-1 to D-6 | devops-engineer, qa-engineer, performance-engineer, developer with sf-consultant | yes |
| B10 | Q75: Legal and works-council (Germany) and staff-representative (France) sign-off for DE and FR before the pilot, plus an erasure runbook (booking times show who is in the office). | audit D-10, Q75 | PO with customer Legal and works council | yes for DE and FR users |
| B11 | Q82: alert recipients. Three names are needed: (a) who gets "no good people copy for 36 hours", (b) who reads FAILED mail rows and a stuck release job, (c) who is paged when the health check fails or instances restart. Proposal: one customer IT mailbox plus BTP Alert Notification on CF application crash and restart events, and a weekly look at `/jobs`. No mail alert exists in the product yet. | audit D-11, Q82, 05-ops 7 | customer operations (the dev team collects the names) | yes (named before the pilot) |
| B12 | Backup and restore of the PostgreSQL plan proven once on a scratch instance, and a backup taken before every prod deploy. This is the only real undo for migrations (section 4). | 05-ops C12 | devops-engineer, customer BTP admin | yes |
| B13 | Smaller PO answers: SuccessFactors API user role and population (Q113, Q110-Q112, Q169), small-cell threshold for the occupancy report and export (Q114), pilot desk count (Q193). | audit D-8, D-12 | PO, customer SF admin | Q113 yes, others before pilot |
| B14 | CSRF control (Q68, audit LATER 1): `csrfProtection` is false on `^/deskbook/(.*)$` and no CSRF token is sent. Writes need a JSON body, If-Match or Idempotency-Key so a cross-site call is blocked by preflight. Accept this in writing or build the control. Also the unused webhook route stays in `xs-app.json`. | audit LATER 1 | security-architect, the user | decision before prod |

Open count: 11 conditions (B1, B4, B8 closed; B5 partly answered: platform tables on PostgreSQL need the developer). Nothing left that the team can close in code. Items only the dev team or customer can close: the rest.

## 3. Smoke checks after deploy

Run on each environment after steps 1-9 of section 1: a person with the dev team watching, about 20 minutes. Use two test users: one with the USER role template (collection "DeskBook User"), one with ADMIN ("DeskBook Admin"). Use a fresh browser profile for S2 and S3.

| # | Check | Pass when |
|---|---|---|
| S1 | Health: `GET <approuter>/deskbook/api/public/health`, without sign-in | 200. Proves `<backend-url>` includes the `/deskbook` context path and the public route works. Also `cf app deskbook-backend` shows 2/2 instances healthy and the log shows pool 20 |
| S2 | Sign-in as USER: open `<approuter>/`, sign in, land on the Today page. Open an admin address (`/admin/offices`) and `/jobs` | the app opens (no 404); admin screens show the forbidden page and the admin API answers 403; USER sees only own bookings |
| S3 | Sign-in as ADMIN: same start. Open `/admin/offices`, `/reports`, `/jobs` | all open; `/jobs` lists the 7 jobs, each with a schedule and next run |
| S4 | Book and cancel as USER: pick an office with one desk, book a desk for a later day, see it under My bookings, cancel it, see it gone and the desk free again. Repeat the same book twice quickly | one booking is created; the second answers with the stable code (`DESK_JUST_TAKEN` or `ALREADY_BOOKED_THAT_DAY`); cancel frees the desk; the audit history shows both actions |
| S5 | Deep link through the approuter, signed out in a fresh browser: open `<approuter>/bookings?focus=<any uuid>&action=hold`, then `/book`, then reload on `/reports` as ADMIN | sign-in appears, then the same address opens inside the app with the query string kept; `/assets/*.js` answers 200 with `immutable`; a missing file (for example `/assets/none.js`) is a real 404 |
| S6 | People copy: PeopleSyncJob result | SUCCESS, count equals the SuccessFactors active-user count, `ppl_sync_runs` row present |
| S7 | Job run: ReleaseBookingsJob with a booking whose release time is due (a test booking in a test office), then watch `/jobs` > Results for 3 minutes | the job runs once per minute (twice per minute would be B2), status SUCCESS, the booking becomes RELEASED with an audit row. Also read one request id in a log line of S4 |
| S8 | Mail in LOG_ONLY: `DESKBOOK_MAIL_MODE=LOG_ONLY` is set; trigger one reminder (a booking inside the pre-release lead of 15 minutes) | NotificationDispatchJob logs the message as logged-only and the notification row ends SENT or the LOG_ONLY equivalent; no mail leaves the system; no message text or address is stored or logged |
| S9 | LIVE test, only after B6 is met: set `LIVE` for a test address only | one reminder arrives; the link host equals `DESKBOOK_APP_BASE_URL`; the link opens the app after sign-in. Set back to `LOG_ONLY` if anything fails |

If any of S1-S8 fails on prod, stop and use section 4.

## 4. Rollback

Rule: the application can go back; the database cannot go back by Flyway. Flyway in this product is forward-only (no undo scripts exist; the base V001-V003 have no rollback note either). Every DeskBook script V010-V063 has a rollback note, but those notes are manual SQL, not a command.

### 4.1 App rollback (any time, fast)

1. Approuter only broke (blank page, 404 on routes): re-push the previous approuter, or fix `approuter/resources` (the usual cause is B1). The backend is untouched. Needs the previous approuter and `resources` copy kept as a zip.
2. Backend broke (health fails, errors after start): the dev team re-pushes the previous WAR (keep the last two WAR files and their versions). Use `cf push` with the previous WAR or `cf rollback` if the space supports revisions. The old WAR runs on the new schema as long as the new migrations were additive (see 4.2).
3. Config: `DESKBOOK_MAIL_MODE=LOG_ONLY` is the fast stop for mail; set it first if mails misbehave (no restart needed if the row is read each run; confirm on dev). Job trouble: disable the job on `/jobs` (enable switch), no deploy needed.
4. The first-deploy case: nothing was live before, so "rollback" means stop the apps (`cf stop`) and tell users the address is closed. No user data exists before the first people copy and first bookings.
5. Test whether the previous WAR starts against the new schema once on test (Flyway tolerance of applied migrations newer than the WAR is the default in current versions, but it is not proven here). Do this before the first prod deploy.

### 4.2 Forward-only migrations: what each does on rollback

| Script | What it did | After an app rollback | If you must undo it |
|---|---|---|---|
| V010, V020, V030 | create office, people, booking tables | old code needs them; leave | not undone. Before go-live: drop the product tables on a scratch or dev database and run again. After go-live: restore the backup |
| V050 | adds `leaver_handled_at` (people) | additive; old code ignores it | leave it |
| V060 | drops the demo tables `projects` and `tasks` (demo data only; audit rows of type PROJECT and TASK stay) | not reversible: the data in those two tables is gone. V004 can recreate empty tables, no rows | restore from the backup taken in step 0 if the demo data were ever needed (they are not product data). Never edit V004 |
| V061 | notification outbox tables | old code ignores them; mail rows already written stay | before go-live drop the tables; after go-live additive changes only (note in the script) |
| V062 | adds four nullable `prev_*` times and a check to `office` | additive, but this is a data change in use: once an admin changes office settings, the previous times are stored there. A rollback to a WAR without V062 code ignores them, so dates before `settings_effective_from` are judged with the current times and a same-day settings change can move today's deadlines | script note: drop the four columns and the check. Only do this together with the old WAR, and tell the PO that earlier office times are lost. Prefer leaving the columns |
| V063 | three booking indexes made partial | no data effect; code works with or without | note: drop the three indexes and create them again as in V030 (without the WHERE clause) |

### 4.3 When the schema itself is wrong (data loss or corrupt rows)

1. Stop writes: set the backend to 0 instances (`cf scale`), or stop the approuter, so no booking is made while you decide.
2. Take a fresh backup of the broken state (for diagnosis).
3. Restore the backup from step 0 to a scratch instance, run Flyway `info` on it, compare. Only after the customer BTP admin agrees, restore into the real instance, re-push the previous WAR, and re-run section 3. Bookings made after the backup are lost: send the list from the audit history to the PO first.
4. Record the incident in `status.md`; do not hand-edit an applied migration. A fix is a new script V064 or higher.

## 5. Who does what

The user and the dev team run every `cf`, `mvn`, `npm`, deploy, scan and database command in this file. I (devops-engineer) never run them and never deploy, push or start servers; I only plan, check the deploy files and write this plan.

| Who | Does |
|---|---|
| The user | Runs Redocly lint, `npm audit` and OWASP dependency-check (D10-3); ratifies D1-D4; decides B14; gives the go for each environment; confirms alert recipients and DE/FR sign-off came in |
| Dev team (developer) | All `cf push`, `cf scale`, build and copy commands; Flyway runs through the backend start-up; fills the `<placeholders>`; enters config rows and the minute-job schedules; keeps the last two WARs; runs the checks C1-C10 and smoke checks S1-S9; fixes scan findings |
| Customer BTP admin | Creates services and role collections, maps the IAS group, takes and restores PostgreSQL backups, approves a restore |
| DeskBook admin of the customer | Types the SuccessFactors integration (secrets only in the screen), schedules and runs jobs on `/jobs`, runs the first people copy |
| Customer mail admin | Confirms the mail service can take 300 mails a minute, gives the sender settings, agrees the switch to `LIVE` |
| Customer operations | Names the alert recipients (B11) |
| PO with customer Legal | DE and FR sign-off and erasure runbook (B10); Q113, Q114, Q193 answers |
| Specialists (agents) | backend-developer: B2, B8; frontend-developer: B3; base-builder: B1; integration-engineer: B4; qa-engineer: B8, B9; performance-engineer: C10; devops-engineer: this plan, reads scan results, answers Q207 once given the facts |

Manual steps in the BTP cockpit (the list asked for by the role): create or check the PostgreSQL, XSUAA and destination instances; create the two role collections and map the IAS group; add two named admins; set up BTP Alert Notification on CF application crash and restart (proposal); take the database backup; confirm the PostgreSQL plan allows 50 connections.

Rollback risk in one line: the database has no undo; V060 (demo tables) cannot be restored without the backup, and V062 holds real office-time history once settings change, so the pre-deploy backup (B12) is the only true rollback for the schema.
