# factory skill: S0 Intake

Part of the `factory` skill (SKILL.md next to this file), read when its step comes. Read it when the stage starts.

## S0 Intake
1. `live_status.py init <slug> --mode product --title "<name>" --size S|M|L --root <products_root>/<slug>`.
   Save the document unchanged as `<work>/<slug>/00-prd.md` (a .docx/.pdf: extract the text). Write
   `00-intake.md`: source, date, what you understood, the plan, the first questions.
   Size: S = one story on an existing product (use the `sdlc` task flow instead), M = a module (skip base),
   L = a new product (all stages).
2. Run in parallel `spec-analyst` (mode `prd-review`) -> `01-prd-review.md` and `devops-engineer` (mode `infra`)
   -> `00-infra.md` (where and how it will run: platform, environments, sign-in, CI/CD, backup, cost). Show the
   verdict, the blockers and the top questions of both merged with yours (at most 10; the platform question always
   among them while it is open). Gate G0 on intake with `00-intake.md`, `01-prd-review.md` and `00-infra.md`.
