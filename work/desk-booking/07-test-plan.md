# 07 Test plan - DeskBook (desk-booking)

Stage S6/S7, 2026-10-29, qa-engineer. Inputs: `04-stories.md` (the 40 MVP stories, 170 acceptance criteria), `02-spec.md`, `05-openapi.yaml`, `05-security.md`, `06-build-log.md`. Result of the run: `07-test-report.md`.

## How to read this plan

- One case per criterion, id `TC-<story>-<n>` (`<n>` = the position of the criterion in the story). The steps and the expected result are the Given/When/Then of the criterion itself (shortened here, full text in `04-stories.md`).
- Levels: U = unit (mocked collaborators), C = API contract (controller against 05-openapi), R = H2 repository (real queries, two tenants), A = acceptance (real services + rules + repositories on H2, a clock the test moves), F = frontend logic (vitest, node), T = frontend text or source scan (vitest), E = manual or E2E step.
- "By" names the automated test that checks it (alias list at the end of the report) or the manual step (E1 to E10, below).
- Existing tests were mapped first; tests written by QA (new): `DeskBookAcceptanceFlowTest` (24), `TimeMathPlacementTest` (1), `ReportPrivacyTest` (1), `DeskBookBatchRaceTest` (5, batch races), frontend `src/qa/screenTexts.test.ts` (24).
- Rule used for screens (the frontend vitest runs in node, no component tests, gap G1): a criterion about a rule, data, answer or wording is automated; a criterion that is only a screen element or state (button present, skeleton, retry, tile) is a manual step. Parts of a PASS row that only show on the screen are named in the row.

### ST-BK-1 Find free desks by office, date and part of day

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-BK-1-1 | AC4.1 Given 40 free desks, when Asha picks Pune, tomorrow, full day, then she sees 40 desks and the number 40. | A,U | BQS#freeDesksArePagedWithTheWholeCountAndTheServerTime; ACC#ac4_10_fiveHundredDesksArePagedWithTheWholeCountAndTheFirstPageIsSmall |
| TC-BK-1-2 | AC4.6 Given a date before today, beyond the horizon, a weekend or a closed day, when she opens the date picker, then it cannot be chosen. | U,F | BQS#theCalendarRunsFromTodayToTheHorizonWithReasonsPerPart; PDR#refusal; FE plan.test "takes the reason of each refused day from the answer" |
| TC-BK-1-3 | AC4.8 Given a blocked or retired desk, then it is never listed. | A,U | ACC#ac4_8_aRetiredDeskIsNeverListedAndCannotBeBooked; BQS#aDeskNotBookableYetIsNotListed |
| TC-BK-1-4 | AC4.10 Given 500 desks, when the list loads, then the first screen shows in under 2 seconds and the rest loads by scrolling. | E | manual step E1 |
| TC-BK-1-5 | AC4.11 Given a morning booking on desk X, when Ravi searches the afternoon, then X is listed for him. | U,A | BQS#aFullDayBookingTakesBothHalvesAndAHalfDayOnlyItsOwn; ACC#ac5_1_and_5_10_aFullDayBookingTakesBothHalvesAndLeavesEveryonesList |
| TC-BK-1-6 | AC1.7 Given no office is Open, when an employee opens booking, then she sees 'No offices are open for booking yet'; the admin sees 'Create the first ... | A,T | ACC#ac1_7_and_os2_aDraftOfficeIsNotInThePickerAndOpeningItPutsItThere (empty answer); FE screenTexts "AC1.7 says ..." (both texts) |

### ST-BK-5 Book a desk

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-BK-5-1 | AC5.1 Given a free desk, when Asha books it, then she sees desk, office, date, part of day, check-in deadline and how to check in, plus one line how ... | A,U | ACC#ac5_1_and_5_10_...; BSV#createsThroughTheCommandWithTheTrimmedKeyAndAssemblesTheResponse; BCS#createsAFullDayBookingWithTwoSlotsAndTheReleaseDeadline |
| TC-BK-5-2 | AC5.2 Given Asha already has an active booking that day, when she tries another, then it is refused with 'You already have a desk that day' and a ... | A,U,T | ACC#ac5_2_a_second_desk_the_same_day_is_refused_and_names_the_first_booking; BCS#aSecondBookingTheSameDayNamesTheExistingOne; FE screenTexts "AC5.2" |
| TC-BK-5-3 | AC5.6 Given a date beyond the horizon sent by a tampered request, when received, then it is refused as on screen (server-side rules). | U,C | BCS#aDateBeyondTheHorizonAndAPastDateAreRefused; BBP#otherRefusalsKeepTheirCodeAndReason; BCS#aWeekendIsRefusedWithItsReason |
| TC-BK-5-4 | AC5.10 Given a full-day booking, then it occupies morning and afternoon of that desk. | A,R | ACC#ac5_1_and_5_10_...; BRT#twoPeopleCannotHoldTheSameDeskHalfAtOnce; BCS#createsAFullDayBookingWithTwoSlotsAndTheReleaseDeadline |
| TC-BK-5-5 | AC17.3 Given her session expired, when she presses Book, then she signs in again and the page says the booking was not saved. | E | manual step E3 |
| TC-BK-5-6 | NEW(GP) [F5] Given any booking confirmation (one day, several days, booked by a manager), then a 'How check-in works' box shows the deadline, the QR ... | E | manual step E4 |

### ST-BK-6 Two people, one desk: just taken, double click, desk blocked a minute ago

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-BK-6-1 | AC5.3 Given Asha and Ravi press Book on the last desk in the same second, then one booking exists and the other sees 'Just taken, here are other free ... | A,R,U | ACC#ac5_3_asecond_person_on_a_taken_desk_gets_just_taken; ACC#ac5_3_and_5_4_twoThreadsPressingBookTogetherLeaveExactlyOneBooking; ... |
| TC-BK-6-2 | AC5.4 Given Asha double-clicks Book, then only one booking exists. | A,U,F | ACC#ac5_4_aDoubleClickWithTheSameKeyIsOneBooking; BCS#theSameKeyReturnsTheFirstBookingAndADifferentRequestIsRefused; FE plan.test "makes a new key for each press" |
| TC-BK-6-3 | AC5.5 Given the desk was blocked a minute ago, when she books, then it is refused with 'desk no longer available'. | U,A | BCS#anOfficeOrDeskThatChangedAfterTheContextWasReadIsRefusedInsideTheTransaction; ACC#ac4_8_... (DESK_NOT_AVAILABLE) |
| TC-BK-6-4 | NEW(R21) Given an office closed or a desk retired a moment ago, when she books, then it is refused with the reason. | U,A | BCS#anOfficeOrDeskThatChangedAfterTheContextWasReadIsRefusedInsideTheTransaction; BCS#anUnknownDeskIs404AndARetiredOrForeignDeskIsNotAvailable |

