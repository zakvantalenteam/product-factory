# Product review - DeskBook

## Verdict
**Good with fixes.** The idea is clear and worth building, but one rule stops the main promise from working (a released desk cannot be booked again), and three more would hurt trust or daily use.
Issues: 1 blocker, 3 high, 6 medium.

## The product in one sentence
DeskBook lets employees book a desk (full or half day) in any office up to two weeks ahead, gives back desks nobody checks into, shows managers where their direct reports sit, and gives Facilities counts of real usage.

## Issues

**P1 - BLOCKER - A released desk cannot be booked again, so the release feature helps nobody.** Spec G16 and R14: booking for today stops at the release time (10:00 full day and morning, 14:00 afternoon). PRD 4.3: "the booking is released so someone else can take the desk".
Who it hurts: Ravi arrives at 10:30 without a booking. Asha's full-day desk was released at 10:00. Ravi sees it free but is not allowed to book it. Journey J2 step 3 ("someone else books it for the rest of the day") cannot happen. Asha herself, released at 10:05, can only book an afternoon desk (R28, AC8.7).
Fix: allow booking for today until the end of that part of the day. A booking made after the release time must be checked in within 30 minutes or it is released again. A full-day desk released at 10:00 is then offered as a full day from "now".
If ignored: desks are freed in the system but stay empty in the office; the "always find a desk" goal fails exactly on the busy mid-week mornings; the no-show data looks bad for nothing.

**P2 - HIGH - Forgetting to check in costs you the desk, with no warning.** PRD 4.3: "If they do not check in by 10:00, the booking is released". The only message before that is the evening reminder (F13, email only).
Who it hurts: Ravi's train is late, or he sits at his desk at 09:58 and forgets the QR. At 10:00 his whole day is gone and a no-show is recorded against him. Facilities then reads a wrong usage number.
Fix: one email or reminder 15 minutes before release ("check in or your desk is released"), and a one-tap "I am running late, keep my desk until 11:30" that is used once per booking. Only a release without that tap counts as a no-show.
If ignored: people stop trusting the app, book "just in case" and ignore it, or sit at desks that the system says are free.

**P3 - HIGH - A manager sees each person's no-show count, and nobody can correct it.** Decisions Q7 and G2; AC15.3 says no correction exists in release 1.
Who it hurts: Ravi was in hospital on Tuesday and his desk was released. Meera sees "3 no-shows" next to his name for 30 days. In Germany and France this is personal attendance data that may need the works council's approval.
Fix: ship release 1 with the count visible only to the employee (reminder email) and to Facilities as office totals. Show the per-person count to managers only after Legal and HR confirm, and only with an admin "mark as excused" action.
If ignored: Legal can stop the go-live in two countries, or managers use a wrong number in a talk with their staff.

**P4 - HIGH - Choosing one desk out of 40 codes is slow and meaningless without a map.** Spec F4/F5: Asha picks office, date, part of day, filters, then a code such as "BLR-3-14". No floor map (intake Q2), PRD 4.2 allowed "a list or floor map".
Who it hurts: Asha books three days a week. Each time she repeats six choices and then picks between codes she cannot place on the floor. PRD goal: "fast and easy to use".
Fix: remember her last office and part of day. Add a "Best desk for me" button: she picks zone and features, the system assigns a free desk. Keep the list for people who want a specific desk. Show the zone name and floor next to every code.
If ignored: the first minutes of use feel like work, and people go back to "arrive and look" - the problem the product exists to fix.

**P5 - MEDIUM - "Release" means three different things, and a desk can be "not available" in four ways.** Spec F6/F8: status "Released" (a no-show), button "Release desk" (leaving early), "release time", and email "Your desk was released". Desks can be blocked, retired, reserved or in a closed office.
Who it hurts: Ravi leaves at 15:00 and presses "Release desk" thinking it is harmless. Asha sees "Released" on her list and does not know if she did something wrong. There are also eight booking statuses for a first release.
Fix: use "No-show" for the automatic one, "Leave early" for the button, "Release time" becomes "Check-in deadline". Use "Maintenance", "Retired", "Reserved" on desks and keep one word each everywhere. Merge "Ended early" and "Completed".
If ignored: confusing texts get built into screens and emails and have to be rewritten.

