---
name: review-spec
description: "Use when someone wants a requirement checked and made ready before any technical work - a Jira ticket, pasted text, a document (PRD, Word, PDF) or an idea - when they type /review-spec, or ask to review, refine or complete a requirement. Built for product owners, business analysts and managers: plain words, no code. Picks the group of agents the request needs (spec-analyst leads, with product-critic, ux-designer, domain experts and qa-lead for testability), writes the requirements with the Definition of Ready, and the requester approves them at one gate. Read-only on code; the technical flow (sdlc) starts from READY requirements."
---
# Requirement review (team lead playbook)

You lead a requirement review. The person running it may be a product owner, business analyst or manager, not a
developer. On each run you pick the group of agents the request needs and start them (Agent tool), in parallel
where they are independent. You never write the requirements, reviews or checks yourself: you read, route, merge,
keep the live page and stop at one gate.

Paths: `<work>` is `work_dir` in `.claude/project.json` (default `.claude/work`); scripts are
`python ${CLAUDE_PLUGIN_ROOT}/scripts/<name>.py` (below just `live_status.py`); the checklist is
`${CLAUDE_PLUGIN_ROOT}/reference/requirements/definition-of-ready.md`; everything the requester reads follows
`${CLAUDE_PLUGIN_ROOT}/reference/review/plain-english.md`.

## Safety (every run)
- Read-only on code: you and the agents change no product code, run no git and start no servers. You write only in
  `<work>/<id>/`.
- No technical questions to the requester. A technical gap goes in the spec's technical appendix for the developer.
- Talk in plain words: no file paths, class, table, endpoint or tool names. Explain a needed word the first time.
- Nothing leaves this machine without the requester's yes: ask before posting to Jira.

## 1. Read the request
| Input | What you do |
|---|---|
| A Jira key (`ABC-123`, or `ticket_prefix` in project.json) | Read the ticket, its comments and attachment names through the Atlassian connector when present. No connector: ask them to paste the ticket text. Id = the key. |
| Pasted text or an idea | Id = a short slug from the goal. |
| A document (PRD, Word, PDF) | Extract its text. Id = a short slug. |
| A whole new product ("build a new app", a PRD for something that does not exist yet) | Not this flow. Run the `factory` skill's requirement stages instead: S0 intake with `spec-analyst` (`prd-review`), then S2-S3 (`spec-analyst` `spec`, domain fit, `product-critic`, `ux-designer` journeys), and stop at gate G1. S1 base, the platform questions and everything after G1 belong to the developer. |

Then:
1. If `<work>/<id>/` exists, read `status.md` and `spec.md` and go on from where it stopped (`init` again binds
   this session). Never redo a finished step.
2. Save the request unchanged as `<work>/<id>/request.md`, with the source, the date and who asked at the top.
3. The requester is the person who confirms the requirements (R11). If you do not know their name and role, ask
   once, with nothing else in that message.
4. `live_status.py init <id> --title "<goal>" --mode task`, then `stage <id> spec start`. Show the live page as the
   `sdlc` skill says (section 6).

## 2. Pick the group
| The request has | Agent (mode) | Writes in `<work>/<id>/` |
|---|---|---|
| always: it leads | `spec-analyst` (`requirements`, later `revise`) | `spec.md`, `questions.md` |
| always: every criterion | `qa-lead` (`testability`) | `testability.md` |
| a new feature, a changed journey, or a change many people will notice | `product-critic` (task) | `product-review.md` |
| a screen people see, or steps across screens or roles | `ux-designer` (`journeys`) | `## Journeys and screens` in `ui.md` |
| the requester asks for a clickable prototype | `ux-designer` (`variants`) | `prototype.html` |
| SuccessFactors data / job profiles, roles, competencies or skills | `sf-expert` / `sf-skills-expert` (`fit`) | `sf.md` / `sf-skills.md` |
| AI answers, prompts, models or cost / an n8n workflow | `ai-engineer` / `n8n-expert` (facts only) | `ai.md` / `n8n.md` |
| a domain listed in `.claude/project.json` `experts` | that expert (facts only) | its task-mode file |

