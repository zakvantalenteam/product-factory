# API notes - DeskBook

Stage S5 (api-designer), 2026-10-28; updated the same day for prototype option A (D5, ADR-12, architecture 8.1). Contract: `05-openapi.yaml` (OpenAPI 3.1, `info.version` 0.1.0). Inputs: `05-architecture.md` (8.1 and task table), `02-spec.md`, `04-stories.md`, `decisions.md` D1-D4, `base/BASE-SPEC.md` B1, B5, B6, B7, B9, `standards/api-standards.md`.
Lint: `npx @redocly/cli@1.25.0 lint` gives zero errors and zero warnings. Every inline example was also validated against its schema with a JSON Schema checker.

Scope (M2 realignment, D6, D7): 45 MVP operations (office 28, booking 12, checkin 2, access 1, reports 2) and 17 base operations are in the YAML. D6 moved `getOccupancyGrid` to R1 (`x-release: R1`, still in the YAML; MVP 44) and D7 moved `exportReport` (ST-RP-4, `GET /reports/occupancy/export`, xlsx) into the MVP (44 + 1 = 45). `getToday` adds `nextTwoWeeks` (MVP, ST-BK-15, 14 days, PF-12); `getToday.usualDesk` is R1. Other R1, R2 and Later operations are only in section 3.

## 1. MVP operations

Paths are under the server `/deskbook` and `/api/v1`. A manager and an admin are also employees, so EMPLOYEE operations list all three roles.

