# SuccessFactors reference (owned by `sf-consultant`)

The knowledge base the SF consultant starts from. Anything marked *verify* must be confirmed in the customer's
tenant (`/odata/v2/$metadata`, Admin Center > OData API Data Dictionary) before a design depends on it.
Add new facts only when verified, with the source.

## Golden rules
1. Every SF tenant is configured differently: custom fields (`customString1..n`, `customDate..`), picklists,
   MDF objects and field labels come from the customer's data model. Read the tenant `$metadata`; never assume.
2. Most Employee Central data is effective-dated. Decide for each read: today (`asOfDate`), a range
   (`fromDate`/`toDate`) or full history. Future-dated hires, transfers and terminations exist.
3. Pick the right id and store it: `userId` (one per employment, the key most entities use),
   `personIdExternal` (the person, stable across rehire and concurrent employment), `assignmentIdExternal`
   (newer assignment id, *verify* it is enabled), `username` (login, can change - never a key), email (can
   change - never a key).
4. SF is usually the master for people and organisation data. We keep a copy only of what the product needs
   and sync it; we never push back fields SF owns unless the customer agrees.
5. The API user's permissions (RBP) decide what the API returns: missing fields are often missing permissions,
   not missing data.

## Employee Central - core entities (OData v2)
| Need | Entity | Key fields and notes |
|---|---|---|
| Who the user is, login, status | `User` | `userId`, `username`, `status` (`t`/`f` active/inactive; inactive users are **left out by default** - filter `status in 't','f'` to include them), `email`, `firstName`, `lastName`, `defaultLocale`, `timeZone`, `manager` (navigation) |
| The person | `PerPerson` | `personIdExternal`, `dateOfBirth` (sensitive); nav to personal, email, phone |
| Names (effective-dated) | `PerPersonal` | `firstName`, `lastName`, `preferredName`, `displayName` (*verify*), `startDate` |
| Work email | `PerEmail` | `emailAddress`, `emailType` (picklist), `isPrimary` |
| Employment | `EmpEmployment` | `userId`, `personIdExternal`, `startDate`, `endDate`, `originalStartDate`, `isContingentWorker` (*verify*) |
| Job (effective-dated) | `EmpJob` | `userId`, `startDate`, `seqNumber`, `company`, `businessUnit`, `division`, `department`, `location`, `costCenter`, `jobCode`, `position`, `managerId` (a `userId`), `emplStatus` (picklist), `eventReason`, `employeeClass`, `fte`, `timezone` |
| Other relationships | `EmpJobRelationships` | `relationshipType` (HR manager, matrix manager...), `relUserId` |
| Termination | `EmpEmploymentTermination` | `endDate`, `eventReason`; also read `emplStatus` on `EmpJob` |
| Organisation | `FOCompany`, `FOBusinessUnit`, `FODivision`, `FODepartment`, `FOLocation`, `FOCostCenter`, `FOJobCode` | `externalCode`, `name`, localised `name_<locale>` (*verify* per object), `status`, `startDate`; department has `parent` |
| Positions | `Position` | `code`, `positionTitle`, `department`, `parentPosition`, `vacant` |
| Picklist labels | `PickListValueV2` / `PicklistOption` + `PicklistLabel` (legacy) | map the stored option id or external code to the label in the user's locale |

Advice
- Manager: `EmpJob.managerId` as of the date you need (it follows the job history); `User.manager` is a
  convenience view of today. A missing manager is `NO_MANAGER` or empty (*verify*); handle both.
- Active employee: `EmpJob.emplStatus` (picklist, e.g. active / leave / terminated) is more precise than
  `User.status`; use both for leavers.
- Concurrent or global assignments: one person, several `userId`s. Decide per product whether a person or an
  employment is "the user" and say so in the spec.
- Org names: read the FO object effective as of today and the localised name for the UI language.

Verified facts (added 2026-10-28 by sf-consultant, DeskBook field mode)
- `User.status` codes: `t` active, `f` inactive, `T`/`F` active/inactive external, `e`/`d` active/inactive
  external suite (Learning or Onboarding-only users). A `User` read with no key and no status filter returns
  only `t` and `T`; to get leavers ask `$filter=status in 't','f'` (list the codes; never `status ne ...`). With a
  key predicate `$filter` is ignored. Writes to inactive users need `processInactiveEmployees=true`.
  Source: SAP KBA 2166571 "How to query inactive users on User entity - OData API" (snippets; full text needs
  SAP for Me). Combining `status in` with other filters reportedly fails in Integration Center (*verify*).
