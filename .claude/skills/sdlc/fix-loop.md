# sdlc skill: 10. Fix loop

Part of the `sdlc` skill (SKILL.md next to this file), read when the developer starts fixes after QA.

## 10. Fix loop (after QA; never automatic)
QA never fixes. `qa-lead` leaves `<work>/<id>/fix-list.md` (format: `.claude/core/reference/qa/fix-list.md`); the
developer decides what gets fixed and when.

Trigger: the developer says `fix <id>` (every MUST item that is `open` or `reopened`, plus the SHOULD items they
name) or `fix <id> F1 F3` (those items only). Several ids in one message are fine; each keeps its own items.

1. `live_status.py init <id>` binds this session to the ticket's task (`/test` made a minimal one when there was
   none). Read `fix-list.md`; `live_status.py fixes <id>` gives the counts. Skip items that are `verified`,
   `wont-fix` or `later`; ask once about a named item that is not `open` or `reopened`.
2. Group the items by `Owner agent`. Another team's code goes to the `dev-handoff` skill (one handoff per
   developer), not to an area agent.
3. Cause: an item whose area is marked `(suspected)` and whose cause the evidence does not prove goes to
   `bug-investigator` first (one run per group, in parallel). A proven cause goes straight to its owner.
4. Brief each owner with the exact items (section 4): the block text (steps, expected, actual, evidence, the proven
   or suspected area), the retest rows, and "fix only these items". Owners whose files do not overlap run in
   parallel in one message. Set each item to `fixing` (top table and a History line).
5. Safety net (section 5) at the task's risk: compile, the full unit suite and the scope check on the changed files.
6. `code-reviewer` re-reviews the changed lines (`review_pack.py <id>`, the delta pack). A MUST goes back to its
   owner.
7. Mark each item `fixed` with a History line: what changed, `path:line`.
8. Tell the developer which items are fixed and that `/test retest <id>` checks them. The retest flips each item to
   `verified` or `reopened`; a reopened item goes round again only on the developer's word.

A ticket closes only on SIGNED OFF. Jira bugs only when the developer asks (ask before creating one). The live page
shows the open, fixed and verified counts per ticket.