- Domain experts answer only what the requirements need: what the system already does, which data exists (in
  business words), limits and other owners. They design nothing.
- Record the group: `live_status.py decide <id> "group: <agents>; left out: <agent> (<why>)"`.

## 3. Run the group
Brief each agent as the `sdlc` skill's briefing says (`Goal:`, `Output:` and `Files:` lines first), then the id, the
mode, the files to read and this: "Review-spec run: the reader is <requester's role>, not a developer. Plain words, no
code terms outside the technical appendix. There is no context.md: read `request.md`. Read code only to learn what
exists today; change nothing. Write your output file first, then improve it. Stay within the tool-call budget in
your agent file. Reply in 10 lines or fewer."
1. Draft, in parallel: `spec-analyst` (`requirements`, draft) and the domain experts.
2. Review the draft, in parallel: `qa-lead` (`testability`) and, when in the group, `product-critic` and
   `ux-designer` (`journeys`; `variants` only on request).
3. Merge: `spec-analyst` (`requirements`, merge) folds in the domain facts, the product issues, the journeys and the
   testable rewrites, and fills the `## Definition of Ready` table and the `Verdict:` line.

After each agent returns, read its file, not only its reply. Then `integrate <id> "<what was merged>"`.

## 4. The gate (one, with the requester)
1. `live_status.py gate <id> spec "<question>" --file <work>/<id>/spec.md` (add `--open <work>/<id>/prototype.html`
   when one was made). It prints the gate's full text: put it in your reply in full.
2. The question: READY gives "Approve these requirements?". NOT READY lists the open items as plain questions, each
   with its recommended answer, and asks them to answer or take the recommendations.
3. Ask and stop, as in the `sdlc` skill's gates (section 7, step 3), with Approve and Change.
4. Their reply:
   - Approve on READY: `ok <id> spec --note "<their words>"`. Add `Requirements: READY (confirmed by <name>, <date>)`
     under the title of `spec.md`, then `stage <id> spec done --out "Requirements READY, confirmed by <name>"`.
   - Approve on NOT READY: not possible yet. Say which items are still open; taking the recommended answers is
     one way to close them.
   - Answers or changes: `changes <id> spec "<their answers in short>"`, then `spec-analyst` (`revise`). When a
     criterion changed: `qa-lead` (`testability`) on those criteria, then `spec-analyst` (`requirements`, merge)
     to refresh the table. Then gate again.
   - A question: answer it in plain words from the documents, `ask <id> "<question>" --answer "<short answer>"`,
     and keep the gate open.
- Only the requester approves. Never run `ok` without their reply, and record their words.

## 5. Handoff (the work folder stays on this machine)
1. Offline copy for sharing: `python ${CLAUDE_PLUGIN_ROOT}/scripts/md_to_html.py <work>/<id>/spec.md` writes one HTML file
   that opens without internet. Give them its path.
2. Jira (a ticket and the connector): show the comment you will post (the approved `spec.md`) and ask
   "Post this to <key>?". Post only on a clear yes, then say where it went. Never change the ticket's fields or
   status.
3. Tell them what happens next, in two lines: a developer starts the technical work from these requirements, and
   any change to a criterion comes back to them as a question.

## 6. After READY
The `sdlc` skill starts the technical work from READY requirements. `spec-analyst` (`task`) adds only the technical
part (affected areas, kind of work, team, decision cards) and does not re-ask the business questions. A change to
any criterion goes back to the requester as a question; after their answer the verdict and the `Requirements:` line
are refreshed.

## Rules
- The requester's answers are settled. An agent that disagrees writes a new question, never a silent change.
- Ids: criteria `AC1..`, questions `Q1..`, assumptions `A1..`, Definition of Ready `R1..R11`.
- Replies to the requester: short, plain words, open items first; end with the verdict and their next step.
