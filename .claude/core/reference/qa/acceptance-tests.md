# Acceptance tests first (`/develop`)

After the test plan and before Build, `qa-engineer` (mode `acceptance`) turns the criteria of `spec.md` into
automated acceptance tests. Each one fails first, for the right reason, and the result is recorded in `test.md`.
Build is done when they pass. A criterion that cannot be automated goes to the QA expert who tests it in the
running app; none is skipped silently.

## Write
- One test or more per criterion, named with its id (`ac3_managerSeesOnlyOwnTeam`, or the AC id in the test's
  display name), in the project's test folder, mirroring the package of the code under test (Java
  `src/test/java/<same package>/`). Never in `src/main/**`, the repo root or the scratchpad.
- Test through an entry point that exists today where you can (the endpoint, the public service method the design
  changes, the screen's API), so the test compiles on today's code and fails on its assertion.
- Assert what the user or caller sees (fields, status, order, counts), with the criterion's example data.
- Model each test on the nearest existing test (same harness, same fixtures); no new framework.

## Run red (the project's safe test command)
1. `app.status` first, as its own command.
2. App UP: only `commands.test` with the named tests (what the IDE compiled). A new test class that is not compiled
   yet: say so and ask the developer to build in the IDE; then run it. Never run a command `guard.block_while_app_up`
   lists.
3. App DOWN: `commands.compile`, then `commands.test` (or `commands.test_app_down` when the project has it).
4. Each test must FAIL before Build, for the right reason:
   - right: the assertion on the missing behaviour (expected vs actual named), or a compile error naming exactly
     the class or method `design.md` `## Planned files` plans and today's code lacks;
   - wrong: a typo, wrong setup or data, a missing dependency or an environment error: fix the test and run again;
   - a test that PASSES before Build tests nothing new: fix it, or report that the behaviour already exists (a
     finding for the lead, first in your reply).

## Not automatable
A criterion that is visual only (the look, a colour, a layout) or needs the running app across screens (a journey,
two users, a notification) goes under `## Not automated` with the reason and its owner: `ui-qa-expert` (one
screen) or `e2e-qa-expert` (a journey). qa-lead's plan gives each one a row for that owner.

## Record (`test.md`)
```
## Acceptance tests
| AC | Test | Before build | Why it fails | After build |
|---|---|---|---|---|
| AC1 | `CourseSearchServiceTest#ac1_filtersBySkill` | FAIL | expected 3 courses, got 10 (no skill filter yet) | |

## Not automated
| AC | Why | Owner |
|---|---|---|
| AC4 | visual only: the badge colour in dark mode | ui-qa-expert |
```
Also the commands run and the new test files with their paths. `handoff_check.py <id> test.md` checks it: every
criterion in one table, each test in backticks, FAIL before Build with a reason, an owner for each row not
automated.

## After Build
- The Build "after" steps run the acceptance tests with the same safe command; the lead records the counts in
  `safety.md` `## After build`. Build is done when every acceptance test passes.
- Area agents never change an acceptance test to make it pass. A test they think is wrong goes to `questions.md`
  for `qa-engineer`, who fixes the test only when the test, not the code, is wrong.
- `/test` (`qa-engineer` mode `test`) keeps both tables and fills the `After build` column.
