# sdlc skill: 5. Safety net (nothing may break; depth set by risk)

Part of the `sdlc` skill (SKILL.md next to this file), read when its step comes. Read it when Build starts.

## 5. Safety net (nothing may break; depth set by risk)
| Step | low | medium | high |
|---|---|---|---|
| Before Build: `python .claude/core/scripts/scope_check.py baseline <id>`; `commands.compile`; the full unit suite (`commands.test_all`, else `commands.test` with no filter); record pass and fail counts | yes | yes | yes |
| Characterization tests: `qa-engineer` (mode `characterize`) locks today's outputs of every changed shared method in the session scratchpad; `char_test.py run <id> before` passes | - | yes | yes |
| After Build: compile; the full unit suite (no new failure); `char_test.py run <id> after` and `char_test.py diff <id>` (no change outside `## Intended changes`); `scope_check.py check <id>` (every changed file planned) | yes | yes | yes |
| Review: every caller in the impact map checked by someone | - | yes | yes |
| QA: `qa-lead`'s plan at Design and sign-off at Test; the UI checklist on every changed screen and the API checklist on every changed endpoint; a checklist MUST fails Test | yes | yes | yes |
| Verify: the changed flow, plus the `.claude/smoke.md` items for each area touched | flow | + smoke | + smoke |

- Record it in `<work>/<id>/safety.md`: `## Before build`, `## After build` (commands, counts, results) and `## Intended changes` (one bullet per characterization test whose output the spec changes on purpose, with the `AC#`).
- A test that already failed before Build is noted, never fixed silently. A new failure after Build sends the task back to Build.
- An unplanned file is a MUST: drop it, or accept it with `scope_check.py add <id> <path> --why "<reason>"`. The stop hook sends the turn back once while one is left.
- Commands come from `.claude/project.json` (`commands`); never one that `guard.block_while_app_up` blocks while the app runs.
