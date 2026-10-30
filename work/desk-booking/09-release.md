# 09 Release - DeskBook MVP (release-manager, S9, 2026-10-29)

Inputs read on 29 Oct: `08-audit.md` (re-audit at the top), `09-deploy-plan.md`, `07-test-report.md`, `decisions.md` (D1-D11), `04-backlog.csv`, `status.md`, and the product tree (read-only). Nothing was run. No secret, host or credential value appears here.

## Go / no-go

**Verdict for the dev environment: GO, once B1 is fixed (and B4, B5 are answered). Verdict for production: NO-GO.** G4 (release ready) stays open until the production conditions below are closed. Only the user decides G4.

Check against the files: the expected verdict holds. Three places disagree with each other and need a small fix (none changes the verdict):

| Where | What the file says | What is true (source) | Fix |
|---|---|---|---|
| `09-deploy-plan.md` top and B8 | audit is FAIL with 5 team MUSTs open | audit is PASS WITH CONDITIONS since 29 Oct 10:57; no team FAIL is left (`08-audit.md:5`). M1, M7, M13 team items closed; D1-D4 ratified by D10-1; S2 skip recorded by D11 | devops-engineer cuts B8 to nothing and rewrites the verdict line (audit LATER 28) |
| `07-test-report.md` | backend 749 tests | 748 after the theme fix (15th closed-body case added, open-theme test removed; surefire 10:57, `08-audit.md:17`) | qa-engineer re-issues the count |
| `status.md` G0-G2 | "demo" wording | the user confirmed G0-G2 in D10-1 ("Accept all 3") | lead adds one line to `status.md` |

Also found: D10-3 says the scan commands are in `05-ops.md`, but that file has none; the proposed commands are in `09-deploy-plan.md` B7. The first-audit LATER 25 / B1 item is still open: `approuter/resources` holds no frontend files and `Backend/releases/deskbook.war` does not exist (both are built at deploy time).

### Checklist

| Check | Dev | Production | Evidence |
|---|---|---|---|
| Audit MUSTs all PASS | OK: none FAIL; 2 DEV CONDITIONs (B7, B9) | NOT MET: B7 and B9 open | `08-audit.md:5` |
| Tests green | OK: backend 748 / 0 failures, frontend 215 passing, `tsc -b` clean | OK | surefire 29 Oct 10:57 (72 suites); `07-test-report.md:24` |
| Acceptance criteria | OK: 166 MVP criteria, 150 PASS, 0 FAIL, 16 NOT RUN | NOT MET: the 16 need a real stack (B9) | `07-test-report.md`; 4 criteria moved to R1 by D10-2 |
| Deploy plan and rollback ready | OK (written, not rehearsed) | NOT MET: previous-WAR-on-new-schema test and backup restore not proven (B12) | `09-deploy-plan.md` sections 1 and 4 |
| Config per environment listed | OK (see Steps 7) | NOT MET: B5 (how config rows are entered), B11 (alert names) | `09-deploy-plan.md` |
| Open blockers none | NOT MET: B1 (copy step), B4 (SF form), B5 | NOT MET: 13 of the 14 conditions block go-live | deploy plan section 2 |
| User-facing text complete | OK for English; de, es, fr, en-GB still carry English text (LATER 17) | NOT MET for DE and FR pilots (also B10 Legal) | `08-audit.md` LATER 17 |
| Questions closed or deferred | 69 open, each with an owner, none a blocker | the lead closes or defers all 69 before G4 | `08-audit.md` process checks |

### Dev: what must be true before the push

- B1: copy `Frontend/dist/*` into `approuter/resources/` (a build step, or by hand in the runbook). Without it every route returns 404.
- B4: the SuccessFactors form needs the four LMS fields; the customer admin types harmless values (or the validator is relaxed).
- B5: how a `DESKBOOK` config row is entered, and the TTCommon platform tables exist before the backend starts.
- B3: the three minute jobs are scheduled through the endpoint workaround. B2 (double runs on 2 instances) is proved here by check C5.
- `DESKBOOK_MAIL_MODE=LOG_ONLY` on dev and test (B6). Never `LIVE` on dev.
- Dev is where B9 gets proved (C1, C3, C6, C8, C9, C10); the results go into `07-test-report.md` and `08-audit.md`.

### Production: what must be closed (all in the deploy plan, section 2)

