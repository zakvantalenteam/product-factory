# Stories - DeskBook

Stage S4, 2026-10-28; revised after gates GP (D5) and G3 (D6) (see `## Changes after GP`). Built from `02-spec.md` (first version, S2), `03-product-review.md`, `03-journeys.md`, `decisions.md` (D1, D2) and `questions.md` Q1-Q48. Sized as `standards/sizing.md` says. Points are relative size, not hours.

## Summary

The spec was not revised after D2, so D2 is applied here. Changes to the spec that this backlog follows (the requirements-analyst should write them into `02-spec.md`):

- P1/Q45: booking for today is allowed until the end of the day part; a booking made after the release must be checked in within 30 minutes or is released again (replaces G16, AC4.7, AC5.7, AC8.7, Q36).
- P2/Q46: a reminder 15 minutes before the release and a one-tap 'Running late' hold once per booking; only a release without the tap counts as a No-show.
- P3/Q47: release 1 shows managers no per-person no-show count (AC15.4 moves to Later); Facilities sees office totals; admin 'mark as excused' is Later.
- P4/Q48: 'Best desk for me' and a remembered office and part of day are in release 1.
- P5: words are Booked, Checked in, Completed, No-show, Cancelled, 'Released after hold', 'Check-in deadline'; 'Leave early' replaces 'Release desk'; 'Ended early' is merged into Completed.
- P6: managers of managers see everyone below; a manager can name one delegate (both in R1).
- P7: 'Profile not ready' shows the last copy date; admin 'Add person now' (R1).
- P8: admin cancel and move with a reason (R1).
- P9: search outcomes are recorded for the success number (R1); per weekday and zone views in R2.
- P10: group booking, 'Move my booking here', 'Leave early', the no-show reminder email, busiest days and weekly use are moved out of the first release (R2 or Later).
- Q39-Q44: Team menu hidden without reports; QR print sheet; office state Draft; zone list per floor; 'Run sync now'; phone slide-over menu.

Release labels used here: **MVP** = the first usable slice (one pilot office); **R1** = the rest of the trimmed release 1; **R2** = after go-live; **Later** = waits for Legal or a decision.

| Epic | Stories | Points | MVP points |
|---|---|---|---|
| BK Book a desk | 16 | 56 | 45 |
| CI Check-in and release | 10 | 37 | 21 |
| OS Offices, desks and Facilities control | 16 | 62 | 31 |
| PP People, roles and access | 10 | 32 | 16 |
| NT Notifications | 7 | 22 | 10 |
| RP Reports | 10 | 42 | 16 |
| TM Team and manager | 12 | 46 | 0 |
| EN Enablers and shell | 4 | 16 | 8 |
| **Total** | **85** | **313** | **147** |

- Points by release: MVP 147 (was 127), R1 125 (was 128), R2 26, Later 15; total 313 (was 296).
- Stories of 8 or more: 0 (PP-1 was split into the copy and the manager mapping).
- Low confidence: 6 (CI-7, PP-1, NT-1, RP-5, TM-11, TM-12).
- Enablers: ST-EN-1, ST-EN-2, ST-EN-3, ST-NT-1.
- Criteria with an AC id come from the spec; 'NEW' criteria come from D2, the product review or the journeys.
- Tasks: one line per story with the tagged parts FE, BE, DB, QA; operation names are proposals for the architect in S5.

## Changes after GP

Gate GP (D5): prototype option A, "Plan my week", is approved; B's zone list becomes the "Change a desk" picker and B's occupancy table stays under A's heat grid. Only the items A adds are sized; items that belong to B or C alone are not built. Points: MVP 127 -> 139, R1 128 -> 133, R2 26, Later 15, total 296 -> 313, stories 80 -> 85.

