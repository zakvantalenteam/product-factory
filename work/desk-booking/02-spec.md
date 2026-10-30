# Spec - DeskBook

Status: first version (S2), 2026-10-28. Built from `00-prd.md` v0.3, `01-prd-review.md`, intake questions 1-5 and Q1-Q11 (all accepted, decision D1).
Open gaps are named `(G<n>)`; each carries the recommended answer in `02-gaps.md`, and the spec follows it until the owner decides.
Anything taken from the base product is an assumption (`A1-A8`): `base/BASE-SPEC.md` is not written yet.

## Goal
Employees book a desk before they come in and always find one; unused bookings are released so others can use them.
Facilities gets real usage per office and floor; managers see where their direct reports sit on which day.

## Roles
| Role | What they do | Must not see or do |
|---|---|---|
| Employee | Finds free desks, books, cancels, checks in, sees own bookings, books in any office (G19) | Anyone else's bookings or names on desks (Q4, G1); any setup or report page |
| Manager (an employee who has direct reports, taken from SuccessFactors, G7) | Everything an employee does, plus sees direct reports' bookings (never their no-shows, D2, Q89), books, cancels and group-books for direct reports | People who are not direct reports; names in reports; setup pages |
| Facilities admin | Sets up offices, floors, zones, desks, blocks, office settings and the accessibility list; sees reports (counts only) and sync status; exports | Who sits where by name (reports show counts, Q4); booking for others; HR data |
| System (background jobs) | Releases unchecked bookings, sends reminders, syncs people, anonymises old data | - |

A manager and an admin are also employees and can book for themselves (A9).

## Modules
- M1 Office setup - offices, floors, zones, desks, blocking, office settings, bulk desk import.
- M2 Booking - find, book, my bookings, cancel.
- M3 Check-in and release - button, QR, automatic release, no-show follow-up.
- M4 Team - team week view, booking for a team member, group booking.
- M5 Reports - occupancy, no-show rate, busiest days, Excel export.
- M6 Notifications - email messages.
- M7 People - nightly SuccessFactors copy, manager derivation, leavers.
- M8 Access - sign-in, roles, reserved (accessibility) desks.

## Features

### F1 Offices and floors (M1)
Admin creates offices (name, city, timezone) and floors per office.
Roles: admin. Data: Office, Floor.
- R1 Office name is unique (ignoring upper/lower case). Floor name is unique within its office.
- R2 An office or floor that has bookings is never deleted, only closed or retired. A closed office or retired floor is hidden from booking.
- R3 Closing an office or retiring a floor with future bookings cancels them under the blocking rule (G3).
- AC1.1 Given an admin, when she saves a new office with name, city and timezone, then it appears in the office list and in the office picker of the booking page.
- AC1.2 Given a missing name, city or timezone, when she saves, then each missing field shows a message and nothing is saved.
- AC1.3 Given an office named "Pune", when she creates another named "pune", then it is refused with "name already used".
- AC1.4 Given an office with bookings, when she tries to delete it, then it is refused and "Close office" is offered; closing hides it from booking (G3 for existing future bookings).
- AC1.5 Given an employee or manager, when she opens office setup by menu or by direct link, then the menu entry is absent and the link is refused.
- AC1.6 Given two admins editing the same office, when the second saves after the first, then she sees "changed by someone else, reload" and the first save is not overwritten.
- AC1.7 Given no office exists, when an employee opens booking, then she sees "No offices are open for booking yet"; the admin sees "Create the first office".
- AC1.8 Given a floor name already used in that office, when saving, then it is refused.
- AC1.9 Given a floor with desks, when the admin retires it, then its desks are hidden from booking and future bookings follow the blocking rule (G3).

### F2 Desks, zones and blocking (M1)
Admin creates desks: code (for example "BLR-3-14"), floor, zone name, features (monitor, docking station, standing desk, other features the admin adds), reserved-for-accessibility flag (F16). Admin blocks a desk for maintenance for a date range.
Roles: admin. Data: Desk, Zone, Feature, Block.
- R4 Desk code is unique across all offices and is never changed once the desk has a booking (it is printed on the QR code).
- R5 Every desk has a zone name (default "Main"); group booking uses the zone (Q8).
- R6 A blocked desk is not offered for booking and does not count in capacity (G10).
- R7 Blocking dates that already hold bookings cancels those bookings and tells the people (G3).
- R8 A block may start today or later; a past date is refused.
- AC2.1 Given an admin, when she creates a desk with code, floor, zone and two features, then it is listed on that floor and bookable from tomorrow's list on.
- AC2.2 Given a code already used anywhere, when she saves, then it is refused with "code already used".
- AC2.3 Given a desk with bookings, when she edits its code, then the field is read-only.
- AC2.4 Given a desk with no zone entered, when she saves, then zone "Main" is stored.
- AC2.5 Given a block from 3 to 5 Nov with no bookings, when saved, then the desk is missing from the free list for those days.
- AC2.6 Given a block whose dates contain 2 bookings, when saved, then the admin first sees "2 bookings will be cancelled", must confirm, and on confirm the bookings are cancelled and both people are emailed (G3).
- AC2.7 Given a block with a past start date, when saved, then it is refused.
- AC2.8 Given a block, when the admin removes it, then the desk is bookable again for the freed days; cancelled bookings are not restored.
- AC2.9 Given a desk is retired, when an employee searches, then it is not listed; its history stays in reports.
- AC2.10 Given a CSV file of desks (code, floor, zone, features), when the admin imports it, then valid rows are created and invalid rows are listed with line number and reason, and nothing is half-saved per row (G24).
- AC2.11 Given two admins blocking the same desk and dates, when the second saves, then she sees the existing block instead of a second one.

