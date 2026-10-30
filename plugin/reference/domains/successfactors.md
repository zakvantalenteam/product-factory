# SuccessFactors reference (generic)

Read by `sf-expert`. It holds what is true for SAP SuccessFactors in any repo. Where this repo calls
SuccessFactors lives in `.claude/experts/sf.md` and is read separately. Anything marked *verify* must be
confirmed on api.sap.com, help.sap.com or in the customer's tenant (`/odata/v2/$metadata`, Admin Center, OData
API Data Dictionary) before a design depends on it. This file is core-owned: the expert proposes new verified
facts in its output file (`## New facts for the core reference`, each with its source) and the lead moves them
here.

## Golden rules
1. Every tenant is configured differently: custom fields (`customString1..n`, `customDate..`), picklists, MDF
   objects and field labels come from the customer's data model. Read the tenant `$metadata`; never assume.
2. Most Employee Central data is effective-dated. For each read decide: today (`asOfDate`), a range
   (`fromDate`/`toDate`) or full history. Future-dated hires, transfers and terminations exist.
3. Pick the right id and store it: `userId` (one per employment, the key most entities use),
   `personIdExternal` (the person, stable across rehire and concurrent employment), `assignmentIdExternal`
   (newer assignment id, *verify* it is enabled), `username` (login, can change: never a key), e-mail (can
   change: never a key).
4. SuccessFactors is usually the master for people and organisation data. Keep a copy only of what the product
   needs and sync it; never push back fields it owns unless the customer agrees.
5. The API user's permissions (RBP) decide what the API returns: a missing field is often a missing
   permission, not missing data, and a missing permission gives null or no rows, not an error.
6. Never assume a module is licensed or configured for a tenant (goal templates, picklists, MDF objects,
   RBP roles): ask the owner.

## Modules and the objects that usually carry them
Confirm every entity, navigation and field name on api.sap.com for the customer's release before citing it;
write "unverified" when you could not.
| Module | Functional purpose | Usual API objects |
|---|---|---|
| Employee Central | person, employment, job, organisation | `PerPerson`, `PerPersonal`, `PerEmail`, `EmpEmployment`, `EmpJob`, `EmpCompensation`, `EmpPayCompRecurring`, foundation objects `FOCompany`, `FODepartment`, `FOBusinessUnit`, `FOLocation`, `FOJobCode` |
| Position Management | positions and reporting lines, matrix | `Position`, matrix relationships |
| Time Off, Time Tracking | absences, balances, time sheets | `EmployeeTime`, `TimeAccount`, `TimeAccountDetail`, `TimeType` (effective by date range; approval status matters) |
| Payroll integration | pay data hand-over | Employee Central Payroll replication; the SFAPI Compound Employee API for point to point |
| Recruiting | requisitions, candidates, applications, offers | `JobRequisition`, `JobApplication`, `Candidate`, `JobOffer`, `JobApplicationStatus`, `Attachment`; fields are template-specific, field permissions vary per status |
| Onboarding | pre-boarding and the hire hand-over | Onboarding 2.0 on MDF (`ONB2Process` and related, *verify*), hand-over into Employee Central |
| Performance and Goals | reviews, goals, continuous performance | `FormHeader`, `FormContent`, `FormTemplate`, `Goal_<plan id>`, `GoalPlanTemplate`, `Activity`, `Achievement`, feedback; forms are route-map driven |
| Compensation | merit, bonus, pay components | forms, `EmpCompensation`, `EmpPayCompRecurring`; highly sensitive: pull only with a clear need |
| Succession and Development | nominations, talent pools, development goals | `Successor`, talent pools, `DevGoal_<plan id>`, `DevGoalPlanTemplate`, competencies, mentoring (names change between releases, *verify*) |
| Learning | catalogue, assignments, curricula, history, approvals, scheduled offerings | OData v4 services under the Learning host (`/learning/odatav4/...`), Learning REST APIs (`/learning/rest/...`, `/learning/public-api/rest/...`), their own OAuth, admin versus user services; not `/odata/v2` |
| Job Profile Builder | job profiles, families, roles, templates | `JobProfile`, `FamilyEntity`, `RoleEntity`, `JobCodeMappingEntity`, `JobDescTemplate`, competency and skill contents |
| Talent Intelligence Hub | skills and competency libraries, growth portfolios | attribute libraries, ratings, the `rest/ecosystem/wholeself/v1/...` APIs (*verify*) |
| Opportunity Marketplace | assignments, mentoring, learning and gig opportunities | module APIs (*verify*) |
| Workforce and People Analytics | stories, reporting data | some data has no API: say so |
| SAP Build Work Zone | workspaces and cards that frame apps | framing needs frame-options and CSP settings decided on purpose |

