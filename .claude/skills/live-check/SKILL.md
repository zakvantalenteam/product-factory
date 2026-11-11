---
name: live-check
description: (repo copy - with the plugin on use /product-factory:live-check) Check a page of the running local app with the built-in browser - load it, act like a user, read what shows, check console and network. Use after a UI change, or when the developer says check it live.
---
# Live check in the browser

Repo notes first: the `## Live check and verify notes` section of AGENTS.md, when the repo has one (pages, routes, sign-in and what not to click); it wins over the defaults below.

## Before
1. The app status command in `.claude/project.json` (`app.status`) must say UP, or `app.url` must answer; if not, ask the developer to start the app (never start it yourself).
2. For changed JS/CSS, check what is actually served first (the repo's asset check in AGENTS.md, or fetch the asset URL), so you test the code you think you are testing.

## URLs
From `app.url` in `.claude/project.json` and the page list in AGENTS.md. The local profile usually signs in a dev user; never type real credentials.

## How
- Keep the browser pane visible while checking: a hidden pane makes screenshots and scripts time out.
- Read with `get_page_text` / `read_page` / `find` first; take a screenshot only to judge layout or colour.
- A slow answer (an AI reply) can take up to a minute: wait on its element, don't poll with screenshots.
- Check `read_console_messages` (errors only) and `read_network_requests` for failed calls.
- Layout: check a narrow width (about 360 px) and, for embedded pages, a short frame.

## Report
For each check: the action, what showed (counts, key text), PASS/FAIL against what was expected, and the evidence (console error, failed request, screenshot) for any FAIL.
