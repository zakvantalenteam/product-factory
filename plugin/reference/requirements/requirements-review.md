# Requirements review (the checker)

qa-lead (mode `requirements-review`) reads the draft `spec.md` that spec-analyst wrote and checks it as a separate
reader: the writer never grades its own draft. Its results fill R10 and R12-R16 of the Definition of Ready
(`definition-of-ready.md` next to this file). spec-analyst's `dor` mode in `/develop` uses the same checks on a
ticket as given. Plain words for the requester; no test jargon.

## What it reads
`spec.md` (the requirement part, above `## Technical appendix`), `request.md`, `questions.md`, `context.md` and the
`## Today vs asked` table when code is there, the other tickets the requester names (their text in `request.md` or
the work folders), `vague-words.md` (plus `glossary.vague_words` in `.claude/project.json`), and the lessons tagged
`[review-spec ...]` in `.claude/review/lessons.md` (each one is an extra check on its R item; skip when the file is
missing).

## The checks
| R | Check | A finding when |
|---|---|---|
| R10 | Testable | a criterion has no observable result, no number where one is needed, no role, no start data or state, or mixes several checks in one |
| R12 | Clear | a vague word (the list) or a term the glossary does not define; the same thing called by two names |
| R13 | Consistent | two statements contradict (scope vs a criterion, two criteria, a role table vs a criterion); a clash with another named ticket; a clash with today's behaviour in `## Today vs asked` that is not marked as meant to change |
| R14 | Complete behaviour | create, change, remove or cancel is neither covered nor ruled out; a state with no way in or out, or no named role that moves it; no limit (most, fewest, longest); no rule for a duplicate; no rule for two people changing the same item at once |
| R15 | Assumptions | a criterion, number or rule that rests on something nobody confirmed and that is not an `A<n>` |
| R16 | Traceable | a criterion that serves no part of the goal or of the in-scope list (gold plating), or a goal or in-scope item that no criterion covers |

## Findings
`requirements-review.md` in this order: `## Summary for people`, `## Plan` (common.md), `## Findings`, `## Results`,
`## Criteria to rewrite first`. Write the file with these headings first (the speed habit), then fill it.
Under `## Findings`, one row per finding, in the order of the table above:

```
| ID | R | Quote | Problem | Question for the requester | Recommended |
|---|---|---|---|---|---|
| RR1 | R12 | "The list loads fast" (AC3) | "fast" has no number | How long may the list take to open with 500 courses? | Within 2 seconds |
```

- `Quote` is the sentence word for word in quotes, with its place (AC id or section).
- One plain question per finding, never technical; `Recommended` is the answer you would pick.
- A finding the writer can fix without the requester (a rewrite with the same meaning) gives the rewrite as
  `Recommended` and says "rewrite" in the question column.
- A behaviour the draft already asks as an open question `Q<n>` (with a Recommended answer) counts as covered:
  no finding, name the `Q` in the Results line.
- Then `## Results`: one line per item, `R10 pass|fail`, `R12 ...` to `R16 ...`, each fail naming its `RR` ids.
  An item passes only with no finding left for it.
- `## Criteria to rewrite first`: the findings that block a test plan.

## How the writer uses it
spec-analyst (mode `requirements`, merge) takes each rewrite that keeps the meaning word for word, turns each other
finding into an open question `Q<n>` (with the requester question and the Recommended answer) or an assumption
`A<n>`, and copies the `## Results` lines into R10 and R12-R16. An item stays `fail` while a finding for it is
open, with its note naming the `Q` ids.

## dor mode (`/develop`)
spec-analyst checks the request as given with the same table, writes each finding as a gap `Q<n>` under
`## Gaps I found` (the quote, the question and the Recommended answer), and fills R12-R16 from them.
