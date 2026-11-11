# Flow files: where things live and who writes them

Read by every core agent that writes a flow document. Paths in a repo with the core installed.

## Places
| What | Path |
|---|---|
| Task or product folder (the lead gives it in the brief) | `<work>/<id>/`; `<work>` is `work_dir` in `.claude/project.json` (default `.claude/work`; product-factory: `work`) |
| Project config | `.claude/project.json` (commands, protected paths, decision triggers, rules) |
| Project facts and hard rules | `AGENTS.md`, `.claude/rules/*.md` (path rules), `.claude/review/checklist.md` (project checklist), `.claude/review/lessons.md` (one line per past mistake), `.claude/smoke.md` (neighbours to check per area) |
| Domain facts for a domain expert | `.claude/experts/<sf|ai|n8n|...>.md` (where this repo uses the domain) |
| Core reference | `${CLAUDE_PLUGIN_ROOT}/reference/` (`review/`, `qa/` (the UI and API test checklists), `standards/`, `base/`, `platform-btp.md`) |
| Core scripts | `python ${CLAUDE_PLUGIN_ROOT}/scripts/<script>.py` |
| Product root (product mode) | the `root` of the task (`live_status.py init <id> --mode product --root <path>`) |

## Modes
- **task**: a change to an existing product. Stages: spec, design, build, review, test, verify, release, wrap.
  Only the stages with somebody on them run; build and wrap always run (the main session).
- **product**: a new product from an idea or a PRD. Stages: intake (S0), base (S1), requirements (S2),
  product (S3 product review), prototype (SP), stories (S4), design (S5), build (S6), review (S7), audit (S8),
  release (S9). Gates G0 intake, G1 product, GP prototype, G2 stories, G3 design, G4 release.

