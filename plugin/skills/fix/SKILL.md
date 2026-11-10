---
name: fix
description: "Use when the developer types /fix, reports something broken, gives a bug ticket, or after QA names fix-list items (/fix BLEN-1 F1 F3), or the sdlc triage routes a bug here. Owns making something broken work again: reproduction steps and a proven root cause from bug-investigator first (never a fix on a suspicion), then the fix by the area agent with a regression test that fails before and passes after and the regression ring, the safety net, a code re-review of the changed lines, and the fix-list items marked fixed for /test retest. Several bugs run in parallel when their files do not overlap. Never adds features or changes scope (/develop)."
---
# Fix (bugs and fix-list items)

Paths: `<work>` is `work_dir` in `.claude/project.json` (default `.claude/work`); `live_status.py` is
`python ${CLAUDE_PLUGIN_ROOT}/scripts/live_status.py`; the fix list format is `${CLAUDE_PLUGIN_ROOT}/reference/qa/fix-list.md`. The
shared rules live once, in the `sdlc` skill: [start a task](../sdlc/SKILL.md) (section 2),
[team.md](../sdlc/team.md), [briefing.md](../sdlc/briefing.md), [safety-net.md](../sdlc/safety-net.md), gates and
decision cards (sdlc section 7), live status (section 6), [stages.md](../sdlc/stages.md) and the lessons loop
(section 9). Every rule in them applies here; this file adds only what is particular to a fix.

You are the Tech Lead of this run. You get the cause proven, brief the owner of the broken code, run the checks and
hand over to `/test`. You never write product code and never fix on a suspicion.

## One job
| The request | Whose |
|---|---|
| Something that should work and does not: a bug ticket, a report, fix-list items | yours |
| New or changed behaviour, or a fix that would change agreed behaviour or scope | `/develop`: say so in one line; that part stops here |
| "Is it fixed?", retest, QA sign-off | `/test` (`/test retest <id>`) |
| Requirements to check | `/review-spec` |

## Commands
| Command | What runs |
|---|---|
| `/fix BLEN-1` | a bug ticket or a reported bug; when `<work>/BLEN-1/fix-list.md` exists, every MUST item that is `open` or `reopened` (plus the SHOULD items the developer names) |
| `/fix BLEN-1 F1 F3` | those fix-list items only |
| `/fix BLEN-1 BLEN-2` | several bugs: the proofs in parallel; the fixes in parallel when their files do not overlap, one after another when they do |

Fixes start only when the developer says so; QA never starts them.

## 1. Start
1. A bug ticket with no task: `live_status.py init <id> --mode task --skill fix --title "<what is broken>" --size
   S|M|L`, the report as it came in `<work>/<id>/request.md`, then sdlc section 2, steps 4-7 (`Kind of work: bug`).
2. Fix-list items: `live_status.py init <id>` binds the ticket's task (`/test` made one when there was none), then
   `skill <id> fix`. Read `fix-list.md`; `live_status.py fixes <id>` gives the counts. Skip items that are
   `verified`, `wont-fix` or `later`; ask once about a named item that is not `open` or `reopened`.
3. Several bugs: one task each. The session is bound to the last `init`, so run `init <id>` before briefing that
   ticket's agents when they run one after another.
4. An obvious small bug takes the small path (below); everything else the full path.

## 2. Proof (before any fix)
`bug-investigator` (mode `spec` for a bug ticket, mode `fix-list` for items; one run per ticket, all in one message)
writes `<work>/<id>/fix-proof.md`, one block per bug (`## <id>`) or item (`## F<n>`):
- `### Reproduction`: numbered steps (for an item: its Steps and Evidence, confirmed);
- `### Root cause`: `Proven: yes` and the first wrong line as `path:line`;
- `### Regression test`: its name and where it goes, failing on today's code;
- `### Regression ring`: the siblings and variants that share the code (fix now or LATER);
- `### Fix plan`: the smallest fix at the cause, one bullet per file.

A bug ticket also gets `brief.md` and `spec.md` as in stages.md row 1. Then `handoff_check.py <id> --fix [F1 F3]`.
A block that fails, or says `Proven: no`, is never fixed. It stays open, with `### What would prove it`, a History
line in the fix list ("cause not proven: <what would prove it>") and `live_status.py next <id> "<what is
needed>"`. The main session runs reproductions that need the app (`live-check`) and passes the results back
(`bug-investigator` mode `revise`).

A fix plan that hits a decision card (D2-D8) or crosses layers gets its card and gate as sdlc section 7. Risk medium
or high: the spec gate as sdlc section 7 before Build.

## 3. The fix
1. Group the proven blocks by owner (`Owner agent` in the fix list, or the area of the `### Fix plan` files).
   Another team's code goes to the `dev-handoff` skill, one handoff per developer, never into their files.
2. Before Build: the "before" steps of safety-net.md at the task's risk.
3. Brief each owner (briefing.md) with its blocks word for word and these steps: write the regression test first
   and see it fail; fix at the cause; see the test pass; fix the ring places marked "fix now"; fix only these blocks.
   Owners whose files do not overlap go in one message; overlapping ones go one after another. Set each item to
   `fixing` (top table and a History line).
4. After Build: the "after" steps of safety-net.md (compile, the full unit suite, the scope check).
5. `review_pack.py <id>` (the delta pack), then `code-reviewer` re-reviews the changed lines. A MUST goes back to
   its owner.

## 4. Hand-off
- Fix-list items: each item `fixed` with a History line (what changed, `path:line`, the regression test), then
  `live_status.py next <id> "/test retest <id>"`.
- A bug ticket: `stage <id> review done`, then `live_status.py next <id> "/test <id>"`.
- Tell the developer which items are fixed, which stay open and why. The retest turns each item `verified` or
  `reopened`; a reopened item goes round again only on the developer's word.
- The lessons loop (sdlc section 9): every bug found in a change this flow made adds a line to
  `.claude/review/lessons.md`.

## Small path (an obvious small bug)
Within `quick_fix` in `.claude/project.json` (about 30 lines in up to 3 files), with a cause you can see in the code
at `path:line` (the report or the fix-list item points straight at it) and nothing to decide:
1. A quick brief (`Quick fix:` line, briefing.md) to the area agent: the cause at `path:line`, the fix, and the
   regression test (fails before, passes after).
2. Self-check: the diff against the hard rules in AGENTS.md and `.claude/rules/`.
3. `live_status.py quick "<what was broken and the fix>" --skill fix` (`--id <id>` with a ticket); a fix-list item
   becomes `fixed` with a History line; then the hand-off above.
4. The cause turns out not to be plain, or the fix grows past the limits: stop and take the full path.

## Rules
- A ticket closes only on SIGNED OFF (`/test`). Jira bugs only when the developer asks; ask before creating each.
- Never commit, push, start or restart servers; no git that changes the repo.
- Keep the live page current: the item statuses, the stage lines and `next`.
