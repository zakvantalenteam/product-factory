---
name: commit-msg
description: (repo copy - with the plugin on use /product-factory:commit-msg) Prepare a copy-ready git commit message for the uncommitted changes; the developer commits and pushes. Use when asked for a commit message, "good to commit?", or at the end of the sdlc flow.
---
# Commit message

Repo notes first: the `## Live check and verify notes` section of AGENTS.md, when the repo has one (files and folders to leave out, message bullets); it wins over the defaults below.

1. `git status --short`, `git diff --stat` and `git diff --cached --stat`. Read hunks only where the purpose is unclear.
2. Leave out files that are not part of the task (other developers' work, scratch files, generated output) and list them as "not included".
3. Message format, in one code block:
   ```
   <ticket> <short subject: what changed for the user>

   - <change 1, user-visible effect first>
   - <up to 5 bullets>
   ```
   Ticket: `ticket_prefix` in `.claude/project.json` (one prefix or a list; with several, the one in the task id) plus the number from the task id or `<work>/<id>/status.md`, else from recent commits (`git log -5 --format=%s`).
4. Under the block: files to include (grouped), files to leave out and why, and for "good to commit?" anything half-done or unverified (stages not done in `status.md`).
5. Never run `git add`, `git commit` or `git push`.
