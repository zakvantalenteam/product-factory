# test skill: several tickets in one run

Part of the `test` skill (SKILL.md next to this file). Read it before step 3 when a run has more than one ticket.
Every rule in SKILL.md still applies.

## One build, one run
- `testrun start` takes every ticket id at once: one run, one fingerprint per ticket.
- The entry check runs once: all tickets share the build. A failure in shared code blocks every ticket; a failing
  unit test in one ticket's files blocks only that ticket.
- One `qa-lead` per ticket, all started in one message (plan, intake or retest, whatever each ticket needs). A
  ticket whose plan is reused gets no `qa-lead` in this step.

## Rounds
1. `qa-lead` per ticket that needs a plan, in one message.
2. The QA experts of every ticket, in one message. The browser rule counts across tickets: ticket A's admin checks
   and ticket B's learner checks never run at the same time. Two tickets whose browser rows need the same other user
   can share one queued run; that expert writes each ticket's rows into that ticket's own file.
3. `testrun check`, then `qa-lead` `sign-off` per ticket, in one message.
4. `testrun ticket` per ticket, then `testrun done` once.

## Test data
Each ticket has its own prefix `QA-<ticket>-` (for example `QA-BLEN-2-course-1`) for every record, name and file QA
creates. A record made for one ticket is never used by another, so a finding never mixes two tickets' data, and the
leftovers can be found by prefix.

## Which ticket a defect belongs to
Each finding names its ticket. The brief gives every expert the other tickets in the run and where their changed
files are listed (`## Changed files` in `qa-brief.md`, `## Planned files` in `design.md` or `triage.md`, or the
commits that name the ticket).
1. The defect touches one ticket's changed files (the suspected `path:line`, the screen or endpoint it serves): it
   belongs to that ticket, whichever ticket's expert found it.
2. Unclear (two tickets change those files, or no file can be named yet): it is cross-ticket. It is listed in the fix
   list of every ticket it may belong to, with one owner ticket named in its `Ticket:` line, for example
   `- Ticket: BLEN-1 (criterion AC2; cross-ticket with BLEN-3, owner BLEN-1)`. The owner is the ticket whose change
   most likely caused it (the latest change to the suspected file). It counts as open in each of those tickets until
   the owner's item is `verified`; then the other copies get `verified` with a History line naming the owner's item.
3. In code no ticket of the run changed: a regression. It belongs to the ticket whose changed files call that code
   (the impact map in `context.md`); when that is unclear, rule 2.

Each `qa-lead` sign-off reads its own ticket's QA files and the findings in the other tickets' QA files that name its
ticket.

## Staleness
`testrun check` lists only the tickets whose files changed. Only those tickets' sign-offs list rows that ran on old
code; the others sign off as usual.

## Summary
One table across tickets (`| Ticket | Verdict | MUST open | SHOULD | Blocked |`), in the chat and in
`<work>/test-runs/<run>.md` (`testrun done` writes it). Then the fix-list counts per ticket and the hand-off
lines from SKILL.md, step 6.
