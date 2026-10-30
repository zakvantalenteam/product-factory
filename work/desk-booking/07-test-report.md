# 07 Test report - DeskBook (desk-booking)

Stage S7, refreshed 2026-10-29 after the S7, pre-audit and audit fix rounds (build log "Fix round S7", "Pre-audit fixes", "Audit fix round"), qa-engineer. Plan: `07-test-plan.md`. Product root `D:/products/desk-booking`.

## Result first

**Lead note 2026-10-29 (after the re-audit theme fix): backend 748 tests, 0 failures. One obsolete test ("theme body ignores unknown fields") was replaced by a 15th case in `ClosedRequestBodiesTest`.**

**Refresh of 2026-10-29: backend 749 tests, 0 failures, 0 errors, 0 skipped (72 suites); frontend 215 tests passed (25 files); `tsc -b` clean.** Before the refresh: 637 and 201.

**166 MVP criteria (40 stories): 150 PASS, 0 FAIL, 16 NOT RUN.** (Before: 149 PASS, 1 FAIL, 20 NOT RUN; 170 criteria until D10 moved four to R1.) Four more criteria are **moved to R1 (D10)** and not counted: BK-8.6, BK-10.2, RP-3.1, RP-3.3.

- **FAIL (0):** ST-BK-8 criterion 3 (BK-8.3, Q198) is now PASS: `proposeDesks` answers NO_MATCH with up to 3 alternatives (Q201), the plan screen lists them with a Choose button (Q202), backend and frontend tests name them.
- **Evidence added since the first report (rows updated):** rate limits (RateLimiterTest, BookingBatchAndProposalTest, BookingServiceTest, DeskAccessGuardTest, RateLimitAndBodyLimitHttpTest), 16 KB body limit and key format, closed request bodies through the application mapper (ClosedRequestBodiesTest, 5), the 16 base shell operations (ShellControllerContractTest, 20), the batch race tests (DeskBookBatchRaceTest, 5), the booking-slot insert-order deadlock fix (race and acceptance tests), tenant-filter guard (TenantFilterGuardTest), test-context isolation (Q199), people sync guards (old leavers, fields missing, drop floor), async settings recompute, hold needs the check-in window.
- **NOT RUN (16):** 6 need a real server, browser, PostgreSQL, SuccessFactors or Approuter (load, session, sync, export, sign-in: E1, E3, E5, E7, E8); 10 are screen elements or states with no component test (E4, gap G1). The 4 criteria for features not built in the MVP (reserved desks x2, blocking a desk, booking for someone) are moved to R1 (D10, Q200) and no longer count; step E10 is dropped.
- **Production code:** not touched. No failing test, no new finding.
- **Not proven, in one line each:** the PostgreSQL race (E2), load figures (E1, E7), the real SuccessFactors call (E5), real mail (E6), the scheduler firing the jobs (E9), what a screen draws (E4), an end-to-end journey over HTTP, filters, Approuter and the SPA (audit M13b, dev step), and the rate and body limits behind the real filter chain of a running app (only RateLimitAndBodyLimitHttpTest, a filter test).

## Commands run

All on 2026-10-29, offline, no server started.