## Files per mode
| Document | Task mode | Product mode | Written by |
|---|---|---|---|
| Context pack (impact map, key code, rules that apply, risk signals, gaps) | `context.md` | - | explorer (`context`); any agent adds a named gap under `## Gaps` |
| Triage card (goal, risk and its evidence, criteria, team, who is left out, planned files without a design) | `triage.md` | `00-intake.md` | main session |
| Readiness of a requirement document | - | `01-prd-review.md` | spec-analyst (`prd-review`) |
| Brief for the developer / owner (gaps Q1.., assumptions A1..) | `brief.md` | `02-gaps.md` | spec-analyst |
| Spec (criteria AC1.., team, decisions needed) | `spec.md` | `02-spec.md` | spec-analyst |
| Non-functional needs (`N1..` with numbers) | `spec.md` `## Non-functional` | `02-nfr.md` | spec-analyst |
| Hosting and deployment facts | `.claude/project.json` `deploy` | `00-infra.md` | devops-engineer |
| SuccessFactors fit / fields | `sf.md` | `02-sf-fit.md`, `05-sf-fields.md` | sf-expert |
| SuccessFactors job profiles and skills fit / fields | `sf-skills.md` | `02-sf-skills-fit.md`, `05-sf-skills-fields.md` | sf-skills-expert |
| n8n workflows (today's flow, node plan, handoff) | `n8n.md` | `05-n8n.md` | n8n-expert |
| Bug root cause | `spec.md` + `brief.md` | - | bug-investigator |
| Fix proof (per bug or fix-list item: reproduction, proven root cause, regression test, regression ring, fix plan; `handoff_check.py <id> --fix`) | `fix-proof.md` | - | bug-investigator (`/fix`) |
| Product review | `product-review.md` (large new feature only) | `03-product-review.md` | product-critic |
| Journeys and screen inventory | `## Journeys and screens` in `ui.md` | `03-journeys.md` | ux-designer (`journeys`) |
| Prototype | `prototype.html` | `P-options.md` + `.html`, `P-prototype.html` | main session (`prototype` skill) or ux-designer (`options`, `variants`) |
| Stories and backlog | `stories.md` (only when several stories) | `04-stories.md`, `04-backlog.csv` | story-sizer |
| Design (with `## Planned files`, read by the scope check) | `design.md` | `05-architecture.md`, `adr/` | solution-architect (`design`) |
| Safety net (`## Before build`, `## After build`, `## Intended changes`) | `safety.md` | - | qa-engineer (`characterize`, `test`) or main session |
| Characterization outputs (before and after) | `char/before/`, `char/after/` (tests stay in the session scratchpad) | - | `char_test.py` |
| Scope baseline (what was already uncommitted at Build start) | `scope-baseline.json` | - | `scope_check.py baseline` |
| API contract | in `design.md` + D3 card | `05-openapi.yaml` | solution-architect (`contract`) |
| Data model | D2 card | `05-data-model.md` + D2 card | data-architect |
| Access and privacy | D4 card | `05-security.md` + D4 card | security-architect (or solution-architect for a small D4) |
| Integrations | `integrations.md` | `05-integrations.md` | integration-engineer |
| Environments, pipeline, deploy | `ops.md` | `05-ops.md`, `09-deploy-plan.md` | devops-engineer |
| UI build spec | `ui.md` | `05-ui.md` | ux-designer (`ui-spec`) |
| Speed | `perf.md` (review pass `review-speed.md`) | `05-performance.md`, `07-performance.md`, load-test scripts in `perf/` | performance-engineer |
| AI behaviour, cost | `ai.md` | `05-ai.md` | ai-engineer |
| Decision cards D2-D8 | `decisions/D<n>-<name>.md` | same | see the decision table in the `sdlc` skill |
| Build log | `## Notes` in `status.md` | `06-build-log.md` | developers / main session |
| Review and design packs | `review-pack.md` + `review-state.json`, `design-pack.md` (`review_pack.py`) | same | main session |
| Code review | `review.md` (`review-<focus>.md` for extra passes) | `07-code-review.md` | code-reviewer |
| Test plan (risks, matrix criterion x type x role x data volume, who tests what, test data, exit criteria) | `test-plan.md` | `05-test-plan.md` | qa-lead (`plan`) |
| Tests and API checks | `test.md` | `07-test-report.md` (with `## Test plan` from S6) | qa-engineer |
| UI tests in the running app (the UI checklist per changed screen) | `qa-ui.md` | `07-qa-ui.md` | ui-qa-expert |
| Journeys, charters and session notes | `qa-e2e.md` | `07-qa-e2e.md` | e2e-qa-expert |
| QA sign-off (one verdict from every QA result) | `qa-signoff.md` | `07-qa-signoff.md` | qa-lead (`sign-off`) |
| The request as it came (Jira text, pasted text or the document's words), saved unchanged | `request.md` (`/review-spec`), `ticket.md` (`/test`) | - | main session |
| QA brief for a ticket with no task (ticket text, diff or commits, criteria to test, `## Changed files`) | `qa-brief.md` | - | qa-lead (`intake`, `/test`) |
| Fix list (defects left by QA, their owners and status; format `${CLAUDE_PLUGIN_ROOT}/reference/qa/fix-list.md`) | `fix-list.md` | `07-fix-list.md` | qa-lead (`sign-off`, `retest`); statuses `fixing`, `fixed` by the main session in `/fix` |
| Testability of each criterion | `testability.md` | - | qa-lead (`testability`, `/review-spec`) |
| QA data map (per need: volume, find / create / ask, how, cleanup, status; `Approved:` line) | `.claude/qa/data-map.md` (committed, shared) | same | test-data-engineer (`learn`, `/test data`); `Approved:` by the main session on the developer's yes |
| Seed and cleanup scripts, create log | `.claude/qa/seed/`, `.claude/qa/create-log.jsonl` | same | test-data-engineer |
| Test data for a ticket (record ids per matrix row, ask list) | `data.md` | same | test-data-engineer (`top-up`, `/test`) |
| Smoke pack (areas, `paths:`, items, journeys, `[P1]`) | `.claude/smoke.md` | same | qa-lead (`smoke`); `smoke: add` lines in `.claude/qa/smoke-inbox.md` from `/develop` and `/fix` |
| Requirements for people and the Definition of Ready (`${CLAUDE_PLUGIN_ROOT}/reference/requirements/definition-of-ready.md`) | `spec.md` (with `Requirements: READY (...)` once approved) | `02-spec.md` | spec-analyst (`requirements`, `/review-spec`; `dor`, `/develop`) |
| Which skill has the ticket and the hand-off line (`skill`, `next`) | `status.json`, `status.md` (`Skill:`, `Next:`) | same | `live_status.py init --skill`, `skill`, `next`, `testrun ticket` |
| Test run across tickets (one table: ticket, verdict, MUST open, SHOULD, blocked) | `<work>/test-runs/<date>-<n>.md` | same | `live_status.py testrun` |
| Verification | `verify.md` (the lead copies PASS/FAIL into `status.md`) | `05-design-review.md`, `07-system-review.md` | verifier |
| Audit | - | `08-audit.md` | audit-expert |
| Release | `release.md` | `09-release.md` | release-manager |
| Docs (only when asked) | - | `docs/` in the product root | release-manager (`docs`) |
| Questions for another expert or a person | `questions.md` | `questions.md` | anyone: `- [open] Q<n> from <agent> to <agent|developer|PO>: <question> - Recommended: <answer>` |
| Decisions made | `decisions.md` (written by `live_status.py ok`) | same | main session |

## Ids
Criteria `AC1..`, gaps `Q1..`, assumptions `A1..`, decisions `D1..D8`, stories `ST-<n>`. Hand-offs cite ids, and
the reviewer fails a change that goes against a confirmed answer or an approved card.

## Rules for every agent
- Read `context.md` first (task mode) and do not explore beyond it; fill only a named gap and add it under its
  `## Gaps` as `### <gap> (by <your name>)`. Then read `status.md`, `decisions.md` and the earlier documents.
- Write your output file first, then improve it, so a cut-off run still leaves it. Stay within the tool-call budget
  in your agent file (about 35 for the agents that decide, about 20 for the others and for `code-reviewer` and
  `solution-architect` in task mode, which work from a pack), at most 3 web lookups. Reply in 10 lines or fewer.
  A reviewer reads `review-pack.md` and a designer `design-pack.md` (both from `review_pack.py`) instead of the
  checklists, rules and lessons one by one.
- Never edit another agent's file: write the problem to `questions.md` addressed to that agent.
- Never commit, push, stash, reset, check out, start or restart servers. Say what needs a restart and why.
- Never copy secret values from config files into documents or chat: name the key only.
