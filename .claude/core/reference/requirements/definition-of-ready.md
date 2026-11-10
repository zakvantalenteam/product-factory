# Definition of Ready (requirements)

The fixed checklist for requirements before any design or build. The `review-spec` skill applies it (spec-analyst
mode `requirements` fills it, qa-lead checks testability); the requester approves the result at one gate. Written in
plain words for the people who asked for the work, no code terms (`path:line` only in the technical appendix).
`handoff_check.py` checks it.

## Where it lives
At the end of `<work>/<id>/spec.md`:

```
## Definition of Ready
| ID | Item | Result | Note |
|---|---|---|---|
| R1 | Goal and who it is for | pass | |
| R2 | In scope and out of scope | pass | |
...
Verdict: READY | NOT READY
```

and, once the requester approved it at the gate, one line near the top of `spec.md`:

```
Requirements: READY (confirmed by <name>, <date>)
```

## The checklist
| ID | Item | Passes when |
|---|---|---|
| R1 | Goal and who it is for | One or two sentences: the problem, who has it and what changes for them. |
| R2 | In scope and out of scope | Both lists exist; anything a reader could assume is in scope but is not, is listed as out. |
| R3 | Criteria | Every criterion is Given/When/Then with a concrete example (real-looking data, not "some value"). |
| R4 | Roles | Every role that sees or uses it, and what each may and may not do. |
| R5 | Empty and error states | What people see with no data, too much data, a failure, no permission, and while waiting. |
| R6 | Non-functional needs | In plain words: how many records or users, how fast, which languages, devices and browsers, who may see personal data. |
| R7 | Data | What is shown or stored and where it comes from (which system, which field in business words). |
| R8 | Other owners and dependencies | Other teams, systems or people this depends on, named. |
| R9 | Open questions | Each has a Recommended answer and an If not decided line; none blocks a MUST criterion. |
| R10 | Testable | qa-lead checked every criterion: each can pass or fail on what a tester can see or measure. |
| R11 | Requester | The person who confirms the requirements is named. |

## Verdict
- **READY** only when every item passes. **NOT READY** otherwise: the Note column says what is missing, in one line,
  as a question for the requester where one is needed.
- `Result` is `pass`, `fail` or `n/a` (with the reason, for example R8 n/a "no other owner").
- A change to any criterion after READY goes back to the requester as a question; the verdict and the
  `Requirements:` line are refreshed after their answer.