### ST-BK-7 Book for today until the end of the day part

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-BK-7-1 | NEW(P1) Given today 10:30 and a desk free for the full day after a release, when she books, then she gets it from now and sees 'check in within 30 ... | A,U | ACC#ciSix_aBookingMadeAfterTheReleaseMustBeCheckedInWithin30MinutesOrIsReleasedAgain; BCS#aBookingMadeAfterTheReleaseTimeIsLateAndGetsThirtyMinutes; ... |
| TC-BK-7-2 | AC4.7 (revised) Given today and the part of the day has ended, when she picks today, then that part is not selectable and the reason is shown. | U,F | BQS#todayIsOpenUntilThePartEndsAndLateBookingsAreFlagged; PDR#morningOfTodayIsRefusedOnceTheMiddayHasPassedButTheAfternoonIsNot; ... |
| TC-BK-7-3 | AC5.7 (revised) Given a booking for a part of today that has ended, when sent, then it is refused. | A,U | ACC#ac5_7_aBookingForAPartOfTodayThatHasEndedIsRefused; BCS#todayIsBookableUntilThePartHasEnded |
| TC-BK-7-4 | NEW Given a booking made before the release time, then the normal deadline applies. | U,A | BCS#createsAFullDayBookingWithTwoSlotsAndTheReleaseDeadline; PDR#bookingMadeBeforeTheReleaseGetsTheReleaseTime; ACC#ac8_1_... (deadline 04:30Z) |
| TC-BK-7-5 | NEW Given she books for an afternoon desk at 11:00, then the afternoon deadline applies. | U,A | PDR#afternoonBookingMadeInTheMorningIsNotLate; ACC#ac8_1_... (afternoon booking released only at 14:05) |

### ST-BK-8 Best desk for me

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-BK-8-1 | NEW(P4) [AC19.1] Given a day and part of the day (and optionally zone and features she ticked), when she asks for the best desk, then one free ... | U | BBP#proposesTheFirstFreeDeskPerDayInDateOrder; DPR#chosenZoneAndFeaturesFilterTheCandidatesAndGiveMatchesChoices |
| TC-BK-8-2 | NEW(GP) [F4/F5, AC19.1, AC19.6] Given a proposal, then it carries a reason tag, chosen in this order: 'Your usual desk' when it is free, else 'Same ... | U | DPR#theUsualDeskWinsWhenItIsFree; DPR#withoutTheUsualDeskTheLowestCodeInHerZoneWins; DPR#chosenZoneAndFeaturesFilterTheCandidatesAndGiveMatchesChoices; ... |
| TC-BK-8-3 | NEW [AC19.5] Given no desk matches her choices, then the nearest zone or feature options are offered. | U,F | BBP#whenDesksAreFreeButNoneMatchesTheAnswerIsNoMatchWithTheNearestOptions; BBP#anUnfilteredRequestNeverGetsNoMatch; DPR#theAlternativesComeInTheDesignedOrderAndStopAtThree; FE plan.test (alternatives of a NO_MATCH day, one tap turns it into her choice). Moved from FAIL (Q198) to PASS on the 2026-10-29 refresh. |
| TC-BK-8-4 | NEW(GP) [F5, AC19.4] Given the proposed desk is taken between the proposal and the booking, then the next desk by the same order is booked and she is ... | U | BBP#aTakenProposedDeskIsRepickedAndReportedWithThePreviousCode; BBP#repicksStopAfterTwoAndThenTheDayFails |
| TC-BK-8-5 | NEW(GP) [F5, AC19.3, AC19.12] Given a proposal, then 'Change' opens the picker for that day (ST-BK-14) and the list stays available for people who ... | F,U | FE plan.test "lets her own choice win over the proposal", "groups free desks by floor and zone in order of appearance"; ... |
| TC-BK-8-6 | NEW [AC19.9] Given a reserved desk, then it is never proposed to someone not on the access list. | E | manual step E10 |

### ST-BK-9 My bookings list

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-BK-9-1 | AC6.3 Given she has no bookings, then My bookings says 'No bookings yet' with a Book a desk button. | E | manual step E4 |
| TC-BK-9-2 | AC5.11 Given the booking succeeded, when she opens My bookings, then it is shown within 1 second. | E | manual step E1 |
| TC-BK-9-3 | NEW Given upcoming and past bookings, then rows show date, office, desk, part, status and 'Booked by <manager>' where it applies. | U,A | BSV#listsHerBookingsPagedAndAssembled; ACC#ac5_4_aDoubleClickWithTheSameKeyIsOneBooking (list); BSV#createsThroughTheCommandWithTheTrimmedKeyAndAssemblesTheResponse |
| TC-BK-9-4 | NEW(P5) Given statuses, then the words are Booked, Checked in, Completed, No-show and Cancelled, used the same on every screen and email. | T,U | FE screenTexts "P5 says ..." (No-show, Checked in, Completed, Cancelled, Booked by, Check-in deadline); MTT#theReleaseNoticeSaysNoShowAndHowToBookForToday |

### ST-BK-10 Cancel my booking

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-BK-10-1 | AC6.1 Given a booked desk, when Asha cancels, then status is Cancelled, the desk is free in other lists within 5 seconds, and she sees a confirmation. | A,U | ACC#ac6_1_and_6_5_and_6_6_cancelFreesTheDeskForOthersAndOthersCannotCancelIt; BCS#cancelFreesTheSlotsAndRecordsTheReason |
| TC-BK-10-2 | AC6.4 Given a booking made by her manager, when she cancels it, then it is cancelled and the manager sees the new status. | E | manual step E10 |
| TC-BK-10-3 | AC6.5 Given a cancel request for someone else's booking sent by a tampered request, then it is refused. | A,U,R | ACC#ac6_1_... (another person gets 404); BCS#cancelOfAnotherPersonsOrACheckedInBookingIsRefused; BSV#getBookingAnswersOnlyHerOwn; BRT#lookupsByIdAreTenantAndOwnerScoped |
| TC-BK-10-4 | AC6.6 Given the booking was already released by the system, when she presses Cancel on an old page, then she sees its real status instead of an error. | A,U,F | ACC#ac6_1_... (BOOKING_STATE_CHANGED with currentStatus NO_SHOW); BSV#aLostRaceAnswersTheRealStatus; FE booking errors.test "shows the real status of a stale booking" |
| TC-BK-10-5 | NEW(D2) Given a checked-in booking, then Cancel is not offered (the day completes). | A,U | ACC#d2_aCheckedInBookingCannotBeCancelled; BSV#allowedActionsFollowTheClockAndTheStatus |

### ST-BK-11 Today page

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-BK-11-1 | NEW Given bookings, when she opens Today, then the next 3 bookings show with check-in deadline and a Check in button when the window is open. | U,F | TSV#carriesTheOfficeTimezoneAndTodayAndFourteenDays (next 3, NEXT_BOOKINGS); BSV#allowedActionsFollowTheClockAndTheStatus; ... |
| TC-BK-11-2 | NEW Given no booking, then 'No bookings yet' and a Book a desk button show. | E | manual step E4 |
| TC-BK-11-3 | NEW(GP) [F4] Given her home office, then 'Pune tomorrow: N of M desks free' shows, where M counts only bookable desks (not blocked or retired). | U | TSV#tomorrowShowsFreeAndBookableDesksAtTheHomeOffice; TSV#tomorrowIsLeftOutOnAWeekend |
| TC-BK-11-4 | NEW Given the admin and a failed people copy for 2 days, then the warning banner shows (links to ST-PP-6). | U | TSV#onlyAdminsSeeTheSyncBannerAfterTwoDaysWithoutACopy |
| TC-BK-11-5 | NEW Given loading or error, then a skeleton or a retry shows. | E | manual step E4 |

