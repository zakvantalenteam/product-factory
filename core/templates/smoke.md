# Smoke list

The neighbouring features to check whenever a change touches an area, so a change never breaks what sits next to it.
`qa-lead` keeps this file (`smoke` mode); every `/test` run adds the items of the areas a ticket touches, `/test smoke`
runs the whole pack, and the verifier runs the items of every area a change touches (risk medium or high). Keep each
item one line, checkable and quick (under a minute). `[P1]` marks what must work for any release.

<!-- One section per area. `paths:` lists the globs that belong to it (same globs as .claude/project.json).

## Example area
paths: src/main/java/**/example/**, src/main/resources/static/js/example/**
- The example page loads with data for a normal user and shows its empty state for a new one.
- The example endpoint still answers for a user without the admin role (403 for admin-only calls).
- [P1] A normal user signs in and the example page shows their data.

### Journey: open and save an example [P1]
Role: normal user
Steps: 1. Open the example page. 2. Open the first record. 3. Change its title and save.
Expected: the list shows the new title, and the record opens again with it.
Data: D1 (the data map's need id, or record ids)
-->
