# factory skill: S5 Design

Part of the `factory` skill (SKILL.md next to this file), read when its step comes. Read it when the stage starts.

## S5 Design
Every design expert reads `00-infra.md` and `02-nfr.md`; each `N<n>` row it owns gets its answer in its own
document (`05-performance.md`, `05-security.md`, `05-ops.md`, `05-ui.md`).
1. `solution-architect` (design) -> `05-architecture.md`, ADRs, the FE/BE task split.
2. Then in parallel: `solution-architect` (contract) -> `05-openapi.yaml`; `data-architect` -> `05-data-model.md`
   + D2 card; `security-architect` -> `05-security.md` + D4 card; `integration-engineer` (design) ->
   `05-integrations.md` (for SuccessFactors run `sf-expert` field mode first -> `05-sf-fields.md`, and `sf-skills-expert` field mode -> `05-sf-skills-fields.md` for job profiles and skills);
   `devops-engineer` -> `05-ops.md`; `ux-designer` (ui-spec, from the approved option) -> `05-ui.md`;
   `ai-engineer` -> `05-ai.md` when the product calls an AI model; `n8n-expert` -> `05-n8n.md` when it runs n8n
   workflows; `qa-lead` (plan) -> `05-test-plan.md` (risks, the test matrix of criterion x type x role x data
   volume, who tests what, test data, exit criteria).
3. `performance-engineer` -> `05-performance.md`, then `verifier` (system, design mode) ->
   `05-design-review.md`: every criterion has a story, every task an operation, every operation a table and a
   role, every screen a journey. Loop the owners on its findings.
4. Gate G3 on design: the design summary, every decision card and the review result, in one gate. Its approval
   opens code writes for the product root.
