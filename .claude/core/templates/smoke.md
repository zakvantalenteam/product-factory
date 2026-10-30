# Smoke list

The neighbouring features to check whenever a change touches an area, so a change never breaks what sits next to it.
The verifier runs the items of every area a change touches (risk medium or high); an item that needs the running app
becomes a live-check step. Keep each item one line, checkable and quick (under a minute).

<!-- One section per area. `paths:` lists the globs that belong to it (same globs as .claude/project.json).

## Example area
paths: src/main/java/**/example/**, src/main/resources/static/js/example/**
- The example page loads with data for a normal user and shows its empty state for a new one.
- The example endpoint still answers for a user without the admin role (403 for admin-only calls).
-->