| operationId | Method | Path | Roles | If-Match | Stories | Error codes |
|---|---|---|---|---|---|---|
| `listOffices` | GET | `/api/v1/offices` | ADMIN | - | ST-OS-1 | VALIDATION_ERROR |
| `getOffice` | GET | `/api/v1/offices/{officeId}` | ADMIN | - | ST-OS-1 | RESOURCE_NOT_FOUND |
| `createOffice` | POST | `/api/v1/offices` | ADMIN | - | ST-OS-1, ST-OS-7 | VALIDATION_ERROR, OFFICE_NAME_TAKEN, INVALID_TIMEZONE |
| `updateOffice` | PUT | `/api/v1/offices/{officeId}` | ADMIN | yes | ST-OS-1 | VALIDATION_ERROR, IF_MATCH_REQUIRED, CONCURRENT_UPDATE, RESOURCE_NOT_FOUND, OFFICE_NAME_TAKEN, INVALID_TIMEZONE |
| `getOfficeHistory` | GET | `/api/v1/offices/{officeId}/history` | ADMIN | - | ST-OS-1 | VALIDATION_ERROR, RESOURCE_NOT_FOUND |
| `openOffice` | POST | `/api/v1/offices/{officeId}/open` | ADMIN | yes | ST-OS-2 | IF_MATCH_REQUIRED, CONCURRENT_UPDATE, RESOURCE_NOT_FOUND, INVALID_STATE_TRANSITION |
| `closeOffice` | POST | `/api/v1/offices/{officeId}/close` | ADMIN | yes | ST-OS-2 | IF_MATCH_REQUIRED, CONCURRENT_UPDATE, RESOURCE_NOT_FOUND, INVALID_STATE_TRANSITION, HAS_FUTURE_BOOKINGS |
| `updateOfficeSettings` | PUT | `/api/v1/offices/{officeId}/settings` | ADMIN | yes | ST-OS-7 | VALIDATION_ERROR, IF_MATCH_REQUIRED, CONCURRENT_UPDATE, RESOURCE_NOT_FOUND, INVALID_RELEASE_TIMES |
| `listFloors` | GET | `/api/v1/offices/{officeId}/floors` | ADMIN | - | ST-OS-3 | VALIDATION_ERROR, RESOURCE_NOT_FOUND |
| `createFloor` | POST | `/api/v1/offices/{officeId}/floors` | ADMIN | - | ST-OS-3, ST-OS-4 | VALIDATION_ERROR, RESOURCE_NOT_FOUND, FLOOR_NAME_TAKEN |
| `updateFloor` | PUT | `/api/v1/floors/{floorId}` | ADMIN | yes | ST-OS-3 | VALIDATION_ERROR, IF_MATCH_REQUIRED, CONCURRENT_UPDATE, RESOURCE_NOT_FOUND, FLOOR_NAME_TAKEN |
| `retireFloor` | POST | `/api/v1/floors/{floorId}/retire` | ADMIN | yes | ST-OS-3 | IF_MATCH_REQUIRED, CONCURRENT_UPDATE, RESOURCE_NOT_FOUND, HAS_FUTURE_BOOKINGS, INVALID_STATE_TRANSITION |
| `listZones` | GET | `/api/v1/floors/{floorId}/zones` | ADMIN | - | ST-OS-4 | VALIDATION_ERROR, RESOURCE_NOT_FOUND |
| `createZone` | POST | `/api/v1/floors/{floorId}/zones` | ADMIN | - | ST-OS-4 | VALIDATION_ERROR, RESOURCE_NOT_FOUND, ZONE_NAME_TAKEN |
| `renameZone` | PUT | `/api/v1/zones/{zoneId}` | ADMIN | yes | ST-OS-4 | VALIDATION_ERROR, IF_MATCH_REQUIRED, CONCURRENT_UPDATE, RESOURCE_NOT_FOUND, ZONE_NAME_TAKEN |
| `deleteZone` | DELETE | `/api/v1/zones/{zoneId}` | ADMIN | yes | ST-OS-4 | IF_MATCH_REQUIRED, CONCURRENT_UPDATE, RESOURCE_NOT_FOUND, ZONE_IN_USE |
| `listDesks` | GET | `/api/v1/desks` | ADMIN | - | ST-OS-5 | VALIDATION_ERROR |
| `getDesk` | GET | `/api/v1/desks/{deskId}` | ADMIN | - | ST-OS-5 | RESOURCE_NOT_FOUND |
| `createDesk` | POST | `/api/v1/desks` | ADMIN | - | ST-OS-5 | VALIDATION_ERROR, DESK_CODE_TAKEN |
| `updateDesk` | PUT | `/api/v1/desks/{deskId}` | ADMIN | yes | ST-OS-5 | VALIDATION_ERROR, IF_MATCH_REQUIRED, CONCURRENT_UPDATE, RESOURCE_NOT_FOUND, DESK_CODE_TAKEN, DESK_CODE_LOCKED |
| `retireDesk` | POST | `/api/v1/desks/{deskId}/retire` | ADMIN | yes | ST-OS-5, ST-RP-3 | IF_MATCH_REQUIRED, CONCURRENT_UPDATE, RESOURCE_NOT_FOUND, HAS_FUTURE_BOOKINGS, INVALID_STATE_TRANSITION |
| `getDeskHistory` | GET | `/api/v1/desks/{deskId}/history` | ADMIN | - | ST-OS-5 | VALIDATION_ERROR, RESOURCE_NOT_FOUND |
| `listFeatures` | GET | `/api/v1/desk-features` | ADMIN | - | ST-OS-6 | VALIDATION_ERROR |
| `createFeature` | POST | `/api/v1/desk-features` | ADMIN | - | ST-OS-6 | VALIDATION_ERROR, FEATURE_NAME_TAKEN |
| `deleteFeature` | DELETE | `/api/v1/desk-features/{featureId}` | ADMIN | yes | ST-OS-6 | IF_MATCH_REQUIRED, CONCURRENT_UPDATE, RESOURCE_NOT_FOUND, FEATURE_IN_USE |
| `listClosedDays` | GET | `/api/v1/offices/{officeId}/closed-days` | ADMIN | - | ST-OS-8 | VALIDATION_ERROR, RESOURCE_NOT_FOUND |
| `addClosedDay` | POST | `/api/v1/offices/{officeId}/closed-days` | ADMIN | - | ST-OS-8 | VALIDATION_ERROR, RESOURCE_NOT_FOUND, CLOSED_DAY_EXISTS, DATE_IN_PAST, HAS_FUTURE_BOOKINGS |
| `removeClosedDay` | DELETE | `/api/v1/offices/{officeId}/closed-days/{closedDayId}` | ADMIN | yes | ST-OS-8 | IF_MATCH_REQUIRED, CONCURRENT_UPDATE, RESOURCE_NOT_FOUND |
| `listBookableOffices` | GET | `/api/v1/bookable-offices` | EMPLOYEE, MANAGER, ADMIN | - | ST-BK-1 | VALIDATION_ERROR |
| `getBookingCalendar` | GET | `/api/v1/bookable-offices/{officeId}/calendar` | EMPLOYEE, MANAGER, ADMIN | - | ST-BK-1, ST-BK-7 | RESOURCE_NOT_FOUND |
| `listFreeDesks` | GET | `/api/v1/free-desks` | EMPLOYEE, MANAGER, ADMIN | - | ST-BK-1, ST-BK-7 | VALIDATION_ERROR, RESOURCE_NOT_FOUND, DATE_NOT_BOOKABLE, PART_ENDED, RATE_LIMITED |
| `proposeDesks` | GET | `/api/v1/desk-proposals` | EMPLOYEE, MANAGER, ADMIN | - | ST-BK-8, ST-BK-13 | VALIDATION_ERROR, RESOURCE_NOT_FOUND, PROFILE_NOT_READY, EMPLOYEE_INACTIVE, RATE_LIMITED |
| `createBookings` | POST | `/api/v1/bookings/batch` | EMPLOYEE, MANAGER, ADMIN | - | ST-BK-13, ST-BK-8, ST-BK-14 | VALIDATION_ERROR, RESOURCE_NOT_FOUND, PROFILE_NOT_READY, EMPLOYEE_INACTIVE, IDEMPOTENCY_KEY_REUSED, RATE_LIMITED; per day: DESK_JUST_TAKEN, ALREADY_BOOKED_THAT_DAY, DESK_NOT_AVAILABLE, DATE_NOT_BOOKABLE, PART_ENDED |
| `createBooking` | POST | `/api/v1/bookings` | EMPLOYEE, MANAGER, ADMIN | - | ST-BK-5, ST-BK-6, ST-BK-7, ST-PP-4 | VALIDATION_ERROR, RESOURCE_NOT_FOUND, DESK_JUST_TAKEN, ALREADY_BOOKED_THAT_DAY, DESK_NOT_AVAILABLE, DATE_NOT_BOOKABLE, PART_ENDED, PROFILE_NOT_READY, EMPLOYEE_INACTIVE, IDEMPOTENCY_KEY_REUSED, RATE_LIMITED |
| `getBooking` | GET | `/api/v1/bookings/{bookingId}` | EMPLOYEE, MANAGER, ADMIN | - | ST-BK-5 | RESOURCE_NOT_FOUND |
| `listMyBookings` | GET | `/api/v1/bookings` | EMPLOYEE, MANAGER, ADMIN | - | ST-BK-9 | VALIDATION_ERROR |
| `cancelBooking` | POST | `/api/v1/bookings/{bookingId}/cancel` | EMPLOYEE, MANAGER, ADMIN | yes | ST-BK-10 | IF_MATCH_REQUIRED, BOOKING_STATE_CHANGED, RESOURCE_NOT_FOUND |
| `getToday` | GET | `/api/v1/today` | EMPLOYEE, MANAGER, ADMIN | - | ST-BK-11, ST-BK-12, ST-BK-16 | - |
| `getBookingRules` | GET | `/api/v1/booking-rules` | ADMIN | - | ST-OS-9 | - |
| `updateBookingRules` | PUT | `/api/v1/booking-rules` | ADMIN | yes | ST-OS-9 | VALIDATION_ERROR, IF_MATCH_REQUIRED, CONCURRENT_UPDATE |
| `checkIn` | POST | `/api/v1/bookings/{bookingId}/check-in` | EMPLOYEE, MANAGER, ADMIN | yes | ST-CI-1 | IF_MATCH_REQUIRED, BOOKING_STATE_CHANGED, RESOURCE_NOT_FOUND, CHECK_IN_NOT_OPEN, DEADLINE_PASSED, RATE_LIMITED |
| `holdBooking` | POST | `/api/v1/bookings/{bookingId}/hold` | EMPLOYEE, MANAGER, ADMIN | yes | ST-CI-7 | IF_MATCH_REQUIRED, BOOKING_STATE_CHANGED, RESOURCE_NOT_FOUND, HOLD_ALREADY_USED, DEADLINE_PASSED |
| `getMyProfile` | GET | `/api/v1/me` | EMPLOYEE, MANAGER, ADMIN | - | ST-PP-2, ST-PP-4, ST-PP-5, ST-EN-1 | - |
| `getOccupancyReport` | GET | `/api/v1/reports/occupancy` | ADMIN | - | ST-RP-1, ST-RP-2, ST-RP-3 | VALIDATION_ERROR |
| `exportReport` | GET | `/api/v1/reports/occupancy/export` | ADMIN | - | ST-RP-4 | VALIDATION_ERROR |

