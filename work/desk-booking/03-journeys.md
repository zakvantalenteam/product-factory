# Journeys and screens - DeskBook

Stage S3, journey mode, 2026-10-28. Built from `02-spec.md` (F1-F17, J1-J6), `decisions.md` (D1) and the base shell (BASE-SPEC B2, B7).
Problems found are in `questions.md` (Q100 onward) and marked `(see Q<n>)` below. Where a screen depends on an open gap, the journey follows the recommended answer.

## Roles and what each one is for
| Role | Main job | Device | Screens used |
|---|---|---|---|
| Employee | Get a desk for a day, turn up, be checked in | phone (check-in, QR), desktop (planning) | S1-S6 |
| Manager | Employee + see the team week, book for the team | desktop mostly, phone to look | S1-S6 + S7-S9 |
| Facilities admin | Keep offices and desks right, read usage | desktop | S1-S6 + S10-S18 |

A manager and an admin are also employees (A9), so they get the employee screens too.

## Journeys per role

### Employee
**E1 Book a desk for a coming day** (weekly, 3-5 times a week for some people)
1. S1 Today -> presses "Book a desk" -> S2 opens with her home office, next working day, full day already chosen.
2. S2: changes office or date or part of the day if needed; optionally filters floor, zone, feature.
3. S2: list of free desks and the count -> picks one -> presses Book.
4. S3 confirmation: desk, office, date, part of day, release time, how to check in. Done in 3 taps after S2 opens.
Stuck: no free desk (offers other days or offices, AC4.3); desk "just taken" (list refreshes with a message, AC5.3); already has a desk that day (link to it, AC5.2); today is past the cut-off (date not selectable, reason shown, AC4.7); profile not ready for a new hire (AC5.8).

**E2 Check in on the day** (daily, the most frequent journey)
1. Phone: scans the QR on the desk -> signs in if needed -> S5 Desk page.
2. S5 shows "Checked in at BLR-3-14" (automatic when it is her own desk and the window is open).
Alternative without QR: S1 Today -> "Check in" button on today's booking.
Stuck: session expired on the phone (sign-in step on top of a scan, see Q101); wrong desk scanned (S5 says "This is not your desk", offers "Move my booking here" only if free, AC7.4); too early or after release (opening time shown, AC7.6); afternoon booking before 12:00 (button disabled with the reason, AC7.8).

**E3 Cancel or release a desk** (weekly)
1. S4 My bookings -> the booking row -> Cancel -> confirm -> row shows Cancelled.
2. After check-in the same row shows "Release desk" (leaving early) instead.
Stuck: booking already released by the system (row shows the real status, AC6.6).

**E4 Arrive after the release** (rare, but the most stressful)
1. Opens the app at 10:05 -> S1 Today shows a one-line note "Your desk was released at 10:00" and the free desks (AC8.7).
2. Wants to book again: only the part of the day whose cut-off has not passed can be booked (see Q36). She picks a desk in S2.
Stuck: she cannot tell why morning is not offered; the note must say what is still possible.

**E5 Book at a different office on a trip** (monthly)
1. S2 -> changes the office picker to another office -> same steps as E1.
Stuck: none beyond E1; the picker lists open offices only (G19).

### Manager
**M1 See the team week** (weekly)
1. Sidebar Team -> S7 shows this week, one row per direct report, one cell per working day (office, desk code, part of day, status).
2. Moves to next week with arrows; filters by office.
3. Reads a report's no-show count of the last 30 days in the row.
Stuck: nobody booked (empty cells, not "absent"); more than 20 people on a phone (see Q100); no direct reports (page says so; but the menu entry is hidden, see Q102).

