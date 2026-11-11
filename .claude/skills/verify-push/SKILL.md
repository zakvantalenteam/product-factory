---
name: verify-push
description: (repo copy - with the plugin on use /product-factory:verify-push) After a teammate pushed and you pulled, check what landed against what was asked (handoff, spec, acceptance criteria) and report PASS/FAIL per item with evidence. Use for "<developer> pushed, I pulled, verify" or any "verify the dev's changes" request.
---
# Verify a teammate's push

Repo notes first: the `## Live check and verify notes` section of AGENTS.md, when the repo has one (the repo's extra checks per kind of file); it wins over the defaults below.

1. What landed: `git log --oneline -15` and `git diff --stat <before>..HEAD` (take `<before>` from `status.md` or the handoff, or ask). Only the commits for this task matter; other changes only if they break it.
2. What was asked: the handoff md and the acceptance criteria in `<work>/<id>/spec.md`.
3. Check each item with the cheapest real evidence. For several items, hand them to the `verifier` agent (mode `change`) in the background.
   - Code: read the changed hunks; run the related tests with `commands.test` in `.claude/project.json` (never a build while the app is up).
   - UI: the `live-check` skill if the app is up; otherwise say what needs a restart.
4. Judge only against the acceptance criteria. Anything else is a LATER note, not a FAIL. Never add new MUST items after the handoff was sent.
5. Update `status.md` (and the team's tracker, if one is used).
6. Reply: a table `item | PASS/FAIL | evidence`, then the exact fix for each FAIL, ready for the `dev-handoff` skill.
