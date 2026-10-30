---
name: dev-handoff
description: Write the handoff for another developer who owns part of a change (another team's service, workflow, backend or UI) - one self-contained md per developer with every change they must make, plus a copy-ready chat message. Use when work needs changes from another owner (Release/handoff stage of the sdlc flow), or when asked to "prepare specs/message for <developer>".
---
# Developer handoff

Repo notes first: the `## Live check and verify notes` section of AGENTS.md, when the repo has one (area owners and how they want their handoff); it wins over the defaults below.

Area owners are listed in AGENTS.md. One file per developer, complete enough to finish in one pass; never one shared spec split across people.

1. Collect every change that developer owns (per area they own). If they have nothing to code, their file says so and lists only what to review.
2. Write `<work>/<id>/handoff-<developer>.md` and share it as a file (put it under `docs/<feature>/` only if the team wants it in git). Structure:
   - Goal in 2 lines, and why.
   - Numbered changes. Each: where (file + method, or the area's unit), the exact change (the code or a precise patch), and the acceptance check (question to ask, test to run, expected result).
   - Order and dependencies (for example "UI ships first; keep today's payload working").
   - What not to change.
   - LATER: anything not required, at the end, never mixed into the numbered list.
3. Message, copy-ready, under 8 lines: what, why, file name, how to verify, deadline if one was given.
4. Reply with the file path(s) and the message in a code block.