### ST-BK-12 After a release: note and rebook

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-BK-12-1 | AC8.7 (revised) Given Asha opens the app at 10:05 after her booking was released, then she sees the free desks first and a line 'Your desk was ... | U,A | TSV#aReleasedBookingTodayGivesTheNoteAndWhetherRebookingIsPossible; ACC#ac8_1_... (released desk is in the free list) |
| TC-BK-12-2 | NEW(P1) Given the note, then it says she can book a desk for the rest of today and one tap opens the list. | U | TSV#aReleasedBookingTodayGivesTheNoteAndWhetherRebookingIsPossible; TSV#noRebookingIsOfferedWhenSheHasAnotherActiveBookingOrTheDayIsOver |
| TC-BK-12-3 | NEW Given a released booking, then it shows as No-show in My bookings. | A,T | ACC#ac8_1_... (status NO_SHOW read back); FE screenTexts "P5 says No-show" |

### ST-BK-13 Plan my days: book several days in one action

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-BK-13-1 | NEW(GP, Q90) [F5] Given she ticks Tue, Wed and Thu within the booking horizon, then each day gets a proposed desk with its reason (ST-BK-8) and 'Book ... | U,F | BBP#everyDayIsBookedWithItsOwnKeyAndStrictnessFollowsTheSource; FE plan.test "books only the days with a desk and marks chosen and proposed desks"; ... |
| TC-BK-13-2 | NEW(GP) [F5] Given a day where she already has an active booking, a closed day, a weekend or a day beyond the horizon, then it cannot be ticked. | F,U | FE plan.test "shows an own booking as booked and not pickable", "drops picked days that are no longer free and counts them"; ... |
| TC-BK-13-3 | NEW(GP) [F5] Given a desk is taken or the day fails between proposal and booking, then the other days stay booked, the failed day is shown with the ... | U,F | BBP#aTakenChosenDeskFailsThatDayOnlyAndOtherDaysStayBooked; BBP#aTakenProposedDeskIsRepickedAndReportedWithThePreviousCode; BBP#otherRefusalsKeepTheirCodeAndReason; ... |
| TC-BK-13-4 | NEW(GP) [F5] Given the result, then one confirmation lists every day with desk, deadline and the 'How check-in works' box. | E | manual step E4 |
| TC-BK-13-5 | NEW(GP) [F5] Given 14 days ticked, then all are accepted; the 15th is not (horizon). | U,C | BBP#theNumberOfDatesIsBoundedAndDatesMustBeDistinct; BBP#theRequestItselfIsValidatedAndAProfileThatIsNotReadyFailsAsAWhole; ... |
| TC-BK-13-6 | NEW(R) Given a tampered request with a day outside the rules, then that day is refused server-side as on screen. | U | BBP#otherRefusalsKeepTheirCodeAndReason; BCS#aWeekendIsRefusedWithItsReason; BCS#aDateBeyondTheHorizonAndAPastDateAreRefused |

### ST-BK-14 Change a desk: picker per proposed day

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-BK-14-1 | NEW(GP) [F4/F5] Given a proposed day, when she presses 'Change', then the free desks for that day and part of day show grouped by zone with desk ... | F,U | FE plan.test "groups free desks by floor and zone in order of appearance"; BQS#freeDesksArePagedWithTheWholeCountAndTheServerTime |
| TC-BK-14-2 | NEW(GP) [F4/F5] Given she picks a desk, then the proposal for that day becomes that desk with the tag 'Your choice' and other days stay as they were. | F | FE plan.test "lets her own choice win over the proposal", "books only the days with a desk and marks chosen and proposed desks" |
| TC-BK-14-3 | NEW(GP) [F4/F5] Given the picked desk is taken before she books, then she is told and the list refreshes. | U,F | BBP#aTakenChosenDeskFailsThatDayOnlyAndOtherDaysStayBooked; FE booking errors.test (DESK_JUST_TAKEN) |

### ST-BK-15 Your next two weeks strip with Add day tiles

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-BK-15-1 | NEW(GP) [F6, AC18.5] Given her bookings, when she opens Today, then a strip shows the next two weeks of working days with desk code and part of day, ... | E | manual step E4 |
| TC-BK-15-2 | NEW(GP) [F6, AC18.2] Given she taps 'Add day', then the plan screen (ST-BK-13) opens with that day ticked. | E | manual step E4 |
| TC-BK-15-3 | NEW(GP) [F6] Given a closed day or weekend, then it is not shown as a tile. | U | TSV#theStripMarksBookedBookableAndNonWorkingDays; TSV#daysBeyondTheHorizonAreOutsideTheWindowAndClosedDaysAreClosed |
| TC-BK-15-4 | NEW Given loading or error, then a skeleton or a retry shows. | E | manual step E4 |

### ST-CI-1 Check in by button

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-CI-1-1 | AC7.1 Given a morning booking and 08:15 local, when Asha presses Check in, then status is Checked in with the time. | A,U | ACC#ciOne_checkInOpensAtSixAndAnAfternoonBookingAtTwelveAndTwoPressesCheckInOnce; BCS#checkInOpensAtSixAndClosesAtTheDeadline |
| TC-CI-1-2 | AC7.6 Given before 06:00 or after the check-in deadline, when she presses Check in, then it is refused with the opening time or 'released'. | A,U,F | ACC#ciOne_... (04:30 refused, CHECK_IN_NOT_OPEN); ACC#ac7_6_afterTheDeadlineCheckInIsRefusedAndTheRealStatusShows; ... |
| TC-CI-1-3 | AC7.7 Given she presses Check in twice, then she is checked in once. | A,U | ACC#ciOne_... (second press, same checkedInAt); BCS#anAfternoonBookingOpensAtTwelveAndASecondPressChangesNothing |
| TC-CI-1-4 | AC7.8 Given an afternoon booking at 11:00, then Check in is disabled until 12:00 and says so. | A,F | ACC#ciOne_... (11:00 refused, 12:01 accepted); FE cardState.test "shows Check in disabled with the opening time before the window opens" |
| TC-CI-1-5 | NEW(P1) Given a booking made after the release time, then the deadline is 30 minutes after booking. | A,U | ACC#ciSix_aBookingMadeAfterTheReleaseMustBeCheckedInWithin30MinutesOrIsReleasedAgain (deadline 10:50 for a booking at 10:20); ... |

### ST-CI-4 Release unchecked bookings at the check-in deadline

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-CI-4-1 | AC8.1 Given a morning booking at Pune not checked in at 10:00 local, when the job runs, then it is No-show by 10:05 and the desk appears free. | A,U | ACC#ac8_1_to_8_3_and_8_6_8_8_theMinuteJobReleasesEachBookingAtItsOwnOfficesDeadline; BCS#releaseMarksNoShowFreesSlotsAndPublishesTheEvent |
| TC-CI-4-2 | AC8.2 Given an afternoon booking, when 10:00 passes, then it is untouched; at 14:00 plus 5 minutes it is a No-show if not checked in. | A | ACC#ac8_1_to_8_3_... (afternoon untouched at 10:05, NO_SHOW at 14:05) |
| TC-CI-4-3 | AC8.3 Given a full-day booking not checked in at 10:00, then the whole booking is released, afternoon part included. | A | ACC#ac8_1_to_8_3_... (full-day released, afternoon half free again) |
| TC-CI-4-4 | AC8.6 Given Bengaluru and Berlin, when 10:00 arrives in Berlin, then only Berlin bookings are released. | A,U | ACC#ac8_1_to_8_3_... (Berlin untouched at 10:05 Pune, released at 10:05 Berlin); ... |
| TC-CI-4-5 | AC8.8 Given a cancelled booking, then the job ignores it and no email is sent. | A,U | ACC#ac8_1_to_8_3_... (cancelled stays Cancelled, 2 notices for 2 releases); BCS#releaseSkipsABookingThatChangedOrIsNotDue |

