# Intake - DeskBook

Source: `00-prd.md` (v0.3 draft, Facilities & HR), received 2026-10-28.

## Reply the lead gave
> Hold on - I won't start building from this directly. Each expert reviews it first: building on gaps
> costs far more than asking now.
>
> What I understood: an app where employees book a desk (full or half day, up to 2 weeks ahead) and check in
> on arrival; unused bookings are released at 10:00. Managers see and book for their team. Facilities sets up
> offices, floors and desks and gets usage reports. Users come from SuccessFactors.
>
> Plan: S0 PRD review -> S1 fresh base (in parallel) -> S2 spec + gap sheet -> S3 product review + journeys
> (you and the product owner answer gaps, G1) -> S4 stories and sizing (you agree the MVP, G2) -> S5 design:
> architecture, API contract, database, security, screen variants (you approve, G3) -> S6-S8 build, review,
> test, audit (G4).
>
> First questions:
> 1. Is the 10:00 release time the same for all offices, in each office's own timezone? Recommended: per office setting, default 10:00 local.
> 2. Is the floor map needed in the first release? Recommended: no - a desk list with filters first; map later.
> 3. Which SuccessFactors data is the source for "my team"? Recommended: direct reports from the employee's manager field, synced nightly.
> 4. Recurring bookings in release 1? Recommended: later - they fight with the 2-week limit and fairness.
> 5. Who may see where a colleague sits? Recommended: own team only (manager and peers), not the whole company.

## Plan
Size: L (new product, all stages). Teams: Product, Design, Architecture, then Engineering, Quality, Audit.

## G0 (demo)
In this demo the lead plays the user and accepts all recommended answers. In a real run the lead waits here.
