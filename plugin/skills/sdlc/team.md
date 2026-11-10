# sdlc skill: 3. Who joins (by need, not by size)

Part of the `sdlc` skill (SKILL.md next to this file), read when its step comes. Read it before you write the `## Who will work on this` table of `triage.md`.

## 3. Who joins (by need, not by size)
The usual task is: `qa-lead` at Design (test plan), the area agents at Build (you brief and route them), `code-reviewer` at Review (one pass), the QA experts the plan names and `qa-lead` (sign-off) at Test, you at Verify, you at Wrap-up. An agent joins only when the task gives it the reason:

| The task has | Agent (stage) |
|---|---|
| A goal with real gaps, or many affected areas | `spec-analyst` (Spec, mode `task`) |
| A bug whose cause is not obvious | `bug-investigator` (Spec) |
| Something slow | `performance-engineer` (Spec, Design, Verify) |
| A large new feature: is it a good product? | `product-critic` (Spec), `story-sizer` when it splits into several stories |
| A new approach, or a change across layers | `solution-architect` (Design) |
| Table or entity changes (D2) | `data-architect` (Design) |
| New roles, permissions, personal data or outside access (D4) | `security-architect` (Design); a small permission change: `solution-architect` |
| A new or changed screen, however small (a demo or a single file too) | `ux-designer` (Design, mode `variants`: it builds the prototype by the `prototype` skill's rules; you show it and ask for the pick; Review `ux-designer (ui)` only for a large screen change). Never design a screen yourself |
| An outside system (sync, API client, SSO, files) | `integration-engineer` (Design) |
| Deploy, environment or pipeline changes | `devops-engineer` (Design) |
| SuccessFactors job profiles, roles, competencies or skills (Job Profile Builder, Talent Intelligence Hub, the skills model, Career Development or Opportunity Marketplace where they use skills) | `sf-skills-expert` (Design, modes `fit` then `field`; Review `sf-skills-expert (sf-skills)` only when most of the change is in this area); other SuccessFactors data stays with `sf-expert`, and a need that spans both gets both |
| A domain the repo lists in `experts` (SuccessFactors, AI, ...) | that domain expert (Design; Review `<expert> (<domain>)` only when most of the change is in that domain, reading the same review pack) |
| Any code change | its area agent at Build, small changes too: `backend-developer` (Java and server code), `frontend-developer` (UI: JS, TS, HTML, CSS, views), `integration-engineer` (a connection to an outside system), `n8n-expert` (workflow JSON), `devops-engineer` (build, deploy and pipeline files), `qa-engineer` (tests); `routing.areas` in project.json maps paths to agents. One agent per part; parts with no shared files run in parallel |
| Any code change | `code-reviewer` (Review), one pass |
| Risk medium or high | `qa-engineer` (Design, mode `characterize`: lock today's outputs before Build) |
| Any task that changes code | `qa-lead` (Design, mode `plan`: `test-plan.md`, the risk-based test matrix and who tests what; Test, mode `sign-off`: `qa-signoff.md`, one verdict from every QA result). No task closes without the sign-off |
| A UI change: a template, script, style, view or label a user sees | `ui-qa-expert` (Test, mode `ui`: every item of `${CLAUDE_PLUGIN_ROOT}/reference/qa/ui-checklist.md` in the running app) |
| A journey change: a step across screens, roles or features, a notification, a status flow | `e2e-qa-expert` (Test, mode `journeys`: end-to-end and exploratory, across roles, real data volumes) |
| A new or changed endpoint, or new tests to write | `qa-engineer` (Test: the tests, and the API checks of `${CLAUDE_PLUGIN_ROOT}/reference/qa/api-checklist.md` for each endpoint); existing tests only: `main session` |
| A pushed change to verify, or many criteria | `verifier` (Verify, mode `change`); otherwise `main session` |
| A release branch or go-live | `release-manager` (Release) |

- With no Spec agent, `triage.md` is the spec. With no Design agent and a small plan, write a short `design.md` yourself only when a decision card needs one.
- Owners when they overlap: `performance-engineer` keeps the time budget and baseline, `ai-engineer` decides model, prompt, cache and cost, a domain expert answers its domain's facts.
- Speed budget unless the spec says otherwise: first useful content 3 s, fully usable 6 s, a server call 2 s, an AI answer's first words 5 s (median of 3, measured in the browser by `ui-qa-expert`, or by you).
- When a Spec agent ran, it writes the team into `spec.md`; run `plan <id>` again. After the spec gate the team changes only with a reason: `plan <id> --why "<reason>"`.
- Agents move their own row on the page through the hooks. Without a SubagentStop hook (Cursor) run `expert <id> <stage> "<expert>" done`.