### ST-CI-5 Release job survives downtime, repeats and races

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-CI-5-1 | AC8.4 Given a booking checked in at 09:59:58, when the job runs at 10:00, then it stays Checked in. | A,U | ACC#ac8_4_aCheckInOneSecondsBeforeTheDeadlineSurvivesTheJob; BCS#releaseSkipsABookingThatChangedOrIsNotDue; ... |
| TC-CI-5-2 | AC8.5 Given the job was down from 09:50 to 10:40, when it restarts, then every overdue booking is released once and one email is sent per booking. | A | ACC#ac8_5_aJobThatWasDownCatchesUpOnceAndSendsOneNoticePerBooking (3 released, 3 notices) |
| TC-CI-5-3 | NEW Given the job runs twice in the same minute, then nothing changes the second time. | A,U | ACC#ac8_5_... (second run releases 0, still 3 notices); BSP#aRunWithNothingDueDoesNothing |

### ST-CI-6 Late booking: check in within 30 minutes or it is released again

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-CI-6-1 | NEW(P1) Given a booking made at 10:20 after the release, when 10:50 passes without check-in, then it is released again. | A | ACC#ciSix_aBookingMadeAfterTheReleaseMustBeCheckedInWithin30MinutesOrIsReleasedAgain |
| TC-CI-6-2 | NEW Given she checks in at 10:45, then it stays Checked in. | A | ACC#ciSix_... (checked in at 10:45 stays Checked in) |
| TC-CI-6-3 | NEW Given an afternoon booking made at 14:20, then the same 30 minutes apply. | A | ACC#ciSix_anAfternoonBookingMadeAt1420HasTheSame30Minutes |
| TC-CI-6-4 | NEW Given such a release, then it is shown as 'Released after hold' and not counted in the No-show rate (Q50). | A,U,T | ACC#rp_aLateReleaseAfterHoldIsItsOwnLineAndStaysOutOfTheNoShowRate; OCC#releasedAfterHoldIsItsOwnLineAndStaysOutOfTheRate; FE screenTexts "Q50 says Released after hold" |

### ST-CI-7 Running late: keep my desk once

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-CI-7-1 | NEW(P2) Given a booking not checked in before the deadline, when she taps 'Running late, keep my desk', then the deadline moves to the hold time ... | A,U,F | ACC#ciSeven_runningLateKeepsTheDeskOnceUntilReleasePlus90MinutesThenReleasesAfterHold (deadline 11:30 for a 10:00 release); ... |
| TC-CI-7-2 | NEW Given she already used it, then the tap is not offered again for that booking. | A,F | ACC#ciSeven_... (holdAvailable false, second tap HOLD_ALREADY_USED); FE cardState.test "hides Running late once it was used" |
| TC-CI-7-3 | NEW Given the hold ends without check-in, then it is released as 'Released after hold' (Q50). | A | ACC#ciSeven_... (RELEASED_AFTER_HOLD at 11:31) |
| TC-CI-7-4 | NEW Given she taps and then checks in, then status is Checked in. | A | ACC#ciSeven_... (checks in during the hold, stays Checked in) |
| TC-CI-7-5 | NEW Given a release without the tap, then it is a No-show. | A | ACC#ac8_1_to_8_3_... (no tap: NO_SHOW) |

### ST-OS-1 Offices: create, list and edit

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-OS-1-1 | AC1.1 Given an admin, when she saves a new office with name, city and timezone, then it appears in the office list and the picker. | U,C,R | OSV#createMakesADraftOfficeWithTheDefaultSettings; OCC2#createOfficeAnswers201WithALocationOfTheNewOffice; ORT#officeListsCountsAndLookupsSeeOnlyTheTenant |
| TC-OS-1-2 | AC1.2 Given a missing name, city or timezone, when she saves, then each missing field shows a message and nothing is saved. | F,C | FE officeSchemas.test "asks for name, city and timezone (AC1.2)"; OCC2#aBlankNameAndABadDeskCodeAreRefusedWithFieldErrors |
| TC-OS-1-3 | AC1.3 Given an office 'Pune', when she creates 'pune', then it is refused with 'name already used'. | U,R,F | OSV#createRefusesANameUsedIgnoringCase; ORT#officeNameIsUniqueIgnoringCaseWithinATenant; FE office errors.test "maps every office code to its label key" |
| TC-OS-1-4 | AC1.6 Given two admins editing the same office, when the second saves, then she sees 'changed by someone else, reload'. | U,F | OSV#updateWithAStaleVersionIsAConflict; FE officeApi.test "turns a 409 CONCURRENT_UPDATE problem into an ApiError with its code"; ... |
| TC-OS-1-5 | AC3.7 Given an unknown timezone value, when saved, then it is refused; the timezone is chosen from a list. | U,F | OSV#createRefusesAnUnknownTimezone; OSV#createAcceptsIanaRegionIdsAndUtc; FE office state.test "lists IANA ids with UTC" |

### ST-OS-2 Office states: Draft, Open, Closed

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-OS-2-1 | AC1.4 Given an office with bookings, when she tries to delete it, then it is refused and 'Close office' is offered. | U,C | There is no delete-office operation in the contract (05-openapi has none); OSV#closeIsRefusedWithFutureBookingsAndCarriesOnlyTheCount; ... |
| TC-OS-2-2 | NEW(Q41) Given a new office, then its state is Draft and it is not in the employee picker. | U,A | OSV#createMakesADraftOfficeWithTheDefaultSettings; ACC#ac1_7_and_os2_aDraftOfficeIsNotInThePickerAndOpeningItPutsItThere |
| TC-OS-2-3 | NEW Given she presses 'Open office', then it is visible to employees. | U,A,F | OSV#openMovesADraftOfficeToOpenAndSetsTheCapacityStart; ACC#ac1_7_and_os2_... (listed after Open); FE office state.test "opens a draft, closes an open office" |
| TC-OS-2-4 | NEW Given a closed office, then it is hidden from booking; with future bookings it is refused until ST-OS-12 ships. | U | OSV#closeMovesAnOpenOfficeToClosed; OSV#closeIsRefusedWithFutureBookingsAndCarriesOnlyTheCount; BQS#listsOpenOfficesWithTheirLocalToday |

### ST-OS-3 Floors: add and retire

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-OS-3-1 | AC1.8 Given a floor name already used in that office, when saving, then it is refused. | U,R | FZS#createFloorRefusesADuplicateNameIgnoringCaseWith409; ORT#floorNameIsUniqueInTheOffice |
| TC-OS-3-2 | NEW Given a new floor name, when saved, then it appears on the Floors tab. | U | FZS#createFloorAlsoCreatesTheDefaultZoneMain; FZS#listFloorsFiltersByStatusAndRefusesAnUnknownOne |
| TC-OS-3-3 | NEW Given she retires a floor without future bookings, then its desks are hidden from booking; with future bookings it is refused until ST-OS-12 ... | U | FZS#retireFloorSetsRetiredOnAndIsFinal; FZS#retireFloorIsRefusedWhileFutureBookingsExistAndCarriesTheCount |

