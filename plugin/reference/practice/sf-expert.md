# Practice pack: sf-expert

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## EC Core and Position Management: reading the HR master right
- Foundation objects (legal entity, business unit, division, department, location, job classification, pay grade, cost center) are effective-dated; read their names as of the job record's date.
- Store the externalCode of foundation objects and picklist values; labels are localised and change.
- Hire date is EmpEmployment.startDate (originalStartDate where seniority counts), not EmpJob.startDate, which only starts one job slice.
- EmpJob rows are keyed by userId, startDate and seqNumber: several changes on one day are separate rows, the highest seqNumber is the result of that day.
- EmpJob.emplStatus holds a picklist option id; resolve it to the option's externalCode before comparing.
- Tell hire, transfer, promotion, leave and termination apart by event and event reason on the job row, not by diffing fields.
- Per-person features (learning history, skills) aggregate by personIdExternal; per-job features (manager, org unit) use the userId of that employment.
- Rehire with new employment gives a new userId under the same person; link by personIdExternal, never by email.
- Matrix, HR and second managers are job relationships (EmpJobRelationships), not EmpJob.managerId; the spec names which manager.
- Positions are effective-dated MDF objects (code plus effectiveStartDate); the incumbent links through EmpJob.position, a vacancy has no job row.
- When positions are used, read the org from the position hierarchy (parent position): it includes vacancies, a manager chain does not.
- Position-to-job sync runs only through the tenant's sync rules; read both records, never assume they match.
- API writes skip onInit and onChange rules; onSave rules run on API writes only where the tenant enables rules for imports. Send every field the UI would default.
- An OData upsert starts an approval workflow only when the entity supports it, an onSave rule sets the workflow and rules are enabled for API writes (MDF objects: `workflowConfirmed=true`); otherwise it writes past approval. Confirm per entity in the tenant.
- purgeType=full replaces the person's whole history of that entity with the payload; incremental is the default and the normal choice.
- Data retention management purges people in SuccessFactors; our copy follows with delete or anonymise.

## SuccessFactors Learning: items, assignments, completions
- An item is keyed by item type, item id and revision date; store all three with every completion.
- A completion counts only when its completion status gives credit; failed and incomplete statuses are history rows too.
- The learning plan holds assigned work not yet done; the learning history holds recorded results. A completed item leaves the plan.
- Curricula carry required dates and retraining periods: complete today can be overdue next month; show the status, not only a date.
- Assignment profiles assign items, curricula and programs by user attributes; use them before building our own assignment rules.
- The student id is the platform userId, synced by the user connector; a user missing in Learning usually means the connector has not run or failed.
- Ask shows only items the learner can reach: in their catalogues, active, in their language; an item outside their catalogues cannot be self-assigned.
- Scheduled offerings have seats, waitlists and registration status; an item can be open while every class is full.
- Learning web services use their own OAuth client and token from the Learning tenant, not the platform OData token.
- External learning a learner records is history too; keep its source so reports can split it.

## SHRM-SCP: HR practice behind skills, roles and learning data
- One job architecture (family, role, level); skills attach to roles, each with a proficiency scale that describes observable behaviour per level.
- Skills may be mastered in Job Profile Builder or in Talent Intelligence Hub; ask which one the tenant uses before we hold a copy.
- Inferred skills are suggestions until the employee or manager confirms them; show where each one came from.
- AI that ranks people for hiring, promotion, termination or task allocation, or evaluates their performance, is high-risk under the EU AI Act (Annex III) even when it only advises, and profiling people is never exempt (Art. 6(3)): do not rank or score individuals unless the high-risk duties (risk management, logs, human oversight, deployer instructions) are planned with security-architect.
- Employee consent is rarely a valid GDPR basis (power imbalance); expect contract or legitimate interest and confirm with the customer's DPO.
- Managers seeing individual learning or skills data can count as monitoring: in Germany it needs works council agreement before go-live.
- Team views show aggregates only above a minimum group size agreed with the customer.
- Walk every lifecycle event (hire, transfer, promotion, leave, termination, rehire) for each feature: what the person sees after it.
- HR process owners decide what a field means ("active", "manager", "completed"); IT does not.

## Traps
- No asOfDate or date range: you get today's slice only, so a future hire or transfer is invisible until that day.
- Delta on an effective-dated entity without a wide date range (fromDate far in the past, toDate 9999-12-31) misses future-dated changes.
- A delta row can be a corrected past slice: apply it by its startDate, never as "the current record".
- The User entity returns active users only unless you filter on status; leavers vanish from a sync that relies on it.
- User.department and similar fields are plain text; join EmpJob and the foundation object for codes.
- Paging with $skip over a changing set loses or repeats rows; follow `__next`, with `paging=snapshot` where the entity supports it.
- OData v2 dates come as `/Date(ms)/`; effective dates are calendar dates, never shift them by time zone.
- Counting learning history rows as completions, or ignoring the item revision, inflates compliance.

## Numbers
- A current slice ends 9999-12-31.
- Delta overlap (default): re-read 5 minutes before the stored checkpoint and dedupe by key.
- Learning item key: 3 fields (type, id, revision date); EmpJob key: 3 fields (userId, startDate, seqNumber).