Tags are the modules: `office`, `booking`, `checkin`, `access`, `reports` (and `base`). `getToday` and `getMyProfile` (`/me`) are backend read models (allowed by fe-be-split). `getToday` returns `nextTwoWeeks` (MVP: 14 office-local days, state BOOKED, BOOKABLE, CLOSED or OUTSIDE_WINDOW, with her booking id, part, desk code and status when BOOKED) and `usualDesk` (R1, ST-BK-16: most booked desk in the last 60 days, absent when none). `getBookingRules` and `updateBookingRules` return `version` read from the counter key `DESKBOOK_RULES_VERSION` (Q93).

## 2. Base operations in the YAML

| operationId | Method | Path | Roles | Base spec |
|---|---|---|---|---|
| `getCurrentUser` | GET | `/api/session/me` | ANY | B1.21 |
| `listLocales` | GET | `/api/i18n/locales` | ANY | B1.22 |
| `getLocalePreferences` | GET | `/api/i18n/preferences` | ANY | B1.22 |
| `updateLocalePreferences` | PUT | `/api/i18n/preferences` | ANY | B1.23 |
| `getLabels` | GET | `/api/i18n/labels` | ANY | B1.22 |
| `getIntegrationStatus` | GET | `/api/integrations/status` | ANY | B5.3 |
| `getSuccessFactorsConfig` | GET | `/api/integrations/successfactors/config` | ADMIN | B5.3 |
| `updateSuccessFactorsConfig` | PUT | `/api/integrations/successfactors/config` | ADMIN | B5.3 |
| `testSuccessFactorsConnection` | POST | `/api/integrations/successfactors/connection/test` | ADMIN | B5.3 |
| `getTheme` | GET | `/api/v1/theme` | ANY | B7.3 |
| `updateTheme` | PUT | `/api/v1/theme` | ADMIN | B7.3 |
| `uploadThemeLogo` | PUT | `/api/v1/theme/logo` | ADMIN | B7.3 |
| `getThemeLogo` | GET | `/api/v1/theme/logo` | ANY | B7.3 |
| `deleteThemeLogo` | DELETE | `/api/v1/theme/logo` | ADMIN | B7.3 |
| `resetTheme` | DELETE | `/api/v1/theme` | ADMIN | B7.3 |
| `getThemeHistory` | GET | `/api/v1/theme/history` | ADMIN | B7.3 |
| `getHealth` | GET | `/api/public/health` | ANY | B1.10 |

Not in the YAML: the TTCommon `/webservices/*` job endpoints (form-encoded, no envelope, used as they are, B4.8, B9.3) behind the base Background Jobs page `/jobs`, and `/api/integrations/azure-openai/*` (DeskBook does not use Azure OpenAI). Both stay as the base ships them.

## 3. R1, R2 and Later operations (id, method, path; no schemas yet)

Paths are proposals for the release that builds them; they only add to v1.

| Story | Release | operationId | Method | Path |
|---|---|---|---|---|
| ST-BK-2 | R1 | `getBookingPreferences` | GET | `/me/booking-preferences` |
| ST-BK-4 | R1 | `suggestFreeDesks` | GET | `/free-desks/suggestions` |
| ST-CI-2 | R1 | `checkInByDesk` | POST | `/desks/{deskId}/check-in` |
| ST-CI-3 | R1 | `getDeskPage` | GET | `/desk-pages/{deskCode}` |
| ST-CI-9 | Later | `moveMyBooking` | POST | `/bookings/{bookingId}/move` |
| ST-CI-10 | Later | `leaveEarly` | POST | `/bookings/{bookingId}/leave-early` |
| ST-TM-12 | Later | `markExcused` | POST | `/bookings/{bookingId}/excuse` |
| ST-OS-10 | R1 | `listBlocks` | GET | `/desk-blocks` |
| ST-OS-10 | R1 | `createBlock` | POST | `/desk-blocks` |
| ST-OS-10 | R1 | `removeBlock` | DELETE | `/desk-blocks/{blockId}` |
| ST-OS-11, 12 | R1 | `previewDisruption` | POST | `/disruption-previews` |
| ST-OS-13 | R1 | `importDesks` | POST | `/offices/{officeId}/desk-imports` |
| ST-OS-14 | R1 | `getQrSheet` | GET | `/offices/{officeId}/qr-sheet` |
| ST-OS-15 | R1 | `getDeskOccupancy` | GET | `/desk-occupancy` |
| ST-OS-15 | R1 | `adminCancelBooking` | POST | `/bookings/{bookingId}/admin-cancel` |
| ST-OS-16 | R1 | `adminMoveBooking` | POST | `/bookings/{bookingId}/admin-move` |
| ST-PP-6 | R1 | `getSyncStatus` | GET | `/people/sync-status` |
| ST-PP-7 | R1 | `runSyncNow` | POST | `/people/sync-runs` |
| ST-PP-8 | R1 | `addPerson` | POST | `/people` |
| ST-PP-8 | R1 | `searchPeople` | POST | `/people/search (POST: a name must not go in a query string)` |
| ST-PP-9 | R1 | `listAccess` | GET | `/access-entries` |
| ST-PP-9 | R1 | `addAccess` | POST | `/access-entries` |
| ST-PP-9 | R1 | `removeAccess` | DELETE | `/access-entries/{accessEntryId}` |
| ST-PP-9 | R1 | `getAccessHistory` | GET | `/access-entries/history` |
| ST-NT-1 log | R1 | `listNotifications` | GET | `/notifications` |
| ST-RP-10 | R1 | `getOccupancyGrid` | GET | `/reports/occupancy/grid` (kept in the YAML with `x-release: R1`, D6) |
| ST-RP-6 | R1 | `getSuccessShare` | GET | `/reports/success-share` |
| ST-RP-7 | R2 | `getBusiestDays` | GET | `/reports/busiest-days` |
| ST-RP-8 | R2 | `getWeeklyUse` | GET | `/reports/weekly-use` |
| ST-RP-8 | R2 | `getMissedSearches` | GET | `/reports/missed-searches` |
| ST-TM-1, 2, 7 | R1 | `getTeamWeek` | GET | `/team/week` |
| ST-TM-5 | R1 | `createBookingForReport` | POST | `/team/bookings` |
| ST-TM-6 | R1 | `cancelBookingForReport` | POST | `/team/bookings/{bookingId}/cancel` |
| ST-TM-8 | R1 | `getDelegate` | GET | `/team/delegate` |
| ST-TM-8 | R1 | `setDelegate` | PUT | `/team/delegate` |
| ST-TM-8 | R1 | `removeDelegate` | DELETE | `/team/delegate` |
| ST-TM-9, 10 | R2 | `previewGroupBooking` | POST | `/team/group-bookings/preview` |
| ST-TM-9, 10 | R2 | `createGroupBooking` | POST | `/team/group-bookings` |

