# Accepted (won't fix, by design)

Findings the developer has closed as won't fix because the behaviour is by design. Reviews, audits and QA do not
raise these again, as MUST or SHOULD, in any later round. A finding goes in the review's `## Dropped findings` as
`accepted <id>` instead.

Raise one again only when a change widens it: a new place, a new caller, or a new kind of secret or personal data
(for a logging item: a value that was not logged before). Then raise only the new part and name the accepted id.
This register is per item. It never switches off a whole check (secret detection, auth, logging) for anything else.

Format: `- <id>: <what is accepted, one line> | where: <path, class or jar> | decided: <date> <who>, "<their words>"`

## Accepted
(none yet)