## Employee Central core entities (OData v2)
| Need | Entity | Key fields and notes |
|---|---|---|
| Who the user is, login, status | `User` | `userId`, `username`, `status` (`t` active, `f` inactive; inactive users are left out by default), `email`, `firstName`, `lastName`, `defaultLocale`, `timeZone`, `manager` (navigation) |
| The person | `PerPerson` | `personIdExternal`, `dateOfBirth` (sensitive); navigation to personal, e-mail, phone |
| Names (effective-dated) | `PerPersonal` | `firstName`, `lastName`, `preferredName`, `displayName` (*verify*), `startDate` |
| Work e-mail | `PerEmail` | `emailAddress`, `emailType` (picklist), `isPrimary` |
| Employment | `EmpEmployment` | `userId`, `personIdExternal`, `startDate`, `endDate`, `originalStartDate`, `isContingentWorker` (*verify*) |
| Job (effective-dated) | `EmpJob` | `userId`, `startDate`, `seqNumber`, `company`, `businessUnit`, `division`, `department`, `location`, `costCenter`, `jobCode`, `position`, `managerId` (a `userId`), `emplStatus` (picklist), `eventReason`, `employeeClass`, `fte`, `timezone` |
| Other relationships | `EmpJobRelationships` | `relationshipType` (HR manager, matrix manager), `relUserId` |
| Termination | `EmpEmploymentTermination` | `endDate`, `eventReason`; also read `emplStatus` on `EmpJob` |
| Organisation | `FOCompany`, `FOBusinessUnit`, `FODivision`, `FODepartment`, `FOLocation`, `FOCostCenter`, `FOJobCode` | `externalCode`, `name`, localised `name_<locale>` (*verify* per object), `status`, `startDate`; department has `parent` |
| Positions | `Position` | `code`, `positionTitle`, `department`, `parentPosition`, `vacant` |
| Picklist labels | `PickListValueV2` (legacy `PicklistOption` plus `PicklistLabel`) | map the stored option id or external code to the label in the user's locale |
| Custom objects | MDF generic objects `cust_*` | `externalCode`, `effectiveStartDate` |

Advice
- Manager: `EmpJob.managerId` as of the date you need (it follows the job history); `User.manager` is a view
  of today. A missing manager is `NO_MANAGER` or empty (*verify*): handle both.
- Active employee: `EmpJob.emplStatus` (active, leave, terminated) is more precise than `User.status`; use
  both for leavers.
- Concurrent or global assignments: one person, several `userId`s. Decide per product whether a person or an
  employment is "the user" and say so in the spec.
- Org names: read the foundation object effective as of today and the localised name for the UI language.

## Verified facts (with source)
- `User.status` codes: `t` active, `f` inactive, `T`/`F` active/inactive external, `e`/`d` active/inactive
  external suite (Learning or Onboarding-only users). A `User` read with no key and no status filter returns only
  `t` and `T`; to get leavers ask `$filter=status in 't','f'` (list the codes; never `status ne ...`). With a key
  predicate `$filter` is ignored. Writes to inactive users need `processInactiveEmployees=true`. Source: SAP KBA
  2166571. Combining `status in` with other filters reportedly fails in Integration Center (*verify*).
- `User.location`, like department and division, is a text copy written by the HRIS sync from Job Information;
  its mapping is tenant-configurable, so its format is not guaranteed to be the foundation-object code. For a
  code read `EmpJob.location`. Source: SAP KBA 2395169, 2506989.
- Effective-dated Employee Central entities (`EmpJob`, `PerPerson`, ...) return the latest active record by
  default; use `fromDate`/`toDate` for past and future slices. Source: SAP KBA 2638422, 2148752.