| Item | What | Owner |
|---|---|---|
| B7 | Redocly lint, `npm audit`, OWASP dependency-check run by the user; no critical finding left open | the user runs; developers fix |
| B9 | Dev-stack proofs C1, C3, C6, C8, C9, C10 | qa-engineer, performance-engineer, devops-engineer, developer with sf-consultant |
| B2, B3 | Minute jobs: one run per minute proved; schedule dialog or workaround on every environment | backend-developer, frontend-developer, devops-engineer |
| B6 | `LIVE` mail only after SMTP timing, the 300 a minute confirmation and a base URL | devops-engineer, customer mail admin |
| B10 | Legal and works-council sign-off for DE and FR, erasure runbook | PO, customer Legal |
| B11 | Three named alert recipients | customer operations |
| B12 | Backup and restore proved once; backup before every prod deploy | devops-engineer, customer BTP admin |
| B13 | SF API user role (Q113), small-cell threshold (Q114), pilot desk count (Q193) | PO, customer SF admin |
| B14 | CSRF control: accept in writing or build | the user, security-architect |
| G4 | The user's own go for production | the user |

## What ships

MVP scope: **40 stories, 147 points** (`04-stories.md`, `04-backlog.csv`; D7 moved the Excel export in, D5 and D6 moved Best desk and the two-week strip in). 45 operations. All 40 are built; 150 of 166 criteria pass in tests, 16 wait for the dev stack.

| Epic | Stories shipped |
|---|---|
| Booking (12) | BK-1 Find free desks by office, date and part of day; BK-5 Book a desk; BK-6 Two people, one desk; BK-7 Book for today until the end of the day part; BK-8 Best desk for me; BK-9 My bookings list; BK-10 Cancel my booking; BK-11 Today page; BK-12 After a release: note and rebook; BK-13 Plan my days (several days in one action); BK-14 Change a desk per day; BK-15 Next two weeks strip |
| Check-in (5) | CI-1 Check in by button; CI-4 Release unchecked bookings at the deadline; CI-5 Release job survives downtime and races; CI-6 Late booking: 30-minute check-in; CI-7 Running late: keep my desk once |
| Offices (9) | OS-1 Offices; OS-2 Office states; OS-3 Floors; OS-4 Zones; OS-5 Desks; OS-6 Desk features; OS-7 Office settings (release times, midday, working days); OS-8 Closed days; OS-9 Company booking horizon |
| People (5) | PP-1 Nightly copy of people from SuccessFactors; PP-2 Direct manager and manager status; PP-3 Leavers: future bookings cancelled; PP-4 Profile-not-ready message; PP-5 Roles and access checks |
| Notifications (3) | NT-1 Send an email once, retry, log; NT-2 Reminder 15 minutes before the deadline; NT-3 Email when a booking was released |
| Reports (4) | RP-1 Occupancy per office, floor and day; RP-2 No-show rate; RP-3 Capacity rules; RP-4 Excel export |
| Enablers (2) | EN-1 DeskBook shell (menu, routes, texts); EN-2 Office time and part-of-day rules in one place |

Moved out (not in this release):

| Moved to | Count | Why |
|---|---|---|
| 4 criteria to R1 (D10-2, closes Q200) | BK-8 c6 (reserved desk), RP-3 c3 (reserved desk), RP-3 c1 (blocked desk), BK-10 c2 (booking made by a manager) | they describe R1 features (ST-PP-9, ST-PP-10, ST-OS-10, ST-TM-5) that are not built; MVP scope and points unchanged |
| R1 stories | 34 stories, 125 pts | sized out at G2; see Known issues |
| R2 stories | 6 stories, 26 pts | later phase (busiest days, weekly use, anonymise old data, group booking, German and French texts) |
| Later | 5 stories, 15 pts | not planned (move my booking, leave early, no-show reminder, manager no-show count, excused no-show) |

## Release notes

### For users (employees)

DeskBook is the new way to book a desk. In this release you can:

