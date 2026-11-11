# test skill: the data map and the smoke pack

Part of the `test` skill (SKILL.md next to this file). Read it for `/test data`, `/test data cleanup` and
`/test smoke`. The data rules are in `test-data-engineer`'s agent file and practice pack; they win over a brief.

## Config (`qa` in `.claude/project.json`)
```
"qa": {
  "facts": ".claude/experts/qa.md",
  "data": {
    "map": ".claude/qa/data-map.md",
    "hosts": ["<dev or test host the app runs on>"],
    "query": "<the read-only query command, for example python .claude/scripts/hana_query.py>",
    "seed": "python .claude/qa/seed/<script>.py",
    "cleanup": "keep"
  }
}
```
`cleanup: keep` (the default) means one lasting QA dataset (`QA-DATA-`), topped up per ticket (`QA-<ticket>-`), with
cleanup only on request. The map, the seed scripts and the create log live in `.claude/qa/`, are committed and are
shared by the team. `qa.data` is missing: `/test data` asks once for the hosts and the query command (one question,
answers recommended from AGENTS.md and the repo) and writes them (setup work).

## `/test data` (learn or refresh the map)
1. `live_status.py init qa-data --mode task --skill test --title "QA data map"`.
2. `test-data-engineer` (`learn`). No QA facts file yet: it drafts `.claude/experts/qa.md` first; you add
   `qa.facts` to project.json. It drafts the seed and cleanup scripts and runs nothing.
3. `python ${CLAUDE_PLUGIN_ROOT}/scripts/handoff_check.py --data-map`; problems go back to the agent.
4. One gate: show the `## Needs` table (by source: find, create, ask), the ask list and the seed scripts in the chat
   and ask "Approve the data map?" (Claude desktop app: Approve and Change). Nothing is created before the yes.
5. Approve: write `Approved: <developer>, <date>` in `data-map.md` and the proposed `qa.data` keys
   (`## Config to add`) in `.claude/project.json`. Change: back to the agent with the developer's words.
6. Then ask once: "Create the lasting dataset now (<n> records)?" On a yes, `test-data-engineer` (`top-up`) with
   `Ticket: DATA` (prefix `QA-DATA-`) for every `create` need of the map, within the volume cap. Then offer the
   smoke refresh (`qa-lead` `smoke`), so the journeys name the new data ids.
7. Run it again when the data model changes (a D2 card was approved, or a migration landed): the agent refreshes the
   map, and the gate shows only what changed.

## `/test data cleanup`
1. Count what the log holds (`.claude/qa/create-log.jsonl`, lines not marked `removed`) per ticket, and show it:
   "Delete <n> QA records (<tickets>) on <host>? This cannot be undone." The lasting `QA-DATA-` set is kept unless the
   developer names it.
2. Only on a clear yes: `test-data-engineer` (`cleanup`) with the tickets named. Report what was removed.

## `/test smoke` (the whole pack)
1. `live_status.py testrun start smoke --title "smoke <date>"`, then the entry check (SKILL.md step 2).
2. `.claude/smoke.md` is missing, has no journeys, or `.claude/qa/smoke-inbox.md` has open lines: `qa-lead`
   (`smoke`) refreshes it first.
3. In one message (browser rule of SKILL.md step 5: shared rows in parallel, other users queued):
   `e2e-qa-expert` (`release-sweep`: every journey and every item that crosses screens, P1 first) and
   `ui-qa-expert` (`smoke`: every one-screen item). Brief both with the data map's ids for the journeys.
4. `qa-lead` (`sign-off`) for `<work>/smoke/`: `## Smoke` with every item's result; a P1 FAIL means FAILED (the
   release gate), and each FAIL goes to `fix-list.md`.
5. `live_status.py smoke <RUN> --pass <n> --fail <n> --blocked <n> --p1-fail <n>`, `testrun ticket <RUN> smoke ...`,
   `testrun done <RUN>`. Report the P1 failures first, then the rest; fixes go to `/fix smoke F1 ...`.

## Keeping the smoke pack current
- `qa-lead` (`smoke`) owns `.claude/smoke.md`: areas with `paths:`, one-line items, `### Journey:` blocks (Role,
  Steps, Expected, Data) and `[P1]` marks. `handoff_check.py --smoke` checks the format.
- `/develop` adds one line to `.claude/qa/smoke-inbox.md` when it adds a screen or a journey
  (`- [ ] <date> <id>: smoke: add <area>: <item>`); `/fix` does the same for a bug that reached a release.
  `qa-lead` folds the open lines in at the next smoke refresh or test run and ticks them.
