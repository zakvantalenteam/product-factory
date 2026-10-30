# Smoke list

The neighbouring features to check whenever a change touches an area, so a change never breaks what sits next to it.
The verifier runs the items of every area a change touches (risk medium or high); an item that needs the running app
becomes a live-check step. Keep each item one line, checkable and quick (under a minute).

## Ask widget
paths: src/main/resources/static/js/AISearch/**, src/main/resources/static/css/AISearch*.css, src/main/java/com/talenteam/aisearch/**, src/main/resources/templates/**
- `/lxp/widget/ai/search` loads with no console error; every script in the template is served (no 404), `AIFrameFit.js` first.
- One question returns a narrative and its widgets; live progress shows while it runs (`?debug=true` shows the trace).
- An unknown widget type in the answer renders the safe fallback, not a blank card.
- Compact mode and a short Work Zone frame still fit (no clipped input, no double scrollbar).
- Follow-up chips send a new question; the conversation keeps its earlier turns.

## Pulse widget
paths: src/main/resources/static/js/Pulse/**, src/main/resources/static/css/Pulse.css, src/main/java/com/talenteam/aipulse/**, src/main/resources/templates/**
- `/lxp/widget/ai/pulse` loads its cards for a learner with data and shows its empty state for a new learner.
- Labels with `{n}` show the number, not `{0}` or a doubled quote.
- Colours follow the tenant primary colour; no fixed hex on cards or chips.

## Admin UI
paths: src/main/resources/static/view/**, src/main/resources/static/controller/**, src/main/resources/static/manifest.json, src/main/resources/static/js/admin-*.js, src/main/resources/static/css/*admin*.css
- `/lxp/` admin opens; the changed page and one neighbouring page render every control (a duplicate XML attribute drops controls silently).
- The changed dialog saves and closes; its Save button is present.
- New CSS or JS is listed in `manifest.json` and served.

## MCP tools
paths: src/main/java/com/talenteam/mcp/**
- `NoInternalFieldsTest` and the caller-scope tests pass (the unit suite covers them).
- A tool call for a learner returns only that learner's data; a manager reaches reports only through the team tools.
- The MCP tools reference (`docs/wiki/reference/mcp-tools.md`) matches the tools added, renamed or parked.

## n8n workflows
paths: n8n_workflows/**
- The patched node passes `run_offline.mjs` with its saved inputs; the node diff shows only the planned change.
- Ask still answers end to end after the import (router 01 -> 05 Guardrails -> 02 Ask Engine).

## Labels
paths: src/main/resources/messages*.properties, src/main/resources/static/i18n/*.properties
- The file keeps UTF-8, CRLF and no trailing newline; every new key exists in the base file.
- A changed label shows on its screen (no raw key visible).

## Backend (any Java change)
paths: src/main/java/**
- The app starts after the restart the developer runs (no bean or JPQL error in the log).
- The endpoints in the context pack's impact map still answer for a normal user and refuse a user without the permission.