Count: 38 new operations (R1 30, R2 5, Later 3). R1 `bookBestDesk` was removed (D5): ST-BK-8 moved into the MVP as `proposeDesks` + `createBookings`. Additive extensions in R1: `listFreeDesks` gets optional `floorId`, `zoneId`, `featureIds` (ST-BK-2, ST-BK-3 polling, ST-PP-10 reserved desks); `getMyProfile` gets `isDelegate`; `createBooking` and `updateDesk` get the reserved flag (ST-PP-10). 45 MVP + 38 = 83, as in the architecture after D5.

## 4. Error codes (problem `code`)

RFC 9457 `application/problem+json`: `type`, `title`, `status`, `detail`, `instance`, `code`, `traceId`, `errors[]` (`field`, `code`, `message`). Extra members are named per code. The SPA maps every code to a message and a next step.

| Code | HTTP | Extra members | Raised by |
|---|---|---|---|
| `VALIDATION_ERROR` | 400 | errors[] | 25 operations (`listOffices`, `createOffice`, `updateOffice` ...) |
| `IF_MATCH_REQUIRED` | 400 | - | 16 operations (`updateOffice`, `openOffice`, `closeOffice` ...) |
| `INVALID_TIMEZONE` | 400 | errors[] | `createOffice`, `updateOffice` |
| `UNAUTHENTICATED` | 401 | - | every /api/v1 operation |
| `FORBIDDEN` | 403 | - | every /api/v1 operation |
| `RESOURCE_NOT_FOUND` | 404 | - | 29 operations (`getOffice`, `updateOffice`, `getOfficeHistory` ...) |
| `CONCURRENT_UPDATE` | 409 | - | 13 operations (`updateOffice`, `openOffice`, `closeOffice` ...) |
| `DESK_JUST_TAKEN` | 409 | - | `createBooking`; `createBookings` (per-day problem of a CHOSEN desk) |
| `ALREADY_BOOKED_THAT_DAY` | 409 | existingBookingId | `createBooking`; `createBookings` (per-day problem) |
| `BOOKING_STATE_CHANGED` | 409 | currentStatus | `cancelBooking`, `checkIn`, `holdBooking` |
| `OFFICE_NAME_TAKEN` | 409 | - | `createOffice`, `updateOffice` |
| `FLOOR_NAME_TAKEN` | 409 | - | `createFloor`, `updateFloor` |
| `ZONE_NAME_TAKEN` | 409 | - | `createZone`, `renameZone` |
| `DESK_CODE_TAKEN` | 409 | - | `createDesk`, `updateDesk` |
| `FEATURE_NAME_TAKEN` | 409 | - | `createFeature` |
| `CLOSED_DAY_EXISTS` | 409 | - | `addClosedDay` |
| `DESK_NOT_AVAILABLE` | 422 | - | `createBooking`; `createBookings` (per-day problem) |
| `DATE_NOT_BOOKABLE` | 422 | reason | `listFreeDesks`, `createBooking`; `createBookings` (per-day problem) |
| `PART_ENDED` | 422 | - | `listFreeDesks`, `createBooking`; `createBookings` (per-day problem) |
| `PROFILE_NOT_READY` | 422 | lastCopyAt | `createBooking`, `createBookings`, `proposeDesks` |
| `EMPLOYEE_INACTIVE` | 422 | - | `createBooking`, `createBookings`, `proposeDesks` |
| `CHECK_IN_NOT_OPEN` | 422 | opensAt | `checkIn`, `holdBooking` |
| `DEADLINE_PASSED` | 422 | - | `checkIn`, `holdBooking` |
| `HOLD_ALREADY_USED` | 422 | - | `holdBooking` |
| `HAS_FUTURE_BOOKINGS` | 422 | count | `updateOffice` (timezone change), `closeOffice`, `retireFloor`, `retireDesk`, `addClosedDay` |
| `DESK_FLOOR_LOCKED` | 422 | - | `updateDesk` (desk with bookings cannot move to another floor) |
| `DUPLICATE` | 409 | errors[] (`sfLocationCode`) | `createOffice`, `updateOffice` |
| `DESK_CODE_LOCKED` | 422 | - | `updateDesk` |
| `ZONE_IN_USE` | 422 | - | `deleteZone` |
| `FEATURE_IN_USE` | 422 | - | `deleteFeature` |
| `INVALID_RELEASE_TIMES` | 422 | - | `updateOfficeSettings` |
| `INVALID_STATE_TRANSITION` | 422 | - | `openOffice`, `closeOffice`, `retireFloor`, `retireDesk` |
| `DATE_IN_PAST` | 422 | - | `addClosedDay` |
| `IDEMPOTENCY_KEY_REUSED` | 422 | - | `createBooking`, `createBookings` |
| `RATE_LIMITED` | 429 | retryAfter (and Retry-After header) | 29 operations, see section 10 |
| `PAYLOAD_TOO_LARGE` | 400 | - | any POST, PUT or PATCH body over 16 KB (not declared per operation) |
| `INTERNAL_ERROR` | 500 | - | every /api/v1 operation |