- `EmpEmployment.isPrimary` is an obsolete legacy field with no meaning for concurrent employment; use the
  primary and secondary employment information. Source: SAP KBA 2816104 (and 2326735).
- OData admin mode (for example granting "Employee Central HRIS OData API (read-only)") overrides RBP and
  returns all data; keep integration users on a scoped RBP role unless full access is wanted. Field-level RBP
  may not stop an API user from reading a restricted field. Source: SAP KBAs 2316798, 2635970.
- Client paging `$top`/`$skip`: KBA 2675265. Server paging follows `__next` or `$skiptoken`: KBA 2489065.
  `paging=snapshot` can fail with "snapshot lost" and the read must restart from page 1: KBA 2990434. The
  1,000 rows per call ceiling is cited by SAP Community only (*verify*).

## OData v2 reading
- `$metadata` first. `$select` always; `$expand` one or two levels; `$filter` with v2 datetime literals
  (`datetimeoffset'...'`); `$orderby`; `$top`/`$skip`; `customPageSize`.
- Paging: follow `__next` (server paging); snapshot or cursor paging for long full loads. `$skip` without
  `$orderby` can skip or repeat rows when data changes during the read.
- Delta: `$filter=lastModifiedDateTime ge datetimeoffset'...'` with a stored checkpoint; on effective-dated
  entities combine it with `fromDate`/`toDate` so future-dated changes are not missed. Alternatives:
  Intelligent Services events (push on hire, transfer, termination), Integration Center jobs, the SFAPI
  `CompoundEmployee` API for full employee deltas (SOAP).
- First load: a full read as of today plus future-dated records, then deltas.
- `$batch` with change sets for many small calls; OData v4 where the API has it (Learning).

## Writing
- `POST /odata/v2/upsert` with the business key. One HTTP 200 can hold failed rows, so check every row's
  status. On effective-dated entities `purgeType=full` replaces the history; incremental (default) adds or
  updates a record: choose deliberately.
- Writes can fire SuccessFactors business rules and workflows: say which. Required fields and allowed picklist
  values come from the tenant configuration.

## Access, authentication, limits
- RBP filters rows and fields for the API user (permission groups, target populations, restricted entities,
  field-level permissions). List the permissions needed per entity and field in every design.
- OAuth 2.0 with a SAML bearer assertion or an X.509 client certificate: the OAuth client is registered in API
  Center; sign the assertion locally (SAP advises against the `/oauth/idp` helper in production, *verify*);
  decide between one API user and the user's own token; cache the token until shortly before expiry. Identity
  Authentication (IAS) handles login and Identity Provisioning (IPS) user provisioning. Basic authentication
  is being retired (*verify* the tenant's state).
- Throttling: 429 and 503 with `Retry-After`: back off with a bound. Page size caps and per-call timeouts
  exist: set a timeout of your own. API hosts differ per data centre and tenant: never hard-code them.
- Operations: API Center (OAuth clients, audit log, monitoring), Integration Center and Execution Manager, the
  OData API audit log to prove what was sent.

## Traps to check first
Inactive and terminated users; rehires; concurrent employment; a missing manager; custom fields that exist in
one tenant only; picklist ids instead of labels; null caused by RBP; effective dates in the future; string-built
`$filter` values with user input; a per-row call inside a loop; a full sync with no delta; a token written to a
log; partial upsert failure inside a 200; hard-coded hosts, template ids or company ids.

## Privacy
Copy only the fields the feature needs. Sensitive fields (date of birth, national id, compensation, gender) only
with a written need, masked in audit history and never sent to an LLM. Respect SuccessFactors data purge
(DRTM) for leavers: the product's copy follows SuccessFactors retention. Another person's data only for an active
direct report (manager scope).

## Sources
- SAP Business Accelerator Hub: api.sap.com (SuccessFactors packages, entity reference).
- SAP Help Portal: "SAP SuccessFactors HXM Suite OData API: Reference Guide" and "Developer Guide".
- The customer's tenant: `$metadata`, OData API Data Dictionary, Manage Business Configuration.