### F3 Office settings and calendar (M1)
Per office: timezone, morning release time (default 10:00), afternoon release time (default 14:00), midday split between morning and afternoon (default 13:00, A10), working days (default Monday-Friday), closed days (public holidays and other days the office is shut). Company-wide: how many days ahead one can book (default 14, G6); how long Running late keeps the desk (default 90 minutes after the release time, both parts, Q49); how long a late booking has to check in (30 minutes, D2 P1).
Roles: admin. Data: Office settings, Closed day.
- R9 Times are in the office's own timezone (intake Q1, Q3).
- R10 A change of release time or midday split applies from the next day on; today's bookings keep the old time.
- R11 Afternoon release time must be later than the morning release time and not earlier than the midday split.
- R12 Closed days and non-working days cannot be booked.
- AC3.1 Given a new office, when created, then it has release times 10:00 and 14:00, midday 13:00 and working days Monday-Friday.
- AC3.2 Given an afternoon release time of 09:00 with a morning release of 10:00, when saved, then it is refused with an explanation.
- AC3.3 Given the morning release time is changed at 09:30 to 09:45, when saved, then today's release still happens at the old time and tomorrow's at 09:45.
- AC3.4 Given 26 Jan is a closed day, when an employee picks that date, then it is greyed out with "Office closed".
- AC3.5 Given a closed day is added on a date with bookings, when saved, then the blocking rule applies (G3).
- AC3.6 Given Pune is in Asia/Kolkata and Berlin in Europe/Berlin, when both offices release at 10:00, then each releases at 10:00 of its own local clock, also across a daylight-saving change.
- AC3.7 Given an unknown timezone value, when saved, then it is refused; the timezone is chosen from a list.

### F4 Find a free desk (M2)
Employee picks office, date and part of the day (full, morning, afternoon); optional filters floor, zone, feature. The page lists free desks (code, floor, zone, features) and the number of free desks. No names.
Roles: employee, manager, admin. Data: Desk, Booking (counts only).
- R13 A desk is free for a part of the day if it has no active booking overlapping it and no block. A full-day booking occupies morning and afternoon; a desk can be booked by one person for the morning and another for the afternoon.
- R14 Bookable dates: today up to the booking horizon (G6), working days of that office only (F3). Today stays bookable until the part of the day has ended: the morning ends at the midday split, the afternoon and a full day at the end of the office day (A21); a booking made after the part has started is booked from now (D2, P1).
- R15 The list refreshes by itself within 5 seconds (Q9).
- R16 Reserved (accessibility) desks are shown only to people on the access list (F16).
- AC4.1 Given 40 free desks, when Asha picks Pune, tomorrow, full day, then she sees 40 desks and the number 40.
- AC4.2 Given she filters zone "3rd floor east" and feature "standing desk", when applied, then only desks with both are shown.
- AC4.3 Given no free desk matches, when she searches, then she sees "No free desks for this day. Try another date or office." and the closest other offices or days that have desks (G22: no waiting list).
- AC4.4 Given another person books desk BLR-3-14, when 5 seconds have passed, then it disappears from Asha's list without a reload.
- AC4.5 Given the refresh fails (network), when 5 seconds pass, then the page keeps the old list and shows "Showing data from N seconds ago" until it works again.
- AC4.6 Given a date before today, beyond the horizon, a weekend or a closed day, when she opens the date picker, then it cannot be chosen.
- AC4.7 Given today and the part of the day has ended, when she picks today, then that part is not selectable and the reason is shown (D2, P1).
- AC4.8 Given a blocked or retired desk, then it is never listed.
- AC4.9 Given an employee who is not on the access list, then reserved desks are neither listed nor counted for her (F16).
- AC4.10 Given a list with 500 desks, when it loads, then the first screen shows in under 2 seconds and the rest loads by scrolling.
- AC4.11 Given a morning booking exists on desk X, when Ravi searches for the afternoon, then X is listed for him.

### F5 Book a desk (M2)
The employee chooses a free desk and books it for a date and part of the day.
Roles: employee, manager, admin. Data: Booking.
- R17 One active booking per employee per day (PRD 4.2). Whether a morning desk and an afternoon desk on the same day count as two is open (G4); until decided, only one booking per day.
- R18 First request wins; the second gets "just taken" and a refreshed list (Q9).
- R19 An employee can book in any office (G19) up to the horizon (G6).
- R20 A booking for a part of today that has ended is refused (R14). A booking for today made after that part's release time is accepted and must be checked in within 30 minutes of booking, else it is released again (R28a, D2, P1).
- R21 Booking an office, date or desk that has just been closed or blocked is refused with a reason.
- AC5.1 Given a free desk, when Asha books it, then the booking is saved, she sees desk, office, date, part of day, release time and how to check in; the desk leaves everyone's list.
- AC5.2 Given Asha already has an active booking that day, when she tries another, then it is refused with "You already have a desk that day" and a link to it.
- AC5.3 Given Asha and Ravi both press Book on the last desk in the same second, when processed, then one booking exists; the other sees "Just taken, here are other free desks".
- AC5.4 Given Asha double-clicks Book, when processed, then only one booking exists.
- AC5.5 Given the desk was blocked by an admin a minute ago, when she books, then it is refused with "desk no longer available".
- AC5.6 Given a date beyond the horizon sent by a tampered request, when received, then it is refused as on screen (rules are enforced on the server, not only the page).
- AC5.7 Given a booking for a part of today that has ended, when sent, then it is refused (D2, P1).
- AC5.8 Given Asha is signed in and the SuccessFactors copy has no record of her, when she books, then she sees "Your profile is not ready yet" and nothing is saved (G18).
- AC5.9 Given an employee's record is inactive (left the company), then she cannot book.
- AC5.10 Given a full-day booking, then it occupies morning and afternoon of that desk.
- AC5.11 Given the booking succeeded, when she opens My bookings, then it is shown within 1 second.
- AC5.12 Given any booking confirmation (one day, several days (F19) or made by a manager (F10)), then it holds a "How check-in works" box: when check-in opens, the check-in deadline, check in by scanning the desk QR or pressing Check in on Today (F18), a reminder 15 minutes before the deadline, and "Running late" keeps the desk once until the hold time (D2); for a booking made after the release time the deadline is 30 minutes after booking (R28a).
- AC5.13 Given today 10:30 and a desk free for the full day after a release, when Asha books it, then she gets it from now and sees "Check in within 30 minutes" (D2, P1).
- AC5.14 Given a booking for today made before the release time, then the normal release time is its deadline (R26a).
- AC5.15 Given she books an afternoon desk at 11:00, then the afternoon release time is its deadline.

### F6 My bookings and cancel (M2)
The employee sees her upcoming bookings and the last 30 days, and can cancel.
Roles: employee, manager, admin. Data: Booking.
- R22 Cancelling is allowed until check-in. After check-in the action is "Release desk" (leaving early), not cancel (G14).
- R23 A cancelled or released desk becomes free at once.
- AC6.1 Given a booked desk, when Asha cancels, then status is Cancelled, the desk shows free in other people's lists within 5 seconds, and she sees a confirmation.
- AC6.2 Given a checked-in booking, when she looks at it, then "Cancel" is replaced by "Release desk"; releasing frees the desk for the rest of the day (G14).
- AC6.3 Given she has no bookings, then My bookings says "No bookings yet" with a Book a desk button.
- AC6.4 Given a booking made for her by her manager, when she cancels it, then it is cancelled and the manager sees the new status.
- AC6.5 Given a cancel request for someone else's booking sent by a tampered request, then it is refused.
- AC6.6 Given a booking that was already released by the system, when she presses Cancel on an old page, then she sees its real status instead of an error.

