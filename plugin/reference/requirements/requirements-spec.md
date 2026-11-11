# Requirements spec (the writer's layout, `review-spec`)

spec-analyst (mode `requirements`) writes `<work>/<id>/spec.md` in this layout and keeps it through the merge and
revise steps. The reader is the requester (product owner, analyst or manager): plain words
(`${CLAUDE_PLUGIN_ROOT}/reference/review/plain-english.md`), no code terms above `## Technical appendix` (no paths, class,
table, field, endpoint or tool names), and never a technical question to the requester.

## Draft (first run)
Write the sections in this order:
1. `# Spec - <id>: <title>`, then `Source: <Jira key, document name or pasted text>` and `Requester: <name, role>`
   (R11).
2. `## Goal and who it is for` (R1): the problem, who has it, what changes for them, then a 2-4 line example with a
   made-up person.
3. `## In scope` and `## Out of scope` (R2): anything a reader could assume is in, but is not, is listed as out.
4. `## Roles` (R4): `| Role | May | May not |`.
5. `## Acceptance criteria` (R3): `- AC1 Given ... When ... Then ...`, an indented `Example:` with real-looking
   made-up data. Cover the main path, each role, no data, wrong input, limits and duplicates, create, change,
   remove and cancel (or say which are out of scope), each state change and who makes it, two people at once, and
   another system down (R14). One resting on a gap names it `(Q2)`. Write the result in the present tense ("Then
   she sees 20 rows"), never "should".
6. `## Empty and error states` (R5): no data, too much data, a failure, no permission, while waiting; the exact
   words where they matter.
7. `## Data` (R7): what is shown or stored, from which system and which field in business words, who may see
   personal data.
8. `## Non-functional` (R6): plain words with numbers: records and users, how long it may take, languages, devices
   and browsers. A number you propose is an assumption `A<n>`.
9. `## Other owners and dependencies` (R8), named.
10. `## Today vs asked` (only when the folder has `context.md`, i.e. code is there; below).
11. `## Journeys` (only when `ux-designer` ran): per role the main steps, one short list.
12. `## Open questions` (R9): `- **Q1** <impact word> <question>`, indented `Recommended:` and `If not decided:`;
    most important first, at most 12, the rest under "Smaller points"; each also into `questions.md` as
    `- [open] Q<n> from spec-analyst to PO: <question> - Recommended: <answer>`.
13. `## Assumptions` (R15): `- **A1** ...`, true unless the requester says otherwise. Every number or rule you added
    that the request did not give is one.
14. `## Confirmed answers` (empty until revise).
15. `## Words used here` (R12): each domain term once, in one line, used the same way everywhere.
16. `## Technical appendix (for the developer)`: what exists today as `path:line` (`### Today vs asked: where in the
    code`, one line per AC); technical gaps, one line each with a recommended answer, never asked of the requester.
17. `## Definition of Ready`: the R1-R16 table and the `Verdict:` line exactly as in `definition-of-ready.md`. In the
    draft R10 and R12-R16 are `fail`, "not reviewed yet" (qa-lead's requirements review fills them).

No vague word survives in the requirement part (`vague-words.md`): replace it with a number or an example; where only
the requester can give it, write your proposal as an assumption `A<n>` or ask it as `Q<n>`, quoting the word.

## Today vs asked (code is there)
`explorer` wrote `context.md` first. One row per criterion (or per in-scope item when a criterion has nothing in
today's product):

```
## Today vs asked
| AC | Today | Asked | Conflict | Also touches |
|---|---|---|---|---|
| AC1 | The course list shows 10 courses and has no filter | A filter by skill above the list | none | the search page uses the same list |
| AC2 | A manager sees every team member's courses | Only courses assigned by that manager | Q3 | the team report counts |
```

- Plain words only: what a user sees or the product does today, never a path or a class (those go in the appendix
  under `### Today vs asked: where in the code`).
- `Conflict`: `none`, or the `Q<n>` that asks the requester which behaviour wins. Every conflict is a question; a
  conflict the change is meant to make (it replaces today's behaviour on purpose) says so in the Asked cell and is
  still confirmed once as a question.
- `Also touches`: the other screens, reports, exports, mails or data the change reaches, from the context pack's
  impact map, in business words; `none found` when there are none.

## Merge (after the review step)
The lead names the group's files: the domain files, `product-review.md`, `ui.md`, `requirements-review.md`.
- Domain facts go into Data and Other owners in business words, detail into the appendix.
- Each BLOCKER or HIGH product issue becomes a scope change you state or an open question with its fix as
  `Recommended:`.
- Journeys go into `## Journeys`.
- From `requirements-review.md`: a rewrite that keeps the meaning replaces its sentence word for word; every other
  finding becomes an open question (its question and Recommended answer) or an assumption. Copy its `## Results`
  into R10 and R12-R16; an item with an open finding stays `fail` with the `Q` ids in its note.
- Fill the rest of the table yourself (R1-R9, R11). `Verdict: READY` only when every item passes (or is `n/a` with
  its reason).
- Never write the `Requirements:` line; the lead adds it once the requester approved.

## Revise (the requester answered)
The answers go under `## Confirmed answers` (`- **Q1** <answer> (<who>, <date>)`); change the criteria, scope,
states and data they affect, drop them from `## Open questions`, and refresh the table and the `Verdict:` line. A
changed criterion sets R10 and R12-R16 back to `fail` ("changed, not reviewed yet") until qa-lead reviews it again.

## Check
`python ${CLAUDE_PLUGIN_ROOT}/scripts/handoff_check.py <id> spec.md` (requirements only, no project: the folder path,
`handoff_check.py requirements/<id> spec.md`), then fix every PROBLEM line about the requirements, the Definition of
Ready, vague words and the Today vs asked table.