Base shell endpoints (`/api/session`, `/api/i18n`, `/api/integrations`) keep the base envelope `{success, message, data, error{code, detail, requestId, fieldErrors}}` and their own codes (B1.12 to B1.15, B9.3, B9.4), described by the `EnvelopeFailure` schema.

## 5. Decisions and deviations

- **Action style (D4, ADR-9).** State changes are `POST /<resource>/{id}/<action>`: `open`, `close`, `retire`, `cancel`, `check-in`, `hold`. Everything else is plain CRUD. Action bodies are empty; the version goes in `If-Match`.
- **Paths.** Server URL `/deskbook`; DeskBook modules under `/api/v1`. Resources are plural kebab-case: `/offices`, `/floors`, `/zones`, `/desks`, `/desk-features`, `/bookings`. Child resources one level deep: `/offices/{id}/floors`, `/offices/{id}/closed-days`, `/floors/{id}/zones`. `/today` and `/me` are read models, not resources. `/free-desks` is a search resource (needs `officeId`, `date`, `part`). `/bookable-offices` and its `/calendar` are the employee view of offices, separate from the admin `/offices`.
- **Concurrency.** Every updatable resource returns an integer `version`; PUT and action POSTs need `If-Match: <version>` (quoted or bare). Missing header gives 400 `IF_MATCH_REQUIRED`; a stale version gives 409 `CONCURRENT_UPDATE`. For the three booking actions (`cancelBooking`, `checkIn`, `holdBooking`) a stale version gives 409 `BOOKING_STATE_CHANGED` with `currentStatus`, so the SPA can show the real status (AC6.6). `checkIn` on an already checked-in booking returns 200 with the booking whatever version is sent (AC7.7).
- **Idempotency.** `createBooking` requires `Idempotency-Key` (UUID). Same key and body returns the first booking; same key with another body gives 422 `IDEMPOTENCY_KEY_REUSED`. Uniqueness in the database stays the real guard (ADR-2).
- **Status choices where the architecture gave none.** 422 for business rules: `DESK_CODE_LOCKED`, `ZONE_IN_USE`, `FEATURE_IN_USE`, `INVALID_RELEASE_TIMES` (cross-field R11), `INVALID_STATE_TRANSITION`, `DATE_IN_PAST`. 400 for field validation: `INVALID_TIMEZONE` (also in `errors[]`). 409 for the five `*_TAKEN` codes and `CLOSED_DAY_EXISTS`. Codes added beyond the architect's list: `IF_MATCH_REQUIRED`, `CLOSED_DAY_EXISTS`, `DATE_IN_PAST`, `IDEMPOTENCY_KEY_REUSED`, `UNAUTHENTICATED`, `RATE_LIMITED`.
- **404 for not yours.** Another person's booking id, and any record outside the caller's right to see, answer 404 `RESOURCE_NOT_FOUND`, never 403.
- **Rate limit.** 429 `RATE_LIMITED` with `Retry-After` on `createBooking`, `createBookings` (each day counts), `listFreeDesks`, `proposeDesks`, `checkIn` (security brief 8.3); the numbers belong to the security-architect.
- **Local time.** Office-local days are `format: date` (booking `date`, calendar, report days, closed days). Office-local times of day (release times) are `HH:mm` strings because they have no date or zone of their own. Instants (`deadline`, `checkInOpensAt`, `bookedAt`, `asOf`) are UTC `date-time`. The SPA formats instants in the office `timezone` the booking carries.
- **Optional means absent, not null.** Optional fields (`cancelReason`, `checkedInAt`, `releasedToday`, `tomorrow`, `syncBanner`, `noShowRate`, `lastCopyAt`) are left out when empty. Only history `oldValue` and `newValue` can be null.
- **Office settings.** Master data (`updateOffice`) and settings (`updateOfficeSettings`, `PUT /offices/{id}/settings`) are two writes on one office record and share its `version`. State changes have their own actions. Settings answer with the whole `Office`, including `settingsEffectiveFrom` (tomorrow, R10).
- **Location header.** Every create returns 201 with `Location`. For floors, zones, desk features and closed days the architect's list has no single-record GET (none added), so the Location URI supports only PUT or DELETE. Raised as a question.
- **Lists.** All lists are paged `?page=0&size=20` (max 100) and answer `{items, page{number,size,totalElements,totalPages}}`; `listFreeDesks` adds `totalFree` and `asOf`; `getOccupancyReport` adds `totals`. `getBookingCalendar` and `getToday` are bounded by construction (horizon at most 60 days; 3 bookings). The report range is at most 93 days; a longer range gives 400 `VALIDATION_ERROR` with `errors[]` code `RANGE_TOO_LONG` on `to`.
- **Privacy in the contract.** `FreeDesk`, `OccupancyRow` and `OccupancyTotals` carry no person data. `Booking` carries no other person's name; `bookedByName` appears only to the booked person when a manager booked (R1). `MyProfile` carries only the caller. No personal data in paths or queries (UUIDs and desk codes only); `searchPeople` (R1) is a POST for that reason.
- **Report maths.** All report counts are desk-days (a half day is 0.5, R40). `noShowRate` = `noShowDeskDays` / `bookedDeskDays`; `bookedDeskDays` already excludes bookings cancelled before the deadline (R41). `releasedAfterHoldDeskDays` stays separate (Q50).
- **Base endpoints.** Included so the file is the complete contract: session, i18n, integrations status, SuccessFactors config and connection test, theme (7 operations), health. Shell endpoints keep the base `ApiResponse` envelope (B9.3). This deviates from the standard's no-wrapper rule only for those base paths, because the base ships them that way and the shell frontend depends on it; DeskBook endpoints do not use it. `/api/v1/theme` is problem details as in B7.3.
- **Security.** One scheme, `bearerAuth` (XSUAA JWT forwarded by the approuter). Roles per operation in `x-roles`; the backend checks role and record on every call (`DeskAccessGuard`). Only `getHealth` has `security: []`.
- **Plan my week (D5, ADR-12).** `proposeDesks` is a read with no side effect: `GET /desk-proposals?officeId&dates&part&zoneId&featureIds` with `dates` and `featureIds` comma-separated (`style: form`, `explode: false`; 1 to 14 distinct dates), so no body is needed and no person data is in the URL. It answers `{items[{date, part, desk, reason | noneReason}]}`, one item per date, not paged (bounded at 14). `createBookings` is `POST /bookings/batch` (the fixed segment `batch` next to `{bookingId}`), requires `Idempotency-Key`, takes `{officeId, items[{date, part, deskId, source PROPOSED|CHOSEN}]}` (1 to 14, distinct dates) and answers 200 with `{items[{date, outcome BOOKED|REPICKED|FAILED, booking | problem}], bookedCount, failedCount}`; `bookedCount` counts BOOKED and REPICKED. A per-day refusal is a `problem {code, detail}` (plus `existingBookingId` or `reason` where the code has one), never an HTTP error; the whole request fails only for 400 validation, 404 office, 422 `PROFILE_NOT_READY` / `EMPLOYEE_INACTIVE` / `IDEMPOTENCY_KEY_REUSED`, 429. The key is stored per day as `<key>:<date>`, so a replay returns the same days; `createBooking` is unchanged and stays for single bookings.
- **Grid.** `getOccupancyGrid` is `GET /reports/occupancy/grid?officeId&from&to`: office required, range at most 31 days, answer `{zones[{id?, name?, floorName, merged?}], days[], cells[{zoneId?, floorName?, merged?, date, capacity, booked, checkedIn, noShow, upcoming}]}`, not paged (bounded by zones x 31 days), counts only, small-cell rule (D2, review M5): a zone under 3 desks or holding a reserved desk is merged into one row per floor (`id` and `name` absent, `merged: true`, identified by `floorName`; its cells carry `floorName` and `merged` and no `zoneId`), desk-days like the report (0.5 steps). Cells are all present, zero when empty. The table `getOccupancyReport` stays paged at 100 with whole-filter totals (Q95).
- **Review fixes M3, M4, M5, M14 (no new operation; MVP 45 operations unchanged).** `BookingCalendar` now has required `zones[{id, name, floorName}]` and `features[{id, name}]` for the S2 filters (new schema `BookableZone`); `TomorrowFree.bookableDesks` (required, AC18.4); `Booking.holdUntil` (optional, absent when `holdAvailable` is false: deadline plus the hold minutes, Q49; AC5.12); `BookingBatchOutcome.previousDeskCode` (optional, only for REPICKED; AC19.4). `listFreeDesks` records nothing in the MVP (search log is R1, PF-6). A proposal with no desk leaves `desk` and `reason` out; grid range stays 31 days. Desk features on `Booking` and `UsualDesk` and `CalendarDay.parts[].freeDesks` are SHOULD (S11), not added.
- **Absent, not null, for no desk.** The architect wrote `desk ... | null` in the proposal item; following the file rule (optional means absent), `desk` and `reason` are left out and `noneReason` is set when no desk can be proposed. Raised as a question.
- **Extensions.** `x-roles`, `x-release` and `x-stories` (story ids) are on every operation.