### F7 Check-in (M3)
Check in by button in the app or by scanning the QR code on the desk.
Roles: employee, manager, admin. Data: Booking, Desk.
- R24 Check-in opens at 06:00 office time for full-day and morning bookings and at 12:00 for afternoon bookings, and closes at the booking's deadline: the release time, the hold time after Running late (R28b) or 30 minutes after a late booking (R28a) (G9, D2).
- R25 The QR code holds the desk address only; opening it requires normal sign-in and then acts on the signed-in person's own booking (G9).
- R26 Scanning a desk that is not the one booked does not check in; the page says "This is not your desk" and shows her desk code, zone and floor. "Move my booking here" is Later (ST-CI-9, D3).
- R26b Scanning her own booked desk inside the check-in window checks her in at once, with no extra tap (Q91). The Check in button stays on Today for people who do not scan.
- AC7.1 Given a morning booking and 08:15 local, when Asha presses Check in, then status is Checked-in with the time.
- AC7.2 Given she scans the QR of her booked desk on her phone inside the check-in window, when signed in, then she is checked in at once, with no further tap, and sees "Checked in at BLR-3-14" (Q91).
- AC7.3 Given she is not signed in, when she scans, then she is asked to sign in and is then taken back to the desk page.
- AC7.4 Given she scans desk BLR-3-15 but booked BLR-3-14, when the page opens, then she is not checked in and sees "This is not your desk. Your desk is BLR-3-14, zone 3 East, floor 3"; there is no "Move my booking here" button (Later).
- AC7.5 Given she has no booking and scans a free desk, when the page opens, then she is offered to book it for today while that part of the day has not ended (R14, G9, D2).
- AC7.6 Given check-in is before 06:00 or after the booking's deadline, when she presses Check in, then it is refused with the opening time or "released".
- AC7.7 Given she presses Check in twice, then she is checked in once.
- AC7.8 Given an afternoon booking at 11:00, then Check in is disabled until 12:00 and says so.
- AC7.9 Given she scans her own desk before check-in opens or after release, then she is not checked in and sees the opening time or "released" (as AC7.6).
- AC7.10 Given she has a booking today and does not scan, then the Check in button is on the Today card (F18) and works as AC7.1.

### F8 Automatic release (M3)
A background job releases bookings not checked in by their deadline: the release time of their part of the day (Q2, Q3), the hold time after Running late, or 30 minutes after a late booking (D2, P1, P2).
Roles: system. Data: Booking.
- R26a Full-day and morning bookings are released at the morning release time, afternoon bookings at the afternoon release time, in the office's own clock.
- R27 A booking released at its release time without a Running late tap is a no-show (counts in the no-show rate); a release at the end of a hold or of a late booking's 30 minutes is "Released after hold", not a no-show (Q50). In both cases the desk becomes free for everyone and the booker is emailed (F13).
- R28 The booker keeps her right to book any other free desk that day until the part of the day has ended (R14, G15, D2).
- R28a A booking for today made after its part's release time must be checked in within 30 minutes of booking, else it is released again (D2, P1).
- R28b Running late: before the deadline, one tap moves the deadline to the hold time (release time + 90 minutes, Q49), once per booking, from Today, My bookings or the reminder email (D2, P2).
- R29 A job that was stopped catches up when it restarts; releasing is safe to repeat.
- R30 Release happens within 5 minutes after the release time (A12).
- AC8.1 Given a morning booking at Pune, not checked in at 10:00 local, when the job runs, then it is Released by 10:05, and the desk appears free.
- AC8.2 Given an afternoon booking, when 10:00 passes, then it is untouched; at 14:00 + 5 min it is Released if not checked in.
- AC8.3 Given a full-day booking not checked in at 10:00, then the whole booking is released, afternoon part included.
- AC8.4 Given a booking checked in at 09:59:58, when the job runs at 10:00, then it stays Checked-in (the saved check-in wins).
- AC8.5 Given the job was down from 09:50 to 10:40, when it restarts, then every overdue booking is released once and a "released" email is sent once per booking.
- AC8.6 Given Bengaluru and Berlin, when 10:00 arrives in Berlin, then only Berlin bookings are released.
- AC8.7 Given Asha arrives at 10:05 after release, when she opens the app, then she sees the free desks first and a one-line note that her booking was released, and she can book a free desk for today that she must check in by 10:35 (G15, D2, P1).
- AC8.8 Given a cancelled booking, then the job ignores it and no email is sent.
- AC8.9 Given a booking made at 10:20 after the release, when 10:50 passes without check-in, then it is released again as "Released after hold"; checked in at 10:45, it stays Checked-in (R28a).
- AC8.10 Given an afternoon booking made at 14:20, then the same 30 minutes apply.
- AC8.11 Given a morning booking not checked in at 09:50, when Asha taps Running late, then the deadline moves to 11:30 and she sees the new time; the tap is not offered again for that booking (R28b).
- AC8.12 Given the hold ends without check-in, then the booking is "Released after hold" and not a no-show; given she checks in during the hold, then status is Checked-in.
- AC8.13 Given a release without the tap, then it is a no-show (R27).

### F9 Team view (M4)
A manager sees a week calendar of her direct reports: for each person and working day the office, desk code, part of the day and status (booked, checked-in, released).
Roles: manager. Data: Booking, Employee.
- R31 "Team" means direct reports only (Q5, G7). Peers do not get a team view (Q4, G1).
- R32 The team is taken from the latest SuccessFactors copy; bookings stay with the employee when the manager changes.
- AC9.1 Given Meera has 6 direct reports, when she opens Team for this week, then she sees 6 rows by 5 working days with each booking.
- AC9.2 Given a report has no booking on a day, then the cell is empty (not "absent").
- AC9.3 Given she moves to next or last week, then the view changes; on past days only desks that were used (checked in) are shown, and a booking that ended as a no-show or was cancelled looks like an empty day (Q89, D2).
- AC9.4 Given she has no direct reports, then she sees "No direct reports found" and the date of the last people update.
- AC9.5 Given an employee without reports, when she opens the Team link directly, then it is refused.
- AC9.6 Given Meera's team changed in last night's copy, then today's view shows the new team; bookings of someone who left her team vanish from her view.
- AC9.7 Given a filter by office, then only bookings in that office are shown.
- AC9.8 Given 40 direct reports, then the week loads in under 2 seconds.
- AC9.9 Given a report booked in another office, then the cell shows that office name.
- R31a An "In the office" row on top of the week shows per day how many direct reports are in (booked or checked in; on past days checked in only) with their initials.
- AC9.10 Given 4 of Meera's 6 reports have a booking on Wednesday, then the row shows "4 of 6" and their 4 initials.
- AC9.11 Given a past day where one report was released as a no-show, then the row counts only the checked-in reports and the no-show is not marked anywhere (Q89).
- AC9.12 Given an employee without reports or an admin, then the row and initials are never sent to the browser (AC17.4).