### ST-OS-4 Zones per floor

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-OS-4-1 | AC2.4 (revised) Given a new floor, then zone 'Main' exists and a desk with no zone gets 'Main'. | U | FZS#createFloorAlsoCreatesTheDefaultZoneMain; DSV#createPutsTheDeskInTheZoneMainWhenNoneIsGivenAndItIsBookableFromTomorrow |
| TC-OS-4-2 | NEW(Q42) Given an admin, when she adds or renames a zone, then desks pick zones from this list only. | U | FZS#createZoneTrimsAndRefusesADuplicateOnTheSameFloor; FZS#renameZoneChecksIfMatchAndNameAndReportsTheDeskCount; DSV#createRefusesAZoneOfAnotherFloor |
| TC-OS-4-3 | NEW Given a zone with desks, then it cannot be deleted. | U | FZS#deleteZoneIsRefusedWhileAnyDeskUsesIt; FZS#deleteZoneSoftDeletesAnUnusedZone |
| TC-OS-4-4 | NEW Given a zone name already used on that floor, then it is refused. | U,R | FZS#createZoneTrimsAndRefusesADuplicateOnTheSameFloor; ORT#zoneNameIsUniqueOnTheFloor |

### ST-OS-5 Desks: create, edit and retire

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-OS-5-1 | AC2.1 Given an admin, when she creates a desk with code, floor, zone and two features, then it is listed on that floor and bookable from tomorrow's ... | U | DSV#createPutsTheDeskInTheZoneMainWhenNoneIsGivenAndItIsBookableFromTomorrow; DSV#createRefusesAnUnknownFeatureAndLinksTheKnownOnes; ... |
| TC-OS-5-2 | AC2.2 Given a code already used anywhere, when she saves, then it is refused with 'code already used'. | U,R | DSV#createRefusesADuplicateCodeInTheTenantIgnoringCase; ORT#deskCodeIsUniquePerTenantIgnoringCase |
| TC-OS-5-3 | AC2.3 Given a desk with bookings, when she edits its code, then the field is read-only. | U | DSV#updateOfTheCodeIsRefusedOnceTheDeskHasBookings; DSV#updateOfTheFloorIsRefusedOnceTheDeskHasBookings; ... |
| TC-OS-5-4 | AC2.9 Given a retired desk, when an employee searches, then it is not listed; history stays in reports. With future bookings, retiring is refused ... | A,U | ACC#ac4_8_aRetiredDeskIsNeverListedAndCannotBeBooked; DSV#retireIsRefusedWhileFutureBookingsExistAndCarriesTheCount; DSV#retireSetsRetiredOnAndASecondRetireIsRefused |
| TC-OS-5-5 | NEW Given a desk list of 1,500 desks, then it is paged and searchable. | A,U | ACC#os5_aListOf1500DesksIsPagedAndSearchable (25 of 1,500, 60 pages, search by code); DSV#listReadsFloorsZonesAndFeaturesInBatchesWhateverThePageSize |

### ST-OS-6 Desk features list

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-OS-6-1 | NEW Given a new product, then monitor, docking station and standing desk exist. | U | FDS#aTenantWithoutFeaturesGetsTheThreeDefaults; FDS#aTenantThatHasFeaturesIsNotSeededAgain |
| TC-OS-6-2 | NEW Given an admin adds a feature, then it can be chosen on desks. | U | FCD#createFeatureTrimsAndRefusesADuplicateIgnoringCase; DSV#createRefusesAnUnknownFeatureAndLinksTheKnownOnes |
| TC-OS-6-3 | NEW Given a feature used by desks, then it cannot be deleted. | U | FCD#deleteFeatureIsRefusedWhileDesksUseIt; FCD#deleteFeatureSoftDeletesAnUnusedFeature |

### ST-OS-7 Office settings: release times, midday and working days

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-OS-7-1 | AC3.1 Given a new office, then it has release times 10:00 and 14:00, midday 13:00 and working days Monday-Friday. | U,F | OSV#createMakesADraftOfficeWithTheDefaultSettings (10:00, 14:00, 13:00, Monday to Friday); FE officeSchemas.test "accepts the defaults of a new office (AC3.1)" |
| TC-OS-7-2 | AC3.2 Given an afternoon release of 09:00 with a morning release of 10:00, when saved, then it is refused with an explanation. | U,F | OSV#settingsRefuseAnAfternoonReleaseBeforeTheMorningRelease; OSV#settingsRefuseAnAfternoonReleaseBeforeMidday; ... |
| TC-OS-7-3 | AC3.3 Given the morning release is changed at 09:30 to 09:45, when saved, then today's release stays and tomorrow's is 09:45. | U,A | OSV#settingsChangeAppliesFromTomorrowAndPublishesTheEvent; OET#aSameDayChangeLeavesTodaysDeadlineAndTheNextDaysTimesMoveOn; ... |
| TC-OS-7-4 | NEW Given working days, then she can choose any set of weekdays. | F,U | FE officeSchemas.test "needs one working day and valid times", "sends working days in week order"; OET#theWorkingDaysAlsoChangeFromTheEffectiveDay |
| TC-OS-7-5 | NEW Given a change, then it is in the change history. | U | AUD#updateRecordsOneRowPerChangedAuditedFieldWithOldAndNewValue; AEC#everyAuditableEntityIsAudited; OSV#historyReadsTheAuditRowsOfTheOfficeAfterTheExistenceCheck |

### ST-OS-8 Closed days

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-OS-8-1 | AC3.4 Given 26 Jan is a closed day, when an employee picks that date, then it is greyed out with 'Office closed'. | U,F,T | BQS#theCalendarRunsFromTodayToTheHorizonWithReasonsPerPart; PDR#refusal; FE plan.test "takes the reason of each refused day from the answer"; ... |
| TC-OS-8-2 | NEW Given a closed day with no bookings, when saved, then it is stored; with bookings it is refused until ST-OS-12 ships. | U | FCD#addClosedDayStoresTheDateAndATrimmedReason; FCD#addClosedDayIsRefusedWhenBookingsExistThatDayAndCarriesTheCount |
| TC-OS-8-3 | NEW Given she removes a closed day, then the date is bookable again. | U | FCD#removeClosedDaySoftDeletesItAfterTheVersionCheck; FCD#addClosedDayTwiceIsRefusedWith409 |
| TC-OS-8-4 | NEW(R12) Given a non-working day, then it is greyed out too. | U | BCS#aWeekendIsRefusedWithItsReason; PDR#refusal; BQS#theCalendarRunsFromTodayToTheHorizonWithReasonsPerPart |

### ST-OS-9 Company booking horizon setting

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-OS-9-1 | NEW Given the tab 'Booking rules', then the default is 14 days. | U,F | BSP#theRulesHaveDefaultsAndReadStoredValues; FE report.test "accepts the defaults and the limits of the contract" |
| TC-OS-9-2 | NEW Given a value that is not a whole number of at least 1, when saved, then it is refused. | C,F | BCC#anUnknownPropertyAMissingFieldAndAnOutOfRangeRuleAreRefusedWith400; FE report.test "refuses values outside the limits and non-whole numbers" |
| TC-OS-9-3 | NEW Given a saved value, then the next search uses it. | U | BSP#updateStoresTheThreeValuesAndBumpsTheVersion; BQS#theCalendarRunsFromTodayToTheHorizonWithReasonsPerPart |