| Story | Change | Points | Release |
|---|---|---|---|
| ST-BK-8 Best desk for me | Moved into the MVP (D5). Now a proposal with a reason tag ('Your usual desk', 'Same zone as usual', 'Matches your choices', 'Closest free desk') and a re-pick when the desk is taken. No longer depends on ST-BK-2 (its own zone and feature choices). | 5 (same) | R1 -> MVP |
| ST-BK-13 Plan my days (several days in one action) NEW | Several days, each its own booking, with a clear partial result (Q90). | 5 | MVP |
| ST-BK-14 Change a desk picker per day NEW | B's zone list reused as the picker for one proposed day. | 2 | MVP |
| ST-BK-15 Your next two weeks strip with Add day tiles NEW | Entry strip on Today. Left out of the MVP at GP; moved into the MVP at G3 (D6). | 3 | R1 -> MVP (D6) |
| ST-BK-16 Your usual desk card on Today NEW | Card and 'Usual' use of the usual desk. | 2 | R1 |
| ST-RP-10 Occupancy heat grid by zone and day NEW | A's heat grid (solid checked in, dashed booked still to come) above B's table. | 5 | R1 |
| ST-BK-5 Book a desk | New criterion: 'How check-in works' box on every confirmation. | 5 (same) | MVP |
| ST-BK-11 Today page | The count becomes 'Pune tomorrow: N of M desks free' (bookable only). | 5 (same) | MVP |
| ST-CI-2 Check in by scanning | Own booked desk: checked in at once (Q91). | 5 (same) | R1 |
| ST-CI-3 QR page: wrong desk | 'This is not your desk' shows desk code, zone and floor. | 3 (same) | R1 |
| ST-TM-1 Team week | 'In the office' row (count of N with initials); past days show only desks that were used (Q89). | 5 (same, check) | R1 |
| ST-TM-5 Book for a direct report | The dialog proposes a desk in the zone where most of the team sits that day. | 5 (same, check) | R1 |
| ST-RP-1 Occupancy per office, floor and day | Total row per day and a 'used' bar in the table (B's table kept). | 5 (same) | MVP |

Why the MVP grows by 12 and not the 5 in D5: D5 counted only ST-BK-8. Multi-day booking (5) and the per-day picker (2) are the working core of option A, so they are in the MVP too; the strip, the usual-desk card and the heat grid are conveniences on top and go to R1. Moving them into the MVP would add 10 more.

Not built (B or C only): 'Updated N seconds ago' counter, 'Usual' tag in B's list, 'Last 30 days' list on Today, the C zone board and seat order (Q92). Stays Later: ST-CI-9 move my booking here. The tenant colour picker is prototype only.

Not yet in `02-spec.md` when this was written (requirements-analyst is updating it): every criterion tagged NEW(GP) below. They are tied to features F4 and F5 (find and book), F7 (check-in), F9 and F10 (team), F12 (reports); the AC ids are to be filled when the spec is final. Open questions Q97-Q99 in `questions.md`.

Gate G3 (D6, 2026-10-28): ST-BK-15 (two-week strip, 3 points) moves R1 -> MVP: MVP 139 -> 142, R1 133 -> 130, BK MVP 42 -> 45; total 313 and 85 stories unchanged. ST-RP-10 heat grid stays R1 (the MVP keeps the occupancy table and Excel export). ST-BK-16 usual desk card stays R1; the usual desk is the one most booked in the last 60 days, at least 3 times, tie to the most recent (Q97). The spec now has AC18.x (Today) and AC19.x (plan my days and best desk); ST-BK-8 and ST-BK-15 criteria carry them, the other NEW(GP) ids are still to be filled.

Decision D10 (2026-10-29): four MVP criteria that describe R1 features not in the build move out of their MVP stories; points and releases do not change (MVP 147, R1 125). ST-BK-8 c6 (AC19.9, reserved desk never proposed) and ST-RP-3 c3 (AC16.6, reserved desk counts as capacity) move to ST-PP-10 (R1); ST-RP-3 c1 (AC12.3, blocked desks reduce capacity) moves to ST-OS-10 (R1); ST-BK-10 c2 (AC6.4, cancel a booking made by a manager) moves to ST-TM-5 (R1). ST-BK-8 now has 5 criteria, ST-BK-10 4, ST-RP-3 2; ST-PP-10 has 6, ST-OS-10 5, ST-TM-5 6. Closes Q200.

Decision D7 (2026-10-28): ST-RP-4 Occupancy Excel export (`exportReport`, 5 points) moves R1 -> MVP: MVP 142 -> 147, R1 130 -> 125, RP MVP 11 -> 16; total 313 and 85 stories unchanged. Its only dependency, ST-RP-1, is already MVP. Closes the D6 answer 2 gap found by solution-architect.

Sprint guess after D7 (still a guess): MVP 147 points = about 6 to 7 sprints at 22 a sprint (6.7); the first sprint is unchanged.

Sprint guess after D6 (superseded by D7): MVP 142 points = about 6 to 7 sprints at 22 a sprint (6.5).

Sprint guess after GP (superseded by D6): MVP 139 points = about 6 to 7 sprints at 22 a sprint (was about 6). The first sprint is unchanged.

## Reference stories

| Points | Anchor in this backlog |
|---|---|
| 1 | change a label or add a field to an existing form with its column (none left in this backlog) |
| 2 | ST-NT-3 one email on one event; ST-OS-9 one setting |
| 3 | ST-BK-9 a list page with paging and a read endpoint on the booking table |
| 5 | ST-OS-1 create/edit form with validation, new table, audit, endpoint pair |
| 8 | one external integration call or a workflow with states and permissions (ST-PP-1 was 8 and was split) |
| 13 | too big, none |

## Epics

### Epic BK - Book a desk

#### ST-BK-1 Find free desks by office, date and part of day | 5 | High | MVP
Size: availability query over desks, bookings and calendar rules + paged list + count = 5. Confidence High: rules are written with examples.

As an employee, I want to see the free desks for an office, a date and a part of the day, so that I know what I can book.

Criteria:
- AC4.1 Given 40 free desks, when Asha picks Pune, tomorrow, full day, then she sees 40 desks and the number 40.
- AC4.6 Given a date before today, beyond the horizon, a weekend or a closed day, when she opens the date picker, then it cannot be chosen.
- AC4.8 Given a blocked or retired desk, then it is never listed.
- AC4.10 Given 500 desks, when the list loads, then the first screen shows in under 2 seconds and the rest loads by scrolling.
- AC4.11 Given a morning booking on desk X, when Ravi searches the afternoon, then X is listed for him.
- AC1.7 Given no office is Open, when an employee opens booking, then she sees 'No offices are open for booking yet'; the admin sees 'Create the first office'.

Tasks: FE S2 pickers (office, date, part), desk list with count, scroll paging, empty state; BE `listFreeDesks` (office, date, part, page); DB index on booking (desk, date, part, status); QA rule matrix: weekend, closed day, horizon, half days; 500 desks under 2 s; 360 px and keyboard.
Depends on: ST-OS-2, ST-OS-5, ST-OS-7, ST-OS-8, ST-OS-9, ST-EN-2.
Open questions: none

#### ST-BK-2 Filter by floor, zone and feature; remember last office and part of day | 3 | High | R1
Size: filters on the existing query + one stored preference = 3. Confidence High: small extension of ST-BK-1.

As an employee who books often, I want filters and my last choices remembered, so that booking takes fewer steps.

Criteria:
- AC4.2 Given she filters zone '3rd floor east' and feature 'standing desk', when applied, then only desks with both are shown.
- NEW(P4) Given she booked before, when she opens Book a desk, then her last office and part of the day are preselected.
- NEW(P4) Given any desk in the list, then the floor and zone name are shown next to the code.
- NEW Given she clears the filters, then the full list and the count return.

Tasks: FE filter bar, preselected pickers, zone and floor beside each code; BE extend `listFreeDesks` with floor, zone, features; `getBookingPreferences`; DB last office and part on the employee preference row; QA filter combinations; preference survives sign-out.
Depends on: ST-BK-1, ST-OS-4, ST-OS-6.
Open questions: none

#### ST-BK-3 The free list refreshes by itself within 5 seconds | 3 | Medium | R1
Size: polling + stale banner + pause in background = 3. Confidence Medium: 500 users polling every 5 s is about 100 requests a second; proven only in ST-RP-5.

As an employee, I want the free desks to stay current, so that I do not pick a desk someone just took.

Criteria:
- AC4.4 Given another person books desk BLR-3-14, when 5 seconds have passed, then it disappears from Asha's list without a reload.
- AC4.5 Given the refresh fails, when 5 seconds pass, then the old list stays and 'Showing data from N seconds ago' appears until it works again.
- NEW Given the browser tab is in the background, then refreshing pauses and resumes when she returns.
- NEW Given a page left open for an hour, then it does not keep growing in memory or requests.

Tasks: FE polling hook, stale banner, pause when hidden; BE reuse `listFreeDesks` (cheap, cacheable per office/date); DB -; QA disconnect network test; two browsers; background tab.
Depends on: ST-BK-1.
Open questions: Polling is assumed (no push channel in the base); the architect confirms in S5.

#### ST-BK-4 No free desk: show other days and offices | 3 | Medium | R1
Size: second query + suggestion list = 3. Confidence Medium: 'closest' needs a simple rule.

As an employee who finds nothing, I want to see where desks are free, so that I can still plan my visit.

Criteria:
- AC4.3 Given no free desk matches, when she searches, then she sees 'No free desks for this day. Try another date or office.' and the closest other days and offices that have desks.
- NEW Given suggestions, then at most 5 are shown, nearest date first, each one tap from the booking list.
- NEW Given there is no desk anywhere in the horizon, then only the message is shown (no waiting list, G22).
- NEW Given a suggestion, then it shows counts only and no names.

Tasks: FE empty state with suggestion list; BE `suggestFreeDesks`; DB -; QA none free; one other day; other office.
Depends on: ST-BK-1.
Open questions: 'Closest' is assumed to mean same office other days first, then other offices on the same date; PO to confirm in design.

#### ST-BK-5 Book a desk | 5 | High | MVP
Size: new booking table + audit + endpoint pair + confirmation + rules = 5. Confidence High: same shape as the reference 5.

As an employee, I want to book a free desk for a date and part of the day, so that I have a place when I arrive.

Criteria:
- AC5.1 Given a free desk, when Asha books it, then she sees desk, office, date, part of day, check-in deadline and how to check in, plus one line how release works; the desk leaves everyone's list.
- AC5.2 Given Asha already has an active booking that day, when she tries another, then it is refused with 'You already have a desk that day' and a link to it.
- AC5.6 Given a date beyond the horizon sent by a tampered request, when received, then it is refused as on screen (server-side rules).
- AC5.10 Given a full-day booking, then it occupies morning and afternoon of that desk.
- AC17.3 Given her session expired, when she presses Book, then she signs in again and the page says the booking was not saved.
- NEW(GP) [F5] Given any booking confirmation (one day, several days, booked by a manager), then a 'How check-in works' box shows the deadline, the QR or button, and the 30-minute hold.

Tasks: FE S3 confirmation panel with deadline, how-release-works line and 'How check-in works' box; BE `createBooking`; DB table booking (employee, desk, date, part, status, booked_by, group_id), audited; unique active booking per employee and day; QA rules: horizon, one per day, closed day, tampered request.
Depends on: ST-BK-1.
Open questions: none

#### ST-BK-6 Two people, one desk: just taken, double click, desk blocked a minute ago | 3 | Medium | MVP
Size: concurrency handling on ST-BK-5 = 3. Confidence Medium: needs a database-level guarantee; verified in S5.

As an employee, I want a clear answer when someone else is faster, so that I can pick another desk at once.

Criteria:
- AC5.3 Given Asha and Ravi press Book on the last desk in the same second, then one booking exists and the other sees 'Just taken, here are other free desks'.
- AC5.4 Given Asha double-clicks Book, then only one booking exists.
- AC5.5 Given the desk was blocked a minute ago, when she books, then it is refused with 'desk no longer available'.
- NEW(R21) Given an office closed or a desk retired a moment ago, when she books, then it is refused with the reason.

Tasks: FE 'just taken' state with refreshed list; BE same `createBooking`, unique constraint and conflict answer; DB unique index per desk, date and part; QA parallel booking test (two threads); double click.
Depends on: ST-BK-5.
Open questions: none

#### ST-BK-7 Book for today until the end of the day part | 3 | Medium | MVP
Size: rule change in booking and date picker + interplay with release = 3. Confidence Medium: rule is new; interplay with the release job proven in ST-CI-6.

As an employee who arrives without a desk, I want to book for today even after the release time, so that a released desk is used (decision P1, Q45; this replaces Q36).

Criteria:
- NEW(P1) Given today 10:30 and a desk free for the full day after a release, when she books, then she gets it from now and sees 'check in within 30 minutes'.
- AC4.7 (revised) Given today and the part of the day has ended, when she picks today, then that part is not selectable and the reason is shown.
- AC5.7 (revised) Given a booking for a part of today that has ended, when sent, then it is refused.
- NEW Given a booking made before the release time, then the normal deadline applies.
- NEW Given she books for an afternoon desk at 11:00, then the afternoon deadline applies.

Tasks: FE date picker allows today until the part has ended; message; BE extend `createBooking` and `listFreeDesks`; DB -; QA times around 10:00 and 14:00 in two timezones.
Depends on: ST-BK-5, ST-EN-2, ST-CI-6.
Open questions: none

#### ST-BK-8 Best desk for me | 5 | Medium | MVP
Size: ranking rule with four reasons + re-pick on conflict + reason text on the screen = 5. Confidence Medium: the meaning of 'usual desk' and the order of the reasons are assumed (Q97). Moved from R1 into the MVP at GP (D5).

As an employee, I want the system to propose the best free desk for the day I pick, so that I do not compare desk codes (P4, Q48, D5).

Criteria:
- NEW(P4) [AC19.1] Given a day and part of the day (and optionally zone and features she ticked), when she asks for the best desk, then one free matching desk is proposed.
- NEW(GP) [F4/F5, AC19.1, AC19.6] Given a proposal, then it carries a reason tag, chosen in this order: 'Your usual desk' when it is free, else 'Same zone as usual', else 'Matches your choices', else 'Closest free desk'.
- NEW [AC19.5] Given no desk matches her choices, then the nearest zone or feature options are offered.
- NEW(GP) [F5, AC19.4] Given the proposed desk is taken between the proposal and the booking, then the next desk by the same order is booked and she is told that the desk changed and why; if none is free she is told nobody matched.
- NEW(GP) [F5, AC19.3, AC19.12] Given a proposal, then 'Change' opens the picker for that day (ST-BK-14) and the list stays available for people who want one exact desk.
Moved out (D10): the old criterion 6 [AC19.9] (a reserved desk is never proposed to someone not on the access list) is now in ST-PP-10 (R1); the MVP build has no reserved desks. Criteria 1-5 keep their order; the story has 5 criteria.

Tasks: FE reason tag and zone/feature choices on the booking screens (S2, S3); BE proposal and booking call (`bookBestDesk`, name for the architect; not yet in 05-openapi.yaml); DB -; QA reason order, taken-in-between retry, no match.
Depends on: ST-BK-5, ST-BK-1, ST-BK-6, ST-OS-4, ST-OS-6 (no longer ST-BK-2).
Open questions: Q97 what 'usual desk' means; ties inside a zone are assumed to go to the lowest desk code.

#### ST-BK-9 My bookings list | 3 | High | MVP
Size: list page with paging and statuses on the new table = 3. Confidence High: same shape as the reference 3.

As an employee, I want to see my upcoming bookings and the last 30 days, so that I know where I sit.

Criteria:
- AC6.3 Given she has no bookings, then My bookings says 'No bookings yet' with a Book a desk button.
- AC5.11 Given the booking succeeded, when she opens My bookings, then it is shown within 1 second.
- NEW Given upcoming and past bookings, then rows show date, office, desk, part, status and 'Booked by <manager>' where it applies.
- NEW(P5) Given statuses, then the words are Booked, Checked in, Completed, No-show and Cancelled, used the same on every screen and email.

Tasks: FE S4 list with empty, loading, error states; BE `listMyBookings`; DB -; QA empty; 30-day window; 360 px.
Depends on: ST-BK-5.
Open questions: none

#### ST-BK-10 Cancel my booking | 3 | High | MVP
Size: one action with state rules on the existing table = 3. Confidence High: clear rules.

As an employee, I want to cancel a booking until I check in, so that the desk is free for others.

Criteria:
- AC6.1 Given a booked desk, when Asha cancels, then status is Cancelled, the desk is free in other lists within 5 seconds, and she sees a confirmation.
- AC6.5 Given a cancel request for someone else's booking sent by a tampered request, then it is refused.
- AC6.6 Given the booking was already released by the system, when she presses Cancel on an old page, then she sees its real status instead of an error.
- NEW(D2) Given a checked-in booking, then Cancel is not offered (the day completes).

Moved out (D10): the old criterion 2 [AC6.4] (a booking made by her manager can be cancelled by her) is now in ST-TM-5 (R1); in the MVP nobody else books for her. The ids AC6.5 and AC6.6 keep their names; the story has 4 criteria.

Tasks: FE cancel confirm, status refresh; BE `cancelBooking`; DB -; QA tampered request; stale page; checked-in.
Depends on: ST-BK-9.
Open questions: none

#### ST-BK-11 Today page | 5 | Medium | MVP
Size: new page that gathers bookings, check-in, notes and a count = 5. Confidence Medium: depends on several other stories for its parts.

As an employee, I want one page that shows what matters today, so that I can check in or book in one tap.

Criteria:
- NEW Given bookings, when she opens Today, then the next 3 bookings show with check-in deadline and a Check in button when the window is open.
- NEW Given no booking, then 'No bookings yet' and a Book a desk button show.
- NEW(GP) [F4] Given her home office, then 'Pune tomorrow: N of M desks free' shows, where M counts only bookable desks (not blocked or retired).
- NEW Given the admin and a failed people copy for 2 days, then the warning banner shows (links to ST-PP-6).
- NEW Given loading or error, then a skeleton or a retry shows.

Tasks: FE S1 page replacing the base dashboard cards; BE `getToday`; DB -; QA empty, loaded, error; phone.
Depends on: ST-BK-9, ST-CI-1.
Open questions: none

#### ST-BK-12 After a release: note and rebook | 3 | Medium | MVP
Size: note + link to rebook on existing parts = 3. Confidence Medium: wording must be exact; replaces Q36 answer.

As an employee whose desk was released, I want to see what happened and what I can do, so that I am not stuck (E4).

Criteria:
- AC8.7 (revised) Given Asha opens the app at 10:05 after her booking was released, then she sees the free desks first and a line 'Your desk was released at 10:00 (No-show)'.
- NEW(P1) Given the note, then it says she can book a desk for the rest of today and one tap opens the list.
- NEW Given a released booking, then it shows as No-show in My bookings.

Tasks: FE note on Today and Book a desk; BE `getToday` adds released info; DB -; QA 10:05 case in two timezones.
Depends on: ST-CI-4, ST-BK-7, ST-BK-11.
Open questions: none

#### ST-BK-13 Plan my days: book several days in one action | 5 | Medium | MVP
Size: multi-day request + one proposal per day + per-day result and partial failure = 5. Confidence Medium: partial-failure rule written in Q90 and Q98, not yet in the spec. Added at GP (D5).

As an employee who comes in several days a week, I want to tick my days and book them in one action, so that three days take about four taps (P4, Q90).

Criteria:
- NEW(GP, Q90) [F5] Given she ticks Tue, Wed and Thu within the booking horizon, then each day gets a proposed desk with its reason (ST-BK-8) and 'Book 3 days' makes three separate bookings, each cancellable alone.
- NEW(GP) [F5] Given a day where she already has an active booking, a closed day, a weekend or a day beyond the horizon, then it cannot be ticked.
- NEW(GP) [F5] Given a desk is taken or the day fails between proposal and booking, then the other days stay booked, the failed day is shown with the reason and a new proposal or the picker (ST-BK-14), and nothing is booked twice.
- NEW(GP) [F5] Given the result, then one confirmation lists every day with desk, deadline and the 'How check-in works' box.
- NEW(GP) [F5] Given 14 days ticked, then all are accepted; the 15th is not (horizon).
- NEW(R) Given a tampered request with a day outside the rules, then that day is refused server-side as on screen.

Tasks: FE two-week calendar with ticks, per-day proposal rows, 'Book N days' and result list; BE multi-day booking call (`createBookings`, name for the architect; reuses `createBooking` rules per day; not yet in 05-openapi.yaml); DB -; QA all ok, one day fails, session expires halfway, tampered day, double click.
Depends on: ST-BK-5, ST-BK-6, ST-BK-8.
Open questions: Q98 whether the call is one request with a per-day result or one request per day.

#### ST-BK-14 Change a desk: picker per proposed day | 2 | Medium | MVP
Size: reuse of the free list grouped by zone inside the plan flow = 2. Confidence Medium: depends on how the list is called per day. Added at GP (D5).

As an employee, I want to swap the proposed desk of one day for another I choose, so that people who want an exact desk can have it.

Criteria:
- NEW(GP) [F4/F5] Given a proposed day, when she presses 'Change', then the free desks for that day and part of day show grouped by zone with desk code, floor, zone and features, and the count.
- NEW(GP) [F4/F5] Given she picks a desk, then the proposal for that day becomes that desk with the tag 'Your choice' and other days stay as they were.
- NEW(GP) [F4/F5] Given the picked desk is taken before she books, then she is told and the list refreshes.

Tasks: FE picker panel reused from the S2 list; BE reuses `listFreeDesks`; DB -; QA grouping, taken meanwhile, phone.
Depends on: ST-BK-1, ST-BK-13.
Open questions: none

#### ST-BK-15 Your next two weeks strip with Add day tiles | 3 | Medium | MVP
Size: strip on Today + tiles that open the plan screen with the day ticked = 3. Confidence Medium: shape settled in the prototype. Added at GP (D5) as R1; moved into the MVP at G3 (D6).

As an employee, I want to see my next two weeks on Today with the days I have no desk, so that I add a day in one tap.

Criteria:
- NEW(GP) [F6, AC18.5] Given her bookings, when she opens Today, then a strip shows the next two weeks of working days with desk code and part of day, and an 'Add day' tile on each day without a booking.
- NEW(GP) [F6, AC18.2] Given she taps 'Add day', then the plan screen (ST-BK-13) opens with that day ticked.
- NEW(GP) [F6] Given a closed day or weekend, then it is not shown as a tile.
- NEW Given loading or error, then a skeleton or a retry shows.

Tasks: FE strip and tiles on S1, phone layout; BE extends `getToday`; DB -; QA closed days, phone 360 px.
Depends on: ST-BK-11, ST-BK-13.
Open questions: none

#### ST-BK-16 Your usual desk card on Today | 2 | Medium | R1
Size: one card + the derived usual desk from ST-BK-8 = 2. Confidence Medium: Q97. Added at GP (D5).

As an employee, I want my usual desk offered first when it is free, so that I can sit where I always sit.

Criteria:
- NEW(GP) [F6] Given a usual desk (Q97) that is free on a chosen day, when she opens Today, then a 'Your usual desk' card shows it with a 'Book it' action for the next free day.
- NEW(GP) [F6] Given the usual desk is taken, blocked or retired, then the card says so and offers the proposal of ST-BK-8.
- NEW(GP) [F6] Given no usual desk yet (too few bookings), then no card shows.

Tasks: FE card on S1; BE extends `getToday` with the usual desk; DB -; QA no history, taken, retired.
Depends on: ST-BK-8, ST-BK-11.
Open questions: Q97.

### Epic CI - Check-in and release

#### ST-CI-1 Check in by button | 5 | High | MVP
Size: window rules in office time + idempotent action + status = 5. Confidence High: rules written with examples.

As an employee, I want to press Check in at my desk, so that my booking is kept.

Criteria:
- AC7.1 Given a morning booking and 08:15 local, when Asha presses Check in, then status is Checked in with the time.
- AC7.6 Given before 06:00 or after the check-in deadline, when she presses Check in, then it is refused with the opening time or 'released'.
- AC7.7 Given she presses Check in twice, then she is checked in once.
- AC7.8 Given an afternoon booking at 11:00, then Check in is disabled until 12:00 and says so.
- NEW(P1) Given a booking made after the release time, then the deadline is 30 minutes after booking.

Tasks: FE Check in button on Today and My bookings, disabled reason; BE `checkIn`; DB check-in time on booking; QA window edges 06:00, 12:00, deadline; double press.
Depends on: ST-BK-5, ST-EN-2.
Open questions: none

#### ST-CI-2 Check in by scanning the desk QR | 5 | Medium | R1
Size: QR landing page + sign-in and return + auto check-in = 5. Confidence Medium: phone session length untested (Q37).

As an employee, I want to scan the QR on my desk, so that I am checked in with no clicks.

Criteria:
- AC7.2 Given she scans the QR of her booked desk, when signed in, then she is checked in and sees 'Checked in at BLR-3-14'.
- AC7.3 Given she is not signed in, when she scans, then she is asked to sign in and is then taken back to the desk page.
- NEW(R25) Given the QR, then it holds the desk address only and checks in only the signed-in person's own booking.
- NEW(GP, Q91) [F7] Given she scans the QR of her own booked desk inside the check-in window, then she is checked in at once with no extra tap; the Check in button on Today stays for people who do not scan.
- NEW(Q37) Given a phone, then the company session is reused for 12 hours; if sign-in takes more than 3 taps, check-in is also offered from the reminder email link.

Tasks: FE S5 desk page, return-after-login; BE `checkInByDesk`; DB -; QA real phone test of the sign-in loop.
Depends on: ST-CI-1, ST-OS-14, ST-PP-5.
Open questions: Phone session length must be tested on a real phone before release (Q37).

#### ST-CI-3 QR page: wrong desk and no booking | 3 | Medium | R1
Size: two variants on the desk page = 3. Confidence Medium: 'Move my booking here' is cut (ST-CI-9).

As an employee at the wrong desk, I want to be told clearly, so that I know what to do.

Criteria:
- AC7.4 Given she scans BLR-3-15 but booked BLR-3-14, then she sees 'This is not your desk. Your desk is BLR-3-14' (no move button in this release).
- AC7.5 Given she has no booking and scans a free desk, then she is offered to book it for today if the part of the day has not ended.
- NEW Given an unknown, retired or blocked desk code, then a clear message shows.
- NEW(GP) [F7] Given 'This is not your desk', then the page shows her own desk code, zone and floor (the move button stays Later, ST-CI-9).

Tasks: FE variants on S5; BE `getDeskPage`; DB -; QA three variants.
Depends on: ST-CI-2, ST-BK-7.
Open questions: none

#### ST-CI-4 Release unchecked bookings at the check-in deadline | 5 | Medium | MVP
Size: scheduled job in each office's clock + status + free desk = 5. Confidence Medium: timezone handling carried by ST-EN-2.

As Facilities, I want unused desks returned to the pool, so that others can use them.

Criteria:
- AC8.1 Given a morning booking at Pune not checked in at 10:00 local, when the job runs, then it is No-show by 10:05 and the desk appears free.
- AC8.2 Given an afternoon booking, when 10:00 passes, then it is untouched; at 14:00 plus 5 minutes it is a No-show if not checked in.
- AC8.3 Given a full-day booking not checked in at 10:00, then the whole booking is released, afternoon part included.
- AC8.6 Given Bengaluru and Berlin, when 10:00 arrives in Berlin, then only Berlin bookings are released.
- AC8.8 Given a cancelled booking, then the job ignores it and no email is sent.

Tasks: FE -; BE job `ReleaseBookingsJob` every 5 minutes; DB status values; QA per-office clock cases.
Depends on: ST-BK-5, ST-OS-7, ST-EN-2.
Open questions: none

#### ST-CI-5 Release job survives downtime, repeats and races | 3 | Medium | MVP
Size: catch-up and idempotency on ST-CI-4 = 3. Confidence Medium: race needs a database check.

As Facilities, I want the release to be safe, so that nobody loses a desk by mistake.

Criteria:
- AC8.4 Given a booking checked in at 09:59:58, when the job runs at 10:00, then it stays Checked in.
- AC8.5 Given the job was down from 09:50 to 10:40, when it restarts, then every overdue booking is released once and one email is sent per booking.
- NEW Given the job runs twice in the same minute, then nothing changes the second time.

Tasks: FE -; BE same job, conditional update; DB -; QA kill and restart job; two runs.
Depends on: ST-CI-4.
Open questions: none

#### ST-CI-6 Late booking: check in within 30 minutes or it is released again | 3 | Medium | MVP
Size: second release rule on the same job = 3. Confidence Medium: wording and count of such releases open (Q50).

As Facilities, I want a desk booked after the release to be freed again if nobody comes, so that it does not stay blocked (P1).

Criteria:
- NEW(P1) Given a booking made at 10:20 after the release, when 10:50 passes without check-in, then it is released again.
- NEW Given she checks in at 10:45, then it stays Checked in.
- NEW Given an afternoon booking made at 14:20, then the same 30 minutes apply.
- NEW Given such a release, then it is shown as 'Released after hold' and not counted in the No-show rate (Q50).

Tasks: FE -; BE extend release job with a deadline per booking; DB deadline column on booking; QA boundary at 30 minutes.
Depends on: ST-BK-7, ST-CI-4.
Open questions: Is a late-booking release a no-show? See Q50.

#### ST-CI-7 Running late: keep my desk once | 5 | Low | MVP
Size: one-tap hold + once-per-booking rule + job change + link = 5. Confidence Low: hold length open (Q49); an email link needs sign-in.

As an employee on my way, I want one tap to keep my desk longer, so that I am not recorded as a no-show (P2, Q46).

Criteria:
- NEW(P2) Given a booking not checked in before the deadline, when she taps 'Running late, keep my desk', then the deadline moves to the hold time (11:30 for a 10:00 release) and she sees the new time.
- NEW Given she already used it, then the tap is not offered again for that booking.
- NEW Given the hold ends without check-in, then it is released as 'Released after hold' (Q50).
- NEW Given she taps and then checks in, then status is Checked in.
- NEW Given a release without the tap, then it is a No-show.

Tasks: FE button on Today, My bookings, email link; BE `holdBooking`; DB hold used flag and hold deadline on booking; QA once per booking; email link.
Depends on: ST-CI-4, ST-BK-11.
Open questions: Hold length for afternoon and per office: Q49. What a post-hold release counts as: Q50.

#### ST-CI-8 Mark checked-in bookings Completed at day end | 2 | High | R1
Size: small job and one status = 2. Confidence High: clear.

As Facilities, I want finished days closed, so that reports tell used from unused.

Criteria:
- NEW Given a Checked-in booking, when the office day ends, then status is Completed.
- NEW Given the job runs twice, then nothing changes the second time.
- NEW Given reports, then Completed counts as checked-in.

Tasks: FE -; BE job `CompleteBookingsJob`; DB -; QA end of day in two timezones.
Depends on: ST-CI-1.
Open questions: none

#### ST-CI-9 Move my booking here (scanned desk is free) | 3 | Medium | Later
Size: extra rule on the QR page = 3. Confidence Medium: cut by the critic: cancel and rebook works.

As an employee at a free desk next to mine, I want to move my booking to it, so that I can stay.

Criteria:
- NEW Given she scans a desk free for her day and part, when she presses 'Move my booking here', then her booking moves and the old desk is free.
- NEW Given the desk was taken in between, then it is refused.
- NEW Given a move, then it is in the change history.

Tasks: FE button on S5; BE `moveMyBooking`; DB -; QA race.
Depends on: ST-CI-3.
Open questions: none

#### ST-CI-10 Leave early: Release desk after check-in | 3 | Medium | Later
Size: extra status path = 3. Confidence Medium: cut by the critic (P5, P10).

As an employee leaving early, I want to hand my desk back, so that others can use the rest of the day.

Criteria:
- AC6.2 Given a checked-in booking, then 'Cancel' is replaced by 'Leave early'; using it frees the desk for the rest of the day.
- NEW Given she leaves early, then reports count the day as used.
- NEW Given the word, then it never says 'Release' (P5).

Tasks: FE button; BE `leaveEarly`; DB -; QA afternoon of a full day.
Depends on: ST-CI-1.
Open questions: none

### Epic OS - Offices, desks and Facilities control

#### ST-OS-1 Offices: create, list and edit | 5 | High | MVP
Size: new table + audit + endpoint pair + form = 5. Confidence High: same shape as the reference 5.

As a Facilities admin, I want to create and edit offices, so that people can book in them.

Criteria:
- AC1.1 Given an admin, when she saves a new office with name, city and timezone, then it appears in the office list and the picker.
- AC1.2 Given a missing name, city or timezone, when she saves, then each missing field shows a message and nothing is saved.
- AC1.3 Given an office 'Pune', when she creates 'pune', then it is refused with 'name already used'.
- AC1.6 Given two admins editing the same office, when the second saves, then she sees 'changed by someone else, reload'.
- AC3.7 Given an unknown timezone value, when saved, then it is refused; the timezone is chosen from a list.

Tasks: FE S10 list, S11 settings tab; BE `createOffice`, `updateOffice`, `listOffices`; DB table office (name, city, timezone, state, version), audited; QA duplicate name any case; stale save.
Depends on: ST-EN-1.
Open questions: none

#### ST-OS-2 Office states: Draft, Open, Closed | 3 | High | MVP
Size: state change with rules = 3. Confidence High: decided in Q41.

As a Facilities admin, I want a new office hidden until it is ready, so that employees do not see half-set-up offices.

Criteria:
- AC1.4 Given an office with bookings, when she tries to delete it, then it is refused and 'Close office' is offered.
- NEW(Q41) Given a new office, then its state is Draft and it is not in the employee picker.
- NEW Given she presses 'Open office', then it is visible to employees.
- NEW Given a closed office, then it is hidden from booking; with future bookings it is refused until ST-OS-12 ships.

Tasks: FE state buttons on S10 and S11; BE `openOffice`, `closeOffice`; DB state column; QA state paths.
Depends on: ST-OS-1.
Open questions: none

#### ST-OS-3 Floors: add and retire | 3 | High | MVP
Size: small CRUD on a new table = 3. Confidence High: clear.

As a Facilities admin, I want floors per office, so that desks are grouped.

Criteria:
- AC1.8 Given a floor name already used in that office, when saving, then it is refused.
- NEW Given a new floor name, when saved, then it appears on the Floors tab.
- NEW Given she retires a floor without future bookings, then its desks are hidden from booking; with future bookings it is refused until ST-OS-12 ships.

Tasks: FE Floors tab; BE `createFloor`, `retireFloor`; DB table floor, audited; QA duplicate name.
Depends on: ST-OS-1.
Open questions: none

#### ST-OS-4 Zones per floor | 3 | High | MVP
Size: small CRUD + default = 3. Confidence High: decided in Q42.

As a Facilities admin, I want a zone list per floor, so that zone names are spelled once.

Criteria:
- AC2.4 (revised) Given a new floor, then zone 'Main' exists and a desk with no zone gets 'Main'.
- NEW(Q42) Given an admin, when she adds or renames a zone, then desks pick zones from this list only.
- NEW Given a zone with desks, then it cannot be deleted.
- NEW Given a zone name already used on that floor, then it is refused.

Tasks: FE zone list on Floors tab; BE `createZone`, `renameZone`; DB table zone, audited; QA duplicate; delete with desks.
Depends on: ST-OS-3.
Open questions: none

#### ST-OS-5 Desks: create, edit and retire | 5 | Medium | MVP
Size: new table + relations + audit + form = 5. Confidence Medium: relations to floor, zone and features.

As a Facilities admin, I want to create and edit desks, so that they can be booked.

Criteria:
- AC2.1 Given an admin, when she creates a desk with code, floor, zone and two features, then it is listed on that floor and bookable from tomorrow's list on.
- AC2.2 Given a code already used anywhere, when she saves, then it is refused with 'code already used'.
- AC2.3 Given a desk with bookings, when she edits its code, then the field is read-only.
- AC2.9 Given a retired desk, when an employee searches, then it is not listed; history stays in reports. With future bookings, retiring is refused until ST-OS-11 ships.
- NEW Given a desk list of 1,500 desks, then it is paged and searchable.

Tasks: FE S11 Desks tab, S12 dialog; BE `createDesk`, `updateDesk`, `retireDesk`; DB table desk, desk_feature link, audited; QA code unique; read-only after booking.
Depends on: ST-OS-4, ST-OS-6.
Open questions: none

#### ST-OS-6 Desk features list | 2 | High | MVP
Size: small list on a new table = 2. Confidence High: clear.

As a Facilities admin, I want to keep the list of desk features, so that filters use the same words.

Criteria:
- NEW Given a new product, then monitor, docking station and standing desk exist.
- NEW Given an admin adds a feature, then it can be chosen on desks.
- NEW Given a feature used by desks, then it cannot be deleted.

Tasks: FE small list screen; BE `listFeatures`, `createFeature`; DB table feature, audited; QA delete refused.
Depends on: ST-OS-1.
Open questions: none

#### ST-OS-7 Office settings: release times, midday and working days | 5 | High | MVP
Size: form with cross-field rules and next-day effect = 5. Confidence High: rules written with examples.

As a Facilities admin, I want to set release times per office, so that the rule fits each site.

Criteria:
- AC3.1 Given a new office, then it has release times 10:00 and 14:00, midday 13:00 and working days Monday-Friday.
- AC3.2 Given an afternoon release of 09:00 with a morning release of 10:00, when saved, then it is refused with an explanation.
- AC3.3 Given the morning release is changed at 09:30 to 09:45, when saved, then today's release stays and tomorrow's is 09:45.
- NEW Given working days, then she can choose any set of weekdays.
- NEW Given a change, then it is in the change history.

Tasks: FE S11 Settings tab; BE `updateOfficeSettings`; DB release and midday columns; QA cross-field rules; next-day effect.
Depends on: ST-OS-1.
Open questions: none

#### ST-OS-8 Closed days | 3 | High | MVP
Size: calendar list + effect on the date picker = 3. Confidence High: clear.

As a Facilities admin, I want to mark public holidays, so that nobody books them.

Criteria:
- AC3.4 Given 26 Jan is a closed day, when an employee picks that date, then it is greyed out with 'Office closed'.
- NEW Given a closed day with no bookings, when saved, then it is stored; with bookings it is refused until ST-OS-12 ships.
- NEW Given she removes a closed day, then the date is bookable again.
- NEW(R12) Given a non-working day, then it is greyed out too.

Tasks: FE S11 Calendar tab; BE `addClosedDay`, `removeClosedDay`; DB table closed_day, audited; QA date picker.
Depends on: ST-OS-7.
Open questions: none

#### ST-OS-9 Company booking horizon setting | 2 | High | MVP
Size: one number on a new Settings tab = 2. Confidence High: clear.

As a Facilities admin, I want to set how many days ahead one can book, so that the limit fits the company.

Criteria:
- NEW Given the tab 'Booking rules', then the default is 14 days.
- NEW Given a value that is not a whole number of at least 1, when saved, then it is refused.
- NEW Given a saved value, then the next search uses it.

Tasks: FE S19 Settings tab; BE `getBookingRules`, `updateBookingRules`; DB uses base settings storage; QA validation.
Depends on: ST-EN-1.
Open questions: none

#### ST-OS-10 Block a desk for dates | 5 | Medium | R1
Size: new table + overlap rule + screens = 5. Confidence Medium: overlap rules.

As a Facilities admin, I want to block a desk for maintenance, so that nobody books it.

Criteria:
- AC2.5 Given a block from 3 to 5 Nov with no bookings, when saved, then the desk is missing from the free list for those days.
- AC2.7 Given a block with a past start date, when saved, then it is refused.
- AC2.8 Given a block, when the admin removes it, then the desk is bookable again for the freed days; cancelled bookings are not restored.
- AC2.11 Given two admins blocking the same desk and dates, when the second saves, then she sees the existing block.
- AC12.3 Given two blocked desks on a day, then capacity for that day is reduced by two. Moved from ST-RP-3 c1 (D10).

Tasks: FE S14 dialog, Blocks tab; BE `createBlock`, `removeBlock`; DB table desk_block, audited; QA overlap.
Depends on: ST-OS-5.
Open questions: none

#### ST-OS-11 A block that hits bookings: confirm, cancel, tell | 5 | Medium | R1
Size: count + confirm + bulk cancel + race = 5. Confidence Medium: race between count and confirm.

As a Facilities admin, I want to see how many bookings a block cancels, so that I decide with the facts.

Criteria:
- AC2.6 Given a block whose dates contain 2 bookings, when saved, then she first sees '2 bookings will be cancelled' with no names, confirms, and both bookings are cancelled with the people emailed.
- NEW Given no bookings, then no confirmation is asked.
- NEW Given a booking made while she confirms, then the count is checked again and she confirms again.
- NEW Given cancelled bookings, then status is 'Cancelled by system' with reason Maintenance.

Tasks: FE count in dialog; BE `createBlock` with confirm token; DB -; QA race.
Depends on: ST-OS-10, ST-NT-5.
Open questions: none

#### ST-OS-12 Same rule for closing an office or floor and adding a closed day | 3 | Medium | R1
Size: reuse of ST-OS-11 rule = 3. Confidence Medium: reuse.

As a Facilities admin, I want the same warning for closures, so that nothing is cancelled silently.

Criteria:
- AC1.9 Given a floor with desks, when she retires it, then its desks are hidden and future bookings follow the blocking rule.
- AC3.5 Given a closed day on a date with bookings, when saved, then the blocking rule applies.
- NEW Given she closes an office with future bookings, then she sees the count, confirms, and the bookings are cancelled with emails.
- NEW Given the interim refusals of ST-OS-2, ST-OS-3, ST-OS-5 and ST-OS-8, then they are replaced by this rule.

Tasks: FE same dialog; BE reuse `createBlock` rule engine; DB -; QA four entry points.
Depends on: ST-OS-11, ST-OS-3, ST-OS-8.
Open questions: none

#### ST-OS-13 Desk CSV import | 5 | Medium | R1
Size: upload + preview + per-row rules = 5. Confidence Medium: file limits open.

As a Facilities admin, I want to import desks from a file, so that 1,500 desks do not take days.

Criteria:
- AC2.10 Given a CSV of desks, when she imports, then valid rows are created and invalid rows are listed with line number and reason; no row is half-saved.
- NEW(Q42) Given an unknown floor or zone, then that row fails.
- NEW Given an empty file or wrong columns, then the file is refused with a message.
- NEW Given 1,500 rows, then the import finishes in under 30 seconds.

Tasks: FE S13 dialog with preview; BE `importDesks`; DB -; QA bad rows; big file.
Depends on: ST-OS-5.
Open questions: none

#### ST-OS-14 QR print sheet per floor | 5 | Medium | R1
Size: QR generation + print layout = 5. Confidence Medium: QR library not in the base.

As a Facilities admin, I want to print the QR codes per desk, so that employees can check in by scanning (Q40).

Criteria:
- NEW Given a floor, when she opens the print sheet, then an A4 grid shows each desk code and its QR.
- NEW(R25) Given a QR, then it holds the desk address only.
- NEW Given she prints, then the page prints without menus.
- NEW Given a floor with no desks, then an empty state shows.

Tasks: FE S15 print page; BE `getQrSheet`; DB -; QA print preview.
Depends on: ST-OS-5.
Open questions: none

#### ST-OS-15 Admin cancels a booking with a reason | 5 | Medium | R1
Size: action + reason + history + permission = 5. Confidence Medium: name display open (Q52).

As a Facilities admin, I want to cancel a booking that is wrong, so that I fix one-off problems without a developer (P8).

Criteria:
- NEW(P8) Given a desk and day, when she opens 'Cancel booking', then she sees who holds it only inside this action.
- NEW Given she confirms, then a reason is required and saved in the change history.
- NEW Given a cancelled booking, then the person is emailed.
- NEW Given a non-admin, then the action is refused (also by a tampered request).

Tasks: FE action dialog; BE `adminCancelBooking`; DB reason on history; QA permission.
Depends on: ST-BK-5, ST-NT-5.
Open questions: Showing a name conflicts with 'admin never sees who sits where by name': Q52.

#### ST-OS-16 Admin moves a booking to another free desk | 3 | Medium | R1
Size: extension of ST-OS-15 = 3. Confidence Medium: reuse.

As a Facilities admin, I want to move a booking, so that a broken desk is not a problem (P8).

Criteria:
- NEW(P8) Given a booking, when she picks another desk free for the same day and part, then it moves.
- NEW Given the move, then a reason is required and saved in history, and the person is emailed.
- NEW Given the desk was taken in between, then it is refused.

Tasks: FE move dialog; BE `adminMoveBooking`; DB -; QA race.
Depends on: ST-OS-15.
Open questions: none

### Epic PP - People, roles and access

#### ST-PP-1 Nightly copy of people from SuccessFactors | 5 | Low | MVP
Size: one external read + sync run table + skip rules (the base gives paging and connection) = 5. Confidence Low: the base mapping may lack manager and home office (Q54).

As the system, I want a nightly read-only copy of people, so that sign-in, offices and active flags are current.

Criteria:
- AC14.1 Given 3,000 employees, then the run finishes in under 10 minutes and shows counts of new, changed and left.
- AC14.2 Given SuccessFactors does not answer, then the last copy is kept, the run is marked failed, and the date of the last good copy is shown.
- AC14.6 Given a new employee, then she can sign in and book from that day on.
- NEW(R49) Given a failure, then the sync retries every hour for the rest of the day.
- NEW Given a record without an email, then it is skipped and counted.

Tasks: FE -; BE job `PeopleSyncJob` on the base job framework; DB table sync_run, employee fields home office, manager; QA failure paths.
Depends on: ST-EN-1.
Open questions: Does the base user sync already keep manager and home office? Q54.

#### ST-PP-2 Direct manager and manager status | 3 | Medium | MVP
Size: mapping + derived flag = 3. Confidence Medium: depends on the answer in Q54.

As the system, I want to know each person's manager, so that team views and manager rights are correct.

Criteria:
- AC14.4 Given Ravi's manager changes, when the next sync completes, then Meera's team view no longer shows him and the new manager's does.
- NEW(R52) Given a person who is manager of at least one active employee, then she has manager status.
- NEW Given a person with no active reports, then she has no manager status.
- NEW Given a manager change, then bookings stay with the employee.

Tasks: FE -; BE extend sync; `getManagerStatus`; DB manager column; QA change cases.
Depends on: ST-PP-1.
Open questions: none

#### ST-PP-3 Leavers: future bookings cancelled silently | 3 | Medium | MVP
Size: cleanup in the sync = 3. Confidence Medium: clear.

As the system, I want leavers' desks freed, so that nobody holds a desk for someone who left.

Criteria:
- AC14.5 Given an employee leaves, when the sync completes, then her future bookings are cancelled and the desks become free.
- AC5.9 Given an inactive employee, then she cannot book.
- NEW(G7) Given such a cancellation, then no email is sent.

Tasks: FE -; BE step in sync; DB -; QA leaver with and without bookings.
Depends on: ST-PP-1, ST-BK-10.
Open questions: none

#### ST-PP-4 Profile not ready for people missing from the copy | 2 | High | MVP
Size: one check and message = 2. Confidence High: decided in G18.

As a new hire, I want to know why I cannot book yet, so that I can ask for help (P7).

Criteria:
- AC5.8 Given Asha is signed in and the copy has no record of her, when she books, then she sees 'Your profile is not ready yet' with the date of the last copy, and nothing is saved.
- NEW Given the same person, then she can still open Today and My bookings.
- NEW Given the next copy has her, then she can book without any other step.

Tasks: FE S6 message; BE check in `createBooking`; DB -; QA new hire case.
Depends on: ST-BK-5, ST-PP-1.
Open questions: none

#### ST-PP-5 Roles and access checks, No access page | 3 | Medium | MVP
Size: role mapping + guards on every call + page = 3. Confidence Medium: base roles are assumed (A2).

As the product, I want every call checked by role on the server, so that nobody sees what they must not.

Criteria:
- AC17.1 Given a person not signed in, when she opens any page, then she is sent to company sign-in and back.
- AC17.2 Given a signed-in person without a DeskBook role, then she sees 'No access'.
- AC17.4 Given any page, then data a role may not see is not in the answer sent to the browser.
- AC1.5 Given an employee or manager, when she opens office setup by menu or link, then the entry is absent and the link is refused.
- AC12.10 Given an employee or manager opens reports by link, then it is refused.

Tasks: FE S6 pages, menu rules; BE role guards on all endpoints; DB -; QA role matrix across endpoints.
Depends on: ST-EN-1.
Open questions: none

#### ST-PP-6 People sync status page | 3 | High | R1
Size: read-only admin tab = 3. Confidence High: clear.

As a Facilities admin, I want to see the state of the people copy, so that I can answer 'my team is wrong'.

Criteria:
- AC14.3 Given 2 days without a good copy, then the admin sees a warning banner.
- AC14.7 Given a record without an email, then it is listed on the sync page.
- NEW Given the tab, then last good copy, last run result and counts of new, changed and left show.
- NEW Given no sync has run, then 'No sync yet' shows.

Tasks: FE S18 Settings tab; BE `getSyncStatus`; DB -; QA failed run; banner.
Depends on: ST-PP-1.
Open questions: none

#### ST-PP-7 Run sync now | 2 | High | R1
Size: button calling the base ad hoc job = 2. Confidence High: decided in Q43.

As a Facilities admin, I want to start the sync myself, so that a wrong team is fixed at once.

Criteria:
- AC14.8 Given two syncs would overlap, then the second is skipped.
- NEW(Q43) Given the admin presses 'Run sync now', then a run starts and the page shows the result.
- NEW Given a non-admin, then it is refused.

Tasks: FE button; BE `runSyncNow`; DB -; QA overlap.
Depends on: ST-PP-6.
Open questions: none

#### ST-PP-8 Admin adds a person now | 3 | Medium | R1
Size: small form on the employee table = 3. Confidence Medium: matching with the nightly copy open (Q60).

As a Facilities admin, I want to add a new hire before the nightly copy, so that she can book on day one (P7).

Criteria:
- NEW(P7) Given name, email and home office, when the admin saves, then the person can book at once.
- NEW Given a duplicate email, then it is refused.
- NEW Given the next copy has her, then it matches by email and fills the manager.
- NEW Given the action, then it is in the change history.

Tasks: FE Add person dialog; BE `addPerson`; DB source flag on employee; QA match by email.
Depends on: ST-PP-1.
Open questions: How the manual record meets the nightly record: Q60.

#### ST-PP-9 Access list for reserved desks | 5 | High | R1
Size: new table + page + audit = 5. Confidence High: decided in G11.

As a Facilities admin, I want to keep who may book reserved desks, so that accessibility needs are met without health data.

Criteria:
- AC16.3 Given Ravi is removed from the list, then existing bookings stay and new ones are refused.
- AC16.4 Given the access-list page, then it has no free-text reason field.
- AC16.5 Given a manager or employee opens the list by link, then it is refused.
- NEW Given an admin, when she searches a name and adds it, then the person is listed.
- NEW(R55) Given any add or remove, then it is in the change history.

Tasks: FE S16 page; BE `listAccess`, `addAccess`, `removeAccess`; DB table access_list_entry, audited; QA no reason field.
Depends on: ST-EN-1.
Open questions: none

#### ST-PP-10 Reserved desks only for people on the list | 3 | Medium | R1
Size: visibility rule in search and booking = 3. Confidence Medium: touches ST-BK-1 and ST-BK-5.

As an employee on the list, I want to see and book reserved desks, so that I have the desk I need.

Criteria:
- AC16.1 Given desk BLR-3-02 is flagged and Asha is not on the list, then she cannot see or book it.
- AC16.2 Given Ravi is on the list, then the desk is listed for him and he books it like any other.
- AC4.9 Given an employee not on the list, then reserved desks are neither listed nor counted for her.
- NEW Given a desk flag change, then it is recorded in history.
- NEW [AC19.9] Given a reserved desk, then it is never proposed to someone not on the access list. Moved from ST-BK-8 c6 (D10).
- AC16.6 Given a flagged reserved desk, then reports count it as capacity as normal. Moved from ST-RP-3 c3 (D10).

Tasks: FE flag field on desk dialog; BE filter in `listFreeDesks` and `createBooking`; DB flag on desk; QA tampered booking of a reserved desk.
Depends on: ST-PP-9, ST-BK-1.
Open questions: none

### Epic NT - Notifications

#### ST-NT-1 Enabler: send an email once, retry, log | 5 | Low | MVP
Size: mail send + log table + retry + once-per-event = 5. Confidence Low: the base has no mail service in the spec (Q53).

As the product, I want one reliable way to send email, so that every message is sent once and never blocks a booking.

Criteria:
- AC13.6 Given the mail service is down, then bookings still work and the email is retried 3 times over 1 hour, then logged as failed.
- NEW(R46) Given an event, then each message is sent once (event key).
- NEW(R47) Given any message, then texts are translatable, English only in this release, and name no other employee.
- NEW Given a failed send, then the admin can see it in the log.

Tasks: FE -; BE `MailService`, retry job; DB table notification_log; QA retry; duplicate prevention.
Depends on: none.
Open questions: Is there a mail sender in the base or TTCommon? Q53.

#### ST-NT-2 Reminder 15 minutes before the deadline | 3 | Medium | MVP
Size: job + one message + link = 3. Confidence Medium: depends on the link in ST-CI-7.

As an employee, I want a warning before my desk is released, so that I can act (P2).

Criteria:
- NEW(P2) Given a booking not checked in 15 minutes before its deadline, then she gets one email 'check in or your desk is released' with a check-in link and the keep-my-desk link.
- NEW Given she checked in or cancelled, then no email is sent.
- NEW Given the job runs twice, then one email per booking.

Tasks: FE -; BE job `PreReleaseReminderJob`; DB -; QA timing in two timezones.
Depends on: ST-NT-1, ST-CI-7.
Open questions: none

#### ST-NT-3 Email when a booking was released | 2 | High | MVP
Size: one message on an event = 2. Confidence High: clear.

As an employee, I want to know my desk was released, so that I can rebook.

Criteria:
- AC13.3 Given a booking released at 10:00, then Asha gets one email 'Your desk was released'.
- NEW Given the email, then it says No-show and how to book a desk for today (P1).
- NEW Given a catch-up run, then one email per booking.

Tasks: FE -; BE template + send; DB -; QA once per booking.
Depends on: ST-NT-1, ST-CI-4.
Open questions: none

#### ST-NT-4 Evening reminder the day before | 5 | Medium | R1
Size: job per timezone + working-day rule + message = 5. Confidence Medium: time zones and weekends.

As an employee, I want a reminder the evening before, so that I remember to go in.

Criteria:
- AC13.1 Given a booking for Tuesday, when it is Monday 18:00 in Pune, then she gets one reminder with desk, office, release time.
- AC13.2 Given the booking was cancelled before 18:00, then no reminder is sent.
- AC13.7 Given the reminder job runs twice, then no duplicate is sent.
- AC13.8 Given a Friday booking, then the reminder goes on Thursday evening and not on weekends.
- NEW Given the email, then it has a one-line how-release-works note.

Tasks: FE -; BE job `EveningReminderJob`; DB -; QA weekend and holiday cases.
Depends on: ST-NT-1, ST-EN-2.
Open questions: none

#### ST-NT-5 Email when a block, closure or Facilities action cancels or moves a booking | 2 | High | R1
Size: templates on existing events = 2. Confidence High: clear.

As an employee, I want to hear when my booking is cancelled or moved for me, so that I find another desk.

Criteria:
- AC13.5 Given a desk block cancels 2 bookings, then both people get one email each offering to find another desk.
- NEW(P8) Given an admin cancels or moves a booking, then the person gets one email with the reason.
- NEW Given a leaver, then no email is sent.

Tasks: FE -; BE templates; DB -; QA block, closure, admin action.
Depends on: ST-NT-1.
Open questions: none

#### ST-NT-6 Email when a manager books or cancels for you | 2 | High | R1
Size: templates on existing events = 2. Confidence High: clear.

As an employee, I want an email when my manager books or cancels a desk for me, so that I know.

Criteria:
- AC13.4 Given Meera books for Ravi, then Ravi gets one email.
- NEW Given Meera cancels it, then Ravi gets one email.
- NEW(R47) Given either email, then it names the manager and no other employee.

Tasks: FE -; BE templates; DB -; QA both events.
Depends on: ST-NT-1.
Open questions: none

#### ST-NT-7 No-show reminder after three in a month | 3 | Medium | Later
Size: monthly count + one message = 3. Confidence Medium: waits for Legal; see Q51.

As an employee, I want a friendly note after three no-shows, so that I can change my habits.

Criteria:
- AC15.1 Given Ravi's third No-show in October, then he gets one reminder; a fourth sends nothing more.
- AC15.2 Given his first No-show in November, then the count starts at one.
- AC15.5 Given any No-show count, then it never blocks a booking.

Tasks: FE -; BE monthly counter and send; DB counter; QA month boundary.
Depends on: ST-NT-1, ST-CI-4.
Open questions: Q47 says the employee gets this reminder; P10 moves it later: Q51.

### Epic RP - Reports

#### ST-RP-1 Occupancy per office, floor and day | 5 | Medium | MVP
Size: aggregation query + filters + counts-only rule = 5. Confidence Medium: capacity rules in ST-RP-3.

As a Facilities admin, I want occupancy per office, floor and day, so that I see real usage.

Criteria:
- AC12.2 Given a date range of 1 to 31 Oct, when she picks office Pune, then rows per day and floor appear with totals.
- AC12.7 Given no data in the range, then she sees 'No bookings in this period' and export is disabled.
- NEW(R39) Given any report, then it shows counts and rates only, never names.
- NEW(R42) Given days, then they follow each office's own timezone.
- NEW Given a booking, then booked and checked-in counts show per floor and day.
- NEW(GP) [F12] Given the table (B's occupancy table, kept under the heat grid), then each day has a total row and each row a 'used' bar (checked in as a share of capacity).

Tasks: FE S17 filters and table with day totals and used bar; BE `getOccupancyReport`; DB report indexes; QA timezone days.
Depends on: ST-BK-5, ST-EN-2.
Open questions: none

#### ST-RP-2 No-show rate | 3 | High | MVP
Size: rate definition on the same query = 3. Confidence High: defined in G10.

As a Facilities admin, I want the no-show rate, so that I know how many desks go unused.

Criteria:
- AC12.1 Given Pune has 60 bookable desks and on Monday 42 booked, 35 checked in, 7 released, then capacity 60, booked 42, checked-in 35 and no-show rate 7/42 = 16.7 %.
- AC12.5 Given a booking cancelled before the release time, then it is not a No-show and not booked at release.
- NEW Given 'Released after hold' bookings, then they are a separate line, not in the rate (Q50).

Tasks: FE rate column; BE extend report; DB -; QA worked example.
Depends on: ST-RP-1, ST-CI-4.
Open questions: none

#### ST-RP-3 Capacity rules: blocked and retired desks, half days | 3 | Medium | MVP
Size: definition rules in the query = 3. Confidence Medium: definitions in G10.

As a Facilities admin, I want capacity to count bookable desks only, so that rates are honest.

Criteria:
- AC12.4 Given a half-day booking, then booked counts 0.5 and capacity is in desk-days.
- NEW Given a retired desk, then it is not capacity.

Moved out (D10): the old criterion 1 [AC12.3] (two blocked desks reduce the capacity by two) is now in ST-OS-10 (R1), and the old criterion 3 [AC16.6] (a flagged reserved desk counts as capacity as normal) is now in ST-PP-10 (R1); the MVP build has neither blocks nor reserved desks. The story has 2 criteria.

Tasks: FE -; BE extend report; DB -; QA worked examples.
Depends on: ST-RP-1, ST-OS-5.
Open questions: none

#### ST-RP-4 Excel export | 5 | Medium | MVP
Size: file generation + limit + same rows as screen = 5. Confidence Medium: no Excel library known in the base.

As a Facilities admin, I want to export the report to Excel, so that I use it in the space plan.

Criteria:
- AC12.8 Given an export of 30,000 rows, when she presses Export, then she gets an Excel file with the same rows and columns as the screen within 30 seconds.
- AC12.9 Given more than 100,000 rows, then export is refused with 'Narrow the dates or office'.
- AC12.11 Given an export file, then it contains no employee names or ids.
- NEW Given an empty range, then the export button is disabled.

Tasks: FE Export button; BE `exportReport`; DB -; QA 30,000 rows; over limit.
Depends on: ST-RP-1.
Open questions: none

#### ST-RP-5 Speed and load check at 500 users | 5 | Low | R1
Size: load test + indexes + tuning = 5. Confidence Low: numbers are proposals (A14); tuning effort unknown.

As the product owner, I want proof that Monday 08:00 works, so that the first morning is not a failure.

Criteria:
- AC12.12 Given a 3-month range for all offices, then the report shows in under 5 seconds.
- NEW(A14) Given 500 users at once, then booking answers in under 1 second for 95 % of requests.
- NEW Given 500 users with the list open, then polling (5 s) keeps pages under 2 seconds.
- NEW Given the load test, then the result is written down with the volumes used.

Tasks: FE -; BE indexes, caching where needed; DB indexes; QA load test script.
Depends on: ST-BK-3, ST-RP-1.
Open questions: none

#### ST-RP-6 Record search results for the success number | 5 | Medium | R1
Size: new log table + weekly measure = 5. Confidence Medium: what is stored (Q59).

As the product owner, I want to measure '90 % get a desk' per office, so that success is real (Q1, G23, P9).

Criteria:
- NEW Given a search, then its outcome (office, day, part, zone, free count, time) is stored with no person.
- NEW Given a week, then the share of searches that found a desk shows per office.
- NEW Given a search that found nothing, then it counts as a miss.
- NEW Given the log, then it is kept 2 years.

Tasks: FE share on S17; BE `logSearch`, `getSuccessShare`; DB table search_log; QA measure on sample data.
Depends on: ST-BK-1.
Open questions: Q59.

#### ST-RP-7 Busiest days (top 5) | 3 | High | R2
Size: one more report query = 3. Confidence High: defined in AC12.6.

As a Facilities admin, I want the busiest days, so that I plan space (cut from release 1 by the critic).

Criteria:
- AC12.6 Given a range, then the top 5 days by checked-in share of capacity are listed.
- NEW Given a tie, then the earlier date comes first.
- NEW Given no data, then 'No bookings in this period'.

Tasks: FE section on S17; BE `getBusiestDays`; DB -; QA tie.
Depends on: ST-RP-1.
Open questions: none

#### ST-RP-8 Desk use per week and zone; days with no desk found | 3 | Medium | R2
Size: two more views on existing data = 3. Confidence Medium: needs ST-RP-6 data.

As a Facilities admin, I want weekly use per office and the days people found nothing (A18, P9), so that the real pain shows.

Criteria:
- NEW Given a range, then weekly desk use per office shows.
- NEW Given searches that found nothing, then counts per weekday and per zone show.
- NEW Given any view, then it shows counts only.

Tasks: FE two views; BE `getWeeklyUse`, `getMissedSearches`; DB -; QA sample data.
Depends on: ST-RP-6.
Open questions: none

#### ST-RP-9 Anonymise old booking data after 2 years | 5 | Medium | R2
Size: job + data rule + report stability = 5. Confidence Medium: must ship before month 24.

As the company, I want names removed from old bookings, so that we keep personal data only 2 years (G8).

Criteria:
- NEW(G8) Given a booking older than 2 years, then the person link is removed and counts stay.
- AC12.13 Given the report is opened during the nightly run, then numbers are the same as before and after.
- NEW Given the job runs twice, then nothing changes the second time.

Tasks: FE -; BE job `AnonymiseJob`; DB -; QA numbers before and after.
Depends on: ST-BK-5, ST-RP-1.
Open questions: none

#### ST-RP-10 Occupancy heat grid by zone and day | 5 | Medium | R1
Size: zone-by-day aggregation + heat grid with two line styles + keyboard and text alternative = 5. Confidence Medium: the report today stops at floor (Q99). Added at GP (D5); the table of ST-RP-1 stays under the grid.

As a Facilities admin, I want zones by day shown as a heat grid, so that I see where the building is full at a glance.

Criteria:
- NEW(GP) [F12] Given an office and a week, then a grid of zones (rows) by days (columns) shows; darker means fuller.
- NEW(GP) [F12] Given a past day, then the cell shows the checked-in share with a solid edge; given a day still to come, then it shows the booked share with a dashed edge.
- NEW(GP) [F12] Given a cell, then its numbers (booked, checked in, capacity) show as text on focus or hover; colour is never the only signal (WCAG 2.1 AA).
- NEW(R39) Given the grid, then it shows counts and shares only, never names.
- NEW(R42) Given days, then they follow the office's own timezone, and blocked or retired desks leave the capacity (as ST-RP-3).

Tasks: FE heat grid above the table on S17; BE extends `getOccupancyReport` with a zone level (or a new zone view; Q99); DB report index by zone; QA past and future cells, empty zone, timezone, keyboard.
Depends on: ST-RP-1, ST-RP-3, ST-OS-4.
Open questions: Q99 whether the zone level goes into the existing report call.

### Epic TM - Team and manager

#### ST-TM-1 Team week for direct reports | 5 | Medium | R1
Size: grid read model + permission + volume = 5. Confidence Medium: grid and permission rules.

As a manager, I want to see my direct reports' week, so that I know who is in (no no-show counts here, Q47).

Criteria:
- AC9.1 Given Meera has 6 direct reports, when she opens Team for this week, then she sees 6 rows by 5 working days with each booking.
- AC9.2 Given a report has no booking on a day, then the cell is empty.
- AC9.5 Given an employee without reports, when she opens the Team link directly, then it is refused.
- AC9.6 Given her team changed in last night's copy, then today's view shows the new team.
- AC9.8 Given 40 direct reports, then the week loads in under 2 seconds.
- NEW(GP) [F9] Given a day, then an 'In the office' row on top shows how many of her reports have a booking that day (for example 4 of 6) with their initials.
- NEW(GP, Q89) [F9] Given a past day, then only desks that were used show; a booking that ended as a no-show looks like an empty cell (no per-person no-show data, D2).

Tasks: FE S7 grid with 'In the office' row; BE `getTeamWeek`; DB -; QA 40 rows; tampered request.
Depends on: ST-BK-9, ST-PP-2, ST-PP-5.
Open questions: none

#### ST-TM-2 Team week: other weeks, office filter, other-office cells | 2 | High | R1
Size: small additions to the grid = 2. Confidence High: clear.

As a manager, I want to move between weeks and filter, so that I plan ahead.

Criteria:
- AC9.3 Given she moves to next or last week, then the view changes; past weeks show Checked in and No-show.
- AC9.7 Given a filter by office, then only bookings in that office show.
- AC9.9 Given a report booked in another office, then the cell shows that office name.

Tasks: FE arrows, filter; BE extend `getTeamWeek`; DB -; QA week edges.
Depends on: ST-TM-1.
Open questions: none

#### ST-TM-3 Team on a phone: one day at a time | 3 | Medium | R1
Size: second layout of the same data = 3. Confidence Medium: decided in Q38.

As a manager on a phone, I want a day list, so that I can read it at 360 px.

Criteria:
- NEW(Q38) Given 360 px, when she opens Team, then one day shows as a list of people.
- NEW Given day arrows, then she moves between days.
- NEW Given touch, then targets are at least 44 px.

Tasks: FE phone layout; BE -; DB -; QA 360 px.
Depends on: ST-TM-1.
Open questions: none

#### ST-TM-4 Team menu only for managers | 2 | High | R1
Size: menu rule + message = 2. Confidence High: decided in Q39.

As an employee without reports, I want no empty Team entry, so that the menu stays short.

Criteria:
- AC9.4 (revised) Given a manager with no direct reports opens the Team link directly, then she sees 'No direct reports found' with the date of the last people update; the menu entry is hidden.
- NEW(R52) Given an active direct report, then the Team entry shows.
- NEW Given a change of manager status in the next copy, then the menu follows.

Tasks: FE menu rule; BE uses manager status; DB -; QA both cases.
Depends on: ST-TM-1.
Open questions: none

#### ST-TM-5 Book for a direct report | 5 | Medium | R1
Size: dialog + rules + permission + email trigger = 5. Confidence Medium: reuses ST-BK-5.

As a manager, I want to book a desk for a direct report, so that the team can sit together.

Criteria:
- AC10.1 Given Ravi has no booking on Tuesday, when Meera books BLR-3-14 for him, then it exists, he is emailed and sees 'Booked by Meera'.
- AC10.2 Given Ravi already has a booking that day, then Meera is refused and nothing is replaced.
- AC10.3 Given a person who is not a direct report, also by a tampered request, then it is refused.
- AC10.4 Given Meera and Ravi book at the same moment, then one booking exists and the other sees 'already booked'.
- AC6.4 Given a booking made by her manager, when she cancels it, then it is cancelled and the manager sees the new status. Moved from ST-BK-10 c2 (D10).
- NEW(GP) [F10] Given an empty future day, when Meera opens 'Book for', then the dialog proposes a free desk in the zone where most of her reports sit that day, with the reason shown, and she can change it.

Tasks: FE S8 dialog with proposed desk; BE `createBookingForReport`; DB -; QA tampered; race.
Depends on: ST-TM-1, ST-BK-5, ST-NT-6.
Open questions: none

#### ST-TM-6 Manager cancels a report's booking | 3 | High | R1
Size: one action with rules = 3. Confidence High: clear.

As a manager, I want to cancel a report's booking, so that the desk is free (A11).

Criteria:
- AC10.5 Given Meera cancels Ravi's booking, then he is emailed and sees 'Cancelled by manager'.
- AC10.6 Given Ravi checked in already, then Meera cannot cancel it.
- NEW Given a non-report, then it is refused.

Tasks: FE cell action; BE `cancelBookingForReport`; DB -; QA checked-in case.
Depends on: ST-TM-5.
Open questions: none

#### ST-TM-7 Managers of managers see everyone below | 5 | Medium | R1
Size: hierarchy query + permission = 5. Confidence Medium: depth open (Q58).

As a department head, I want to see everyone below me, so that my Team page is not empty (P6a).

Criteria:
- NEW(P6) Given Priya has four managers below her, when she opens Team, then she sees all people below with bookings.
- NEW Given a person changes team in the next copy, then the view follows.
- NEW Given a person outside her tree, then they never show.
- NEW Given 200 people below, then the week loads in under 3 seconds.

Tasks: FE same grid, grouped; BE extend `getTeamWeek`; DB -; QA tree depth cases.
Depends on: ST-TM-1, ST-PP-2.
Open questions: How many levels and whether she can book: Q58.

#### ST-TM-8 Manager names a delegate | 5 | Medium | R1
Size: new table + permission extension + history = 5. Confidence Medium: rights open (Q58).

As a manager, I want to name one delegate, so that my assistant can handle my team's desks (P6b).

Criteria:
- NEW(P6) Given a manager names a delegate, then the delegate sees the Team week and can book and cancel for the team.
- NEW Given she removes the delegate, then the rights end at once.
- NEW Given a delegate, then she cannot name another delegate.
- NEW Given the change, then it is in the change history.

Tasks: FE delegate field on Team; BE `setDelegate`; DB table manager_delegate, audited; QA permission checks.
Depends on: ST-TM-1, ST-TM-5.
Open questions: Q58.

#### ST-TM-9 Group booking in one zone, all or nobody | 5 | Medium | R2
Size: multi-person booking with one rule = 5. Confidence Medium: cut from release 1 by the critic.

As a manager, I want to book desks in one zone for several reports, so that the team sits together.

Criteria:
- AC11.1 Given 5 reports without bookings and zone '3rd east' with 8 free desks, when Meera confirms, then 5 bookings exist in that zone and each person is emailed.
- AC11.2 Given a zone with 3 free desks and 5 people, then no booking is made and she sees which zones have enough desks.
- AC11.7 Given a date outside the horizon or a closed day, then it is refused as in booking.
- AC11.8 Given a group booking, then each booking can be cancelled on its own.

Tasks: FE S9 screen; BE `createGroupBooking`; DB group id use; QA all-or-nobody.
Depends on: ST-TM-5, ST-OS-4.
Open questions: none

#### ST-TM-10 Group booking: skipped people, limit 20 and races | 5 | Medium | R2
Size: edge rules on ST-TM-9 = 5. Confidence Medium: cut from release 1 by the critic.

As a manager, I want clear handling of edge cases, so that group booking is safe.

Criteria:
- AC11.3 Given 2 of 5 people already booked, then they are listed as skipped and it proceeds with 3 after she confirms.
- AC11.4 Given another booking takes a desk while she confirms, then other free desks are picked or nobody is booked and she is told.
- AC11.5 Given more than 20 people are selected, then she is stopped with the limit message.
- AC11.6 Given a person not in her team selected by a tampered request, then the whole request is refused.

Tasks: FE skipped list, limit message; BE extend `createGroupBooking`; DB -; QA race; tampered.
Depends on: ST-TM-9.
Open questions: none

#### ST-TM-11 Manager sees direct reports' no-show count | 3 | Low | Later
Size: one column + rule = 3. Confidence Low: waits for Legal and HR.

As a manager, I want each report's no-show count, so that I can talk about habits (only after Legal and HR agree, Q47).

Criteria:
- AC15.4 (revised) Given Meera opens the team view and Legal has approved, then she sees each report's no-show count for the last 30 days.
- NEW Given 'excused' bookings (ST-TM-12), then they are not counted.
- NEW Given a person outside her team, then no count shows.

Tasks: FE column; BE extend `getTeamWeek`; DB -; QA privacy check.
Depends on: ST-TM-1, ST-CI-4.
Open questions: none

#### ST-TM-12 Admin marks a no-show as excused | 3 | Low | Later
Size: one action + history = 3. Confidence Low: waits for Legal and HR.

As a Facilities admin, I want to mark a no-show as excused, so that illness does not count (P3).

Criteria:
- AC15.3 (revised) Given a No-show, when the admin marks it excused with a reason, then it is not counted and the change is in history.
- NEW Given a non-admin, then it is refused.
- NEW Given an excused booking, then reports show it as excused.

Tasks: FE action; BE `markExcused`; DB excused flag; QA permission.
Depends on: ST-CI-4.
Open questions: none

### Epic EN - Enablers and shell

#### ST-EN-1 Enabler: DeskBook shell - menu, routes and texts | 3 | High | MVP
Size: replace the base example items and set up texts = 3. Confidence High: base gives the shell (B2).

As the team, I want the product menu, routes and text keys in place, so that every story has a home.

Criteria:
- NEW Given the navigation table in the journeys, then the sidebar shows those items per role.
- NEW Given the base example items (Projects), then they are gone.
- NEW Given any text, then it comes from translation keys.
- NEW Given the product name and colours, then they come from the base theme.

Tasks: FE sidebar, routes, keys; BE -; DB -; QA menu per role.
Depends on: none.
Open questions: none

#### ST-EN-2 Enabler: office time and part-of-day rules in one place | 5 | Medium | MVP
Size: shared rules for deadlines, cut-offs, horizon, DST = 5. Confidence Medium: daylight-saving cases.

As the team, I want one tested place for office time rules, so that booking, release, reminders and reports agree.

Criteria:
- AC3.6 Given Pune in Asia/Kolkata and Berlin in Europe/Berlin, when both release at 10:00, then each releases at 10:00 of its own clock, also across a daylight-saving change.
- NEW Given a date, a part of the day and an office, then one function returns the deadline, cut-off and working-day answer.
- NEW Given all other stories, then they use this and not their own time maths.
- NEW Given a table of at least 20 cases, then all pass.

Tasks: FE -; BE `OfficeClock` service; DB -; QA case table, DST.
Depends on: none.
Open questions: none

#### ST-EN-3 Enabler: phone menu as a slide-over | 3 | Medium | R1
Size: shell change = 3. Confidence Medium: may belong to the base (Q56).

As a phone user, I want a slide-over menu, so that content gets the full width (Q44).

Criteria:
- NEW(Q44) Given below 768 px, when she taps the menu icon, then the sidebar slides over the page.
- NEW Given Today, Book a desk and My bookings, then each is one tap away.
- NEW Given the menu, then focus is trapped inside and Escape closes it.

Tasks: FE shell layout; BE -; DB -; QA 360 px; keyboard.
Depends on: ST-EN-1.
Open questions: Base change or product? Q56.

#### ST-EN-4 German and French texts | 5 | Medium | R2
Size: translation + formats = 5. Confidence Medium: translation work.

As a German or French employee, I want the app and emails in my language, so that I can use it (G21).

Criteria:
- NEW Given a user with locale de or fr, then all labels and emails show in that language.
- NEW Given a missing key, then English shows.
- NEW Given dates and times, then they follow the locale.

Tasks: FE locale files; BE email templates; DB -; QA visual check in 2 locales.
Depends on: ST-EN-1.
Open questions: none

## MVP slice

Goal: one pilot office where employees book, check in, lose unused desks, and Facilities reads counts. 40 stories, 147 points (was 35 and 127; after GP: Best desk for me, Plan my days, Change a desk; G3 (D6): two-week strip; D7: Excel export).

- Book a desk: BK-1 (5), BK-5 (5), BK-6 (3), BK-7 (3), BK-8 (5), BK-9 (3), BK-10 (3), BK-11 (5), BK-12 (3), BK-13 (5), BK-14 (2), BK-15 (3)
- Check-in and release: CI-1 (5), CI-4 (5), CI-5 (3), CI-6 (3), CI-7 (5)
- Offices, desks and Facilities control: OS-1 (5), OS-2 (3), OS-3 (3), OS-4 (3), OS-5 (5), OS-6 (2), OS-7 (5), OS-8 (3), OS-9 (2)
- People, roles and access: PP-1 (5), PP-2 (3), PP-3 (3), PP-4 (2), PP-5 (3)
- Notifications: NT-1 (5), NT-2 (3), NT-3 (2)
- Reports: RP-1 (5), RP-2 (3), RP-3 (3), RP-4 (5)
- Enablers and shell: EN-1 (3), EN-2 (5)

Not in the MVP: QR (print sheet and scan), blocks, desk CSV import, evening reminder, refresh by itself, usual desk card, occupancy heat grid, Team and manager features, reserved desks. The next-two-weeks strip (ST-BK-15, D6) and the Excel export (ST-RP-4, D7) are in the MVP. Until the blocking rule ships (ST-OS-12), closing or retiring something that holds bookings is refused (see criteria). The pilot needs an answer to Q55 first.

## Release plan

All sprint numbers are a **guess**; recalibrate after sprint 1 from the points really done. Assumed team: 2 developers, 2-week sprints, 20-25 points a sprint (Q57).

- First sprint guess: EN-1, EN-2, OS-1, OS-2, OS-3, OS-9 = 21 points (foundation: shell, time rules, offices, floors, setting).
- MVP: 147 points = about 6 to 7 sprints at 22 a sprint (was 127, about 6).
- R1: 125 points = about 6 more sprints. MVP plus R1 = 272 points (the trimmed release 1; was 255).
- R2: 26 points = about 1 sprint. Later: 15 points, waits for Legal, HR or a decision.
- Order inside the MVP: foundation (EN, OS, PP-1) -> booking and release (BK, CI) -> mail (NT) -> reports (RP) -> pilot.
- Risks to the guess: Low-confidence stories (6), base mail and SuccessFactors mapping unknown (Q53, Q54), 500-user load (ST-RP-5).

## Not placed

None for the criteria of the first spec. The criteria added at GP (tagged NEW(GP)) are not in `02-spec.md` yet and get AC ids when the requirements-analyst has finished. All 138 acceptance criteria of the spec are in exactly one story; PRD items are covered by the spec traceability. Items the spec marks out of scope (meeting rooms, parking, recurring bookings, floor map, waiting list, penalties, per-office admins, native app) have no story.

