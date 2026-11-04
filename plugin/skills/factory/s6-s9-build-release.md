# factory skill: S6 Build, S7 Review, S8 Audit, S9 Release

Part of the `factory` skill (SKILL.md next to this file), read when its step comes. Read it when the stage starts.

## S6 Build, S7 Review, S8 Audit, S9 Release
- Build story by story in backlog order: `backend-developer` and `frontend-developer` in parallel once the
  contract is fixed, `integration-engineer` (build) for stories with an outside system, `devops-engineer` for
  environment changes, `qa-engineer` writes the tests from the acceptance criteria. Log each story in
  `06-build-log.md`. Builders work in slices; run them again where they stopped.
- After each story or batch: `review_pack.py <slug> --root <product root> --files <the story's files>`, then one
  `code-reviewer` pass from that pack -> `07-code-review.md` (MUSTs go back to the developer
  agent with the exact findings; re-run only what failed). `qa-engineer` runs the tests and the API checks
  (`${CLAUDE_PLUGIN_ROOT}/reference/qa/api-checklist.md`) -> `07-test-report.md`; `ui-qa-expert` tests every screen of the
  story in the running app against `${CLAUDE_PLUGIN_ROOT}/reference/qa/ui-checklist.md` -> `07-qa-ui.md`; at the end of the
  build `e2e-qa-expert` runs the journeys across roles -> `07-qa-e2e.md`, and `qa-lead` (sign-off) merges every QA
  result -> `07-qa-signoff.md`. A checklist MUST or NOT SIGNED OFF goes back to the developer agent; Review is not
  done until the sign-off says SIGNED OFF. The app is started by the developer; with it down the QA rows are BLOCKED.
  At the end `performance-engineer` -> `07-performance.md`, `verifier` (system, build mode) ->
  `07-system-review.md`, `sf-expert` (review) when SF code changed, `sf-skills-expert` (review) when job profile or skills code changed.
- `audit-expert` -> `08-audit.md` against `${CLAUDE_PLUGIN_ROOT}/reference/standards/definition-of-done.md`; every MUST
  must pass; the rest goes to a LATER backlog. Then `live_status.py code <slug> closed`.
- S9: `devops-engineer` -> `09-deploy-plan.md`, `release-manager` (release) -> `09-release.md`; docs only when the
  user asks (`release-manager` docs). Gate G4 go-live is the user's call.
