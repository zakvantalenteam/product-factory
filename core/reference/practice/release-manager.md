# Practice pack: release-manager

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## ITIL Managing Professional and DORA metrics: change, release, incident, delivery
- Change types: standard (pre-approved, repeatable, low and known risk, written procedure), normal (assessed, then authorised), emergency (approval shortened; the back-out plan and the test evidence are not).
- Risk = impact x likelihood. Impact: tenants and users hit, personal data touched, whether it can be undone. Likelihood: size of the change, new or known component, test coverage, record of similar changes.
- Approval follows risk: peer review plus a green pipeline for low risk; the service owner or a wider authority for high risk. One board for every change adds delay and no safety.
- A change that failed in production loses standard status until its procedure is reviewed. A schema migration is standard only when it is scripted, rehearsed and has a down step.
- Change record fields: what, why, owner, window, risk, test evidence, back-out, who is told. A missing field is an ACTION.
- Window: avoid the customer's peak periods (month end, review and payroll cycles) and the last day of the working week; state the window in each customer's time zone.
- Deployment puts a build in an environment; release makes the change usable. When they are one moment, rollback means the whole build; say which case this is.
- Check the four dimensions before go: people (support and users told), information and technology (build, config, data), partners (HR system and platform vendors: their windows and notices), processes (runbook, rollback, incident path).
- Database and API changes go expand then contract: release N adds (nullable column, optional field), switches reads and writes; release N+1 removes. A rename or drop in one step has no old and new overlap and no safe rollback.
- Decide per step before release: roll back or roll forward. Roll back only where the data change is reversible; once data is written in the new shape, roll forward. Name the point of no return in the file.
- Small and frequent beats big and rare. Split a release that mixes a risky migration with unrelated features.
- Utility and warranty: a release can do the right thing (utility) and still be unfit for use (warranty: availability, performance, security, continuity). Check both against the budgets and the SLO.
- Service value: release notes say what a user or an admin can now do, per audience, not what changed. Name one user outcome and the measure to watch after release.
- Incident follow-up: restore first, find the cause after. A workaround is valid; it goes to support as a known error with its steps.
- Link every incident caused by a change to that change record. Without the link the change failure rate reads zero by omission.
- Open a problem record when the cause is unknown or the incident repeats: the incident closes on restore, the problem when the cause is removed.
- Post-incident review, blameless: timeline, cause, what detection missed, actions with an owner and a date. Go/no-go reads the open actions and problems in the changed area.
- Personal data in an incident: the GDPR clock starts when we become aware. As processor we tell the customer without undue delay; they tell the authority. Put who tells whom in the runbook.
- DORA metrics: deployment frequency, lead time for changes (commit to running in production), change failure rate (share of deployments needing rollback, hotfix or patch), time to restore after a failed deployment.
- Define deployment, failure and restore once and count them the same way each time. Report medians and spread for times, per service, never per person and never as a target (it will be gamed).
- Read the numbers as a constraint finder: long lead time points to queues and approvals, high failure rate to weak tests or big batches. DORA research shows no forced trade-off between speed and stability; small batches help both.
- Post-release review: planned against actual duration, triggers hit, incidents opened. Update the change record and the DORA data.
- SuccessFactors ships twice a year (1H and 2H) with a preview tenant before each. Run the integration smoke (the sync, the fields we read) on the preview first; put preview and production dates in the plan.

## SAP Cloud ALM (C_STC): operating the release on SAP BTP
- (SAP) Cloud ALM has an implementation side (requirements, features, tasks, test management, deployment) and an operations side (monitoring). When the customer runs it, link scope, test results and the go decision there; do not keep a second copy.
- (SAP) For the first-hour watch use Cloud ALM health, job and automation, and integration and exception monitoring for the HR sync; name who looks and which alert means rollback.
- (SAP) Moves between subaccounts follow the customer's transport route; list each transport in order with source and target. A manual change in production is a deviation: record it and who made it.
- (SAP) Each customer tenant has its own window and approver; the plan has one row per tenant in order, not one global date.

## Traps
- Deploy and release treated as one. Fix: say which step makes the change usable and what undoes each step.
- "Rollback" promised for a destructive migration. Fix: expand then contract; name the point of no return.
- Emergency used to skip approval for a convenient change. Fix: emergency means service is down or data or security is at risk now; testing and the back-out still apply.
- A board for every change. Fix: standard and peer-reviewed paths for low risk; the board only for high risk.
- Incident closed with no cause recorded and no link to the change. Fix: problem record and the link.
- DORA metrics mixed up with the EU DORA regulation for financial entities. Fix: ask which one the customer means.
- DORA numbers used as targets or rankings. Fix: trends per service to find the constraint.
- Release notes that list tickets or internal names. Fix: outcomes per audience.
- Go on test results alone while support has no notes or workarounds. Fix: support readiness is on the checklist.
- Production updated while the SuccessFactors preview was ignored. Fix: preview smoke first.

## Numbers
- 30 days = 43,200 minutes. Allowed downtime: 99.0% = 432 min; 99.5% = 216 min; 99.9% = 43.2 min; 99.95% = 21.6 min; 99.99% = 4.3 min.
- Error budget = 100% minus the SLO; when it is spent, hold risky releases until it recovers.
- GDPR personal-data breach: controller reports to the authority within 72 hours of becoming aware; processor tells the controller without undue delay.
- NIS2, if a customer is in scope: early warning 24 hours, incident notification 72 hours, final report within one month.
- DORA units: frequency per day or week; lead time and restore time as medians in hours or days; change failure rate in percent.