### F10 Book for a team member (M4)
A manager books or cancels a desk for one direct report.
Roles: manager. Data: Booking.
- R33 Same rules as F5 (horizon, one per day, today until the part has ended with the 30-minute check-in, free desk). A person who already has a booking that day is refused (Q5).
- R34 The employee is emailed. The booking shows "Booked by <manager>" to the employee.
- R35 A manager may cancel a booking of a direct report; the employee is emailed (A11).
- AC10.1 Given Ravi (direct report) has no booking on Tuesday, when Meera books desk BLR-3-14 for him, then the booking exists, he is emailed and sees "Booked by Meera".
- AC10.2 Given Ravi already has a booking that day, then Meera is refused with "Ravi already has a desk that day" and nothing is replaced.
- AC10.3 Given a person who is not Meera's direct report, when she tries to book for them (also by a tampered request), then it is refused.
- AC10.4 Given Meera and Ravi book at the same moment, then one booking exists and the other sees "already booked".
- AC10.5 Given Meera cancels Ravi's booking, then he is emailed and sees status Cancelled by manager.
- AC10.6 Given Ravi checked in already, then Meera cannot cancel it.
- R57 "+ Book" shows on an empty future day of a direct report (today only while booking is open, F5). The dialog proposes a free desk in the zone where most of her direct reports are booked that day; tie: the zone with more free desks; nobody booked: the desk R63 would pick for that report. She can change it from the zone list (F19).
- AC10.7 Given 3 of Meera's reports are booked in zone 3 East on Wednesday and 1 in 2 West, when she presses "+ Book" for Ravi on Wednesday, then a free desk in 3 East is proposed with "Where most of your team sits".
- AC10.8 Given 3 East has no free desk, then the next zone by team count that has one is proposed; if none, the R63 pick for Ravi.
- AC10.9 Given the proposal, then it shows zone and desk code only and uses only her direct reports' bookings; no other person's booking or name is used or shown.
- AC10.10 Given a past day or a day Ravi already has a booking, then no "+ Book" is shown.

### F11 Group booking (M4)
A manager books desks in one zone for several direct reports for one day (Q8).
Roles: manager. Data: Booking, Zone.
- R36 Needs a zone with enough free desks for the selected people for the whole part of the day. Either every selected person gets a desk or nobody does (G5).
- R37 Selected people who already have a booking that day are skipped and listed before confirming (G5). Maximum 20 people per group booking (G5).
- R38 Desks are assigned by the system; the manager does not choose single desks.
- AC11.1 Given 5 direct reports without bookings and zone "3rd east" with 8 free desks, when Meera confirms, then 5 bookings exist in that zone and each person is emailed.
- AC11.2 Given a zone with 3 free desks and 5 people, then no booking is made and she sees which zones have enough desks, or the largest free number.
- AC11.3 Given 2 of 5 people already booked, then the screen lists them as skipped and proceeds with 3 only after she confirms.
- AC11.4 Given another booking takes a desk while she confirms, when processed, then the system picks other free desks in the zone or, if not enough remain, books nobody and says so.
- AC11.5 Given more than 20 people are selected, then she is stopped with the limit message.
- AC11.6 Given a person not in her team is selected by a tampered request, then the whole request is refused.
- AC11.7 Given a date outside the horizon or a closed day, then it is refused as in F5.
- AC11.8 Given a group booking was made, then each person's booking can be cancelled on its own.

### F12 Reports (M5)
Facilities sees occupancy per office, floor and day (capacity, booked, checked-in), no-show rate and busiest days; weekly desk use per office (Q1); export to Excel.
Roles: admin (counts only). Managers see no no-show data (D2, Q89). Data: Booking (counts), Desk.
- R39 Reports show counts and rates only, never names (Q4).
- R40 Capacity counts bookable desks only; blocked and retired desks are not capacity (G10). A half day is half a desk-day (G10).
- R41 No-show rate = no-show releases (R27) divided by bookings that were not cancelled before the release time (G10). "Released after hold" is counted on a separate line in the office totals and not in the rate (Q50).
- R42 Days follow each office's own timezone.
- R43 Export holds what is on screen, up to 100,000 rows (G20).
- AC12.1 Given Pune has 60 bookable desks and on Monday 42 booked, 35 checked in, 7 released, then the report shows capacity 60, booked 42, checked-in 35, no-show rate 7/42 = 16.7 %.
- AC12.2 Given a date range of 1 to 31 Oct, when she picks office Pune, then rows per day and floor appear with totals.
- AC12.3 Given two blocked desks on a day, then capacity for that day is reduced by two.
- AC12.4 Given a half-day booking, then it counts 0.5 in booked and capacity is in desk-days.
- AC12.5 Given a cancelled booking before the release time, then it is not a no-show and not booked at release.
- AC12.6 Given "busiest days" for the range, then the top 5 days by checked-in share of capacity are listed.
- AC12.7 Given no data in the range, then she sees "No bookings in this period" and the export is disabled.
- AC12.8 Given an export of 30,000 rows, when she presses Export, then she gets an Excel file with the same rows and columns as the screen within 30 seconds.
- AC12.9 Given more than 100,000 rows, then the export is refused with "Narrow the dates or office".
- AC12.10 Given an employee or manager opens reports by link, then it is refused.
- AC12.11 Given an export file, then it contains no employee names or ids.
- AC12.12 Given a 3-month range for all offices, then the report shows in under 5 seconds (A14).
- AC12.13 Given the report is opened during the nightly release of old data, then numbers are the same as before and after.
- R58 Occupancy page (D5): four totals (capacity, booked, checked in, no-show rate), then a heat grid of zones by day for the chosen office and range (darker = fuller: checked-in share of capacity for past days and today; booked share with a dashed edge for days to come), then the occupancy table: one row per day with capacity, booked, checked in, no-show rate and a "used" bar, plus a total row. The Excel export holds this table (R43).
- AC12.14 Given Pune and this week, then four totals show above a grid of 5 zones by 5 working days, and the table below it.
- AC12.15 Given zone 3 East on Monday with 12 bookable desks and 9 checked in, then the cell shows 75 % and is darker than a 25 % cell; shades come from the tenant theme (A7).
- AC12.16 Given Thursday is still to come with 6 of 12 desks booked, then the cell shows 50 % booked with a dashed edge.
- AC12.17 Given a zone with no bookable desk that day, then its cell shows "-", not 0 %.
- AC12.18 Given the table, then the total row equals the sum of the day rows and its no-show rate is computed from the totals (R41), not averaged.
- AC12.19 Given Export, then the Excel file holds the table rows and the total row as on screen, with no names (AC12.11).
- AC12.20 Given a screen reader or no colour vision, then every grid cell carries its percentage as text (WCAG 2.1 AA).

