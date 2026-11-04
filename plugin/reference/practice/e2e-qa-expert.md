# Practice pack: e2e-qa-expert

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## CTAL-TA: exploratory testing and journeys
- Charter format: `Explore <area> with <resources> to discover <information>`; resources are the role, the data and the tools; information is a risk or a question, not "check that it works".
- Time box 60-120 min, or about 8 calls in this agent; one charter per box; stop when the box ends and write what is left.
- Session notes PROOF: Past (what you did), Results (what you found), Obstacles (what blocked or slowed you), Outlook (what to test next), Feelings (where it felt wrong or confusing, even with no defect).
- Tours: money tour (the path that earns or loses most), feature tour (every control once), landmark tour (the key steps in different order), back-alley tour (the rarely used screens), all-nighter (leave a session open, return later), saboteur (break a step on purpose).
- Heuristics: CRUD (create, read, update, delete, then read again everywhere), goldilocks data (too little, just right, too much: 0, 1, a page, 3+ pages, the maximum), interruptions (back, reload, second tab, session timeout mid-step), follow the data (track one record from entry to every place that shows it), boundaries and odd input, role swap.
- Journey design: write steps first (role, screen, action, expected), including the main flow, each alternative flow and each exception flow (outside system down, permission removed mid-journey).
- Journey across roles: what the admin sets, the manager sees, the learner gets, and back; each hand-off is a step with an expected result for the next role.
- Cross-feature effect checklist, after each step: counts and badges; list totals; reports and exports; search results; notifications and emails in the dev outbox; history and audit; caches after a reload; the areas of `.claude/smoke.md`.
- Data volume strategy: run the journey on the volume the plan names; a journey on an empty tenant says so and is not PASS for scale; check that totals, paging and search still hold at 3+ pages.
- Concurrency with two tabs: two users edit the same record (second save gets a conflict or a clear result, not a silent overwrite); one user deletes while another has it open; the same action sent twice from two tabs creates one result.
- A finding is reported only when reproducible: repeat once from a clean start; if it comes back only sometimes, say how often and under what.
- Reproducible defect report: title with the effect; environment (URL, role, data volume); numbered steps from a known start; expected (with the criterion id); actual; evidence (text, console or network line, screenshot); frequency; MUST or SHOULD; owner agent.
- Isolate before reporting: the shortest steps, the one role or data piece that triggers it, and what still works.
- Cross-role and cross-tenant leaks, lost data, and a step that silently does nothing are MUST.

## CT-AcT: acceptance testing
- Types: user acceptance (business users confirm it fits their work), operational acceptance (backup, restore, jobs, monitoring, deploy and rollback; owned by the developer and devops), contractual or regulatory acceptance (stated terms, legal or audit rules).
- Who accepts what: the product owner or business user accepts the journeys and criteria; the developer accepts the residual risk; operations accepts run and restore; you report evidence, never the acceptance itself.
- Acceptance criteria as Given/When/Then with real values: `Given a manager with 25 open requests, When she opens the list, Then she sees "1-20 of 25" and a next control`; one behaviour per criterion, measurable, no "fast" or "easy".
- Business-process-based tests: follow the process the business runs (request, approve, notify, report), not the screen list; each criterion is judged as the business user would accept it, not as the code reads.
- Review each criterion before running: if it cannot fail, or two readings give different results, raise a question for the owner instead of guessing.
- Entry for acceptance: build stable, dev data in place, criteria fixed; exit: every criterion with PASS evidence or an owner-accepted deviation.
- Use real roles, real wording and real data shapes; a test user with admin rights hides permission defects.
- Each screen on a journey gets UQ0, UQ1, UQ15, UQ16, UQ18 and a list gets UQ3-UQ6; refer by id, do not copy the text.
- (SAP) SuccessFactors-linked journeys: effective dating (a record with a future start date, a change with a past effective date, two records on one date); permission roles (the role in SuccessFactors that lets the user see or write the data, and one without it); check what the journey reads or writes in the dev or test instance the developer names, never production.
- (SAP) After a write to SuccessFactors, read it back there and in the app; a sync delay is noted with its time.

## Traps
- Testing only the happy path across roles; fix: one exception flow and one denied role per journey.
- A journey seen working for an admin only; fix: run each step as the role that does it.
- Notes with no outlook, so the next session repeats the first; fix: PROOF notes with Outlook filled.
- Reporting "sometimes broken"; fix: repeat, find the trigger, state the rate.
- Checking only where the change shows; fix: the cross-feature list, counts and notifications next door.

## Numbers
- Charter: 60-120 min or about 8 calls; data volumes 0, 1, page, page + 1, 3+ pages, plan maximum.
- Journey: main flow, every alternative flow, every exception flow, each role once.
- Two tabs for concurrency; repeat an intermittent defect at least 3 times before reporting.