## 6. Open questions

Appended to `questions.md` as four open questions from api-designer to solution-architect: BookingRules version source (ConfigService has no row version), Location header for records without a single GET, report paging at 100 rows, and whether changed hold or late-check-in minutes touch existing bookings (all four answered, Q93-Q96). D5 added three more for solution-architect (Q115): grid range 31 or 62 days (security Q114 says 62), grid release (stories say R1, architecture says MVP), and `desk` absent versus null in a proposal.

## 7. Changes after code review (29 Oct 2026)

Source: 07-code-review.md MUST 1, 2, 5 and questions Q133-Q153. Additive except the path prefix; operation ids, `x-release` tags and existing shapes are unchanged; MVP stays 45 operations.

- **Path prefix (MUST 1, Q133).** All 35 DeskBook paths now start with `/api/v1` in `paths:` (the base theme paths already did); `servers.url` stays `/deskbook` (context path). The full URL is `/deskbook/api/v1/...`. Regenerate `deskbook.gen.ts`; the contract test must compare full paths. Note: `D:/products/desk-booking/Backend/.../openapi.yaml` is the backend lane's copy and still has the old paths; the backend lane re-merges from this file (S10: one source).
- **Built answers now listed (MUST 2, Q139, Q143, Q144).** `updateOffice` 422 `HAS_FUTURE_BOOKINGS` (timezone change, member `count`); `updateDesk` 422 `DESK_FLOOR_LOCKED`; `createOffice` and `updateOffice` 409 `DUPLICATE` for a duplicate `sfLocationCode` (kept `DUPLICATE`, not `SF_LOCATION_TAKEN`; `errors[]` names the field); `openOffice` on a CLOSED office 422 `INVALID_STATE_TRANSITION` (CLOSED is final). `settings_effective_from` is already `settingsEffectiveFrom` in `OfficeSettings`, closed-day reason is already 200: no change.
- **`OfficeSummary` (Q145).** Optional integers `floorCount`, `deskCount` (active floors; active desks on active floors).
- **`TodayView` (Q151).** Optional `timezone` (IANA) and `today` (office-local date); absent when there is no home office or it is closed.
- **Late note on S2 (Q150).** Put on the calendar, not on `listFreeDesks`: `PartAvailability.late` and `BookingCalendar.lateCheckInMinutes`. The S2 row reads them from the calendar it already loads; no rule in the SPA.
- **Problem `deadline` (Q153).** Optional `deadline` (date-time, UTC) on `HOLD_ALREADY_USED`, and also on `DEADLINE_PASSED` (same need). The SPA formats it in the office timezone.
- **Day totals (MUST 5, Q152).** `getOccupancyReport` has required `dayTotals[]` (`OccupancyDayTotal`: date, officeId, officeName, capacity, booked, checked-in, no-show, released-after-hold, cancelled-before-deadline desk-days, `noShowRate`) with one entry for every office and day in `items`, summed on the server over all floors of that day (not only the rows on the page). The SPA shows these as the "All floors" line and no longer sums pages. `exportReport` writes the same rows (floor column "All floors"). `totals` still covers the whole filter.

