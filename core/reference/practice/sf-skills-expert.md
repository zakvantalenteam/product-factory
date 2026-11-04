# Practice pack: sf-skills-expert

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## SHRM-SCP: job architecture and skills practice
- One job architecture: family, then role, then job profile (level). Skills and competencies attach to roles; the proficiency scale says what each level looks like at work.
- Ask who is the master before we hold a copy: Job Profile Builder (JPB) owns families, roles, profiles, job descriptions and their linked competencies and skills.
- Talent Intelligence Hub (TIH) owns the skills ontology, employee skills and the attributes library where the tenant runs it; where both are live, ask which one wins per object.
- Inferred skills are suggestions until the employee or manager confirms them; keep where each skill came from (self, manager, inferred, imported).
- Ranking, scoring or matching people to roles or opportunities can be high-risk under the EU AI Act (Annex III): show a gap per skill, not a person score, unless security-architect has planned the duties.
- A role skill gap is a development input, never a performance rating; the HR owner decides what "required" and "expected level" mean.
- Walk each lifecycle event (hire, transfer, promotion, termination, rehire): which role skills and growth entries the person sees afterwards.

## Succession Management: roles, competencies and job architecture
- Succession and talent pools read the job architecture; a role change in JPB changes who is matched, so ask when a role is retired or merged.
- Competencies and skills linked to a role are the master for gap views; keep only a cache with its source and date, not a second master.
- Job code mapping links a job profile to the Employee Central job classification (`FOJobCode`); read the mapping object (check $metadata), never guess by title.
- Content library sections (competencies, skills, responsibilities, qualifications) come from the job description template (check $metadata); read the template before assuming a section exists.
- Localised content (names, descriptions) exists per locale; read the user's locale and fall back to the default locale on purpose, never to the first row.
- JPB import order: families, roles, job profiles, job code mapping, competency and skill links, localised text (confirm against the tenant's current import guide). Each step needs the key of the one before it.
- Import by externalCode, never by label; a changed label then updates instead of duplicating.
- Imports and upserts return per-row status: read every row, a 200 can hold failures (see the shared reference).

## Career Development Planning and Mentoring: how role skills are consumed
- Career Development shows a person the skills of a target role beside their own: role skills and levels come from JPB, the person's ratings from the profile (or TIH where live).
- Opportunity Marketplace matches on skills, interests and role skills; no skills on the role or the person means no matches, which is a data problem, not a bug.
- Growth portfolio entries (development goals, mentoring, learning, gigs) are the person's own plan; read within the person's permission scope and never rewrite them.
- Development goals hang on a plan template (`DevGoalPlanTemplate`, `DevGoal_<plan id>`): read the template id from the tenant, never hard-code it.
- Mentoring and opportunity entities differ by release: name them only after `$metadata` or api.sap.com confirms them (check $metadata).
- Show the source of each suggested role or opportunity so the person can see why.

## Entities, ids, effective dating, permissions, delta
- Ids: store the externalCode of family, role and profile; internal GUIDs and numeric ids differ per tenant (test versus production), so they are never a key across systems.
- Person ids: skills and growth data belong to the person (`personIdExternal`); job-based data uses the job's `userId` (see the shared reference).
- Effective dating: check in `$metadata` whether the JPB profile and its content are versioned by an effective date; `FOJobCode` is effective-dated. Read `asOfDate` for today, a range for history.
- Permissions: the API user needs read on the JPB objects and the skill and competency libraries through its RBP role; a missing permission gives empty rows or null fields, not an error. List the permissions with the tenant owner, never guess one.
- Paging: `$select` the fields used, follow `__next`, never `$skip` over a set that is being edited.
- Delta: `lastModifiedDateTime` with a stored checkpoint and 5 minutes overlap; deletions and inactive profiles may not show as changes, so run a full key compare on a schedule.
- (SAP) Keep the API client and destination per tenant on BTP; the id rules above do not change.

## Traps
- A deleted or inactive family, role or profile still sits in old links; filter on status, keep the rows in history, keep them out of pickers.
- Locale fallback: a profile with no text in the user's locale can return empty text; fall back on purpose.
- Duplicate skill names exist (same label, different id or library); match on id or externalCode, never on the name.
- JPB skills and TIH skills can describe the same real skill; keep a mapping and say which side wins.
- Large libraries (tens of thousands of skills): never load them into a picker; search with a limit and server paging.
- A new role with no skills gives an empty gap view: show "no skills defined", not a 100 percent match.
- Imports out of order fail on missing parents; a re-run must not create duplicates.
- A skill rating without a date or source cannot be audited; keep both.

## Numbers
- Server paging: up to 1,000 rows per call; follow `__next`.
- Delta overlap (default): re-read 5 minutes before the stored checkpoint and dedupe by key.
- JPB import order: 6 steps (family, role, profile, job code mapping, skill and competency links, localised text).
- A current effective-dated slice ends 9999-12-31.