### F13 Notifications (M6)
Email only (G12). Messages: (1) evening reminder the day before, (2) booking released, (3) booking made or cancelled for you by your manager, (4) booking cancelled because a desk or office was blocked or closed, (5) no-show reminder after three in a month (F15), (6) check-in reminder 15 minutes before the deadline (D2, P2).
Roles: system. Data: Notification log.
- R45 Reminder goes at 18:00 office time on the evening before each booked working day, only for bookings still active (G12). A second reminder goes 15 minutes before each booking's check-in deadline if it is not checked in, once per booking, with a check-in link and the Running late link (D2, P2).
- R46 Each message is sent once per event; a failed send is retried 3 times over 1 hour, logged, and never blocks or undoes the booking.
- R47 Messages are in English in release 1 and use translatable texts (A8, G21). A message never names another employee.
- AC13.1 Given Asha has a booking for Tuesday, when it is Monday 18:00 in Pune, then she gets one reminder with desk, office and release time.
- AC13.2 Given the booking was cancelled before 18:00, then no reminder is sent.
- AC13.3 Given a booking released at 10:00, then Asha gets one email "Your desk was released".
- AC13.4 Given Meera books for Ravi, then Ravi gets one email.
- AC13.5 Given a desk block cancels 2 bookings, then both people get one email each offering to find another desk.
- AC13.6 Given the mail service is down, then bookings still work and the email is retried 3 times, then logged as failed.
- AC13.7 Given the reminder job runs twice, then no one gets a duplicate.
- AC13.8 Given a Friday booking on Monday, then the reminder goes on Thursday evening and not on weekends (the evening before a working day only).
- AC13.9 Given a morning booking not checked in at 09:45 in Pune, then Asha gets one email "Check in or your desk is released" with a check-in link and the Running late link (R45).
- AC13.10 Given she checked in or cancelled before 09:45, then no check-in reminder is sent; given the job runs twice, then one email per booking.
- AC13.11 Given she tapped Running late, then the check-in reminder goes 15 minutes before the hold time (11:15), once.

### F14 People from SuccessFactors (M7)
Read-only copy every night of: employee id, name, email, direct manager, home office, active flag (Q11).
Roles: system; admin sees status. Data: Employee, Sync run.
- R48 Nothing is written back to SuccessFactors.
- R49 If SuccessFactors is down or the file is bad, the last good copy stays in use; the admin sees "People data last updated <date>"; the sync retries every hour for the rest of the day (A13).
- R50 A manager change takes effect for the team view from the next sync; bookings stay with the employee (R32).
- R51 A person who is no longer active has all future bookings cancelled and gets no email (G7).
- R52 Manager status: anyone who is the manager of at least one active employee (G7).
- AC14.1 Given a nightly run with 3,000 employees, then it finishes in under 10 minutes and shows counts of new, changed and left people.
- AC14.2 Given SuccessFactors does not answer, then the last copy is kept, the run is marked failed, and the admin page shows the date of the last good copy.
- AC14.3 Given 2 days without a good copy, then the admin sees a warning banner.
- AC14.4 Given Ravi's manager changes, when the next sync completes, then Meera's team view no longer shows him and the new manager's does.
- AC14.5 Given an employee leaves, when the sync completes, then her future bookings are cancelled and the desks become free (G7).
- AC14.6 Given a new employee appears, then she can sign in and book from that day on.
- AC14.7 Given a record without an email, then it is skipped and listed on the admin sync page.
- AC14.8 Given two syncs would overlap, then the second is skipped.

### F15 No-show follow-up (M3)
No penalty in release 1 (Q7). After three no-show releases (R27, not "Released after hold") in one calendar month the employee gets one reminder email. The no-show rate is visible to the admin as counts only; managers see no no-show data (D2, Q89).
Roles: system, manager, admin.
- R53 Three or more in a calendar month, counted at the time of the third release, triggers one email for that month.
- AC15.1 Given Ravi's third release in October, then he gets one reminder; a fourth release in October sends nothing more.
- AC15.2 Given his first release in November, then the count starts at one.
- AC15.3 Given a released booking later corrected by an admin, then no correction exists in release 1 (no manual changes of status).
- AC15.4 Given Meera opens the team view, then she sees no no-show count or mark for any person (D2, Q89).
- AC15.5 Given any no-show count, then it never blocks a booking.

### F16 Reserved desks for accessibility (M8)
A desk can be flagged "reserved for accessibility". Only people on an admin-kept access list see and book it (G11).
Roles: admin (list and flags), employee (books). Data: Desk flag, Access list.
- R54 The access list holds names only; no reason or health detail is ever entered or stored (G11).
- R55 Admin-only: adding or removing a person is recorded in change history (A6).
- AC16.1 Given desk BLR-3-02 is flagged, when Asha is not on the list, then she cannot see or book it.
- AC16.2 Given Ravi is on the list, then the desk is listed for him and he books it like any other.
- AC16.3 Given Ravi is removed from the list, then his existing bookings stay, new ones are refused.
- AC16.4 Given the access-list page, then it has no free-text reason field.
- AC16.5 Given a manager or employee opens the list by link, then it is refused.
- AC16.6 Given a flagged desk, then reports count it as capacity as normal.

### F17 Sign-in and access (M8)
Company sign-in through the base (A1, A2). Page and data access is checked on the server for every call.
- R56 Only signed-in people with a role can open a page; every action checks the role (A2).
- AC17.1 Given a person not signed in, when she opens any page, then she is sent to company sign-in and back.
- AC17.2 Given a signed-in person without a DeskBook role, then she sees "No access".
- AC17.3 Given a person whose session expired, when she presses Book, then she signs in again and no booking is lost silently (the page tells her it was not saved).
- AC17.4 Given any page, then the data a role may not see is not in the answer sent to the browser, not only hidden on screen.