New or changed error rows: `HAS_FUTURE_BOOKINGS` also on `updateOffice`; `DESK_FLOOR_LOCKED` (422, `updateDesk`); `DUPLICATE` (409, `createOffice`, `updateOffice`); `INVALID_STATE_TRANSITION` also on `openOffice` for CLOSED.

Not done here: the field error codes of S8/Q136 (`NOT_BLANK`, `SIZE`, `PATTERN`) and Q149 (inclusive horizon note) were not in this change.

## 8. Changes after wave 3a (29 Oct 2026)

Source: Q159, Q160 (built answers listed in the contract). Descriptions and 400 responses only; no new operation, schema or field; operation ids and `x-release` unchanged; MVP unchanged. Codes read against the built services.

- **Reports (Q159).** `getOccupancyReport` and `exportReport`: an unknown or other-tenant `officeId` is 400 `VALIDATION_ERROR` with `errors[]` field `officeId`, code `NOT_FOUND` (no 404: it is a filter value, and the answer does not reveal whether the office exists for another tenant). A `to` over 93 days after `from` is 400 on `to`, code `RANGE_TOO_LONG`. `exportReport` above 100,000 rows is 400 on `to`, code `EXPORT_TOO_LARGE` (narrow the range or pick one office).
- **Parent-state refusals (Q160), all 400 `VALIDATION_ERROR`.** `createZone`: retired floor, field `floorId`, code `FLOOR_RETIRED`. `createFloor`: CLOSED office, field `officeId`, code `OFFICE_CLOSED`. `createDesk`: retired floor `FLOOR_RETIRED` and CLOSED office `OFFICE_CLOSED`, both on `floorId`; a repeated id in `featureIds` (cap 20, already `maxItems`) is `DUPLICATE` on `featureIds`. `updateDesk` (same service rules, added for consistency): moving to a retired floor is `FLOOR_RETIRED` on `floorId`, a repeated feature id is `DUPLICATE`; a desk already on a retired floor can still be edited and retired.
- **Style.** Field-level codes live in `errors[]` under the one problem code `VALIDATION_ERROR` (as `EXPORT_TOO_LARGE` and `RANGE_TOO_LONG` do), so no new top-level problem code and no new HTTP status; the five operations now have a named 400 response with an example per refusal (`updateDesk` keeps its existing 400 block, the new codes are in its description).

New field-level codes in `errors[]`: `NOT_FOUND` (reports, `officeId`), `RANGE_TOO_LONG`, `EXPORT_TOO_LARGE`, `FLOOR_RETIRED`, `OFFICE_CLOSED`, `DUPLICATE` (`featureIds`; the 409 `DUPLICATE` for a location code is unchanged). Lint: Redocly not run (npx refused in this session); checked by Python yaml load (63 operations, ids unique), `$ref` resolution (none missing) and reading against the standard.

## 9. Changes after S7 (29 Oct 2026)

Source: Q198 (QA FAIL, ST-BK-8 criterion 3 / AC19.5), Q191 and the code differences of 07-system-review S1 and 07-code-review B2-S14. Additive except one description (item 6). Operation ids, `x-release`, the 45 MVP operations and the 429 design are unchanged; the file still has 63 operations (same count as before this change). Checked by a Python yaml load, operationId uniqueness and a `$ref` resolve check; Redocly not run.