**M2 Book a desk for one report** (weekly)
1. S7 -> empty cell of Ravi on Tuesday -> "Book a desk" -> S8 dialog (S2's picker, date and person already filled).
2. Picks a desk -> Book -> the cell shows the booking; Ravi is emailed.
Stuck: Ravi already has a desk (refused with his name only in the manager's own message, AC10.2); "just taken".

**M3 Arrange a team day** (weekly, the J3 of the spec)
1. S7 -> sees three empty cells on Wednesday -> selects the three people (checkboxes in the column header or rows) -> "Group booking".
2. S9: date and office carried over; picks zone; screen shows free desks in the zone against the number of people; skipped people (already booked) listed.
3. Confirms -> all or nobody is booked; each person is emailed; result list per person.
Stuck: zone too small (shows zones that fit or the largest free number, AC11.2); somebody takes a desk while confirming (re-picked or nobody booked, AC11.4); more than 20 people.

**M4 Cancel a report's booking** (rare)
1. S7 -> booking cell -> Cancel -> confirm -> report emailed, cell shows "Cancelled by manager".
Stuck: report already checked in (Cancel not offered, AC10.6).

### Facilities admin
**A1 Set up a new office** (once per office, 4 now, 8 within a year; the J4 of the spec)
1. S10 Offices -> "New office" -> name, city, timezone (list) -> Save; release times, midday and working days start at defaults.
2. S11 Office detail, tab Calendar: adds closed days.
3. Tab Floors: adds floors. Tab Desks: adds desks (zone, features, accessibility flag) one by one or imports a CSV (S13); errors listed per line.
4. S15 print QR codes for the desks (screen missing in spec, see Q103).
5. Opens the office to booking (state change, see Q104).
Stuck: about 1,500 desks one by one (CSV); typing a zone slightly differently splits one zone into two (see Q105); an office is visible to employees before it is ready (see Q104).

**A2 Block a desk for maintenance** (weekly)
1. S11 Desks -> a desk -> Block -> dates -> Save.
2. The dialog says "2 bookings will be cancelled" with no names (Q4) -> Confirm.
3. People are emailed; the desk leaves the free list.
Stuck: past dates (refused); somebody else blocked the same desk (existing block shown, AC2.11).

**A3 Review usage and export** (weekly or monthly)
1. S17 Reports -> picks office and date range -> sees capacity, booked, checked-in, no-show rate per floor and day; busiest days.
2. Export -> Excel with the same rows.
Stuck: more than 100,000 rows ("Narrow the dates or office"); empty range (export disabled).

**A4 Keep the accessibility list** (monthly)
1. S16 Access list -> add or remove a person (search by name) -> Save.
Stuck: the page must not offer a reason field (AC16.4); removal keeps existing bookings (AC16.3).

**A5 Check people sync** (when a manager reports a wrong team)
1. S18 People sync -> sees last good copy date, counts of new/changed/left, skipped records without email.
Stuck: warning banner after 2 days without a good copy.

## Screen inventory
States column: E empty, L loading, X error, P no permission, M many rows, T long text. All screens also have the base's session-expired and error-boundary screens (B2.6, B2.16).

| # | Screen (route) | Job | Who | Data shown | Actions | States | Entry points |
|---|---|---|---|---|---|---|---|
| S1 | Today `/dashboard` (replaces the base dashboard cards) | Show what matters now: today's and next bookings, check-in, release note | all | own next 3 bookings, release time, free-desk count for her home office tomorrow | Check in, Book a desk, Cancel | E "No bookings yet" + Book button; L skeleton; X retry; released note (AC8.7); profile-not-ready (AC5.8); no role "No access" (AC17.2) | Sidebar "Today"; `/` redirect; login |
| S2 | Book a desk `/book` | Find and book a free desk | all | office, date, part-of-day pickers; filters floor, zone, feature; free desks (code, floor, zone, features); count; "Showing data from N s ago" | Change filters, Book | E "No free desks..." + other days/offices (AC4.3); "No offices open yet" (AC1.7); L; X stale banner (AC4.5); M 500 desks scroll (AC4.10); date greyed with reason (closed, weekend, past cut-off); T long zone name wraps | Sidebar; S1; S4 empty state; S7 (carried filters) |
| S3 | Booking confirmation (dialog or panel on S2) | Confirm what was booked | all | desk, office, date, part, release time, check-in hint | Done, View my bookings, Add to calendar (later, not in scope) | "Just taken" variant (AC5.3); "Desk no longer available" (AC5.5); "You already have a desk" (AC5.2) | S2 Book |
| S4 | My bookings `/bookings` | See upcoming and last 30 days, cancel or release | all | date, office, desk, part, status, "Booked by <manager>" | Cancel, Release desk, Check in | E "No bookings yet" + Book a desk (AC6.3); L; X; M (30 days) fine; status changes by system shown (AC6.6) | Sidebar; S1; S3; reminder email link |
| S5 | Desk page `/desk/<code>` (QR landing) | Check in at a desk, or fix a wrong desk | all | desk code, office, floor, own booking state | Check in (automatic when own desk), Move my booking here, Book this desk | Not signed in -> sign-in and back (AC7.3); wrong desk (AC7.4); no booking + free (AC7.5); outside window (AC7.6, AC7.8); already checked in (AC7.7); unknown or retired desk code; blocked desk | QR scan only; S1/S4 button reuses the same action |
| S6 | Access states: No access, Profile not ready, Office closed | Explain why the user cannot continue | all | one message and one next step | Sign in again, go to Today | per message | Any route |
| S7 | Team week `/team` | See direct reports' week; entry to book for or group-book | manager | row per direct report; per working day: office, desk, part, status; no-show count last 30 days; last people-update date | Week arrows, office filter, Book for (cell), Cancel (cell), select people -> Group booking | E "No direct reports found" + last update date (AC9.4); L; X; M 40 rows under 2 s (AC9.8); P refused for non-managers (AC9.5); phone layout needs a different form (Q100); other-office cell shows office name (AC9.9) | Sidebar Team (managers only) |
| S8 | Book for a report (dialog on S7) | Book one desk for one person | manager | person, date, S2 picker | Book | refused: not a direct report, already has a desk, past cut-off, just taken (AC10.2-10.4) | S7 cell |
| S9 | Group booking `/team/group` | Book desks in one zone for up to 20 reports | manager | date, office, zone with free count, selected people, skipped people | Pick zone, Confirm, Cancel | too few desks (AC11.2); skipped list (AC11.3); over 20 (AC11.5); result list per person; P tampered person refused as a whole (AC11.6) | S7 selection |
| S10 | Offices `/admin/offices` | List and create offices | admin | name, city, timezone, floors, desks, open/closed state | New office, Open, Close | E "Create the first office" (AC1.7); L; X; P refused (AC1.5); duplicate name error (AC1.3) | Sidebar Facilities > Offices and desks |
| S11 | Office detail `/admin/offices/<id>` with tabs Settings, Calendar, Floors, Desks, Blocks | Edit one office completely | admin | settings (timezone, release times, midday, working days); closed days; floors; desks table; blocks | Edit, Retire floor, Close office, Add closed day, Add or edit desk, Block, Remove block | validation messages (AC1.2, AC3.2, AC3.7); stale-save dialog (AC1.6); "N bookings will be cancelled" confirm (AC2.6, AC3.5); E per tab; M 1,500 desks (paged, search); code read-only once booked (AC2.3) | S10 row |
| S12 | Desk dialog (on S11 Desks) | Create and edit one desk | admin | code, floor, zone, features, accessibility flag | Save, Retire | code used (AC2.2); zone default Main (AC2.4); flag change recorded (R55) | S11 |
| S13 | Desk CSV import (dialog on S11 Desks) | Create many desks | admin | file picker, preview with valid and invalid rows by line | Import valid rows | invalid rows list (AC2.10); empty file; wrong columns; large file progress | S11 |
| S14 | Block dialog (on S11 Desks and Blocks) | Block a desk for dates | admin | desk, from, to, reason, number of affected bookings | Save, Confirm cancel | past date refused (AC2.7); existing block shown (AC2.11) | S11 |
| S15 | QR print sheet `/admin/offices/<id>/qr` | Print the code for each desk | admin | desk code and QR, per floor, print layout | Print, choose floor | not in spec, see Q103; E no desks | S11 Desks |
| S16 | Access list `/admin/access` | Keep who may book reserved desks | admin | names on list, reserved desks per office | Add person, remove person | E "No one on the list"; no reason field (AC16.4); P refused (AC16.5) | Sidebar Facilities |
| S17 | Reports `/reports` | Read usage, export | admin | office, range; capacity, booked, checked-in, no-show rate per floor and day; busiest 5 days; counts only | Pick filters, Export | E "No bookings in this period" export disabled (AC12.7); over 100,000 rows (AC12.9); L under 5 s (AC12.12); P refused (AC12.10) | Sidebar Facilities |
| S18 | People sync (new tab in Settings) | See the SuccessFactors copy status | admin | last good copy, last run result, counts new/changed/left, skipped records, warning after 2 days | Retry now (not in spec, see Q106) | failed run; warning banner (AC14.3); E "No sync yet" | Settings tab; warning banner on S1 for admin |
| S19 | Booking rules (new tab in Settings) | Set the company-wide booking horizon | admin | days ahead (14) | Save | validation (whole number, minimum 1) | Settings tab |

Reused from the base without change: Background Jobs, Settings > General/Integrations/Theme, history panels (B6, change history of offices, desks, access list), login, toast, error screens.

## Navigation (base sidebar, B2.25; product adds its own items)
The base lists Overview/Workspace/Admin; DeskBook replaces the example items (Projects) with its own. Proposed sidebar:

| Section | Item | Route | Visible to |
|---|---|---|---|
| Overview | Today | `/dashboard` | all |
| Workspace | Book a desk | `/book` | all |
| Workspace | My bookings | `/bookings` | all |
| Workspace | Team | `/team` | managers (has an active direct report, R52) |
| Facilities | Offices and desks | `/admin/offices` | admin |
| Facilities | Access list | `/admin/access` | admin |
| Facilities | Reports | `/reports` | admin |
| Admin | Background Jobs | `/jobs` | admin (base) |
| Admin | Settings (tabs General, Integrations, Theme, Booking rules, People sync) | `/settings` | admin (base) |

Top bar: base sidebar toggle and user menu only; no notification icon (B2.26), so release notes appear on S1 and by email.
Entry without the sidebar: S5 (QR) and the email links. On phones (360 px) the base shell keeps a 72 px icon rail, which leaves 288 px for content (see Q107).
S2, S4 and S1 are the three screens employees use on a phone; S7 is the one that is hard on a phone.

## Overall check
- Employee journeys are short (E1 three taps, E2 one scan). Admin set-up A1 is the longest (5 steps over 4 tabs, once per office) and acceptable.
- Screens carried only by a dialog (S3, S8, S12-S14) must work with the keyboard and at 360 px.
- Everything in the spec has a screen except QR printing (S15, Q103), "open the office" (Q104) and the manager's zero-team view (Q102).