### F18 Today page (M2)
The first page after sign-in (option A, D5). It shows her booking for today with desk code, zone, floor, check-in deadline and the buttons Check in and Running late (D2); a "Your usual desk" card; "<office> tomorrow: N of M desks free"; and a strip of her next two weeks where a booked day shows its desk code and a free working day shows an "Add day" tile that opens F19.
Roles: employee, manager, admin (for themselves). Data: Booking (own), Desk, Office.
- R59 The usual desk is the desk she booked most often in the last 60 days, with at least 3 bookings; a tie goes to the most recent (G25, Q97). Without one the card is hidden.
- R60 The office on Today is her remembered office (ST-BK-2), else her home office.
- R61 "N of M desks free" counts bookable desks only: M leaves out blocked and retired desks and, for people not on the access list, reserved desks (R16, R40); N is the desks free for the full day on the office's next working day.
- R62 Today shows only her own bookings; no other person's booking or name.
- AC18.1 Given Asha has PUN-3-14 booked today, when she opens Today at 08:35, then she sees desk, zone, floor, the check-in deadline, Check in and Running late.
- AC18.2 Given she has no booking today, then the card says "No desk today" with Add day while booking for today is open (F5).
- AC18.3 Given she booked PUN-3-14 on 9 of her last 12 office days in 60 days, then "Your usual desk PUN-3-14" is shown; given no desk with 3 bookings in 60 days, the card is hidden.
- AC18.4 Given Pune has 60 desks, 2 blocked, 1 reserved (Asha not on the list) and 17 booked for tomorrow, then she sees "Pune tomorrow: 40 of 57 desks free".
- AC18.5 Given the strip, then it shows the next 14 days; weekends and closed days have no Add day tile; booked days show the desk code; free working days show Add day.
- AC18.6 Given the free count fails to load, then the rest of Today still shows and the count says "Not available right now".
- AC18.7 Given 500 people open Today on Monday 08:00, then it shows in under 2 seconds (Non-functional).