- **See and book a free desk.** Pick an office, a day and morning, afternoon or the full day. See the free desks and book one. You can book for today until the end of the part of the day.
- **Let DeskBook suggest a desk.** "Best desk for me" proposes a desk with the reason (for example, the one you use most). If nothing fits, it shows up to three other choices.
- **Plan several days at once.** Pick days in a two-week calendar, review the proposed desk for each day, change any desk from a list, then book all of them in one step. If one day fails you see which, and the others stay booked.
- **See your plan.** The Today page shows your booking, your next two weeks and a note if a booking was released. My bookings lists your upcoming bookings; you can cancel one.
- **Keep your desk.** Check in with a button on the day. If you do not check in by the deadline, the desk is released for others and you get an email. About 15 minutes before the deadline you get a reminder. If you are running late, one tap keeps your desk once.
- **If someone books first**, you get a clear "just taken" message and a fresh list.
- It works on a phone and with the keyboard only. Your bookings are private: other employees cannot see them.

### For admins (office admins and DeskBook admins)

- **Roles.** Two roles: "DeskBook User" (employees) and "DeskBook Admin" (office and system admins). A person with neither sees the No access page. Admin screens and admin API calls are closed to users.
- **Offices.** Create an office (name, city, time zone), set it Draft, Open or Closed. A closed office cannot be reopened in this release; create a new one. Add floors (retire when not needed), zones per floor, desks and desk features. A desk with bookings can only be retired, not edited freely.
- **Office settings.** Set release times, midday, working days and closed days per office; a change takes effect from the next day and the previous times are kept for older bookings. Set the company booking horizon.
- **People.** A nightly job copies employees and contingent workers from SuccessFactors (about 6,500 people), with their manager. Leavers lose their future bookings quietly. Nobody can book before the first copy has run. Run it once by hand from the jobs screen after set-up.
- **Reports.** Occupancy per office, floor and day, no-show rate, and an Excel export. Counts only: there is no per-person no-show list. Small groups below a threshold may be hidden once the PO sets it (Q114).
- **Jobs.** Seven DeskBook jobs on the jobs screen: release bookings, pre-release reminder, notification dispatch, the people copy, and others (schedules in `05-ops.md` section 4). The three every-minute jobs need the endpoint workaround until the base schedule dialog is fixed (B3).
- **Mail.** Starts in LOG_ONLY (messages are written to the log, nothing is sent). Switch to LIVE only after the conditions in B6.
- **History.** Changes to offices, desks, bookings and settings are written to the audit history.

## Steps

In order, per environment (dev, then test, then prod). Full commands are in `09-deploy-plan.md` section 1; the user and the dev team run every command, I run none.

| # | Step | Who |
|---|---|---|
| 0 | Space ready: PostgreSQL (at least 50 connections), XSUAA from `approuter/xs-security.json`, destination service; TTCommon platform tables exist; database backup taken | dev team, customer BTP admin |
| 1 | Close the pre-deploy conditions for this environment (dev: B1, B4, B5; prod: all of section 2) | dev team, owners as listed |
| 2 | Build the WAR (`mvn -pl Backend clean package -DskipTests`) | dev team |
| 3 | Database migrations V001-V063 run on the backend start-up (Flyway, forward-only); first on a clean database, once on a copy that has V004 (C3) | dev team |
| 4 | Push `deskbook-backend` (2 instances); wait for the health check | dev team |
| 5 | Build the frontend and copy `Frontend/dist/*` into `approuter/resources/` (never commit the copy) | dev team (B1) |
| 6 | Push `deskbook-approuter` with the backend URL including `/deskbook` | dev team |
| 7 | Config (group `DESKBOOK`): `DESKBOOK_APP_BASE_URL=https://<approuter-host>`, `DESKBOOK_MAIL_WORKERS=8`, `DESKBOOK_MAIL_MODE=LOG_ONLY`; SuccessFactors settings, Test connection to SUCCESS (the secret is typed in the screen only) | dev team, customer SF admin |
| 8 | Role assignment: create role collections "DeskBook User" and "DeskBook Admin"; map the customer IAS group to User; at least 2 named admins | customer BTP admin |
| 9 | Jobs: schedule the 7 DeskBook jobs and the monthly audit partition job; the 3 minute jobs through the workaround (B3); do not schedule the demo and users-sync jobs | DeskBook admin, dev team watching |
| 10 | Data load: run PeopleSyncJob by hand until SUCCESS; count equals the SuccessFactors count | DeskBook admin, dev team |
| 11 | Smoke checks S1-S8 (about 20 minutes, two test users); then open the first office | dev team, PO |
| 12 | Prod only: after S9 and B6, set `DESKBOOK_MAIL_MODE=LIVE`; one real reminder arrives with a working link | dev team, customer mail admin |