### ST-PP-1 Nightly copy of people from SuccessFactors

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-PP-1-1 | AC14.1 Given 3,000 employees, then the run finishes in under 10 minutes and shows counts of new, changed and left. | E | manual step E5 |
| TC-PP-1-2 | AC14.2 Given SuccessFactors does not answer, then the last copy is kept, the run is marked failed, and the date of the last good copy is shown. | U,R | PSR#aPageThatFailsThreeTimesFailsTheRunAndNothingIsApplied; PSR#anEmptyAnswerFailsTheRunAndKeepsTheCopy; PSS#aFailedRunKeepsTheCodeAndIsNotAGoodCopy; ... |
| TC-PP-1-3 | AC14.6 Given a new employee, then she can sign in and book from that day on. | R,A,U | PSS#theFirstLoadInsertsActivePeopleAndStoresOldLeaversInactiveAndAlreadyHandled; MPS#anEmployeeInTheCopyIsReadyAndHasTheEmployeeRoleOnly; ... |
| TC-PP-1-4 | NEW(R49) Given a failure, then the sync retries every hour for the rest of the day. | U | PSR#afterAFailedRunTheNextHourlyInvocationTriesAgain; PSR#afterASuccessToday_theHourlyInvocationEndsAtOnce |
| TC-PP-1-5 | NEW Given a record without an email, then it is skipped and counted. | R,U | PSS#aNewPersonWithoutAUsableEmailIsSkippedCountedAndListedByUserIdOnly; PMT#aBlankUserIdIsSkipped |

### ST-PP-2 Direct manager and manager status

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-PP-2-1 | AC14.4 Given Ravi's manager changes, when the next sync completes, then Meera's team view no longer shows him and the new manager's does. | R | PSS#aChangedValueWritesOnlyThatRow; PSS#aPersonWithAnActiveReportBecomesManagerAndLosesTheFlagWhenTheLastReportGoes |
| TC-PP-2-2 | NEW(R52) Given a person who is manager of at least one active employee, then she has manager status. | R,U | PSS#aPersonWithAnActiveReportBecomesManagerAndLosesTheFlagWhenTheLastReportGoes; MPS#aManagerFlagFromTheCopyAddsTheManagerRoleOnlyForAnEmployee |
| TC-PP-2-3 | NEW Given a person with no active reports, then she has no manager status. | R | PSS#aPersonWithAnActiveReportBecomesManagerAndLosesTheFlagWhenTheLastReportGoes; PSS#anInactiveReportDoesNotMakeAManager |
| TC-PP-2-4 | NEW Given a manager change, then bookings stay with the employee. | R | PSS#aChangedValueWritesOnlyThatRow (only the people row changes; bookings point at the employee id, BRT#lookupsByIdAreTenantAndOwnerScoped) |

### ST-PP-3 Leavers: future bookings cancelled silently

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-PP-3-1 | AC14.5 Given an employee leaves, when the sync completes, then her future bookings are cancelled and the desks become free. | R,A,U | ELL#futureBookedBookingsAreCancelledWithReasonLeaverAndTheirSlotsAreFreed; SCS#aLeaverHandOverCancelsTheFutureBookingAndMarksThePersonHandled; ... |
| TC-PP-3-2 | AC5.9 Given an inactive employee, then she cannot book. | A,U | ACC#ac5_9_anInactiveEmployeeCannotBook; MPS#anInactiveRecordIsNotReadyForAnotherReason |
| TC-PP-3-3 | NEW(G7) Given such a cancellation, then no email is sent. | A | SCS#aLeaverHandOverCancelsTheFutureBookingAndMarksThePersonHandled (0 notices for a leaver) |

### ST-PP-4 Profile not ready for people missing from the copy

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-PP-4-1 | AC5.8 Given Asha is signed in and the copy has no record of her, when she books, then she sees 'Your profile is not ready yet' with the date of the ... | A,U,F | ACC#ac5_8_aPersonMissingFromTheCopyCannotBookCanStillListAndBooksAfterTheNextCopy (PROFILE_NOT_READY, desk still free); BBP#aProfileThatIsNotReadyStopsTheProposal; ... |
| TC-PP-4-2 | NEW Given the same person, then she can still open Today and My bookings. | A,U | ACC#ac5_8_... (My bookings answers empty); TSV#aPersonNotInTheCopyStillGetsAnEmptyToday |
| TC-PP-4-3 | NEW Given the next copy has her, then she can book without any other step. | A | ACC#ac5_8_... (books once the copy has her) |

### ST-PP-5 Roles and access checks, No access page

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-PP-5-1 | AC17.1 Given a person not signed in, when she opens any page, then she is sent to company sign-in and back. | E | manual step E8 |
| TC-PP-5-2 | AC17.2 Given a signed-in person without a DeskBook role, then she sees 'No access'. | F,U | FE guards.test "sends a person without roles to No access"; RMC#everyOperationRefusesASignedInPersonWithoutRoleWith403AndTouchesNothing; ... |
| TC-PP-5-3 | AC17.4 Given any page, then data a role may not see is not in the answer sent to the browser. | U,R | RMC; BRM; BSV#getBookingAnswersOnlyHerOwn; BRT#theListSpecificationNeverCrossesTenants; RPT#everyReportRecordHoldsCountsAndPlacesOnly |
| TC-PP-5-4 | AC1.5 Given an employee or manager, when she opens office setup by menu or link, then the entry is absent and the link is refused. | F,U | FE navConfig.test "shows Today, Book a desk and My bookings to an employee or manager"; FE guards.test "keeps non-admins off admin pages"; ... |
| TC-PP-5-5 | AC12.10 Given an employee or manager opens reports by link, then it is refused. | C,U,F | RCT#aPlainEmployeeGets403AndAnAnonymousCallerGets401OnBothOperations; ORS#onlyAnAdminMayReadAndAGuardRefusalTouchesNoData; FE guards.test |

### ST-NT-1 Enabler: send an email once, retry, log

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-NT-1-1 | AC13.6 Given the mail service is down, then bookings still work and the email is retried 3 times over 1 hour, then logged as failed. | A,U | NFT#aMailServerThatIsDownRetriesAt20And40And60MinutesThenFailsAndTheBookingIsUntouched; NPT#aReleaseNoticeIsRetriedAt20And40And60MinutesAfterCreationThenFailed |
| TC-NT-1-2 | NEW(R46) Given an event, then each message is sent once (event key). | A,U | NFT#theOutboxWritesOneRowPerEventKeyAndASecondEnqueueAddsNothing; ACC#ac8_5_... (one notice per booking) |
| TC-NT-1-3 | NEW(R47) Given any message, then texts are translatable, English only in this release, and name no other employee. | U | MTT#noMessageNamesAnotherEmployeeOrTheProduct; MTT#theHtmlHasParagraphsAndLinks |
| TC-NT-1-4 | NEW Given a failed send, then the admin can see it in the log. | U | NJT#theDispatchJobReportsCountsAndEveryFailedRowWithoutAnAddress |

### ST-NT-2 Reminder 15 minutes before the deadline

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-NT-2-1 | NEW(P2) Given a booking not checked in 15 minutes before its deadline, then she gets one email 'check in or your desk is released' with a check-in ... | A,U | NFT#theReminderIsQueuedFifteenMinutesBeforeTheDeadlineOnceAndCarriesBothLinks; MTT#theReminderSaysCheckInAndCarriesBothLinksAndTheLocalDeadline |
| TC-NT-2-2 | NEW Given she checked in or cancelled, then no email is sent. | A | NFT#nothingIsQueuedForSomeoneWhoCheckedInOrCancelledOrForADeadlineThatHasPassed; NFT#aReminderQueuedBeforeCheckInIsSkippedAtSendTime |
| TC-NT-2-3 | NEW Given the job runs twice, then one email per booking. | A,U | NFT#theReminderIsQueuedFifteenMinutesBeforeTheDeadlineOnceAndCarriesBothLinks; NPT#eventKeysAreStablePerEventAndTheReminderKeyCarriesTheDeadline |