- `User.location` (like department/division) is a text copy written by HRIS sync from Job Information; the
  mapping is tenant-configurable and can be remapped (e.g. to geozone), so its format is not guaranteed to be the
  FOLocation code. Source: SAP KBA 2395169, 2506989. For a code, read `EmpJob.location`.
- EC effective-dated entities (`EmpJob`, `PerPerson`, ...) return the latest active record by default; use
  `fromDate`/`toDate` for past and future slices. Source: SAP KBA 2638422, 2148752.
- `EmpEmployment.isPrimary` is an obsolete legacy field with no meaning for concurrent employment; use the
  primary/secondary employment information instead. Source: SAP KBA 2816104 (and 2326735 for the API approach).
- OData admin mode (e.g. granting "Employee Central HRIS OData API (read-only)") overrides RBP and returns all
  data; keep integration users on a scoped RBP role unless full access is wanted. Field-level RBP may not stop an
  API user from reading a restricted field. Source: SAP KBAs on OData admin mode, 2316798, 2635970.

## Other modules (entity names to verify on api.sap.com for the customer's release)
| Module | Main objects | Notes |
|---|---|---|
| Learning (LMS) | learning plan, learning history (completions), assignments, catalog items, curricula | separate LMS OData services with their own OAuth on the LMS host, not `/odata/v2` (*verify* service names) |
| Performance and Goals | `Goal_<planId>`, `GoalPlanTemplate`, `FormHeader`, `FormContent` | goal entity name includes the plan id; forms are route-map driven |
| Recruiting | `JobRequisition`, `Candidate`, `JobApplication`, `JobOffer` | template-driven fields per requisition template |
| Onboarding | `ONB2Process` and related | *verify* |
| Time | `EmployeeTime`, `TimeAccount`, `TimeAccountDetail`, `TimeType` | absences are effective by date range; approval status matters |
| Compensation | `EmpCompensation`, `EmpPayCompRecurring` | highly sensitive; pull only with a clear need |
| Succession and talent | `Successor`, talent pools, skills and competencies (Talent Intelligence Hub attributes) | names change between releases (*verify*) |

## Reading (pull)
- Delta: `$filter=lastModifiedDateTime ge datetimeoffset'...'` per entity, with a stored checkpoint; on
  effective-dated entities combine with `fromDate`/`toDate` so future-dated changes are not missed.
  Alternatives: Intelligent Services events (push from SF on hire, transfer, termination), Integration Center
  jobs, the SFAPI `CompoundEmployee` API for full employee deltas (SOAP).
- Paging: server pages (default and max page size, `$skiptoken`); snapshot paging for long full loads
  (*verify* options in the tenant). Use `$select` always; `$expand` only one or two levels.
  Verified: client paging `$top`/`$skip` (SAP KBA 2675265); server paging follows `__next` / `$skiptoken`
  (KBA 2489065); `paging=snapshot` can fail with "snapshot lost" and the read must restart from page 1
  (KBA 2990434). The 1,000 rows per call ceiling is cited by SAP Community only (*verify*).
- First load: full read as of today plus future-dated records; then deltas.

## Writing (push)
- `POST /odata/v2/upsert` with the business key; on effective-dated entities `purgeType=full` replaces the
  history, incremental (the default) adds or updates a record - choose deliberately.
- Writes can trigger SF business rules and workflows; say which ones will fire.
- Required fields and allowed picklist values come from the tenant configuration.

## Security and privacy
- OAuth 2.0 (SAML bearer assertion or X.509 client certificate) for an API user; basic auth is being retired
  (*verify* the tenant's state).
- RBP permissions per entity and field for the API user; list them in the design.
- Sensitive fields (date of birth, national id, compensation, gender) are copied only with a written need and
  are masked in our audit history. Respect SF data purge (DRTM) for leavers: our copy follows SF retention.

## Sources
- SAP Business Accelerator Hub: api.sap.com (SuccessFactors packages, entity reference).
- SAP Help Portal: "SAP SuccessFactors HXM Suite OData API: Reference Guide" and "Developer Guide".
- The customer's tenant: `$metadata`, OData API Data Dictionary, Manage Business Configuration.
