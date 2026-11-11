# Vague words (Definition of Ready R12)

Words that let two readers understand a requirement in two ways. `handoff_check.py` flags each one in the
requirement part of `spec.md` (above `## Technical appendix`) as a PROBLEM line. spec-analyst replaces it before the
gate; qa-lead's requirements review quotes the sentence and asks the requester one plain question.

A project adds its own words in `.claude/project.json`: `"glossary": {"vague_words": ["seamless", "on time"]}`.

## What the check skips (no false positives)
- Quoted text: anything in "double quotes" or curly quotes, and `>` quote lines (the requester's own words, a
  question that quotes a word).
- Code: `inline code`, fenced code blocks and HTML comments.
- Sections that are not requirements: `## Open questions` (and Smaller points, Gaps I found), `## Words used here`,
  `## Confirmed answers`, `## Questions and answers`, `## Changes in revision`, `## Definition of Ready`, the
  technical appendix and everything after it, and the technical sections (Affected areas, Who will work on this,
  Decisions this change needs, Technical questions).
- The lines `Source:`, `Requester:`, `Requirements:` and `Size:`.
- A word defined on the spot by a number: `fast (within 2 seconds)`; a label such as "how fast".
- "Should" as a priority label (`| Should |`, `(Should)`, `Should:` at the start of an item) and in a sentence that
  ends with a question mark.

## The core list
| Word | Replace it with |
|---|---|
| fast, quick, quickly | a time with its condition: "the list opens within 2 seconds for 500 rows" |
| easy, easily, simple, intuitive, user-friendly | the steps or a measure: "in 3 clicks from the home page", "a new admin does it without help" |
| relevant | the rule that decides it: "courses with at least one of the learner's skills" |
| appropriate, appropriately, as appropriate | the exact value, message or rule |
| as needed, if possible, where possible, as soon as possible | when it happens, or a numbered rule; or move it out of scope |
| etc. | the full list, or "the 4 types: A, B, C and D" |
| and/or | "A, B or both" written out, or two criteria |
| some users | the role or the rule that picks them: "managers with 2 or more direct reports" |
| should (as a requirement) | "must" with the result, or the present tense: "Then she sees 20 rows" |
| TBD, to be decided | an open question `Q<n>` with a Recommended answer |