### ST-NT-3 Email when a booking was released

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-NT-3-1 | AC13.3 Given a booking released at 10:00, then Asha gets one email 'Your desk was released'. | A | ACC#ac8_1_to_8_3_... (one notice per release); NFT#theReleaseNoticeIsSentOnceWithNoShowAndHowToBookForToday; ... |
| TC-NT-3-2 | NEW Given the email, then it says No-show and how to book a desk for today (P1). | U | MTT#theReleaseNoticeSaysNoShowAndHowToBookForToday; MTT#aReleaseAfterAHoldIsNotCalledANoShow |
| TC-NT-3-3 | NEW Given a catch-up run, then one email per booking. | A | ACC#ac8_5_... (3 notices for 3 bookings after a catch-up); NFT#aReleasedBookingQueuesOneNoticeEvenWhenTheEventArrivesTwice |

### ST-RP-1 Occupancy per office, floor and day

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-RP-1-1 | AC12.2 Given a date range of 1 to 31 Oct, when she picks office Pune, then rows per day and floor appear with totals. | A,R,C | ACC#rp_theReportAfterARealDayCountsCapacityBookedCheckedInNoShowAndCancelledPerOffice; BSQ#twoFloorsGiveTwoRowsAndOneDayTotalWithTheSumOfBoth; ... |
| TC-RP-1-2 | AC12.7 Given no data in the range, then she sees 'No bookings in this period' and export is disabled. | E | manual step E4 |
| TC-RP-1-3 | NEW(R39) Given any report, then it shows counts and rates only, never names. | U | RPT#everyReportRecordHoldsCountsAndPlacesOnly; OES#theFileHasAHeaderThenTheFloorRowsAndTheAllFloorsLinePerOfficeAndDay |
| TC-RP-1-4 | NEW(R42) Given days, then they follow each office's own timezone. | A,F,U | ACC#rp_... (Pune and Berlin on their own Monday); PDR#todayIsJudgedOnTheOfficeClockNotOnUtc; FE report.test "finds today in the office timezone" |
| TC-RP-1-5 | NEW Given a booking, then booked and checked-in counts show per floor and day. | A,U | ACC#rp_... (booked 2.0, checked in 0.5 per day); OCC#capacityIsTheBookableDesksOfEachWorkingDay; BSQ#statusesAndPartsAreCountedAndTheCancelledSplitFollowsTheDeadline |
| TC-RP-1-6 | NEW(GP) [F12] Given the table (B's occupancy table, kept under the heat grid), then each day has a total row and each row a 'used' bar (checked in as ... | F,U | FE report.test "bounds the used bar between 0 and 1", "takes the All floors line from the server day totals and sums nothing"; ... |

### ST-RP-2 No-show rate

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-RP-2-1 | AC12.1 Given Pune has 60 bookable desks and on Monday 42 booked, 35 checked in, 7 released, then capacity 60, booked 42, checked-in 35 and no-show ... | U | OCC#ac12_1SixtyDesksFortyTwoBookedThirtyFiveInSevenReleasedGivesSixteenPointSevenPercent |
| TC-RP-2-2 | AC12.5 Given a booking cancelled before the release time, then it is not a No-show and not booked at release. | U,A | OCC#cancelledBeforeTheDeadlineIsApartAndCancelledAfterItStillCountsAsBooked; ACC#rp_theReportAfterARealDay... (cancelled 0.5, not booked) |
| TC-RP-2-3 | NEW Given 'Released after hold' bookings, then they are a separate line, not in the rate (Q50). | U,A | OCC#releasedAfterHoldIsItsOwnLineAndStaysOutOfTheRate; ACC#rp_aLateReleaseAfterHoldIsItsOwnLineAndStaysOutOfTheNoShowRate |

### ST-RP-3 Capacity rules: blocked and retired desks, half days

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-RP-3-1 | AC12.3 Given two blocked desks on a day, then capacity for that day is reduced by two. | E | manual step E10 |
| TC-RP-3-2 | AC12.4 Given a half-day booking, then booked counts 0.5 and capacity is in desk-days. | U,A | OCC#halfDaysCountHalfADeskDay; ACC#rp_theReportAfterARealDay... (0.5 desk-days) |
| TC-RP-3-3 | AC16.6 Given a flagged reserved desk, then reports count it as capacity as normal. | E | manual step E10 |
| TC-RP-3-4 | NEW Given a retired desk, then it is not capacity. | U,R | OCC#aRetiredFloorLeavesTheCapacity; OCC#aDeskCountsFromItsBookableFromDayAndNotFromItsRetiredOnDay; BSQ#capacityFollowsDeskDatesAndClosedDays |

### ST-RP-4 Excel export

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-RP-4-1 | AC12.8 Given an export of 30,000 rows, when she presses Export, then she gets an Excel file with the same rows and columns as the screen within 30 ... | E | manual step E7 |
| TC-RP-4-2 | AC12.9 Given more than 100,000 rows, then export is refused with 'Narrow the dates or office'. | U,F | OES#moreThan100000RowsIsRefusedBeforeAnythingIsWritten; FE report.test "reads the field code of the 400 (05-api-notes 8)" |
| TC-RP-4-3 | AC12.11 Given an export file, then it contains no employee names or ids. | U | RPT#everyReportRecordHoldsCountsAndPlacesOnly; OES#theFileHasAHeaderThenTheFloorRowsAndTheAllFloorsLinePerOfficeAndDay |
| TC-RP-4-4 | NEW Given an empty range, then the export button is disabled. | E | manual step E4 |

### ST-EN-1 Enabler: DeskBook shell - menu, routes and texts

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-EN-1-1 | NEW Given the navigation table in the journeys, then the sidebar shows those items per role. | F | FE navConfig.test (all four roles cases) |
| TC-EN-1-2 | NEW Given the base example items (Projects), then they are gone. | T,U | FE screenTexts "has no Projects route or feature file", "shows no Projects menu item to any role"; MMT#theDemoModuleStaysInTheHistoryAndV060DropsItsTables |
| TC-EN-1-3 | NEW Given any text, then it comes from translation keys. | T | FE screenTexts "no screen file has a sentence typed between tags or in a visible attribute"; FE locales.test (all 5 files have the keys of en.json) |
| TC-EN-1-4 | NEW Given the product name and colours, then they come from the base theme. | F,U | FE deriveTokens.test (colours and fonts from the theme); THM#returnsDefaultsWhenNoRowExists |

### ST-EN-2 Enabler: office time and part-of-day rules in one place

| Case | Criterion (shortened) | Level | By |
|---|---|---|---|
| TC-EN-2-1 | AC3.6 Given Pune in Asia/Kolkata and Berlin in Europe/Berlin, when both release at 10:00, then each releases at 10:00 of its own clock, also across a ... | U,A | PDR#pune_and_berlin_both_release_at_ten_on_their_own_clock_across_the_daylight_saving_change; ACC#ac8_1_to_8_3_... (Pune 04:30Z, Berlin 09:00Z) |
| TC-EN-2-2 | NEW Given a date, a part of the day and an office, then one function returns the deadline, cut-off and working-day answer. | U | PDR#officeClockAssessGivesDeadlineCutOffAndWorkingDayInOneAnswer; OCS#assessAnswersWithTheInjectedClock |
| TC-EN-2-3 | NEW Given all other stories, then they use this and not their own time maths. | U | TMP#zoneArithmeticLivesInTheTimePackageAndTheKnownHelpers (scan of the DeskBook modules) |
| TC-EN-2-4 | NEW Given a table of at least 20 cases, then all pass. | U | PDR: 48 cases in the surefire report (release, check-in, part-end and refusal tables incl. DST gap and overlap) |

## Cases the criteria imply but do not state

| Kind | Case | Level | By |
|---|---|---|---|
| Validation limit | Batch of 14 days accepted, 15th refused; Idempotency-Key 1 to 64 characters; featureIds at most 20 and unique; report range at most 93 days after from; export at most 100,000 rows; horizon 1 to 60, hold 15 to 240, late window 5 to 120 | U,C | BBP#theNumberOfDatesIsBoundedAndDatesMustBeDistinct; BSV#theIdempotencyKeyIsRequiredAndBounded; BCC#anUnknownPropertyAMissingFieldAndAnOutOfRangeRuleAreRefusedWith400; RCT#aRangeOver93DaysAndABadSortAreA400; OES#moreThan100000RowsIsRefusedBeforeAnythingIsWritten |
| Concurrency | Stale version = 409 CONCURRENT_UPDATE on every update; release job against a check-in (version check, check-in wins); two threads on one desk; same key twice | U,A | OSV#updateWithAStaleVersionIsAConflict; BCS#releaseSkipsABookingThatChangedOrIsNotDue; ACC#ac5_3_and_5_4_twoThreadsPressingBookTogetherLeaveExactlyOneBooking; ACC#ac5_4_aDoubleClickWithTheSameKeyIsOneBooking |
| Permission | Every operation, every role: anonymous 401, signed in without role 403, plain employee 403 on admin operations, admin and super-admin pass; employee operations open to employees | U | RMC (6 tests, 28 office operations); BRM (6 tests, booking operations); RCT#aPlainEmployeeGets403AndAnAnonymousCallerGets401OnBothOperations; DAG (5) |
| Tenant | Another tenant record answers 404, queries filter tenant and deleted_at, same names and dates in two tenants, mutation check done by the developer | R | ORT (21), BRT (14), PPR (5), BSQ (6), PSS#theApplyReadsAndWritesOnlyTheCallersTenant, NFT#theDispatcherClaimsOnlyItsOwnTenantsRows |
| Empty and many | No offices, no bookings, empty report range; 500 desks, 1,500 desks, 1,250-row sync chunks, 200-booking release batches | A,U | ACC#ac1_7_and_os2_...; ACC#rp_...; ACC#ac4_10_...; ACC#os5_...; PSS#aLargeSetIsAppliedInChunks; BSP#theRunReleasesBatchByBatchSkipsChangedOnesAndCountsFailures |
| Integration down | SuccessFactors unreachable, 401/403, 429, empty answer, drop guard; mail service down (retry 3 times, circuit breaker); a hand-over listener that throws rolls back the whole transaction | U,A | PSR (28), BaseClientPeopleSourceTest (6), NFT#aMailServerThatIsDownRetriesAt20And40And60MinutesThenFailsAndTheBookingIsUntouched, NFT#fiveFailuresInARowStopTheRunOpenTheBreakerAndUseNoFurtherAttempts, SCS (3 rollback tests) |
| Privacy | Reports hold no person field; export header has no names or ids; mail address never logged; no message names another employee | U | RPT; OES#theFileHasAHeaderThenTheFloorRowsAndTheAllFloorsLinePerOfficeAndDay; MAT#theMessageNeverPrintsTheAddress; MTT#noMessageNamesAnotherEmployeeOrTheProduct |
| Idempotence | Job runs twice in a minute: nothing changes; reminder key carries the deadline; sync second run changes no version column | A,U,R | ACC#ac8_5_...; NPT#eventKeysAreStablePerEventAndTheReminderKeyCarriesTheDeadline; PSS#aSecondRunOverTheSameDataChangesNothingNotEvenTheVersionColumns |
| Contract | Every route in the controllers is in 05-openapi with the same operationId; the frontend calls only paths of the generated contract; migrations match the entities | C,F,R | OCC2#everyRouteIsDeclaredInTheContractFile; BCC#everyRouteIsInTheContractFileWithTheSameOperationId; FE contract.test (2); MMT (7); H2SchemaTest |

## Manual and end-to-end steps for the developer

Nothing here was started by QA (no server, no browser, no real service).

| Step | What to do and what must happen |
|---|---|
| E1 | Load: sign in as an employee on dev (real PostgreSQL), seed one office with 500 desks, open Book a desk for tomorrow; the first screen must show in under 2 s and the rest load by scrolling. Then open My bookings right after booking: the new row must show within 1 s. Repeat with 500 users for ST-RP-5. |
| E2 | Race on real PostgreSQL: from two browsers (two users) press Book on the last free desk at the same moment, and double-click Book once; exactly one booking must exist, the other user sees "Just taken". Check ux_bkg slot and person-day unique indexes exist (Flyway V030 ran). |
| E3 | Session expiry: sign in, wait for the session to end (or delete the Approuter cookie), press Book; expect sign-in again and a page that says the booking was not saved. |
| E4 | Screens in a browser (desktop and 360 px): S1 Today (empty state with Book a desk, skeleton, error with retry, two-week strip with Add day tile and its link to /book?days=), S2 (How check-in works box on S3 for one day, several days and a booking made for someone), S4 My bookings empty state, S17 Reports (empty range shows the text and disables Export). Needs a browser or a component test stack (jsdom + Testing Library, review item S17). |
| E5 | Real SuccessFactors: on dev run PeopleSyncJob with Run now (ADHOC) for a tenant with about 3,000 users; check the run finishes in under 10 minutes and shows counts new/changed/left; then block the SF host and run again: the last copy stays, the run is Failed, the date of the last good copy shows. Also proves Q167 and Q168. |
| E6 | Real mail: set DESKBOOK_MAIL_MODE=LIVE on dev, book a morning desk, wait for the 15-minute reminder (check-in and keep-my-desk links) and for the release notice at the deadline; stop the mail service and check 3 retries over 1 hour then Failed in the job log. |
| E7 | Export: on dev with 30,000 report rows press Export to Excel; the file must arrive within 30 s with the same rows and columns as the screen; with more than 100,000 rows the message asks to narrow the dates or office. |
| E8 | Sign-in: open any DeskBook URL without a session; expect the company sign-in page and, after sign-in, the page you asked for. Open an employee account without a DeskBook role: expect No access. |
| E9 | Scheduler: on the Background Jobs page register ReleaseBookingsJob, NotificationDispatchJob and PreReleaseReminderJob with a one-minute schedule; after 2 minutes check a result row each and that a failed mail row shows in the job log without an address. |
| E10 | After the feature exists: reserved desks (ST-BK-8 criterion 6, ST-RP-3 criterion 3), blocking a desk (ST-RP-3 criterion 1), booking for a direct report (ST-BK-10 criterion 2, with ST-TM-5). Not in the MVP build, so not testable now. |

Alias list: see the end of `07-test-report.md`.