- **Nearest options when nothing matches (Q198, AC19.5).** `DeskProposal.noneReason` gets `NO_MATCH`; new optional `DeskProposal.alternatives` (1 to 3, only with NO_MATCH) of new schema `DeskAlternative {desk, reason, missingFeature?}`. `NOTHING_FREE` now means no desk at all is free; an unfiltered request never gets NO_MATCH. Order (one desk per zone or dropped feature, lowest code, cut at 3): `USUAL_DESK` (her usual desk if free but outside her choices; D6 rule: most booked in the last 60 days, at least 3 times, tie to the most recent), `NEAREST_ZONE` (zone on the same floor as the chosen zone, else the floor of her usual desk, with all her features), `OTHER_ZONE` (any other zone, by name), `WITHOUT_FEATURE` (her zone kept, one chosen feature dropped; `missingFeature` names it), `ANY_FREE` (first free desk by code; only when nothing above gave a desk, so NO_MATCH always has at least 1). Read-only, no person data, no new operation: she books an alternative with `createBookings` (source CHOSEN) like a desk picked in Change. Old clients that do not know NO_MATCH see a day without a desk, as before. AC19.5 as worded (a day lost at confirm time, "other days or offices") is the existing FAILED outcome of `createBookings` plus the other days of the proposal list; other offices stay the user action in the S2 text.
- **401 code (Q191, S1).** Code is right: the guard answers `UNAUTHORIZED`. The `Unauthorized` response and the error table row now use `UNAUTHORIZED` (was `UNAUTHENTICATED`). A 401 raised by the platform filter before the app has no problem body; the response description says clients decide on the status.
- **`REQUEST_IN_PROGRESS` (Q191, S1, B2-S14).** 409 on `createBooking` (same Idempotency-Key still being processed: wait and resend); on `createBookings` it is a per-day problem code (`BookingBatchProblem.code`).
- **`IDEMPOTENCY_KEY_REUSED` on `createBookings`.** The code checks the key per day (`<key>:<date>`), so it is a FAILED day with problem code `IDEMPOTENCY_KEY_REUSED`, not the whole-request 422 the design had. The contract follows the code: the 422 of `createBookings` lists only `PROFILE_NOT_READY` and `EMPLOYEE_INACTIVE` (its example was removed); `createBooking` keeps the 422. Asked in Q201.
- **Report `from` and `to` (Q191, S1).** Stay `required: true` in the contract. The controller binds them optional and the service answers 400 `VALIDATION_ERROR` with field code `REQUIRED` on `from` or `to`, and `BEFORE_FROM` on `to`: same visible result, so the contract only lists the field codes (descriptions of `getOccupancyReport`, `exportReport`). No change asked of the code.
- **`INVALID_SORT` (B2-S14).** Field code on `sort` under 400 `VALIDATION_ERROR` (built in `PageParams` and the report service); every `sort` parameter description says so.
- **`CONFIGURATION_NOT_SAVED` (B2-S14).** 500 on `updateBookingRules` with its own problem example, when the configuration store refuses the write (nothing changed, version not raised).
- **Named 400 answers (B2-S14).** `createDesk`, `createFloor`, `createZone`, `getOccupancyReport`, `exportReport` already have them in this file (section 8); the Backend `openapi.yaml` is a stale copy. No contract change: Q201 asks backend-developer to copy this file in the build step.
- **Rate limit.** 429 `RATE_LIMITED` unchanged (being built).

New or changed codes: `NO_MATCH` (noneReason, 200), `UNAUTHORIZED` (401, replaces `UNAUTHENTICATED`), `REQUEST_IN_PROGRESS` (409, or per-day), `IDEMPOTENCY_KEY_REUSED` (also per-day on `createBookings`), `CONFIGURATION_NOT_SAVED` (500), field codes `INVALID_SORT`, `REQUIRED`, `BEFORE_FROM`.

Open: Q201 (backend-developer), Q202 (frontend-developer, qa-engineer).

## 10. Changes after S7 fixes (29 Oct 2026)

Additive only: 63 operations in the file, 62 MVP (45 module plus base), no path, operation id or schema removed. Answers Q209 (backend-developer). Lint: `npx` could not be run here, so lint is not run; checked with a Python YAML load, unique operation ids and all 107 `$ref` values resolving.

- **Body limit (Q209 item 1).** A POST, PUT or PATCH body over 16 KB answers `400 PAYLOAD_TOO_LARGE` (problem details). Decision: stays 400. The API standard has no 413 and 400 is its status for a request the server will not process; the frontend already handles 400. Stated once in the `info.description` of the YAML, not on every write operation (no 413 response added). Multipart uploads (theme logo) are outside the limit. Code `PAYLOAD_TOO_LARGE` is added to the error table (section 4).
- **Rate limit (Q209 item 3).** `429 RATE_LIMITED` carries the `Retry-After` header and the problem member `retryAfter` (integer seconds, same number). `Problem.retryAfter` added; the shared `TooManyRequests` response, its example and the `RetryAfter` header text say so. A refused call counts nothing. Per person and minute, one instance (the count is per instance).
- **429 on every limited operation.** Before: 5 operations plus the base health check. Now 29 in the file:

| Limit per person and minute | Operations |
|---|---|
| createBooking 10 | `createBooking` |
| 20 each | `cancelBooking`, `checkIn`, `holdBooking`, `proposeDesks` |
| listFreeDesks 30 | `listFreeDesks` |
| createBookings 3 | `createBookings` (also charges 1 booking-day per day; booking-days 30 shared with `createBooking`; all or none) |
| occupancy report 10 | `getOccupancyReport` |
| export 5 | `exportReport` |
| admin writes 60 | the 19 writes of office setup and booking rules: `createOffice`, `updateOffice`, `openOffice`, `closeOffice`, `updateOfficeSettings`, `createFloor`, `updateFloor`, `retireFloor`, `createZone`, `renameZone`, `deleteZone`, `createDesk`, `updateDesk`, `retireDesk`, `createFeature`, `deleteFeature`, `addClosedDay`, `removeClosedDay`, `updateBookingRules` |

  Not limited: reads of the office setup, `getBookingCalendar`, `listBookableOffices`, `listMyBookings`, `getBooking`, `getToday`, `getMyProfile`, `getOccupancyGrid`, base theme writes. The numbers are build facts, not contract promises: clients read `retryAfter`, never hard-code a limit.
- **`holdBooking` 422 `CHECK_IN_NOT_OPEN` (Q209 item 2).** Before the check-in window of that day opens, the hold is refused with `opensAt` (the hold is not spent). Operation description, 422 text and example updated, like `checkIn`. The frontend maps it like on `checkIn`.
- **Idempotency-Key (Q209 item 4).** `format: uuid` replaced by `minLength 1`, `maxLength 64`, `pattern ^[A-Za-z0-9_-]{1,64}$` (a UUID still fits). A colon or any other character, or a longer key: `400 VALIDATION_ERROR` with field code `INVALID_FORMAT`. The batch call builds `<key>:<date>` per day on the server only; clients never send a colon. The security minimum of 16 characters (05-security 4.2a) is not in the contract (Q210, security-architect).

New codes: `PAYLOAD_TOO_LARGE` (400, no field), field code `INVALID_FORMAT` now also on `Idempotency-Key`. Changed: `RATE_LIMITED` (adds `retryAfter`), `CHECK_IN_NOT_OPEN` (also on `holdBooking`).

Open: none for api-designer. Backend copies the file to `Backend/src/main/resources/openapi/openapi.yaml` (Q201).