Manual steps in the BTP cockpit: create or check the three services, the two role collections, the IAS group mapping, two named admins, alerts on app crash and restart, the backup, the connection limit.

## Known issues

Limits users and admins may notice (R1 and later features are not in this release; LATER items from `08-audit.md`).

| Limit | Seen as |
|---|---|
| **R1 features not in this release** | no filters by floor, zone or feature and no remembered office; the free list does not refresh by itself (reload to see changes); no suggestion of other days or offices when none is free; no scan-the-desk QR check-in and no QR print sheet; no desk blocks, no reserved desks or access lists; admins cannot cancel or move a booking, and cannot import desks from CSV; no people-sync status page, "Run sync now" button or "Add person"; no evening reminder, no email for block or closure; managers have no team week, cannot book for a report and cannot name a delegate; no heat grid in reports; no usual-desk card; no phone slide-over menu; checked-in bookings are not marked Completed at day end |
| R2 and Later | no group booking, no busiest-days view, no old-data anonymising; no "move my booking here", "leave early", no-show reminder, or excused no-show |
| Languages | English only in practice: German, French, Spanish and en-GB show English text for many labels (LATER 17); German and French users need Legal sign-off first (B10) |
| Closed offices | cannot be reopened; create a new one (D6-4) |
| Minute jobs | on a new environment they are set by an endpoint workaround until the base schedule dialog is fixed (Q203) |
| Mail | LOG_ONLY until the switch; at-least-once, so a rare duplicate reminder after a crash is accepted (LATER 26) |
| Rate limits | counted per instance (LATER 8) |
| Report details | past days use today's working days (LATER 13); a same-day settings change can shift today's deadlines; the afternoon end time on the same day and report row rules wait for the PO (Q130, Q161) |
| People copy | no "last updated" line yet (Q80); an alert for "no good copy for 36 hours" does not exist (B11, Q82) |
| Security | no CSRF token; cross-site writes are blocked because every write needs a JSON body, If-Match or Idempotency-Key (B14, LATER 1) |
| Not proven yet | PostgreSQL race, load figures, real SuccessFactors and mail, screen states in a browser, jobs firing on a schedule (B9); the 16 NOT RUN criteria |
| Documents | `05-data-model.md` still labels V063 "planned" (LATER 27); error envelopes differ between the shell and DeskBook (LATER 29) |

## Rollback

From `09-deploy-plan.md` section 4. The application can go back; the database cannot (Flyway is forward-only).

1. **Approuter broke** (blank page, 404): re-push the previous approuter or fix `approuter/resources` (usual cause: B1). Keep the previous approuter and its `resources` copy as a zip.
2. **Backend broke** (health fails, errors after start): re-push the previous WAR (keep the last two) or `cf rollback` if the space supports it. The old WAR runs on the new schema because the new migrations are additive. Prove once on test that the previous WAR starts on the new schema, before the first prod deploy.
3. **Mail misbehaves:** set `DESKBOOK_MAIL_MODE=LOG_ONLY` first (confirm on dev that no restart is needed). **A job misbehaves:** disable it on the jobs screen; no deploy needed.
4. **First deploy:** nothing was live before, so rollback means `cf stop` and telling users the address is closed.
5. **Schema wrong (data loss or corrupt rows):** stop writes (scale the backend to 0), take a backup of the broken state, restore the pre-deploy backup to a scratch instance, compare, and restore into the real instance only after the customer BTP admin agrees. Bookings made after the backup are lost; send the list from the audit history to the PO first. Never edit an applied migration; a fix is V064 or higher.
6. **Per script:** V050 and V061 additive, leave them; V063 index change has no data effect; V060 dropped the demo tables (restore from backup only if ever needed); V062 holds real office-time history once settings change, so prefer leaving the columns.

Rollback risk in one line: the pre-deploy backup (B12) is the only true undo for the schema, so B12 must be proved before prod.

## Next

- Lead: fix the three disagreements in the check table; close or defer the 69 open questions; record the user's confirmation of G0-G2 in `status.md`.
- Dev team: close B1, B4, B5; deploy to dev; run B9 and the smoke checks.
- The user: run the three scans (B7); decide B14; give G4 only when production items above are closed.