**P6 - MEDIUM - "Team" means direct reports only, so the goal "teams can meet in person" is half met.** PRD 2 and 4.4; spec F9, R31, G1.
Who it hurts: Priya, a department head, has four managers and no direct employees; her team view is empty. Meera's assistant cannot book for her. Asha cannot see whether anyone from her project is in on Wednesday, so she messages them in chat.
Fix: keep the privacy rule, but add (a) managers of managers see everyone below them, (b) a manager can name one delegate, (c) later, an opt-in "share my days with my team" for each employee.
If ignored: managers' views are empty for senior people, and teams keep coordinating outside the app.

**P7 - MEDIUM - A new hire cannot book on her first day.** G18: "Your profile is not ready yet, try tomorrow"; the people copy runs once each night.
Who it hurts: Nisha joins on Monday and needs a desk on Monday. HR added her on Friday evening, but if the copy missed her she is turned away on day one.
Fix: allow booking from the sign-in identity (name, email) and fill the manager later; or give admin a "add person now" button. Show the last copy time on the "not ready" message.
If ignored: the first impression of the product, for the people who most need a desk, is an error.

**P8 - MEDIUM - Facilities cannot fix anything by hand.** Spec Roles: admin "must not ... book for others"; AC15.3: no status corrections.
Who it hurts: Imran in Facilities finds someone sitting at BLR-3-14 that is booked by another person, or a broken chair. He cannot see who holds the desk, move a booking, or cancel it. He can only block the desk, which emails everyone.
Fix: give the admin "move" and "cancel" on a booking, with a reason in the change history, and "who holds this desk today" shown only inside that action (not in reports).
If ignored: every one-off problem becomes a request to the developers.

**P9 - MEDIUM - The success number "90 % get a desk" is too easy to pass.** Q1 and G23: share of searches that found at least one free desk in the office.
Who it hurts: On Wednesday, 3 free desks exist in the far corner. Asha's search "succeeds" but she cannot sit with her team. Mondays and Fridays always pass. The real problem (full mid-week, empty Mondays) stays hidden.
Fix: measure per day of the week and per zone, and count "searches for a day that found nothing". Later: "tell me when a desk is free" (G22).
If ignored: the dashboard shows green while people are still turned away.

**P10 - MEDIUM - Release 1 is large; some of it does not serve the main value.** 17 features, 8 modules.
Fix: see "Cut or move to later". The smaller release gets to the first real use sooner and the rules for group booking and leaving early are better written after people have used the simple version.
If ignored: a long build, with the riskiest rules (all-or-nothing group booking, moving a booking by QR) coded before anyone has tried booking one desk.

## Cut or move to later
- Group booking (F11): the most complicated rule set (all or nothing, skipped people, 20 maximum, a race with other bookings), and F10 lets a manager book several people one at a time. Reason: not needed for the main value.
- "Move my booking here" after scanning another desk (R26, AC7.4): rare; the person can cancel and rebook. Reason: adds a second rule to check-in.
- "Release desk" after check-in (F6, G14): leaving early is rare and the word is confusing (P5). Reason: after check-in, no cancel; the day ends as completed.
- Fifth email, the no-show reminder (F13 message 5, F15): tied to P3, wait for Legal. Reason: it only makes sense with the Legal answer.
- Busiest-days list and weekly use view (AC12.6, A18) can be a second report page; the first release needs occupancy and no-show totals.

## Must add
- Booking after the release time, and a late check-in hold (P1, P2): without them the release feature has no effect.
- "Best desk for me" and a remembered office (P4): the main value in the first minute of use.
- Admin cancel and move with a reason (P8): real offices need it from the first week.
- A short "how release works" line on the confirmation and in the reminder (deadline, what happens, how to keep the desk): the rule is new for everyone.
- A manager delegate and a "manager of managers" view (P6): otherwise senior people see an empty page.

## What is good
- The data rules are careful: no names in reports, no health data, retention stated, rules checked on the server.
- The spec covers the hard moments (two people booking the same desk, time zones, job restarts, blocks over existing bookings) with testable examples.
- The scope stays small on purpose: no floor map, no penalties, no waiting list, no recurring bookings.

## What happens next
You answer P1 to P4 at gate G1 (or say "go with recommended"); the medium points go to the story stage as stories or later items.
The requirements analyst then updates the spec, and the story sizer starts on the smaller release 1.