| Command | Result |
|---|---|
| `mvn -o -q clean test -pl Backend` | exit 0; 72 suites, **749 tests, 0 failures, 0 errors, 0 skipped** (summed from the surefire XML in `Backend/target/surefire-reports`) |
| `npx vitest run` in Frontend | 25 files, **215 tests passed** |
| `npx tsc -b` in Frontend | exit 0, no output |
| Check that every test named in this report exists in the surefire XML | 2 stale names corrected (PSS people first load, RCT employee 403); the rest are listed by prefix on purpose (ACC#ciOne_..., PDR#refusal) |

## Criteria

PASS = an automated test that ran and passed covers the rule, data or wording. FAIL = the criterion is not met. NOT RUN = needs something the offline run cannot give, or the feature is not built; the step is in the plan.

| Criterion | Case | Result | Evidence (test class#method) |
|---|---|---|---|
| **ST-BK-1 Find free desks by office, date and part of day** | | | |
| BK-1.1 AC4.1 Given 40 free desks, when Asha picks Pune, tomorrow, full day, then she sees 40 desks ... | TC-BK-1-1 | **PASS** | BQS#freeDesksArePagedWithTheWholeCountAndTheServerTime; ACC#ac4_10_fiveHundredDesksArePagedWithTheWholeCountAndTheFirstPageIsSmall |
| BK-1.2 AC4.6 Given a date before today, beyond the horizon, a weekend or a closed day, when she opens ... | TC-BK-1-2 | **PASS** | BQS#theCalendarRunsFromTodayToTheHorizonWithReasonsPerPart; PDR#refusal; FE plan.test "takes the reason of each refused day from the answer" |
| BK-1.3 AC4.8 Given a blocked or retired desk, then it is never listed. | TC-BK-1-3 | **PASS** | ACC#ac4_8_aRetiredDeskIsNeverListedAndCannotBeBooked; BQS#aDeskNotBookableYetIsNotListed Note: Blocked desks (ST-OS-11) are not in the MVP build; retired covers the rule. |
| BK-1.4 AC4.10 Given 500 desks, when the list loads, then the first screen shows in under 2 seconds ... | TC-BK-1-4 | **NOT RUN** | Paging proven (ACC#ac4_10: first page 50 of 500, count 500, 10 pages; H2 first page well under 2 s, indicative only). The 2 s on real PostgreSQL in a browser is a load figure. Step E1 |
| BK-1.5 AC4.11 Given a morning booking on desk X, when Ravi searches the afternoon, then X is listed ... | TC-BK-1-5 | **PASS** | BQS#aFullDayBookingTakesBothHalvesAndAHalfDayOnlyItsOwn; ACC#ac5_1_and_5_10_aFullDayBookingTakesBothHalvesAndLeavesEveryonesList |
| BK-1.6 AC1.7 Given no office is Open, when an employee opens booking, then she sees 'No offices are ... | TC-BK-1-6 | **PASS** | ACC#ac1_7_and_os2_aDraftOfficeIsNotInThePickerAndOpeningItPutsItThere (empty answer); FE screenTexts "AC1.7 says ..." (both texts) Note: Screen shows the text from the empty answer: part of gap G1. |
| **ST-BK-5 Book a desk** | | | |
| BK-5.1 AC5.1 Given a free desk, when Asha books it, then she sees desk, office, date, part of day, ... | TC-BK-5-1 | **PASS** | ACC#ac5_1_and_5_10_...; BSV#createsThroughTheCommandWithTheTrimmedKeyAndAssemblesTheResponse; BCS#createsAFullDayBookingWithTwoSlotsAndTheReleaseDeadline Note: Desk, office, date, part, deadline and check-in opening are in the answer; the screen is gap G1. |
| BK-5.2 AC5.2 Given Asha already has an active booking that day, when she tries another, then it is ... | TC-BK-5-2 | **PASS** | ACC#ac5_2_a_second_desk_the_same_day_is_refused_and_names_the_first_booking; BCS#aSecondBookingTheSameDayNamesTheExistingOne; FE screenTexts "AC5.2" |
| BK-5.3 AC5.6 Given a date beyond the horizon sent by a tampered request, when received, then it is ... | TC-BK-5-3 | **PASS** | BCS#aDateBeyondTheHorizonAndAPastDateAreRefused; BBP#otherRefusalsKeepTheirCodeAndReason; BCS#aWeekendIsRefusedWithItsReason; CRB#everyClosedRequestSchemaRefusesAnUnknownFieldWithUnknownField; BSV#theKeyMayHoldOnlyLettersDigitsUnderscoreAndHyphen; RBH#aBodyOfExactlySixteenKilobytesPassesAndOneByteMoreIsRefused |
| BK-5.4 AC5.10 Given a full-day booking, then it occupies morning and afternoon of that desk. | TC-BK-5-4 | **PASS** | ACC#ac5_1_and_5_10_...; BRT#twoPeopleCannotHoldTheSameDeskHalfAtOnce; BCS#createsAFullDayBookingWithTwoSlotsAndTheReleaseDeadline |
| BK-5.5 AC17.3 Given her session expired, when she presses Book, then she signs in again and the page ... | TC-BK-5-5 | **NOT RUN** | Session expiry and sign-in again are Approuter/IAS behaviour; the API answers 401 (RMC#everyOperationRefusesAnAnonymousCallerWith401AndTouchesNothing). Step E3 |
| BK-5.6 NEW(GP) [F5] Given any booking confirmation (one day, several days, booked by a manager), then ... | TC-BK-5-6 | **NOT RUN** | The box is a screen element (HowCheckInNote on S3); no component test exists (gap G1). The label "How check-in works" exists (FE screenTexts). Step E4 |
| **ST-BK-6 Two people, one desk: just taken, double click, desk blocked a minute ago** | | | |
| BK-6.1 AC5.3 Given Asha and Ravi press Book on the last desk in the same second, then one booking ... | TC-BK-6-1 | **PASS** | ACC#ac5_3_asecond_person_on_a_taken_desk_gets_just_taken; ACC#ac5_3_and_5_4_twoThreadsPressingBookTogetherLeaveExactlyOneBooking; BRT#twoPeopleCannotHoldTheSameDeskHalfAtOnce; BCS#aTakenSlotBecomesDeskJustTaken Note: Proven on H2 (unique index rebuilt there); the PostgreSQL race itself (Q158) is step E2.; DBR#a1_twoPeopleBookTheSameFiveDeskDaysAtOnceEachDayHasOneWinner, DBR b1 (10 runs each); TCI#rowsCommittedInOneContextAreNotVisibleInAnother. The booking-slot insert-order deadlock found before the audit is fixed in BookingCommandService; the race tests ran 10 of 10 after the fix |
| BK-6.2 AC5.4 Given Asha double-clicks Book, then only one booking exists. | TC-BK-6-2 | **PASS** | ACC#ac5_4_aDoubleClickWithTheSameKeyIsOneBooking; BCS#theSameKeyReturnsTheFirstBookingAndADifferentRequestIsRefused; FE plan.test "makes a new key for each press"; BSV#aDoubleSubmitWithTheSameKeyAnswersWithTheFirstBookingNotAlreadyBooked; BCS#replayOfReturnsTheFirstBookingOfTheSameKeyOnlyAfterTheTwoRaceFailures; BCS#theSameKeyWithAnotherDayIsStill422EvenAfterARace; DBR#c1_theSamePersonSubmitsTheSameBatchTwiceWithOneKeyAtOnce |
| BK-6.3 AC5.5 Given the desk was blocked a minute ago, when she books, then it is refused with 'desk ... | TC-BK-6-3 | **PASS** | BCS#anOfficeOrDeskThatChangedAfterTheContextWasReadIsRefusedInsideTheTransaction; ACC#ac4_8_... (DESK_NOT_AVAILABLE) Note: Criterion says blocked: blocking is R1; retired desk uses the same answer. |
| BK-6.4 NEW(R21) Given an office closed or a desk retired a moment ago, when she books, then it is ... | TC-BK-6-4 | **PASS** | BCS#anOfficeOrDeskThatChangedAfterTheContextWasReadIsRefusedInsideTheTransaction; BCS#anUnknownDeskIs404AndARetiredOrForeignDeskIsNotAvailable |
| **ST-BK-7 Book for today until the end of the day part** | | | |
| BK-7.1 NEW(P1) Given today 10:30 and a desk free for the full day after a release, when she books, ... | TC-BK-7-1 | **PASS** | ACC#ciSix_aBookingMadeAfterTheReleaseMustBeCheckedInWithin30MinutesOrIsReleasedAgain; BCS#aBookingMadeAfterTheReleaseTimeIsLateAndGetsThirtyMinutes; FE plan.test "marks a free cell late only when the server says so" |
| BK-7.2 AC4.7 (revised) Given today and the part of the day has ended, when she picks today, then that ... | TC-BK-7-2 | **PASS** | BQS#todayIsOpenUntilThePartEndsAndLateBookingsAreFlagged; PDR#morningOfTodayIsRefusedOnceTheMiddayHasPassedButTheAfternoonIsNot; FE plan.test "takes the reason of each refused day from the answer" |
| BK-7.3 AC5.7 (revised) Given a booking for a part of today that has ended, when sent, then it is ... | TC-BK-7-3 | **PASS** | ACC#ac5_7_aBookingForAPartOfTodayThatHasEndedIsRefused; BCS#todayIsBookableUntilThePartHasEnded |
| BK-7.4 NEW Given a booking made before the release time, then the normal deadline applies. | TC-BK-7-4 | **PASS** | BCS#createsAFullDayBookingWithTwoSlotsAndTheReleaseDeadline; PDR#bookingMadeBeforeTheReleaseGetsTheReleaseTime; ACC#ac8_1_... (deadline 04:30Z) |
| BK-7.5 NEW Given she books for an afternoon desk at 11:00, then the afternoon deadline applies. | TC-BK-7-5 | **PASS** | PDR#afternoonBookingMadeInTheMorningIsNotLate; ACC#ac8_1_... (afternoon booking released only at 14:05) |
| **ST-BK-8 Best desk for me** | | | |
| BK-8.1 NEW(P4) [AC19.1] Given a day and part of the day (and optionally zone and features she ... | TC-BK-8-1 | **PASS** | BBP#proposesTheFirstFreeDeskPerDayInDateOrder; DPR#chosenZoneAndFeaturesFilterTheCandidatesAndGiveMatchesChoices |
| BK-8.2 NEW(GP) [F4/F5, AC19.1, AC19.6] Given a proposal, then it carries a reason tag, chosen in this ... | TC-BK-8-2 | **PASS** | DPR#theUsualDeskWinsWhenItIsFree; DPR#withoutTheUsualDeskTheLowestCodeInHerZoneWins; DPR#chosenZoneAndFeaturesFilterTheCandidatesAndGiveMatchesChoices; DPR#withNoUsualDeskTheFirstFreeCodeWinsAndCodesAreComparedIgnoringCase Note: Last tag is the lowest free code ("Closest free desk" in the story). |
| BK-8.3 NEW [AC19.5] Given no desk matches her choices, then the nearest zone or feature options are ... | TC-BK-8-3 | **PASS** | BBP#whenDesksAreFreeButNoneMatchesTheAnswerIsNoMatchWithTheNearestOptions; BBP#anUnfilteredRequestNeverGetsNoMatch; BBP#noDeskFreeAtAllIsNothingFreeEvenWithFilters; DPR#theAlternativesComeInTheDesignedOrderAndStopAtThree; FE plan.test "keeps the alternatives of a NO_MATCH day (at most 3) with their reasons", "one tap on an alternative turns the day into her own choice, booked as CHOSEN", "NOTHING_FREE keeps the old text and has no alternatives", "does not say all full while a day offers alternatives" Note: Was FAIL (Q198); fixed in fix round S7 (Q201, Q202): NO_MATCH carries up to 3 alternatives (usual desk, nearest zone, other zone, without a feature, any free). The Choose button on the screen is gap G1. |
| BK-8.4 NEW(GP) [F5, AC19.4] Given the proposed desk is taken between the proposal and the booking, ... | TC-BK-8-4 | **PASS** | BBP#aTakenProposedDeskIsRepickedAndReportedWithThePreviousCode; BBP#repicksStopAfterTwoAndThenTheDayFails |
| BK-8.5 NEW(GP) [F5, AC19.3, AC19.12] Given a proposal, then 'Change' opens the picker for that day ... | TC-BK-8-5 | **PASS** | FE plan.test "lets her own choice win over the proposal", "groups free desks by floor and zone in order of appearance"; BQS#freeDesksArePagedWithTheWholeCountAndTheServerTime Note: Dialog rendering is gap G1. |
| BK-8.6 NEW [AC19.9] Given a reserved desk, then it is never proposed to someone not on the access ... | TC-BK-8-6 | **Moved to R1 (D10)** | Now ST-PP-10 (reserved desks are not in the MVP build). Not counted in the MVP totals. |
| **ST-BK-9 My bookings list** | | | |
| BK-9.1 AC6.3 Given she has no bookings, then My bookings says 'No bookings yet' with a Book a desk ... | TC-BK-9-1 | **NOT RUN** | Empty list answer is covered (BSV#anUnknownSortIsRefusedAndAPersonOutsideTheCopyHasNoBookings) and the text exists (FE screenTexts "AC6.3"); the empty state with its Book a desk button is a screen element. Step E4 |
| BK-9.2 AC5.11 Given the booking succeeded, when she opens My bookings, then it is shown within 1 ... | TC-BK-9-2 | **NOT RUN** | ACC#ac5_4_... shows the new booking in the list at once; the 1 s figure needs real PostgreSQL and a browser. Step E1 |
| BK-9.3 NEW Given upcoming and past bookings, then rows show date, office, desk, part, status and ... | TC-BK-9-3 | **PASS** | BSV#listsHerBookingsPagedAndAssembled; ACC#ac5_4_aDoubleClickWithTheSameKeyIsOneBooking (list); BSV#createsThroughTheCommandWithTheTrimmedKeyAndAssemblesTheResponse Note: "Booked by" is in the answer (bookedByName); the manager flow is R1 (Q200). |
| BK-9.4 NEW(P5) Given statuses, then the words are Booked, Checked in, Completed, No-show and ... | TC-BK-9-4 | **PASS** | FE screenTexts "P5 says ..." (No-show, Checked in, Completed, Cancelled, Booked by, Check-in deadline); MTT#theReleaseNoticeSaysNoShowAndHowToBookForToday |
| **ST-BK-10 Cancel my booking** | | | |
| BK-10.1 AC6.1 Given a booked desk, when Asha cancels, then status is Cancelled, the desk is free in ... | TC-BK-10-1 | **PASS** | ACC#ac6_1_and_6_5_and_6_6_cancelFreesTheDeskForOthersAndOthersCannotCancelIt; BCS#cancelFreesTheSlotsAndRecordsTheReason Note: Confirmation toast is gap G1. |
| BK-10.2 AC6.4 Given a booking made by her manager, when she cancels it, then it is cancelled and the ... | TC-BK-10-2 | **Moved to R1 (D10)** | Now ST-TM-5 (a booking made by a manager has no producer in the MVP build); the cancel rule is owner-based and tested for the person herself. Not counted in the MVP totals. |
| BK-10.3 AC6.5 Given a cancel request for someone else's booking sent by a tampered request, then it is ... | TC-BK-10-3 | **PASS** | ACC#ac6_1_... (another person gets 404); BCS#cancelOfAnotherPersonsOrACheckedInBookingIsRefused; BSV#getBookingAnswersOnlyHerOwn; BRT#lookupsByIdAreTenantAndOwnerScoped |
| BK-10.4 AC6.6 Given the booking was already released by the system, when she presses Cancel on an old ... | TC-BK-10-4 | **PASS** | ACC#ac6_1_... (BOOKING_STATE_CHANGED with currentStatus NO_SHOW); BSV#aLostRaceAnswersTheRealStatus; FE booking errors.test "shows the real status of a stale booking" |
| BK-10.5 NEW(D2) Given a checked-in booking, then Cancel is not offered (the day completes). | TC-BK-10-5 | **PASS** | ACC#d2_aCheckedInBookingCannotBeCancelled; BSV#allowedActionsFollowTheClockAndTheStatus |
| **ST-BK-11 Today page** | | | |
| BK-11.1 NEW Given bookings, when she opens Today, then the next 3 bookings show with check-in deadline ... | TC-BK-11-1 | **PASS** | TSV#carriesTheOfficeTimezoneAndTodayAndFourteenDays (next 3, NEXT_BOOKINGS); BSV#allowedActionsFollowTheClockAndTheStatus; FE cardState.test "offers Check in when the server lists CHECK_IN" Note: Deadline and button on the card are gap G1. |
| BK-11.2 NEW Given no booking, then 'No bookings yet' and a Book a desk button show. | TC-BK-11-2 | **NOT RUN** | Empty answer covered (TSV#aPersonNotInTheCopyStillGetsAnEmptyToday); the "No bookings yet" text and button are screen elements. Step E4 |
| BK-11.3 NEW(GP) [F4] Given her home office, then 'Pune tomorrow: N of M desks free' shows, where M ... | TC-BK-11-3 | **PASS** | TSV#tomorrowShowsFreeAndBookableDesksAtTheHomeOffice; TSV#tomorrowIsLeftOutOnAWeekend |
| BK-11.4 NEW Given the admin and a failed people copy for 2 days, then the warning banner shows (links ... | TC-BK-11-4 | **PASS** | TSV#onlyAdminsSeeTheSyncBannerAfterTwoDaysWithoutACopy Note: Banner render is gap G1. |
| BK-11.5 NEW Given loading or error, then a skeleton or a retry shows. | TC-BK-11-5 | **NOT RUN** | Skeleton and retry card are screen states with no component test. Step E4 |
| **ST-BK-12 After a release: note and rebook** | | | |
| BK-12.1 AC8.7 (revised) Given Asha opens the app at 10:05 after her booking was released, then she ... | TC-BK-12-1 | **PASS** | TSV#aReleasedBookingTodayGivesTheNoteAndWhetherRebookingIsPossible; ACC#ac8_1_... (released desk is in the free list) Note: Note render is gap G1. |
| BK-12.2 NEW(P1) Given the note, then it says she can book a desk for the rest of today and one tap ... | TC-BK-12-2 | **PASS** | TSV#aReleasedBookingTodayGivesTheNoteAndWhetherRebookingIsPossible; TSV#noRebookingIsOfferedWhenSheHasAnotherActiveBookingOrTheDayIsOver Note: The one-tap link is gap G1. |
| BK-12.3 NEW Given a released booking, then it shows as No-show in My bookings. | TC-BK-12-3 | **PASS** | ACC#ac8_1_... (status NO_SHOW read back); FE screenTexts "P5 says No-show" |
| **ST-BK-13 Plan my days: book several days in one action** | | | |
| BK-13.1 NEW(GP, Q90) [F5] Given she ticks Tue, Wed and Thu within the booking horizon, then each day ... | TC-BK-13-1 | **PASS** | BBP#everyDayIsBookedWithItsOwnKeyAndStrictnessFollowsTheSource; FE plan.test "books only the days with a desk and marks chosen and proposed desks"; BRT#aPersonCannotHaveTwoActiveBookingsOnOneDay Note: Separate bookings: each has its own key and id, so each cancels alone.; DBR#a2_fourPeopleOverlappingOffsetBatchesWithProposedDesksStayConsistent; DBR#b2_aBatchAndTheSamePersonsSingleBookingOnAnotherDeskNeverGiveTwoBookingsOnOneDay |
| BK-13.2 NEW(GP) [F5] Given a day where she already has an active booking, a closed day, a weekend or a ... | TC-BK-13-2 | **PASS** | FE plan.test "shows an own booking as booked and not pickable", "drops picked days that are no longer free and counts them"; BQS#theCalendarRunsFromTodayToTheHorizonWithReasonsPerPart |
| BK-13.3 NEW(GP) [F5] Given a desk is taken or the day fails between proposal and booking, then the ... | TC-BK-13-3 | **PASS** | BBP#aTakenChosenDeskFailsThatDayOnlyAndOtherDaysStayBooked; BBP#aTakenProposedDeskIsRepickedAndReportedWithThePreviousCode; BBP#otherRefusalsKeepTheirCodeAndReason; FE booking errors.test; DBR#b1_aBatchAndAnotherPersonsSingleBookingFightOverOneDay; BBP#aBatchDayThatLostTheSameKeyRaceAnswersWithTheFirstBooking; BBP#aDayKeyUsedWithOtherContentFailsThatDayOnlyWithIdempotencyKeyReused |
| BK-13.4 NEW(GP) [F5] Given the result, then one confirmation lists every day with desk, deadline and ... | TC-BK-13-4 | **NOT RUN** | One confirmation page (DonePage, BookingResultList) is rendering only; no component test. Step E4 |
| BK-13.5 NEW(GP) [F5] Given 14 days ticked, then all are accepted; the 15th is not (horizon). | TC-BK-13-5 | **PASS** | BBP#theNumberOfDatesIsBoundedAndDatesMustBeDistinct; BBP#theRequestItselfIsValidatedAndAProfileThatIsNotReadyFailsAsAWhole; BCC#anUnknownPropertyAMissingFieldAndAnOutOfRangeRuleAreRefusedWith400; BBP#thirtyOneBookingDaysInAMinuteGive429AndNoPartialBatch; BBP#aFourthBatchInAMinuteIsRefusedEvenWithOneDay; RLT#thirtyOneBookingDaysAcrossBothOperationsAreRefusedWithNoPartialBatch; CRB#anUnknownFieldInsideABatchItemIsRefusedWithItsPath |
| BK-13.6 NEW(R) Given a tampered request with a day outside the rules, then that day is refused ... | TC-BK-13-6 | **PASS** | BBP#otherRefusalsKeepTheirCodeAndReason; BCS#aWeekendIsRefusedWithItsReason; BCS#aDateBeyondTheHorizonAndAPastDateAreRefused; BBP#aRepeatedDateIsRefusedBeforeAnyLimitIsCounted |
| **ST-BK-14 Change a desk: picker per proposed day** | | | |
| BK-14.1 NEW(GP) [F4/F5] Given a proposed day, when she presses 'Change', then the free desks for that ... | TC-BK-14-1 | **PASS** | FE plan.test "groups free desks by floor and zone in order of appearance"; BQS#freeDesksArePagedWithTheWholeCountAndTheServerTime Note: Dialog is gap G1. |
| BK-14.2 NEW(GP) [F4/F5] Given she picks a desk, then the proposal for that day becomes that desk with ... | TC-BK-14-2 | **PASS** | FE plan.test "lets her own choice win over the proposal", "books only the days with a desk and marks chosen and proposed desks" |
| BK-14.3 NEW(GP) [F4/F5] Given the picked desk is taken before she books, then she is told and the list ... | TC-BK-14-3 | **PASS** | BBP#aTakenChosenDeskFailsThatDayOnlyAndOtherDaysStayBooked; FE booking errors.test (DESK_JUST_TAKEN) Note: The list refresh after the message is gap G1. |
| **ST-BK-15 Your next two weeks strip with Add day tiles** | | | |
| BK-15.1 NEW(GP) [F6, AC18.5] Given her bookings, when she opens Today, then a strip shows the next two ... | TC-BK-15-1 | **NOT RUN** | Strip data covered (TSV#theStripMarksBookedBookableAndNonWorkingDays); the tiles and the Add day tile are rendering. Step E4 |
| BK-15.2 NEW(GP) [F6, AC18.2] Given she taps 'Add day', then the plan screen (ST-BK-13) opens with that ... | TC-BK-15-2 | **NOT RUN** | The link from Add day to /book?days= is routing and rendering; not unit tested. Step E4 |
| BK-15.3 NEW(GP) [F6] Given a closed day or weekend, then it is not shown as a tile. | TC-BK-15-3 | **PASS** | TSV#theStripMarksBookedBookableAndNonWorkingDays; TSV#daysBeyondTheHorizonAreOutsideTheWindowAndClosedDaysAreClosed |
| BK-15.4 NEW Given loading or error, then a skeleton or a retry shows. | TC-BK-15-4 | **NOT RUN** | Skeleton and retry are screen states with no component test. Step E4 |
| **ST-CI-1 Check in by button** | | | |
| CI-1.1 AC7.1 Given a morning booking and 08:15 local, when Asha presses Check in, then status is ... | TC-CI-1-1 | **PASS** | ACC#ciOne_checkInOpensAtSixAndAnAfternoonBookingAtTwelveAndTwoPressesCheckInOnce; BCS#checkInOpensAtSixAndClosesAtTheDeadline |
| CI-1.2 AC7.6 Given before 06:00 or after the check-in deadline, when she presses Check in, then it is ... | TC-CI-1-2 | **PASS** | ACC#ciOne_... (04:30 refused, CHECK_IN_NOT_OPEN); ACC#ac7_6_afterTheDeadlineCheckInIsRefusedAndTheRealStatusShows; FE booking errors.test "shows the opening time of check-in in the office timezone" |
| CI-1.3 AC7.7 Given she presses Check in twice, then she is checked in once. | TC-CI-1-3 | **PASS** | ACC#ciOne_... (second press, same checkedInAt); BCS#anAfternoonBookingOpensAtTwelveAndASecondPressChangesNothing |
| CI-1.4 AC7.8 Given an afternoon booking at 11:00, then Check in is disabled until 12:00 and says so. | TC-CI-1-4 | **PASS** | ACC#ciOne_... (11:00 refused, 12:01 accepted); FE cardState.test "shows Check in disabled with the opening time before the window opens" |
| CI-1.5 NEW(P1) Given a booking made after the release time, then the deadline is 30 minutes after ... | TC-CI-1-5 | **PASS** | ACC#ciSix_aBookingMadeAfterTheReleaseMustBeCheckedInWithin30MinutesOrIsReleasedAgain (deadline 10:50 for a booking at 10:20); BCS#aBookingMadeAfterTheReleaseTimeIsLateAndGetsThirtyMinutes |
| **ST-CI-4 Release unchecked bookings at the check-in deadline** | | | |
| CI-4.1 AC8.1 Given a morning booking at Pune not checked in at 10:00 local, when the job runs, then ... | TC-CI-4-1 | **PASS** | ACC#ac8_1_to_8_3_and_8_6_8_8_theMinuteJobReleasesEachBookingAtItsOwnOfficesDeadline; BCS#releaseMarksNoShowFreesSlotsAndPublishesTheEvent Note: The base scheduler firing the job every minute is step E9. |
| CI-4.2 AC8.2 Given an afternoon booking, when 10:00 passes, then it is untouched; at 14:00 plus 5 ... | TC-CI-4-2 | **PASS** | ACC#ac8_1_to_8_3_... (afternoon untouched at 10:05, NO_SHOW at 14:05) |
| CI-4.3 AC8.3 Given a full-day booking not checked in at 10:00, then the whole booking is released, ... | TC-CI-4-3 | **PASS** | ACC#ac8_1_to_8_3_... (full-day released, afternoon half free again) |
| CI-4.4 AC8.6 Given Bengaluru and Berlin, when 10:00 arrives in Berlin, then only Berlin bookings are ... | TC-CI-4-4 | **PASS** | ACC#ac8_1_to_8_3_... (Berlin untouched at 10:05 Pune, released at 10:05 Berlin); PDR#pune_and_berlin_both_release_at_ten_on_their_own_clock_across_the_daylight_saving_change |
| CI-4.5 AC8.8 Given a cancelled booking, then the job ignores it and no email is sent. | TC-CI-4-5 | **PASS** | ACC#ac8_1_to_8_3_... (cancelled stays Cancelled, 2 notices for 2 releases); BCS#releaseSkipsABookingThatChangedOrIsNotDue |
| **ST-CI-5 Release job survives downtime, repeats and races** | | | |
| CI-5.1 AC8.4 Given a booking checked in at 09:59:58, when the job runs at 10:00, then it stays ... | TC-CI-5-1 | **PASS** | ACC#ac8_4_aCheckInOneSecondsBeforeTheDeadlineSurvivesTheJob; BCS#releaseSkipsABookingThatChangedOrIsNotDue; BSP#theRunReleasesBatchByBatchSkipsChangedOnesAndCountsFailures |
| CI-5.2 AC8.5 Given the job was down from 09:50 to 10:40, when it restarts, then every overdue booking ... | TC-CI-5-2 | **PASS** | ACC#ac8_5_aJobThatWasDownCatchesUpOnceAndSendsOneNoticePerBooking (3 released, 3 notices) |
| CI-5.3 NEW Given the job runs twice in the same minute, then nothing changes the second time. | TC-CI-5-3 | **PASS** | ACC#ac8_5_... (second run releases 0, still 3 notices); BSP#aRunWithNothingDueDoesNothing |
| **ST-CI-6 Late booking: check in within 30 minutes or it is released again** | | | |
| CI-6.1 NEW(P1) Given a booking made at 10:20 after the release, when 10:50 passes without check-in, ... | TC-CI-6-1 | **PASS** | ACC#ciSix_aBookingMadeAfterTheReleaseMustBeCheckedInWithin30MinutesOrIsReleasedAgain |
| CI-6.2 NEW Given she checks in at 10:45, then it stays Checked in. | TC-CI-6-2 | **PASS** | ACC#ciSix_... (checked in at 10:45 stays Checked in) |
| CI-6.3 NEW Given an afternoon booking made at 14:20, then the same 30 minutes apply. | TC-CI-6-3 | **PASS** | ACC#ciSix_anAfternoonBookingMadeAt1420HasTheSame30Minutes |
| CI-6.4 NEW Given such a release, then it is shown as 'Released after hold' and not counted in the ... | TC-CI-6-4 | **PASS** | ACC#rp_aLateReleaseAfterHoldIsItsOwnLineAndStaysOutOfTheNoShowRate; OCC#releasedAfterHoldIsItsOwnLineAndStaysOutOfTheRate; FE screenTexts "Q50 says Released after hold" |
| **ST-CI-7 Running late: keep my desk once** | | | |
| CI-7.1 NEW(P2) Given a booking not checked in before the deadline, when she taps 'Running late, keep ... | TC-CI-7-1 | **PASS** | ACC#ciSeven_runningLateKeepsTheDeskOnceUntilReleasePlus90MinutesThenReleasesAfterHold (deadline 11:30 for a 10:00 release); BCS#holdMovesTheDeadlineToReleasePlusNinetyMinutesOnce; FE cardState.test "lets the server list decide Running late when it names HOLD"; BCS#holdIsRefusedUntilTheCheckInWindowOfThatDayOpens (hold needs the check-in window open, 422 CHECK_IN_NOT_OPEN; B2-S1); BSV#theTwentyFirstCancelCheckInAndHoldInAMinuteAre429 |
| CI-7.2 NEW Given she already used it, then the tap is not offered again for that booking. | TC-CI-7-2 | **PASS** | ACC#ciSeven_... (holdAvailable false, second tap HOLD_ALREADY_USED); FE cardState.test "hides Running late once it was used" |
| CI-7.3 NEW Given the hold ends without check-in, then it is released as 'Released after hold' (Q50). | TC-CI-7-3 | **PASS** | ACC#ciSeven_... (RELEASED_AFTER_HOLD at 11:31) |
| CI-7.4 NEW Given she taps and then checks in, then status is Checked in. | TC-CI-7-4 | **PASS** | ACC#ciSeven_... (checks in during the hold, stays Checked in) |
| CI-7.5 NEW Given a release without the tap, then it is a No-show. | TC-CI-7-5 | **PASS** | ACC#ac8_1_to_8_3_... (no tap: NO_SHOW) |
| **ST-OS-1 Offices: create, list and edit** | | | |
| OS-1.1 AC1.1 Given an admin, when she saves a new office with name, city and timezone, then it ... | TC-OS-1-1 | **PASS** | OSV#createMakesADraftOfficeWithTheDefaultSettings; OCC2#createOfficeAnswers201WithALocationOfTheNewOffice; ORT#officeListsCountsAndLookupsSeeOnlyTheTenant Note: In the picker only after Open (ST-OS-2). |
| OS-1.2 AC1.2 Given a missing name, city or timezone, when she saves, then each missing field shows a ... | TC-OS-1-2 | **PASS** | FE officeSchemas.test "asks for name, city and timezone (AC1.2)"; OCC2#aBlankNameAndABadDeskCodeAreRefusedWithFieldErrors; CRB#everyClosedRequestSchemaRefusesAnUnknownFieldWithUnknownField (an unknown office field is 400 UNKNOWN_FIELD) |
| OS-1.3 AC1.3 Given an office 'Pune', when she creates 'pune', then it is refused with 'name already ... | TC-OS-1-3 | **PASS** | OSV#createRefusesANameUsedIgnoringCase; ORT#officeNameIsUniqueIgnoringCaseWithinATenant; FE office errors.test "maps every office code to its label key" Note: Wording is "An office with this name already exists." (UX text), not "name already used". |
| OS-1.4 AC1.6 Given two admins editing the same office, when the second saves, then she sees 'changed ... | TC-OS-1-4 | **PASS** | OSV#updateWithAStaleVersionIsAConflict; FE officeApi.test "turns a 409 CONCURRENT_UPDATE problem into an ApiError with its code"; FE office errors.test "is true for CONCURRENT_UPDATE and a bare 409" Note: Conflict dialog is gap G1. |
| OS-1.5 AC3.7 Given an unknown timezone value, when saved, then it is refused; the timezone is chosen ... | TC-OS-1-5 | **PASS** | OSV#createRefusesAnUnknownTimezone; OSV#createAcceptsIanaRegionIdsAndUtc; FE office state.test "lists IANA ids with UTC" |
| **ST-OS-2 Office states: Draft, Open, Closed** | | | |
| OS-2.1 AC1.4 Given an office with bookings, when she tries to delete it, then it is refused and ... | TC-OS-2-1 | **PASS** | There is no delete-office operation in the contract (05-openapi has none); OSV#closeIsRefusedWithFutureBookingsAndCarriesOnlyTheCount; OCC2#hasFutureBookingsCarriesTheCountAsAProblemMember Note: Refusal is by design: nothing to delete, Close is offered. |
| OS-2.2 NEW(Q41) Given a new office, then its state is Draft and it is not in the employee picker. | TC-OS-2-2 | **PASS** | OSV#createMakesADraftOfficeWithTheDefaultSettings; ACC#ac1_7_and_os2_aDraftOfficeIsNotInThePickerAndOpeningItPutsItThere |
| OS-2.3 NEW Given she presses 'Open office', then it is visible to employees. | TC-OS-2-3 | **PASS** | OSV#openMovesADraftOfficeToOpenAndSetsTheCapacityStart; ACC#ac1_7_and_os2_... (listed after Open); FE office state.test "opens a draft, closes an open office" |
| OS-2.4 NEW Given a closed office, then it is hidden from booking; with future bookings it is refused ... | TC-OS-2-4 | **PASS** | OSV#closeMovesAnOpenOfficeToClosed; OSV#closeIsRefusedWithFutureBookingsAndCarriesOnlyTheCount; BQS#listsOpenOfficesWithTheirLocalToday |
| **ST-OS-3 Floors: add and retire** | | | |
| OS-3.1 AC1.8 Given a floor name already used in that office, when saving, then it is refused. | TC-OS-3-1 | **PASS** | FZS#createFloorRefusesADuplicateNameIgnoringCaseWith409; ORT#floorNameIsUniqueInTheOffice |
| OS-3.2 NEW Given a new floor name, when saved, then it appears on the Floors tab. | TC-OS-3-2 | **PASS** | FZS#createFloorAlsoCreatesTheDefaultZoneMain; FZS#listFloorsFiltersByStatusAndRefusesAnUnknownOne |
| OS-3.3 NEW Given she retires a floor without future bookings, then its desks are hidden from booking; ... | TC-OS-3-3 | **PASS** | FZS#retireFloorSetsRetiredOnAndIsFinal; FZS#retireFloorIsRefusedWhileFutureBookingsExistAndCarriesTheCount |
| **ST-OS-4 Zones per floor** | | | |
| OS-4.1 AC2.4 (revised) Given a new floor, then zone 'Main' exists and a desk with no zone gets 'Main'. | TC-OS-4-1 | **PASS** | FZS#createFloorAlsoCreatesTheDefaultZoneMain; DSV#createPutsTheDeskInTheZoneMainWhenNoneIsGivenAndItIsBookableFromTomorrow |
| OS-4.2 NEW(Q42) Given an admin, when she adds or renames a zone, then desks pick zones from this list ... | TC-OS-4-2 | **PASS** | FZS#createZoneTrimsAndRefusesADuplicateOnTheSameFloor; FZS#renameZoneChecksIfMatchAndNameAndReportsTheDeskCount; DSV#createRefusesAZoneOfAnotherFloor |
| OS-4.3 NEW Given a zone with desks, then it cannot be deleted. | TC-OS-4-3 | **PASS** | FZS#deleteZoneIsRefusedWhileAnyDeskUsesIt; FZS#deleteZoneSoftDeletesAnUnusedZone |
| OS-4.4 NEW Given a zone name already used on that floor, then it is refused. | TC-OS-4-4 | **PASS** | FZS#createZoneTrimsAndRefusesADuplicateOnTheSameFloor; ORT#zoneNameIsUniqueOnTheFloor |
| **ST-OS-5 Desks: create, edit and retire** | | | |
| OS-5.1 AC2.1 Given an admin, when she creates a desk with code, floor, zone and two features, then it ... | TC-OS-5-1 | **PASS** | DSV#createPutsTheDeskInTheZoneMainWhenNoneIsGivenAndItIsBookableFromTomorrow; DSV#createRefusesAnUnknownFeatureAndLinksTheKnownOnes; DSV#createRefusesAnUnknownOrRetiredFloorAsAFieldError |
| OS-5.2 AC2.2 Given a code already used anywhere, when she saves, then it is refused with 'code ... | TC-OS-5-2 | **PASS** | DSV#createRefusesADuplicateCodeInTheTenantIgnoringCase; ORT#deskCodeIsUniquePerTenantIgnoringCase Note: Wording is "This desk code is already used..." (UX text). |
| OS-5.3 AC2.3 Given a desk with bookings, when she edits its code, then the field is read-only. | TC-OS-5-3 | **PASS** | DSV#updateOfTheCodeIsRefusedOnceTheDeskHasBookings; DSV#updateOfTheFloorIsRefusedOnceTheDeskHasBookings; DSV#updateWithoutChangingCodeOrFloorIsAllowedEvenWithBookingsAndEvenOnARetiredFloor Note: Server enforces; the read-only field is gap G1. |
| OS-5.4 AC2.9 Given a retired desk, when an employee searches, then it is not listed; history stays in ... | TC-OS-5-4 | **PASS** | ACC#ac4_8_aRetiredDeskIsNeverListedAndCannotBeBooked; DSV#retireIsRefusedWhileFutureBookingsExistAndCarriesTheCount; DSV#retireSetsRetiredOnAndASecondRetireIsRefused |
| OS-5.5 NEW Given a desk list of 1,500 desks, then it is paged and searchable. | TC-OS-5-5 | **PASS** | ACC#os5_aListOf1500DesksIsPagedAndSearchable (25 of 1,500, 60 pages, search by code); DSV#listReadsFloorsZonesAndFeaturesInBatchesWhateverThePageSize |
| **ST-OS-6 Desk features list** | | | |
| OS-6.1 NEW Given a new product, then monitor, docking station and standing desk exist. | TC-OS-6-1 | **PASS** | FDS#aTenantWithoutFeaturesGetsTheThreeDefaults; FDS#aTenantThatHasFeaturesIsNotSeededAgain |
| OS-6.2 NEW Given an admin adds a feature, then it can be chosen on desks. | TC-OS-6-2 | **PASS** | FCD#createFeatureTrimsAndRefusesADuplicateIgnoringCase; DSV#createRefusesAnUnknownFeatureAndLinksTheKnownOnes |
| OS-6.3 NEW Given a feature used by desks, then it cannot be deleted. | TC-OS-6-3 | **PASS** | FCD#deleteFeatureIsRefusedWhileDesksUseIt; FCD#deleteFeatureSoftDeletesAnUnusedFeature |
| **ST-OS-7 Office settings: release times, midday and working days** | | | |
| OS-7.1 AC3.1 Given a new office, then it has release times 10:00 and 14:00, midday 13:00 and working ... | TC-OS-7-1 | **PASS** | OSV#createMakesADraftOfficeWithTheDefaultSettings (10:00, 14:00, 13:00, Monday to Friday); FE officeSchemas.test "accepts the defaults of a new office (AC3.1)" |
| OS-7.2 AC3.2 Given an afternoon release of 09:00 with a morning release of 10:00, when saved, then it ... | TC-OS-7-2 | **PASS** | OSV#settingsRefuseAnAfternoonReleaseBeforeTheMorningRelease; OSV#settingsRefuseAnAfternoonReleaseBeforeMidday; FE officeSchemas.test "refuses an afternoon release before the morning release (AC3.2)" |
| OS-7.3 AC3.3 Given the morning release is changed at 09:30 to 09:45, when saved, then today's release ... | TC-OS-7-3 | **PASS** | OSV#settingsChangeAppliesFromTomorrowAndPublishesTheEvent; OET#aSameDayChangeLeavesTodaysDeadlineAndTheNextDaysTimesMoveOn; BDE#aBookingForTodayMadeAfterTheChangeKeepsTodaysOldDeadline; SCS#changingTheOfficeTimesMovesTheDeadlineOfALaterBookingAndKeepsTheEarlierTimesForToday; BSP#theListenerIsAsyncAfterCommitSoTheSaveReturnsAtOnce (the recompute no longer runs inside the save request) |
| OS-7.4 NEW Given working days, then she can choose any set of weekdays. | TC-OS-7-4 | **PASS** | FE officeSchemas.test "needs one working day and valid times", "sends working days in week order"; OET#theWorkingDaysAlsoChangeFromTheEffectiveDay |
| OS-7.5 NEW Given a change, then it is in the change history. | TC-OS-7-5 | **PASS** | AUD#updateRecordsOneRowPerChangedAuditedFieldWithOldAndNewValue; AEC#everyAuditableEntityIsAudited; OSV#historyReadsTheAuditRowsOfTheOfficeAfterTheExistenceCheck Note: History panel is gap G1. |
| **ST-OS-8 Closed days** | | | |
| OS-8.1 AC3.4 Given 26 Jan is a closed day, when an employee picks that date, then it is greyed out ... | TC-OS-8-1 | **PASS** | BQS#theCalendarRunsFromTodayToTheHorizonWithReasonsPerPart; PDR#refusal; FE plan.test "takes the reason of each refused day from the answer"; FE screenTexts "AC3.4 says Office closed" |
| OS-8.2 NEW Given a closed day with no bookings, when saved, then it is stored; with bookings it is ... | TC-OS-8-2 | **PASS** | FCD#addClosedDayStoresTheDateAndATrimmedReason; FCD#addClosedDayIsRefusedWhenBookingsExistThatDayAndCarriesTheCount |
| OS-8.3 NEW Given she removes a closed day, then the date is bookable again. | TC-OS-8-3 | **PASS** | FCD#removeClosedDaySoftDeletesItAfterTheVersionCheck; FCD#addClosedDayTwiceIsRefusedWith409 |
| OS-8.4 NEW(R12) Given a non-working day, then it is greyed out too. | TC-OS-8-4 | **PASS** | BCS#aWeekendIsRefusedWithItsReason; PDR#refusal; BQS#theCalendarRunsFromTodayToTheHorizonWithReasonsPerPart |
| **ST-OS-9 Company booking horizon setting** | | | |
| OS-9.1 NEW Given the tab 'Booking rules', then the default is 14 days. | TC-OS-9-1 | **PASS** | BSP#theRulesHaveDefaultsAndReadStoredValues; FE report.test "accepts the defaults and the limits of the contract" |
| OS-9.2 NEW Given a value that is not a whole number of at least 1, when saved, then it is refused. | TC-OS-9-2 | **PASS** | BCC#anUnknownPropertyAMissingFieldAndAnOutOfRangeRuleAreRefusedWith400; FE report.test "refuses values outside the limits and non-whole numbers"; CRB#theTableCoversEveryClosedDeskBookRequestSchemaOfTheContract; OCC2#anUnknownPropertyInABodyIsRefusedWith400 (both through the application mapper, support/AppJson) |
| OS-9.3 NEW Given a saved value, then the next search uses it. | TC-OS-9-3 | **PASS** | BSP#updateStoresTheThreeValuesAndBumpsTheVersion; BQS#theCalendarRunsFromTodayToTheHorizonWithReasonsPerPart |
| **ST-PP-1 Nightly copy of people from SuccessFactors** | | | |
| PP-1.1 AC14.1 Given 3,000 employees, then the run finishes in under 10 minutes and shows counts of ... | TC-PP-1-1 | **NOT RUN** | Chunked apply and the counts are proven (PSS#aLargeSetIsAppliedInChunks, PSS#aSuccessCloseStoresTheCountsAndMakesTodayDone); 3,000 people in under 10 minutes needs real SuccessFactors and PostgreSQL. Step E5 |
| PP-1.2 AC14.2 Given SuccessFactors does not answer, then the last copy is kept, the run is marked ... | TC-PP-1-2 | **PASS** | PSR#aPageThatFailsThreeTimesFailsTheRunAndNothingIsApplied; PSR#anEmptyAnswerFailsTheRunAndKeepsTheCopy; PSS#aFailedRunKeepsTheCodeAndIsNotAGoodCopy; PPR#theLastGoodCopyIsPerTenantAndIgnoresRunsThatDidNotSucceed; MPS#notInTheCopyIsNotReadyAndUsesTheSessionName Note: SuccessFactors failure is simulated at the PeopleSource port; the real service is step E5. |
| PP-1.3 AC14.6 Given a new employee, then she can sign in and book from that day on. | TC-PP-1-3 | **PASS** | PSS#theFirstLoadInsertsActivePeopleAndDoesNotStoreOrListOldLeavers; MPS#anEmployeeInTheCopyIsReadyAndHasTheEmployeeRoleOnly; ACC#ac5_8_aPersonMissingFromTheCopyCannotBookCanStillListAndBooksAfterTheNextCopy Note: Company sign-in itself is outside DeskBook. |
| PP-1.4 NEW(R49) Given a failure, then the sync retries every hour for the rest of the day. | TC-PP-1-4 | **PASS** | PSR#afterAFailedRunTheNextHourlyInvocationTriesAgain; PSR#afterASuccessToday_theHourlyInvocationEndsAtOnce |
| PP-1.5 NEW Given a record without an email, then it is skipped and counted. | TC-PP-1-5 | **PASS** | PSS#aNewPersonWithoutAUsableEmailIsSkippedCountedAndListedByUserIdOnly; PMT#aBlankUserIdIsSkipped; PSS#oldLeaversDoNotFillTheSkippedListThatShowsActivePeopleWithoutEmail |
| **ST-PP-2 Direct manager and manager status** | | | |
| PP-2.1 AC14.4 Given Ravi's manager changes, when the next sync completes, then Meera's team view no ... | TC-PP-2-1 | **PASS** | PSS#aChangedValueWritesOnlyThatRow; PSS#aPersonWithAnActiveReportBecomesManagerAndLosesTheFlagWhenTheLastReportGoes Note: Data level; the team view is R1. |
| PP-2.2 NEW(R52) Given a person who is manager of at least one active employee, then she has manager ... | TC-PP-2-2 | **PASS** | PSS#aPersonWithAnActiveReportBecomesManagerAndLosesTheFlagWhenTheLastReportGoes; MPS#aManagerFlagFromTheCopyAddsTheManagerRoleOnlyForAnEmployee |
| PP-2.3 NEW Given a person with no active reports, then she has no manager status. | TC-PP-2-3 | **PASS** | PSS#aPersonWithAnActiveReportBecomesManagerAndLosesTheFlagWhenTheLastReportGoes; PSS#anInactiveReportDoesNotMakeAManager |
| PP-2.4 NEW Given a manager change, then bookings stay with the employee. | TC-PP-2-4 | **PASS** | PSS#aChangedValueWritesOnlyThatRow (only the people row changes; bookings point at the employee id, BRT#lookupsByIdAreTenantAndOwnerScoped) |
| **ST-PP-3 Leavers: future bookings cancelled silently** | | | |
| PP-3.1 AC14.5 Given an employee leaves, when the sync completes, then her future bookings are ... | TC-PP-3-1 | **PASS** | ELL#futureBookedBookingsAreCancelledWithReasonLeaverAndTheirSlotsAreFreed; SCS#aLeaverHandOverCancelsTheFutureBookingAndMarksThePersonHandled; PSR#leaversAreHandedOverEvenWhenTheSyncFailed; PSS#aKnownPersonWhoTurnsInactiveIsStillALeaverAndAPreHireBecomesANormalPersonWhenActive |
| PP-3.2 AC5.9 Given an inactive employee, then she cannot book. | TC-PP-3-2 | **PASS** | ACC#ac5_9_anInactiveEmployeeCannotBook; MPS#anInactiveRecordIsNotReadyForAnotherReason |
| PP-3.3 NEW(G7) Given such a cancellation, then no email is sent. | TC-PP-3-3 | **PASS** | SCS#aLeaverHandOverCancelsTheFutureBookingAndMarksThePersonHandled (0 notices for a leaver) |
| **ST-PP-4 Profile not ready for people missing from the copy** | | | |
| PP-4.1 AC5.8 Given Asha is signed in and the copy has no record of her, when she books, then she sees ... | TC-PP-4-1 | **PASS** | ACC#ac5_8_aPersonMissingFromTheCopyCannotBookCanStillListAndBooksAfterTheNextCopy (PROFILE_NOT_READY, desk still free); BBP#aProfileThatIsNotReadyStopsTheProposal; FE profileNote.test |
| PP-4.2 NEW Given the same person, then she can still open Today and My bookings. | TC-PP-4-2 | **PASS** | ACC#ac5_8_... (My bookings answers empty); TSV#aPersonNotInTheCopyStillGetsAnEmptyToday |
| PP-4.3 NEW Given the next copy has her, then she can book without any other step. | TC-PP-4-3 | **PASS** | ACC#ac5_8_... (books once the copy has her) |
| **ST-PP-5 Roles and access checks, No access page** | | | |
| PP-5.1 AC17.1 Given a person not signed in, when she opens any page, then she is sent to company ... | TC-PP-5-1 | **NOT RUN** | Redirect to company sign-in and back is Approuter/IAS; the API side answers 401 (RMC#everyOperationRefusesAnAnonymousCallerWith401AndTouchesNothing, BRM#everyEmployeeOperationRefusesAnAnonymousCallerWith401). Step E8 |
| PP-5.2 AC17.2 Given a signed-in person without a DeskBook role, then she sees 'No access'. | TC-PP-5-2 | **PASS** | FE guards.test "sends a person without roles to No access"; RMC#everyOperationRefusesASignedInPersonWithoutRoleWith403AndTouchesNothing; MPS#aSignedInPersonWithoutRoleStillGetsAProfileWithNoRoles Note: No access page render is gap G1.; SHC#getCurrentUserAnswersTheSessionUser; DAG#theRoleIsCheckedBeforeTheLimitSoAForbiddenCallerSeesForbiddenNotLimited |
| PP-5.3 AC17.4 Given any page, then data a role may not see is not in the answer sent to the browser. | TC-PP-5-3 | **PASS** | RMC; BRM; BSV#getBookingAnswersOnlyHerOwn; BRT#theListSpecificationNeverCrossesTenants; RPT#everyReportRecordHoldsCountsAndPlacesOnly; TFG#everyRepositoryQueryFiltersByTenant; TFG#everyNamedQueryOfAnEntityFiltersByTenant (every JPQL query filters on tenant) |
| PP-5.4 AC1.5 Given an employee or manager, when she opens office setup by menu or link, then the ... | TC-PP-5-4 | **PASS** | FE navConfig.test "shows Today, Book a desk and My bookings to an employee or manager"; FE guards.test "keeps non-admins off admin pages"; RMC#everyOperationRefusesAPlainEmployeeWith403AndTouchesNothing |
| PP-5.5 AC12.10 Given an employee or manager opens reports by link, then it is refused. | TC-PP-5-5 | **PASS** | RCT#aPlainEmployeeGets403AndAnAnonymousCaller401OnBothOperations; ORS#onlyAnAdminMayReadAndAGuardRefusalTouchesNoData; FE guards.test |
| **ST-NT-1 Enabler: send an email once, retry, log** | | | |
| NT-1.1 AC13.6 Given the mail service is down, then bookings still work and the email is retried 3 ... | TC-NT-1-1 | **PASS** | NFT#aMailServerThatIsDownRetriesAt20And40And60MinutesThenFailsAndTheBookingIsUntouched; NPT#aReleaseNoticeIsRetriedAt20And40And60MinutesAfterCreationThenFailed Note: Mail failure is simulated at the MailSender port; real mail is step E6. |
| NT-1.2 NEW(R46) Given an event, then each message is sent once (event key). | TC-NT-1-2 | **PASS** | NFT#theOutboxWritesOneRowPerEventKeyAndASecondEnqueueAddsNothing; ACC#ac8_5_... (one notice per booking) |
| NT-1.3 NEW(R47) Given any message, then texts are translatable, English only in this release, and ... | TC-NT-1-3 | **PASS** | MTT#noMessageNamesAnotherEmployeeOrTheProduct; MTT#theHtmlHasParagraphsAndLinks Note: Texts are label keys deskbook.mail.* in messages.properties (English only). |
| NT-1.4 NEW Given a failed send, then the admin can see it in the log. | TC-NT-1-4 | **PASS** | NJT#theDispatchJobReportsCountsAndEveryFailedRowWithoutAnAddress Note: The job log screen is the base page (step E9). |
| **ST-NT-2 Reminder 15 minutes before the deadline** | | | |
| NT-2.1 NEW(P2) Given a booking not checked in 15 minutes before its deadline, then she gets one email ... | TC-NT-2-1 | **PASS** | NFT#theReminderIsQueuedFifteenMinutesBeforeTheDeadlineOnceAndCarriesBothLinks; MTT#theReminderSaysCheckInAndCarriesBothLinksAndTheLocalDeadline Note: Real delivery is step E6. |
| NT-2.2 NEW Given she checked in or cancelled, then no email is sent. | TC-NT-2-2 | **PASS** | NFT#nothingIsQueuedForSomeoneWhoCheckedInOrCancelledOrForADeadlineThatHasPassed; NFT#aReminderQueuedBeforeCheckInIsSkippedAtSendTime |
| NT-2.3 NEW Given the job runs twice, then one email per booking. | TC-NT-2-3 | **PASS** | NFT#theReminderIsQueuedFifteenMinutesBeforeTheDeadlineOnceAndCarriesBothLinks; NPT#eventKeysAreStablePerEventAndTheReminderKeyCarriesTheDeadline |
| **ST-NT-3 Email when a booking was released** | | | |
| NT-3.1 AC13.3 Given a booking released at 10:00, then Asha gets one email 'Your desk was released'. | TC-NT-3-1 | **PASS** | ACC#ac8_1_to_8_3_... (one notice per release); NFT#theReleaseNoticeIsSentOnceWithNoShowAndHowToBookForToday; SCS#releasingABookingQueuesTheNoticeInTheSameTransactionAndTheMailGoesOutLogOnly Note: Real delivery is step E6. |
| NT-3.2 NEW Given the email, then it says No-show and how to book a desk for today (P1). | TC-NT-3-2 | **PASS** | MTT#theReleaseNoticeSaysNoShowAndHowToBookForToday; MTT#aReleaseAfterAHoldIsNotCalledANoShow |
| NT-3.3 NEW Given a catch-up run, then one email per booking. | TC-NT-3-3 | **PASS** | ACC#ac8_5_... (3 notices for 3 bookings after a catch-up); NFT#aReleasedBookingQueuesOneNoticeEvenWhenTheEventArrivesTwice |
| **ST-RP-1 Occupancy per office, floor and day** | | | |
| RP-1.1 AC12.2 Given a date range of 1 to 31 Oct, when she picks office Pune, then rows per day and ... | TC-RP-1-1 | **PASS** | ACC#rp_theReportAfterARealDayCountsCapacityBookedCheckedInNoShowAndCancelledPerOffice; BSQ#twoFloorsGiveTwoRowsAndOneDayTotalWithTheSumOfBoth; RCT#theReportAnswersEveryRequiredMemberIncludingDayTotals |
| RP-1.2 AC12.7 Given no data in the range, then she sees 'No bookings in this period' and export is ... | TC-RP-1-2 | **NOT RUN** | Empty range answer is covered (ACC#rp_... empty range gives 0 booked) and the text exists (FE screenTexts "AC12.7"); the disabled Export button is a screen state. Step E4 |
| RP-1.3 NEW(R39) Given any report, then it shows counts and rates only, never names. | TC-RP-1-3 | **PASS** | RPT#everyReportRecordHoldsCountsAndPlacesOnly; OES#theFileHasAHeaderThenTheFloorRowsAndTheAllFloorsLinePerOfficeAndDay |
| RP-1.4 NEW(R42) Given days, then they follow each office's own timezone. | TC-RP-1-4 | **PASS** | ACC#rp_... (Pune and Berlin on their own Monday); PDR#todayIsJudgedOnTheOfficeClockNotOnUtc; FE report.test "finds today in the office timezone" Note: Booking dates are office-local dates; the report groups on them. |
| RP-1.5 NEW Given a booking, then booked and checked-in counts show per floor and day. | TC-RP-1-5 | **PASS** | ACC#rp_... (booked 2.0, checked in 0.5 per day); OCC#capacityIsTheBookableDesksOfEachWorkingDay; BSQ#statusesAndPartsAreCountedAndTheCancelledSplitFollowsTheDeadline |
| RP-1.6 NEW(GP) [F12] Given the table (B's occupancy table, kept under the heat grid), then each day ... | TC-RP-1-6 | **PASS** | FE report.test "bounds the used bar between 0 and 1", "takes the All floors line from the server day totals and sums nothing"; OCC#dayTotalsSumAllFloorsAndTheRateComesFromTheSumsNotFromAveragingFloors Note: Bar and total row render is gap G1. |
| **ST-RP-2 No-show rate** | | | |
| RP-2.1 AC12.1 Given Pune has 60 bookable desks and on Monday 42 booked, 35 checked in, 7 released, ... | TC-RP-2-1 | **PASS** | OCC#ac12_1SixtyDesksFortyTwoBookedThirtyFiveInSevenReleasedGivesSixteenPointSevenPercent |
| RP-2.2 AC12.5 Given a booking cancelled before the release time, then it is not a No-show and not ... | TC-RP-2-2 | **PASS** | OCC#cancelledBeforeTheDeadlineIsApartAndCancelledAfterItStillCountsAsBooked; ACC#rp_theReportAfterARealDay... (cancelled 0.5, not booked) |
| RP-2.3 NEW Given 'Released after hold' bookings, then they are a separate line, not in the rate (Q50). | TC-RP-2-3 | **PASS** | OCC#releasedAfterHoldIsItsOwnLineAndStaysOutOfTheRate; ACC#rp_aLateReleaseAfterHoldIsItsOwnLineAndStaysOutOfTheNoShowRate |
| **ST-RP-3 Capacity rules: blocked and retired desks, half days** | | | |
| RP-3.1 AC12.3 Given two blocked desks on a day, then capacity for that day is reduced by two. | TC-RP-3-1 | **Moved to R1 (D10)** | Now ST-OS-10 (blocking a desk is not in the MVP build); closed-day and retired capacity are covered (BSQ#aClosedDayRemovesTheCapacityOfThatOfficeOnly, OCC#aRetiredFloorLeavesTheCapacity). Not counted in the MVP totals. |
| RP-3.2 AC12.4 Given a half-day booking, then booked counts 0.5 and capacity is in desk-days. | TC-RP-3-2 | **PASS** | OCC#halfDaysCountHalfADeskDay; ACC#rp_theReportAfterARealDay... (0.5 desk-days) |
| RP-3.3 AC16.6 Given a flagged reserved desk, then reports count it as capacity as normal. | TC-RP-3-3 | **Moved to R1 (D10)** | Now ST-PP-10 (reserved desks are not in the MVP build). Not counted in the MVP totals. |
| RP-3.4 NEW Given a retired desk, then it is not capacity. | TC-RP-3-4 | **PASS** | OCC#aRetiredFloorLeavesTheCapacity; OCC#aDeskCountsFromItsBookableFromDayAndNotFromItsRetiredOnDay; BSQ#capacityFollowsDeskDatesAndClosedDays |
| **ST-RP-4 Excel export** | | | |
| RP-4.1 AC12.8 Given an export of 30,000 rows, when she presses Export, then she gets an Excel file ... | TC-RP-4-1 | **NOT RUN** | Streaming of a large result and the row bound are proven (OES#aLargeResultStreamsWithoutBuildingTheWholeSheetInMemory, RCT#theExportIsAnXlsxFileOfTheSameRows); 30,000 rows in 30 s on real PostgreSQL is a load figure. Step E7 |
| RP-4.2 AC12.9 Given more than 100,000 rows, then export is refused with 'Narrow the dates or office'. | TC-RP-4-2 | **PASS** | OES#moreThan100000RowsIsRefusedBeforeAnythingIsWritten; FE report.test "reads the field code of the 400 (05-api-notes 8)" Note: Wording is "There are too many rows for one file. Pick a shorter period or one office." |
| RP-4.3 AC12.11 Given an export file, then it contains no employee names or ids. | TC-RP-4-3 | **PASS** | RPT#everyReportRecordHoldsCountsAndPlacesOnly; OES#theFileHasAHeaderThenTheFloorRowsAndTheAllFloorsLinePerOfficeAndDay |
| RP-4.4 NEW Given an empty range, then the export button is disabled. | TC-RP-4-4 | **NOT RUN** | The disabled Export button on an empty range is a screen state with no component test. Step E4 |
| **ST-EN-1 Enabler: DeskBook shell - menu, routes and texts** | | | |
| EN-1.1 NEW Given the navigation table in the journeys, then the sidebar shows those items per role. | TC-EN-1-1 | **PASS** | FE navConfig.test (all four roles cases) |
| EN-1.2 NEW Given the base example items (Projects), then they are gone. | TC-EN-1-2 | **PASS** | FE screenTexts "has no Projects route or feature file", "shows no Projects menu item to any role"; MMT#theDemoModuleStaysInTheHistoryAndV060DropsItsTables |
| EN-1.3 NEW Given any text, then it comes from translation keys. | TC-EN-1-3 | **PASS** | FE screenTexts "no screen file has a sentence typed between tags or in a visible attribute"; FE locales.test (all 5 files have the keys of en.json) |
| EN-1.4 NEW Given the product name and colours, then they come from the base theme. | TC-EN-1-4 | **PASS** | FE deriveTokens.test (colours and fonts from the theme); THM#returnsDefaultsWhenNoRowExists; SHC#getThemeAnswersTheTheme; SHC#updateThemePassesIfMatchAndAnswersTheThemeOr400; SHC#theControllersServeExactlyTheSixteenShellRoutes (base shell contract tests) |
| **ST-EN-2 Enabler: office time and part-of-day rules in one place** | | | |
| EN-2.1 AC3.6 Given Pune in Asia/Kolkata and Berlin in Europe/Berlin, when both release at 10:00, then ... | TC-EN-2-1 | **PASS** | PDR#pune_and_berlin_both_release_at_ten_on_their_own_clock_across_the_daylight_saving_change; ACC#ac8_1_to_8_3_... (Pune 04:30Z, Berlin 09:00Z) |
| EN-2.2 NEW Given a date, a part of the day and an office, then one function returns the deadline, ... | TC-EN-2-2 | **PASS** | PDR#officeClockAssessGivesDeadlineCutOffAndWorkingDayInOneAnswer; OCS#assessAnswersWithTheInjectedClock |
| EN-2.3 NEW Given all other stories, then they use this and not their own time maths. | TC-EN-2-3 | **PASS** | TMP#zoneArithmeticLivesInTheTimePackageAndTheKnownHelpers (scan of the DeskBook modules) Note: One duplicate helper allowed: office OfficeProblems.today, same arithmetic (Q197). |
| EN-2.4 NEW Given a table of at least 20 cases, then all pass. | TC-EN-2-4 | **PASS** | PDR: 48 cases in the surefire report (release, check-in, part-end and refusal tables incl. DST gap and overlap) |

## Failures and findings (with owner)

| Id | Severity | What | Probable cause | Owner |
|---|---|---|---|---|
| Q198 | Medium, **closed** | ST-BK-8 criterion 3 (AC19.5): when nothing matches her zone or features the proposal says only "no free desk" and the screen says "Try another office or part of the day". No nearest zone or feature options are offered. | The proposal contract (`DeskProposal.noneReason`) has no field for alternatives; `DeskProposalService` answers NOTHING_FREE. A story gap, not a coding slip. Fixed in fix round S7 (Q201, Q202): NO_MATCH with `alternatives`; BK-8.3 is PASS in this run. | - |
| Q197 | Low, answered | ST-EN-2 criterion 3: the office admin services compute the office-local today with their own helper (`OfficeProblems.today`) instead of `OfficeClock`. Same arithmetic, DST-safe; `TimeMathPlacementTest` allows exactly this one helper and fails on any new one. | Helper written before the clock module. Delegates to `PartOfDayRules.localDate` since the fix round; the allow-list entry is gone. | - |
| Q199 | Low (suite health), answered | The Spring test contexts of the Backend share one in-memory H2 database (EclipseLink reuses a session by name), and `SpringContextSmokeTest` commits rows. A non-transactional test therefore leaks rows into the global counts of `NotificationFlowTest` and `PurgeStoresTest` (14 and 1 failures seen when the QA journeys did not clean up). QA cleans its own tenant; the smoke test does not. | `RepositoryTestConfig` did not set a unique `eclipselink.session-name`. Fixed: unique session name per test context, `TestContextIsolationTest`. | - |
| Q200 | Low (story hygiene) | Four MVP criteria describe features that are not in the MVP build: reserved desks (ST-BK-8 c6, ST-RP-3 c3), blocking a desk (ST-RP-3 c1), a booking made by a manager (ST-BK-10 c2). They could not be tested and were NOT RUN. **Closed: moved to R1 (D10).** Wording also differs from the stories in three messages (office name, desk code, export too large); the UX text is clearer and was accepted. | Stories were written for R1 features and tagged MVP. | story-sizer (move or reword) |

No test fails in the refresh run, so no new finding was recorded (`questions.md` next free number is unchanged: Q214). Q200 is closed: the four MVP criteria for features that are not built were moved to R1 (D10) and no longer count as NOT RUN.

## NOT RUN: why and what to do

| Criterion | Reason | Step |
|---|---|---|
| BK-1.4 AC4.10 Given 500 desks, when the list loads, then the first screen shows in ... | Paging proven (ACC#ac4_10: first page 50 of 500, count 500, 10 pages; H2 first page well under 2 s, indicative only). The 2 s on real PostgreSQL in a browser is a load figure. | E1 |
| BK-5.5 AC17.3 Given her session expired, when she presses Book, then she signs in ... | Session expiry and sign-in again are Approuter/IAS behaviour; the API answers 401 (RMC#everyOperationRefusesAnAnonymousCallerWith401AndTouchesNothing). | E3 |
| BK-5.6 NEW(GP) [F5] Given any booking confirmation (one day, several days, booked by a ... | The box is a screen element (HowCheckInNote on S3); no component test exists (gap G1). The label "How check-in works" exists (FE screenTexts). | E4 |
| BK-9.1 AC6.3 Given she has no bookings, then My bookings says 'No bookings yet' with a ... | Empty list answer is covered (BSV#anUnknownSortIsRefusedAndAPersonOutsideTheCopyHasNoBookings) and the text exists (FE screenTexts "AC6.3"); the empty state with its Book a desk button is a screen element. | E4 |
| BK-9.2 AC5.11 Given the booking succeeded, when she opens My bookings, then it is ... | ACC#ac5_4_... shows the new booking in the list at once; the 1 s figure needs real PostgreSQL and a browser. | E1 |
| BK-11.2 NEW Given no booking, then 'No bookings yet' and a Book a desk button show. | Empty answer covered (TSV#aPersonNotInTheCopyStillGetsAnEmptyToday); the "No bookings yet" text and button are screen elements. | E4 |
| BK-11.5 NEW Given loading or error, then a skeleton or a retry shows. | Skeleton and retry card are screen states with no component test. | E4 |
| BK-13.4 NEW(GP) [F5] Given the result, then one confirmation lists every day with desk, ... | One confirmation page (DonePage, BookingResultList) is rendering only; no component test. | E4 |
| BK-15.1 NEW(GP) [F6, AC18.5] Given her bookings, when she opens Today, then a strip ... | Strip data covered (TSV#theStripMarksBookedBookableAndNonWorkingDays); the tiles and the Add day tile are rendering. | E4 |
| BK-15.2 NEW(GP) [F6, AC18.2] Given she taps 'Add day', then the plan screen (ST-BK-13) ... | The link from Add day to /book?days= is routing and rendering; not unit tested. | E4 |
| BK-15.4 NEW Given loading or error, then a skeleton or a retry shows. | Skeleton and retry are screen states with no component test. | E4 |
| PP-1.1 AC14.1 Given 3,000 employees, then the run finishes in under 10 minutes and ... | Chunked apply and the counts are proven (PSS#aLargeSetIsAppliedInChunks, PSS#aSuccessCloseStoresTheCountsAndMakesTodayDone); 3,000 people in under 10 minutes needs real SuccessFactors and PostgreSQL. | E5 |
| PP-5.1 AC17.1 Given a person not signed in, when she opens any page, then she is sent ... | Redirect to company sign-in and back is Approuter/IAS; the API side answers 401 (RMC#everyOperationRefusesAnAnonymousCallerWith401AndTouchesNothing, BRM#everyEmployeeOperationRefusesAnAnonymousCallerWith401). | E8 |
| RP-1.2 AC12.7 Given no data in the range, then she sees 'No bookings in this period' ... | Empty range answer is covered (ACC#rp_... empty range gives 0 booked) and the text exists (FE screenTexts "AC12.7"); the disabled Export button is a screen state. | E4 |
| RP-4.1 AC12.8 Given an export of 30,000 rows, when she presses Export, then she gets ... | Streaming of a large result and the row bound are proven (OES#aLargeResultStreamsWithoutBuildingTheWholeSheetInMemory, RCT#theExportIsAnXlsxFileOfTheSameRows); 30,000 rows in 30 s on real PostgreSQL is a load figure. | E7 |
| RP-4.4 NEW Given an empty range, then the export button is disabled. | The disabled Export button on an empty range is a screen state with no component test. | E4 |

## Tests written by QA

| File | Tests | What it proves |
|---|---|---|
| `Backend/src/test/java/com/talenteam/deskbook/DeskBookAcceptanceFlowTest.java` | 24 | The real booking, check-in, release, notice outbox, people and report services on H2 with a clock the test moves: release at each office own deadline (Pune and Berlin, morning, afternoon, full day, cancelled), check-in 2 s before the deadline, catch-up after downtime with one notice each, late booking 30 minutes, Running late once, check-in window, two threads on one desk, double click, cancel and others, profile not ready, inactive employee, retired desk, 500 and 1,500 desks, report numbers after a real day, draft office not in the picker. Cleans its tenant after each test. |
| `Backend/.../common/time/TimeMathPlacementTest.java` | 1 | No zone arithmetic in the DeskBook modules outside the time package and two known helpers. |
| `Backend/.../reports/service/ReportPrivacyTest.java` | 1 | No report record can hold a person (name, id, email, user). |
| `Frontend/src/qa/screenTexts.test.ts` | 24 | No sentence typed into a screen file; the story words exist in en.json; no Projects route or menu item. |

## Coverage gaps

- **G1 No component tests.** The frontend vitest runs in node (`*.test.ts`, no jsdom). Every PASS row that says "screen" or "render" rests on tsc, lint, build and pure-logic tests. Review item S17 (jsdom + Testing Library) would close it; E4 is the manual list until then.
- **G2 PostgreSQL.** Flyway on PostgreSQL (V002 partitions), the partial unique indexes as written, index plans and the real race run on H2 with rebuilt keys (`H2Schema`, Q158, Q165). Step E2.
- **G3 Load.** No figure for 500 desks, 500 users polling, 3,000 people, 30,000 export rows (E1, E5, E7). The H2 times in the tests are not evidence.
- **G4 Outside systems.** SuccessFactors, mail and sign-in are simulated at their ports (E5, E6, E8). The scheduler firing the minute jobs is not tested (E9).
- **G5 Controllers.** Contract tests call the controllers directly, not through HTTP, security filters or Approuter.
- **G6 Languages.** de, es, fr, en-GB carry English text for most keys (to translate); only key parity is tested.

## Alias list

Backend tests are under `Backend/src/test/java/com/talenteam/deskbook/`; `FE` = under `Frontend/src/`.

| Alias | Test class |
|---|---|
| ACC | DeskBookAcceptanceFlowTest (QA, new) |
| AEC | audit/AuditedEntityCoverageTest |
| AUD | audit/listener/AuditDescriptorEventListenerTest |
| BBP | booking/service/BookingBatchAndProposalTest |
| BCC | booking/controller/BookingControllerContractTest |
| BCS | booking/service/BookingCommandServiceTest |
| BDE | booking/service/BookingDateEffectiveTimesTest |
| BQS | booking/service/BookingQueryServiceTest |
| BRM | booking/BookingRoleMatrixTest |
| BRT | booking/repository/BookingRepositoriesTest |
| BSP | booking/service/BookingSupportTest |
| BSQ | reports/service/BookingStatsQueryTest |
| BSV | booking/service/BookingServiceTest |
| DPR | booking/rules/DeskProposalRulesTest |
| DSV | office/service/DeskServiceTest |
| ELL | booking/listener/EmployeeLeftListenerTest |
| FCD | office/service/FeatureClosedDayServiceTest |
| FDS | office/service/FeatureDefaultsSeederTest |
| FZS | office/service/FloorZoneServiceTest |
| MMT | common/db/MigrationMappingTest |
| MPS | access/service/MyProfileServiceTest |
| MTT | notification/service/MailTemplatesTest |
| NFT | notification/NotificationFlowTest |
| NJT | notification/job/NotificationJobsTest |
| NPT | notification/service/NotificationPolicyTest |
| OCC | reports/rules/OccupancyCalculatorTest |
| OCC2 | office/controller/OfficeControllerContractTest |
| OCS | office/service/OfficeClockServiceTest |
| OES | reports/service/OccupancyExportServiceTest |
| OET | office/domain/OfficeEffectiveTimesTest |
| ORS | reports/service/OccupancyReportServiceTest |
| ORT | office/repository/OfficeRepositoriesTest |
| OSV | office/service/OfficeServiceTest |
| PDR | common/time/PartOfDayRulesTest |
| PMT | people/service/PeopleMapperTest |
| PPR | people/repository/PeopleRepositoriesTest |
| PSR | people/service/PeopleSyncRunnerTest |
| PSS | people/service/PeopleSyncStoreTest |
| RCT | reports/controller/ReportControllerContractTest |
| RMC | access/RoleMatrixContractTest |
| RPT | reports/service/ReportPrivacyTest (QA, new) |
| SCS | SpringContextSmokeTest |
| THM | theme/service/ThemeServiceTest |
| TMP | common/time/TimeMathPlacementTest (QA, new) |
| TSV | booking/service/TodayServiceTest |
| MAT | notification/adapter/MailAdaptersTest |
| CRB | common/web/ClosedRequestBodiesTest |
| DAG | access/service/DeskAccessGuardTest |
| DBR | DeskBookBatchRaceTest (QA) |
| RBH | common/web/RateLimitAndBodyLimitHttpTest |
| RLT | common/ratelimit/RateLimiterTest |
| SHC | common/api/ShellControllerContractTest |
| TCI | support/TestContextIsolationTest |
| TFG | common/db/TenantFilterGuardTest |
| FE screenTexts | qa/screenTexts.test.ts |

## Batch race tests

Class `Backend/src/test/java/com/talenteam/deskbook/DeskBookBatchRaceTest.java` (QA, new; 5 tests, same H2 setup and Spring context as `DeskBookAcceptanceFlowTest.ac5_3_and_5_4`: one thread per person, a latch starts them together, `BookingBatchService.createBookings` and `BookingService.createBooking` called directly). Checked after every race: no two active bookings on one desk and day (`bkg_bookings`), none on one desk, day and half (`bkg_booking_slots`), none for one person on one day, no exception out of the service (would be a 500), every day BOOKED, REPICKED or FAILED with a clean code (DESK_JUST_TAKEN, REQUEST_IN_PROGRESS, ALREADY_BOOKED_THAT_DAY), and the rows in the database equal the booked days the callers were told.

| Case | What races | Result, 10 runs in a loop |
|---|---|---|
| a1 | asha and ravi, the same 5 days (Mon-Fri 2-6 Nov, full day) on desk P1, CHOSEN: exactly one winner per day | PASS 10/10 |
| a2 | 4 people, overlapping 4-day windows, PROPOSED desk P1 with re-pick: database equals the answers | PASS 10/10 |
| b1 | asha's 5-day batch against ravi's single booking of P1 on the Wednesday: one winner on that day, the other 4 days booked | PASS 10/10 |
| b2 | asha's batch (P1) against asha's own single booking of P2 on the Wednesday: never two bookings that day | PASS 10/10 |
| c1 | asha submits the same batch twice at once with one Idempotency-Key: 5 bookings, replay returns the same ids | PASS 10/10 |

Commands: `mvn -o -q test-compile -pl Backend`, then 10 times `mvn -o -q surefire:test -pl Backend -Dtest=DeskBookBatchRaceTest` (script `qar_loop.py` in QA scratchpad, reads the surefire XML each run). Full suite at that time: 719 tests, 0 failures (714 + 5 new); the refresh run above has 749. No findings, no production code changed.
Not proven: the PostgreSQL race itself (H2 only), the HTTP layer and rate limits (a fresh tenant per test), and per-half bookings (the batch races use full-day bookings; the slot-level check still runs).
