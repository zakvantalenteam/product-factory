# PRD review - DeskBook (v0.3 draft)

## Verdict
**Ready with questions.** The idea, users and main journey are clear enough to start the spec, but 11 rules are missing or contradict each other, so the spec will carry recommended answers until you confirm them.

Blockers: 0, High: 11, Medium: 7, Low: 3

## What the document covers
1. Background - why the offices are badly used.
2. Goals - four goals, two without numbers.
3. Users - Employee, Manager, Facilities admin (one line each).
4. Features - office setup, booking, check-in, team view, reports, notifications.
5. Non-functional - six short bullets.
6. Out of scope - meeting rooms, parking.
7. Open - one TBD (repeated no-shows).

| Area | Coverage |
|---|---|
| Purpose (problem, who, why now, success numbers) | Partly - problem is clear, no numbers |
| Users and roles | Partly - roles named, no limits per role, no admin scope |
| Scope (in, out, first release) | Partly - out is listed, first release vs later is not |
| Flows | Partly - book, check-in, release are there; cancel, change, no-show end states are not |
| Data | Partly - desks and bookings yes; personal data, source and keeping time no |
| Rules | Partly - several clash (see below) |
| Non-functional | Missing numbers - only "real time", "mobile", 3,000 people |
| Integrations | Partly - SuccessFactors named, nothing on direction, timing or outage |
| Ambiguity | 7 vague spots (see Words to define) |
| Conflicts | 3 found |
| Testability | Partly - "fast and easy", "real time", "Etc." cannot be checked |

## Must answer before we start

1. **HIGH** - No success numbers. Section 2 says "always find a desk" and "fast and easy to use". How will Facilities know it worked?
   Recommended: target 90 % of bookers get a desk, no-show rate under 15 %, booking takes under 1 minute, desk use per office reported weekly.
   If not decided: we cannot say when the product is good enough, and the audit has nothing to check.

2. **HIGH** - Half-day bookings clash with the 10:00 release. Section 4.3 releases anything not checked in by 10:00. Asha books an afternoon desk in Pune; at 10:00 it is released before she arrives.
   Recommended: a morning booking is released at 10:00, an afternoon booking at 14:00 (both per office setting).
   If not decided: every afternoon booking is lost every day.

3. **HIGH** - Whose clock is 10:00? Section 4.1 gives each office a timezone, section 4.3 gives one time. (Also asked at intake.)
   Recommended: per-office setting, default 10:00 in the office's local time.
   If not decided: Bengaluru desks may be released at the wrong hour.

4. **HIGH** - Who may see where a colleague sits? Section 4.4 shows managers their team, but nothing says what peers or other people see. This is personal data of staff, including in Germany and France.
   Recommended: employee sees own bookings only; manager sees direct reports; admin sees counts, not names, in reports.
   If not decided: we may show everyone's location to everyone, and Legal may block release.

5. **HIGH** - Manager booking vs "One booking per employee per day" (section 4.2). A manager books a desk for Ravi, who already booked one. Also unclear: who counts as "team" (direct reports only, or the whole line below)?
   Recommended: direct reports only; a manager booking replaces nothing and is refused if Ravi already has one; the employee is notified.
   If not decided: double bookings, or managers cancelling staff bookings silently.

6. **HIGH** - Recurring bookings "should be possible" (4.2) but employees can book only 2 weeks ahead. A "every Tuesday" booking must reach beyond 2 weeks.
   Recommended: not in release 1; add later with a clear limit and fairness rule.
   If not decided: the same people hold the best desks every week, and the booking rule breaks.

7. **HIGH** - Repeated no-shows are an open TBD (section 7), yet the no-show rate is a report and the release rule exists because of it.
   Recommended: show the rate to manager and admin only, no penalty in release 1; after 3 no-shows in a month send a reminder, nothing blocked.
   If not decided: the build has no rule, or someone adds a penalty without HR approval.

8. **HIGH** - "A group of desks near each other" (4.4) needs a way to say "near", but the floor map is not required and no desk position exists in 4.1.
   Recommended: each desk has a zone name (e.g. "3rd floor, east"); group booking picks free desks in one zone.
   If not decided: the feature cannot be built, or is built as a map nobody asked for.

9. **HIGH** - "Real time availability" (section 5) with two people booking the last desk at the same second. What is the promise?
   Recommended: the desk list refreshes within 5 seconds, and the system gives a desk to the first booker; the second sees "just taken".
   If not decided: either double-booked desks or an expensive live-push system we did not need.

10. **HIGH** - Non-functional rules are almost empty. Missing: how many people book at once at 8:00 on Monday, response time, uptime, who may sign in and how, accessibility, record of who changed what, how long data is kept, languages beyond "English first".
    Recommended: 3,000 users, 500 at peak, page under 2 s, 99.5 % weekdays 06:00-20:00, company sign-in only, accessible to WCAG 2.1 AA, change history kept 2 years.
    If not decided: we design for the wrong size and the audit cannot pass.

11. **HIGH** - SuccessFactors link has no detail (section 5). Which data (name, manager, office), one way or both, how often, and what happens when it is down or Ravi changes manager mid-week.
    Recommended: read-only, nightly sync of employees, direct manager and office; the app keeps working on the last copy if SuccessFactors is down.
    If not decided: wrong team lists, or the app stops when SuccessFactors does.

## Smaller points
- **MEDIUM** - "Cancel any time" (4.2): after check-in, or after the day started? Recommended: allowed until checked in; after that, "release desk" instead.
- **MEDIUM** - Employee arrives at 10:05 after the desk was released (4.3): what does she see? Recommended: show free desks first, no apology wall.
- **MEDIUM** - Notifications (4.6) end with "Etc.": which messages and which channel (email, Teams, push)? Recommended: email only; evening reminder and release notice.
- **MEDIUM** - "Capacity" in reports (4.5): does a blocked desk count? Recommended: no, only bookable desks.
- **MEDIUM** - Who administers: one global admin team, or one per office (4.1)? Recommended: global admins, per-office admins later.
- **MEDIUM** - Can a booking be made for today, and until what time (4.2)? Recommended: yes, until 10:00 local (afternoon desks until 14:00).
- **MEDIUM** - Desks for people who need them (ergonomic, accessible) are not mentioned. Recommended: a desk feature "reserved for accessibility", booking by approval.
- **LOW** - Can an employee book in an office that is not their own (4.2)? Recommended: yes.
- **LOW** - Export to Excel (4.5): which columns, how big? Recommended: whatever is on screen, up to 100,000 rows.
- **LOW** - German and French "later": is that release 2? Recommended: yes; all texts prepared for translation from the start.

## Words to define
- "Team" (4.4) - direct reports or everyone below the manager?
- "Fast", "easy to use" (section 2) and "real time" (section 5) - give numbers.
- "Occupancy" and "capacity" (4.5) - capacity of desks, or of people allowed?
- "Blocked for maintenance" (4.1) - can it be set for a past or booked date, and what happens to existing bookings?
- "Released" (4.3) - does the original booker lose the booking, or can she still claim any free desk?
- "Checked in" (4.3) - does a QR scan on the desk count the same as the button, and may a person scan a desk they did not book?
- "Etc." (4.6) and "maybe phase 2" (section 6) - say which items, or remove.

## What happens next
You answer the 11 items above (or say "go with recommended"); the intake questions already asked count for items 3, 4 and part of 5.
The requirements analyst then writes the spec and the gap sheet with these answers built in.