### F19 Plan my days and best desk (M2)
From "Add day" or "Plan my days" she ticks working days on a two-week calendar (office and part of day remembered, changeable). For each ticked day the system proposes a free desk with a reason tag. "Change" on a day opens the free desks of that day as a list grouped by zone with counts (option B's zone list, D5; F4 rules and filters). "Book N days" makes N separate bookings (Q90). Replaces ST-BK-8 "Best desk for me", now in the MVP (D5).
Roles: employee, manager, admin (for themselves). Data: Booking, Desk, Zone.
- R63 Proposal per day, first match wins: (1) her usual desk if free, "Your usual desk"; (2) a free desk in her usual desk's zone, "Same zone as usual"; (3) a free desk matching her chosen zone and features, "Matches your choices"; (4) a free desk on her usual floor, else any free desk in the office, "Closest free desk" (no floor map, A20). Within a step the lowest desk code wins. Reserved desks only for people on the access list (R16).
- R64 Each day is its own booking (Q90): every F5 rule applies per day (one per day, 14-day horizon, closed days, blocks, booking for today); each day can be cancelled alone. This is not a recurring booking (Q6 stays out of scope).
- R65 Days are booked independently: if one day fails, the others are still booked and the result lists each failed day with its reason (A19).
- R66 If a proposed desk is taken between showing and booking, the system books the next desk by R63 and says "Desk changed: PUN-3-15 instead of PUN-3-14"; if no desk is left that day, that day fails (R65).
- R67 A day she already has a booking on cannot be ticked; it shows the booked desk.
- AC19.1 Given Asha ticks Tue, Wed and Thu and her usual PUN-3-14 is free on Tue and Thu, when the proposals show, then Tue and Thu show PUN-3-14 "Your usual desk" and Wed a free desk in zone 3 East "Same zone as usual".
- AC19.2 Given she presses "Book 3 days", then three bookings exist, the confirmation lists each with its desk, and each can be cancelled alone.
- AC19.3 Given she taps Change on Wed, then she sees Wednesday's free desks grouped by zone with free counts and filters, and picking one replaces only the Wednesday proposal.
- AC19.4 Given PUN-3-14 is booked by someone else on Thu a moment before she confirms, then Thu gets the next desk by R63 and the result says which desk changed.
- AC19.5 Given Thu has no free desk left when she confirms, then Tue and Wed are booked and Thu is listed "Not booked: no free desk" with other days or offices that have desks (AC4.3).
- AC19.6 Given she has no usual desk and no filters, then every day shows "Closest free desk"; a proposal always shows its reason.
- AC19.7 Given she already has Wed booked, then Wed cannot be ticked and shows the booked desk.
- AC19.8 Given a weekend, a closed day or a day beyond the booking horizon, then it cannot be ticked (AC4.6).
- AC19.9 Given a free reserved desk and Asha is not on the access list, then it is never proposed (AC4.9).
- AC19.10 Given 10 days ticked, when she presses Book, then all are processed in under 2 seconds and a double tap creates no duplicates (AC5.4).
- AC19.11 Given a tampered request with one day that breaks a rule, then the server refuses that day as in F5 and processes the others.
- AC19.12 Given she wants one exact desk, then the plain list of F4 stays reachable from Change and from Book a desk.

## Journeys
**J1 Employee books and checks in**
1. Asha signs in, opens Book a desk, picks Pune, Tuesday, full day.
2. She filters "standing desk", sees 12 desks, picks BLR-3-14, presses Book.
3. She sees the confirmation with release time 10:00.
4. On Monday 18:00 she gets the reminder email.
5. On Tuesday 08:40 she scans the QR on the desk and sees "Checked in".

**J2 No-show and release**
1. Ravi booked a desk and does not come.
2. At 09:45 Ravi gets the check-in reminder; he does not tap Running late.
3. At 10:00 Pune time the system releases the booking; Ravi gets an email.
4. The desk shows free; someone else books it for the rest of the day and must check in within 30 minutes.
5. The release counts in the office no-show rate and towards Ravi's own monthly reminder (F15); his manager sees no no-show data (D2).

**J3 Manager arranges a team day**
1. Meera opens Team and sees next week: three people not booked on Wednesday.
2. She opens Group booking, picks Pune, Wednesday, zone "3rd east", the three people.
3. The system finds 3 free desks in the zone, books all, emails each person.
4. Ravi cancels his own desk later; Meera sees it in the week view.

**J4 Admin sets up a new office**
1. Admin creates the office with timezone and release times, adds closed days.
2. She adds floors, zones and desks (or imports a CSV), flags accessibility desks.
3. She prints QR codes per desk (QR content defined in design).
4. She opens the office to booking.

**J5 Facilities reviews usage**
1. Admin opens Reports, picks Pune and last month.
2. She sees capacity, booked, checked-in and the no-show rate per floor and day, and the busiest days.
3. She exports to Excel for the space plan.

**J7 Employee plans her week (option A, D5)**
1. Asha opens Today: her desk for today with Check in, her usual desk, and the next two weeks.
2. She taps Add day and ticks Tue, Wed, Thu.
3. Each day shows a proposed desk with its reason; she taps Change on Wed and picks a desk from the zone list.
4. She presses "Book 3 days"; three bookings exist and the confirmation explains how check-in works.
5. On Tuesday she scans the desk QR and is checked in at once.

**J6 A desk is blocked for maintenance**
1. Admin blocks BLR-3-14 for 3-5 Nov; the page says 2 bookings are affected.
2. She confirms; both people are emailed and the desk leaves the free list.
3. The two people book other desks.

## Business objects
| Object | Fields (business words) | States and who moves them |
|---|---|---|
| Office | name, city, timezone, release times, midday split, working days, closed days, open/closed | Open -> Closed (admin) |
| Floor | name, office | Active -> Retired (admin) |
| Zone | name, floor | Exists while desks use it |
| Desk | code, floor, zone, features, reserved-for-accessibility | Active -> Blocked (admin, dates) -> Active; Active -> Retired (admin) |
| Block | desk, from, to, reason | Created and removed by admin |
| Employee | id, name, email, manager, home office, active | Copied nightly (system) |
| Booking | employee, desk, date, part of day (full, morning, afternoon), booked by (self, manager), group id, check-in deadline, Running late used | Booked -> Checked-in (employee) -> Ended early (employee, "Release desk") or Completed (system, end of day); Booked -> Cancelled (employee or manager); Booked -> Released (system, no-show); Booked -> Released after hold (system, after Running late or a late booking's 30 minutes, Q50); Booked -> Cancelled by system (block, closure, leaver) |
| Access list entry | employee | Added and removed by admin |
| Notification | type, booking, sent time, result | Sent or Failed (system) |
| Sync run | start, end, counts, result | Success or Failed (system) |

## Non-functional
| Need | Number | Source |
|---|---|---|
| Users | 3,000 employees, 4 offices now, 8 offices within a year | PRD 5; growth assumption A13 |
| Peak load | 500 people using the app at once (Monday 08:00) | Q10 |
| Booking data volume | about 450,000 bookings a year, 2 million rows in the first 4 years | assumption A13 |
| Page response | under 2 seconds for any page; booking action under 1 second (95 % of requests) | Q10; A14 |
| Availability freshness | desk list refreshes within 5 seconds | Q9 |
| Uptime | 99.5 % on weekdays 06:00-20:00 | Q10 |
| Release accuracy | within 5 minutes after the release time | assumption A12 |
| Sign-in | company sign-in only, no separate passwords | Q10, A1 |
| Devices | phone browsers from 360 px wide, tablets, desktop; current Chrome, Edge, Safari, Firefox | PRD 5 "works on mobile"; A15, G13 |
| Accessibility | WCAG 2.1 AA, keyboard use, screen reader labels | Q10 |
| Languages | English in release 1; German and French in release 2; all texts translatable from day one | PRD 5; G21; A8 |
| Audit | history of who changed what on every table, kept 2 years | Q10; A6 |
| Retention | booking records with names kept 2 years then made anonymous (counts stay) | G8 (recommended) |
| Privacy | personal data limited to name, email, manager, office; no health data; employees see only their own bookings | Q4, G1, G11 |
| Export | up to 100,000 rows | G20 |
| Report speed | 3 months, all offices, under 5 seconds | assumption A14 |
| Time handling | every date and time is in the office's timezone | Q3 |

## Integrations
| System | Direction | Data | Frequency | If it fails |
|---|---|---|---|---|
| SuccessFactors | into DeskBook only | employee, direct manager, home office, active flag | nightly; retry hourly | last good copy stays in use; admin sees date and a warning after 2 days (Q11, A13) |
| Email service | out | the five messages in F13 | on event | retried 3 times over 1 hour, then logged; booking never blocked |
| Company sign-in (approuter/XSUAA) | in | who the person is and her role | each visit | no sign-in possible; app shows the sign-in error (A1) |
| Excel file | out | report rows | on request | download error with retry |

## Assumptions
- A1 (base) Login through the SAP approuter/XSUAA; the product receives user and role. To confirm in BASE-SPEC.
- A2 (base) Session and roles plumbing exist: roles Employee, Manager, Facilities admin are role collections the base can map; every call is checked on the server.
- A3 (base) Settings pages exist where the office settings and the SuccessFactors link settings live.
- A4 (base) A background jobs framework runs the release, reminder, sync and anonymise jobs and shows failures.
- A5 (base) SuccessFactors integration settings (connection) are in the base; the sync rules in F14 are ours.
- A6 (base) Change history on every table, kept 2 years (Q10).
- A7 (base) Theme manager gives the company colours; DeskBook takes all colours from it.
- A8 (base) i18n with 5 locales exists; DeskBook ships English only in release 1 and keeps every text translatable.
- A9 Managers and admins are also employees and can book for themselves.
- A10 Morning is before 13:00 and afternoon from 13:00 (per office setting). Full day = both.
- A11 A manager may cancel bookings of direct reports (PRD says only "book for"); recommended, not in PRD.
- A12 A release job runs every 5 minutes.
- A13 Volume: about 3 booked days per week for each of 3,000 people over 50 weeks; 8 offices after a year; nightly sync retry every hour.
- A14 Booking action under 1 second and reports under 5 seconds at the stated volumes are our proposed targets; the PRD gives none.
- A15 Responsive web in the phone browser, no native app (G13).
- A16 One desk holds one person per part of the day; no overbooking.
- A17 "Booked" in the success measure counts every successful booking; "got a desk" is measured by search attempts that found at least one desk (G23).
- A18 Weekly desk use per office is a report view by week in release 1; no scheduled email.
- A19 Several days booked in one action succeed or fail day by day (follows from Q90: each day is its own booking); no all-or-nothing.
- A20 Without a floor map, "Closest free desk" means same floor as her usual desk, else lowest desk code in the office.
- A21 The afternoon part and a full day end at the end of the office day (midnight office time) for same-day booking (R14); open as Q130.

## Out of scope
Meeting room booking (PRD 6, "maybe phase 2" - not in this spec), parking, recurring bookings (Q6), a floor map (intake Q2), waiting list (G22), no-show penalties (Q7), per-office admins (G17), push or Teams notifications (G12), writing back to SuccessFactors, native mobile app (G13), booking beyond the horizon.

## Traceability
| PRD section | Feature, assumption, gap or out of scope |
|---|---|
| 1 Background | context; success numbers Q1 -> F12, A17, G23 |
| 2 Goals: always find a desk | F4, F5, F8, F12, G22, G23 |
| 2 Goals: usage per office and floor | F12 |
| 2 Goals: manager sees team | F9, G1, G7 |
| 2 Goals: fast and easy | Non-functional (Q1, Q10), AC4.10, AC9.8, AC12.12 |
| 3 Users | Roles table, F17, G7, G17 |
| 4.1 Office setup | F1, F2, F3, F16, G3, G24 |
| 4.2 Booking (full/half day) | F4, F5, F18, F19, G4, G25 |
| 4.2 Up to 2 weeks ahead | R14, F3, G6 |
| 4.2 One booking per day | R17, F5, F10, G4 |
| 4.2 Cancel any time | F6, G14 |
| 4.2 Recurring bookings | Out of scope (Q6) |
| 4.3 Check-in button or QR | F7, G9 |
| 4.3 Release at 10:00 | F8, F3, Q2, Q3 |
| 4.4 Week calendar | F9 (In the office row, Q89) |
| 4.4 Manager books for team | F10 (team zone proposal), Q5 |
| 4.4 Group of desks near each other | F11, Q8, G5 |
| 4.5 Occupancy, no-show, busiest days | F12 (heat grid + table, D5), G10 |
| 4.5 Export to Excel | F12, G20 |
| 4.6 Reminder and release message | F13, G12 |
| 4.6 "Etc." | resolved to five messages in F13, G12 |
| 5 Real time availability | R15, AC4.4, Q9 |
| 5 Works on mobile | NFR devices, A15, G13 |
| 5 SuccessFactors integration | F14, Integrations, Q11 |
| 5 3,000 employees, 4 offices | NFR volume, A13 |
| 5 English first | NFR languages, A8, G21 |
| 6 Out of scope | Out of scope |
| 7 Repeated no-shows | F15, Q7, G2 |

## Changes after GP
Gate GP, 2026-10-28, decision D5 (option A "Plan my week"; Q89-Q92 recommended answers).
Added:
- F18 Today page: today's desk with Check in and Running late, "Your usual desk" card, "<office> tomorrow: N of M desks free" (bookable desks only), two-week strip with "Add day" tiles (AC18.1-AC18.7).
- F19 Plan my days and best desk: several days in one action, each its own booking (Q90); reason tag per proposed desk; "Change" picker = option B's zone list (D5); ST-BK-8 now MVP (AC19.1-AC19.12).
- F10: "+ Book" proposes a desk in the zone where most of the team sits that day (R57, AC10.7-AC10.10).
- F9: "In the office" row with count and initials (R31a, AC9.10-AC9.12); past days show only used desks, no-show days look empty (Q89, AC9.3 changed).
- F7: scanning your own desk checks you in at once (Q91, R26b, AC7.2 changed, AC7.9-AC7.10); "This is not your desk" shows desk code, zone and floor, "Move my booking here" stays Later (R26, AC7.4 changed).
- F5: "How check-in works" box on every booking confirmation (AC5.12).
- F12: heat grid of zones by day with option B's occupancy table (total row, used bar) under it; the export is that table (D5, R58, AC12.14-AC12.20).
- Journey J7; assumptions A19, A20; new gap G25 (what is the usual desk, same as open Q97 from story-sizer; spec follows its recommendation).
- Q89 also applied to the manager role row, F12 roles, F15 text and AC15.4: managers see no no-show data (D2).
Dropped:
- B "Updated N seconds ago" counter on the free list: B only (the failure note of AC4.5 stays).
- B "Usual" tag on the free list: B only; A shows the reason tag instead.
- B "Last 30 days" list on Today: B only; the last 30 days stay in My bookings (F6).
- C zone board with seats and seat order by desk code (Q92): C only; Q92 is moot.
- C zone tiles tinted by use on occupancy: C only; A's heat grid covers it.
- Tenant colour picker in the top bar: prototype only; colours come from the base theme (A7).
The pre-D2 text noted here (AC4.7, AC5.7, R14, R20, F8, F13) is revised in "Changes for D2" below.

## Changes for D2
Decision D2, 2026-10-28 (P1 same-day booking, P2 reminder and Running late, stricter privacy rule); design review finding M1.
- F3: company settings for the Running late hold (release + 90 min, Q49) and the 30-minute late-booking check-in.
- R14, AC4.7: today bookable until the part of the day has ended (was: until the cut-off, G16).
- R20, AC5.7: refused only when the part of today has ended; a late booking must be checked in within 30 minutes. New AC5.13-AC5.15 (ST-BK-7); AC5.12 names the 30-minute deadline.
- R24, AC7.5, AC7.6: check-in closes at the booking's deadline; a free desk scanned today can be booked until the part ends.
- F8 text, R27, R28, AC8.7: release at the deadline; "Released after hold" is not a no-show (Q50); after a release she can book again until the part ends. New R28a, R28b, AC8.9-AC8.13 (ST-CI-6, ST-CI-7).
- R33 (F10): same D2 booking-for-today rule for managers.
- R41 (F12): no-show rate counts no-show releases only; "Released after hold" on a separate line (Q50).
- F13 text, R45: check-in reminder 15 minutes before the deadline. New AC13.9-AC13.11 (ST-NT-2).
- F15: the monthly reminder counts no-show releases only.
- AC19.8: "beyond 14 days" -> "beyond the booking horizon".
- J2: reminder step added; the no-show is visible to Ravi and the office rate, not to his manager.
- Booking object: check-in deadline, Running late used, state Released after hold.
- A21 (new) and Q130: when the afternoon part ends for same-day booking. Q100 answered by D2.
- Privacy (own bookings only, manager sees direct reports, reports show counts, no per-person no-show count for managers): already in the role rows, F9, F12, F15, R39, R62 and the privacy row; no further change.
