# Product options - DeskBook

Stage SP, product mode, 2026-10-28. Built from `02-spec.md`, `03-journeys.md`, `03-product-review.md`, `decisions.md` (D1-D3; D2 applies the critic's fixes P1-P10 and the stricter privacy rule) and the MVP slice in `04-stories.md`.
Prototype: `P-prototype.html` (one offline file). Tabs at the top switch option A, B, C and the six screens: Today, booking, booked, check-in on a phone (358 px), manager team week, facilities occupancy. A colour picker in the same bar shows that every colour comes from the tenant primary colour.

Rules every option follows (from the spec and D2): employees never see names on desks; a manager sees direct reports only and no per-person no-show count; reports show counts only; words are "Check-in deadline", "No-show", "Running late, keep until 11:30" (one hold per booking); booking for today stays open after the deadline (check in within 30 minutes); a reminder goes 15 minutes before the deadline; one booking per person per day; 14 days ahead.

Demo data: offices Pune (60 desks, 5 zones on 3 floors), Berlin (40), Paris (30, closed 11 Nov), London (36). Asha Kulkarni (employee, Pune, usual desk PUN-3-14), Meera Iyer (manager, 6 direct reports in 4 offices), Imran Shaikh (Facilities). Today is Wed 28 Oct 2026, 08:35 in Pune.

## Option A - Plan my week
**Idea:** the employee picks the days she comes in and the app picks the best free desk for each day (her usual desk first, then the same zone and features); she can change any day.
**Suits best:** hybrid staff who come in 2-4 days a week and do not care which desk exactly, which is most of the 3,000 people.
**Main journey:**
1. Today shows her desk for today with Check in and Running late, and a strip of the next two weeks.
2. She taps "Add day" (or Plan my days) and ticks Tue, Wed, Thu on a two-week calendar.
3. Each day gets a proposed desk with the reason ("Your usual desk", "Same zone as usual"); she taps Change on one day to pick another.
4. "Book 3 days" makes three separate bookings; the confirmation explains how check-in works.
5. On the day she scans the desk QR and is checked in at once (no extra tap).

**Manager team week:** a grid of direct reports by day with an "In the office" row on top (how many of 6, with initials). An empty future day has "+ Book"; the dialog proposes a desk in the zone where most of the team sits that day.
**Facilities occupancy:** four totals (capacity, booked, checked in, no-show rate) and a heat grid of zones by day, darker means fuller; days still to come show booked share with a dashed edge.
**Strengths:** fewest taps for the most frequent job (3 days in about 4 taps, the critic's P4); "Best desk for me" and the remembered office are built in, not added on; check-in lives on the one screen people open anyway; the team week answers "who is in on Wednesday" at a glance.
**Weaknesses:** people who want one exact desk go through "Change"; a proposed desk can be taken between seeing and booking, so the app must re-pick and say so; several bookings in one action need a clear partial result if one day fails.
**Scope and effort:** slightly bigger than the spec (about +5 points): best desk (ST-BK-8) moves from R1 into the MVP and the multi-day booking is new; the list screen of the spec is reused as the "Change" picker.
**Risks:** the proposal logic must be explainable (why this desk) or people distrust it; multi-day booking needs the partial-failure rule (Q90).

## Option B - Pick from the list
**Idea:** the spec as written: choose office, day and part of the day, filter by floor, zone and features, then pick one desk from a list grouped by zone.
**Suits best:** people who want a specific desk or zone every time, and offices where desks differ a lot (monitors, standing desks).
**Main journey:**
1. Today lists upcoming bookings with Check in and Cancel, and a line with today's check-in deadline.
2. Book a desk opens with her office and the next working day; she changes day or part of the day and filters.
3. The count ("23 free desks") and the list grouped by zone update every 5 seconds; she presses Book on a row.
4. A dialog confirms desk, place, day and how check-in works.
5. On the day the QR opens the desk page; one tap on Check in.

**Manager team week:** a plain table, one row per report, each cell desk code, part of day and status; an empty future day has a Book link that opens a short list of free desks in the report's home office.
**Facilities occupancy:** the same four totals and a table by day and floor (capacity, booked, checked in, no-shows, rate, used bar) with day totals and "Export to Excel".
**Strengths:** smallest build, matches the spec and the stories one to one; easy to test; works the same on desktop and phone; the occupancy table is exactly what the Excel export holds.
**Weaknesses:** one day per booking, so a 3-day week is three rounds of the same choices; choosing between codes nobody can place on the floor is the slow, meaningless step the critic called P4; the team table is dense on a phone.
**Scope and effort:** same as the spec (MVP 127 points); best desk stays in R1.
**Risks:** low adoption ("arrive and look" again) if booking feels like work.

## Option C - Zone board
**Idea:** each floor is shown as its zones with their seats as small squares (free, taken, yours, maintenance; no names); the employee taps a free seat to book it.
**Suits best:** people who want to sit in a certain area or near their team, and Facilities who think in zones and floors.
**Main journey:**
1. Today shows her desk and a small picture of her zone with her seat marked.
2. The zone board shows the next days with free counts; she picks a day and part of the day.
3. Each zone shows "8 of 16 free" and its seats; she taps a free seat and sees the code and features.
4. She presses Book; the panel confirms and explains check-in.
5. On the day the QR opens her zone with her seat marked and checks her in; a wrong desk shows both seats.

**Manager team week:** rows are zones (and other offices), columns are days, each cell shows the initials and desk numbers of the reports sitting there; a "Not booked" row lets her book a report in the zone where the team is.
**Facilities occupancy:** a day picker and every floor as zone tiles tinted by use, with seats shaded by booked or not, and the four totals for the day.
**Strengths:** the most visual; "how full is my zone" and "where is my team" are seen at once without a floor map; the same picture serves employee, manager and Facilities.
**Weaknesses:** seats in a grid look like a map but are not one (rows do not match the real room), which can mislead; many small targets on a phone; hardest to make fully keyboard and screen-reader friendly.
**Scope and effort:** bigger than the spec (about +15 to +20 points): seat order per zone (Q92), a board component used on four screens, accessible seat navigation; floor plans stay out of scope.
**Risks:** people ask for a real floor map next (out of scope, intake Q2); accessibility (WCAG 2.1 AA) of the seat grid needs extra work.

## Recommendation
**Option A, with B's list as its "Change" picker and B's occupancy table under A's heat grid.**
Why: the main promise is "book before you come in and always find a desk" for people who come in several days a week; A makes that one short action and puts check-in where people already look, which is what the critic's P1, P2 and P4 ask for. It costs about 5 more points than B because best desk moves into the MVP, while C costs three to four times that and drifts toward the floor map the intake ruled out. Facilities needs the table anyway for the Excel export, so A's heat grid sits above B's table on one page.
If the build must stay at exactly 127 points, ship B first and add A's "Plan my days" in R1; the screens are built so that B's list becomes A's picker.

## Added by the prototype
- A: "Your next two weeks" strip on Today with "Add day" tiles.
- A: booking several days in one action, each a separate booking (Q90).
- A: a reason tag on each proposed desk ("Your usual desk", "Same zone as usual", "Matches your choices", "Closest free desk") and a "Change" picker per day.
- A: "Your usual desk" card on Today (the desk offered first when free) and "Pune tomorrow: N of M desks free" (bookable desks only).
- A, C: the manager's "Book for" proposes a desk in the zone where most of the team sits that day.
- A: "In the office" row (count of 6 with initials) on the team week.
- All: on past days the team week shows only desks that were used; no-show days look empty (Q89, D2).
- All: scanning your own desk checks you in at once in A and C; B asks for one tap (Q91).
- All: "This is not your desk" page shows your desk code, zone and floor (move-my-booking stays Later).
- All: a "How check-in works" box on every booking confirmation (the critic's must-add).
- B: "Updated N seconds ago" counter on the free list; "Usual" tag on the usual desk; "Last 30 days" list on Today.
- B: occupancy table with a total row per day and a "used" bar.
- A: occupancy heat grid of zones by day (solid checked in, dashed booked still to come).
- C: zone board with seats (free, taken, half-day, yours, maintenance), seat order by desk code (Q92); zone tiles tinted by use on occupancy.
- Prototype only: the tenant colour picker in the top bar.

## Questions
Asked in `questions.md` Q89-Q92; in this demo run the recommended answers are taken as accepted and the prototype follows them.
