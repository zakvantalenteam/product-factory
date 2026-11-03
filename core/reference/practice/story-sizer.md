# Practice pack: story-sizer

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## PSM II and PSPO II: slicing, Done and the Sprint
- Your points are a first proposal. The Developers who do the work own the size; say so in the file and expect them to re-size after sprint 1.
- Size all the work the Definition of Done asks for (tests, review, docs, deploy readiness), not only coding. Work left out of the size comes back as a "hardening sprint"; there is none, Done means releasable.
- A story is Done only when the Increment meets the Definition of Done. Unfinished work returns to the backlog whole, the rest is re-sized, and it earns no partial points.
- The Sprint Goal is the commitment; the chosen stories are a forecast. Give each planned sprint one goal sentence and keep only stories that serve it.
- Scope inside a sprint may be clarified with the product owner as the team learns; the Sprint Goal does not change. A sprint with five goals has none.
- Slice by workflow step, business rule, data variation, operation (create, change, delete) or interface variation, then happy path before edges. Each slice has a user-visible result you can demo.
- The first slice of a new capability carries the new plumbing and is large; later variations are small. Size the first honestly; do not average.
- Defer performance or polish to a later story only when no criterion or NFR needs it in this one.
- After a split, size each piece against the anchors on its own. Pieces that add up to the old number (13 = 8 + 5) were not re-sized.
- A story whose criteria need more than one separate "When" flow is probably two stories.
- Uncertainty gets a spike: a time box set before it starts (hours or days), one question to answer, a re-size at the end. A spike delivers an answer, not value; list it apart and name the story it unblocks.
- An "Enabler" names the first story it unblocks and holds only what that story needs. A "setup sprint" with nothing a user can see is a layer split in disguise.
- Ready is a working agreement, not a Scrum rule. A story with a gap stays in the backlog with Low confidence and an open question; do not hide it and do not block on it.
- Refine the stories for the next sprints; keep Later items coarse. Sizing far-off work finely is waste that the next learning will undo.
- Remove dependencies by re-slicing before you list them. A dependency on another owner (an HR system, another team) is Low confidence until that owner confirms a date.
- Order by value, risk and dependency. At equal value, higher cost of delay per size first. Put the riskiest integration (for example the HR system sync) into the first sprints as a thin end-to-end slice.
- The MVP is the thinnest end-to-end path that tests the main value with a real user, including the integration and the data it needs. If it works only on seeded data it is a demo.
- Release plan: give a range, not a point. Sprints = total points / velocity, rounded up, for a low, expected and high velocity. Subtract planned leave and public holidays per country from capacity first.
- Velocity is the points of Done stories per sprint, for one team. It is a planning input: never a target, never compared across teams, never converted to hours.

## SAP Activate (C_ACT): rollouts of our products at a customer
- (SAP) Phases: Discover, Prepare, Explore, Realize, Deploy, Run. Our sprints sit inside Realize; the plan says what Prepare and Explore must settle before sprint 1.
- (SAP) Each phase ends at a quality gate with exit criteria. A plan that names the Realize and Deploy gates and who signs them is complete; "go live when ready" is not.
- (SAP) Fit-to-standard in Explore: a need that the standard meets (SuccessFactors configuration, a BTP service) becomes a small Config story; a custom-build story names the standard option it rejected and why.
- (SAP) A gap found in Explore is a backlog item with a story and a size, not a note. A gap found in Realize goes through the product owner's order, not into the running sprint.
- (SAP) Add and size the non-code stories a rollout needs: data load or migration and cutover, end-user and admin training, change communication, user acceptance test (UAT). Left for "after", they move go-live.
- (SAP) Name the sign-off owner per gate (scope, UAT, go-live). No named owner means Low confidence on every story that waits for it.
- (SAP) Plan test cycles inside the Realize sprints (unit, integration against a test tenant, UAT), not after the last sprint.
- (SAP) Software alone does not deliver adoption: a change in who approves learning or how managers use the data is a stakeholder task with an owner.

## Traps
- Points turned into hours or days. Fix: points are relative to the anchors; the tasks carry the hours (a day or less each).
- A velocity target per sprint. Fix: velocity is measured; a target makes the team inflate points.
- Layer stories ("API 3, screen 3"). Fix: one vertical slice that works end to end.
- Uncertainty pushed into a bigger number. Fix: a time-boxed spike, then re-size.
- Testing and review left for a later sprint. Fix: they are in the size and in Done.
- A 40-point "story". Fix: it is an epic; split it before you size.
- Half-done work counted. Fix: no partial points; re-size the rest.
- The plan read as a commitment ("done in 6 sprints"). Fix: a forecast range, recalibrated after each sprint.
- Criteria not placed, or placed twice. Fix: each AC in exactly one story; "Not placed" stays empty.
- Technical stories with no user value filling the MVP. Fix: attach the work to the slice it serves, or label it Enabler with the story it unblocks.
- Sizing from the story title. Fix: size from the criteria and the data they touch.
- (SAP) Fit-to-standard skipped. Fix: custom stories only after the standard option is checked and rejected.

## Numbers
- A Sprint is one month at most; shorter is allowed. For a one-month Sprint the limits are Planning 8 hours, Review 4 hours, Retrospective 3 hours; the Daily Scrum is 15 minutes.
- A Scrum Team is typically 10 people or fewer.
- Sprints needed = total points / velocity, rounded up; show it for low and high velocity.
- (SAP) SAP Activate has 6 phases, each closed by a quality gate.
