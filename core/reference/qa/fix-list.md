# Fix list (format)

`qa-lead` writes `<work>/<id>/fix-list.md` at every sign-off that leaves a defect open, and updates it after each
retest. It is the only list of what QA found for a ticket. Fixes are never automatic: the developer starts them with
`fix <id>` or `fix <id> F1 F3` (sdlc fix loop), and `/test retest <id>` checks them. `handoff_check.py` checks this
format; the live page counts the statuses per ticket.

## Layout
```
# Fix list: <ticket id> - <ticket title>

Run: <work>/test-runs/<run>.md (or "task test stage") | Signed off: <date> by qa-lead | Verdict: FAILED | SIGNED OFF
Fingerprint: <short hash of the ticket's changed files when the run started>

| ID | Sev | Title | Owner agent | Status |
|---|---|---|---|---|
| F1 | MUST | Save keeps the old title after reopen | frontend-developer | open |
| F2 | SHOULD | Export date column in UTC | backend-developer | fixed |

## F1 Save keeps the old title after reopen
- Ticket: BLEN-1 (criterion C2) | Found by: ui-qa-expert, row UQ20
- Where: role admin, page Content > Edit, environment local (http://localhost:8080)
- Steps:
  1. ...
  2. ...
- Expected: ...
- Actual: ...
- Evidence: qa-ui.md row UQ20; screenshot <path>; console "<text>"
- Suspected area: `path/File.java:120` (suspected) - or proven, with the reason
- Fix owner: frontend-developer
- Retest: UQ20, C2; regression ring: UQ2, E2E journey J3
- History: 2026-11-06 open (qa-lead)
```

## Rules
- **IDs** `F1`, `F2`, ... per ticket, never reused; a reopened item keeps its id.
- **Sev** is `MUST` (fails the ticket: a broken criterion, a checklist MUST, data loss, a security or access hole) or
  `SHOULD` (worth fixing, does not fail the ticket).
- **Owner agent** is the area agent that fixes it: `backend-developer`, `frontend-developer`, `n8n-expert`,
  `integration-engineer` or `devops-engineer` (`qa-engineer` for a wrong test). Another team's code: the owner is
  `dev-handoff` and the block names the developer.
- **Status**, one of:
  - `open`: found, not started.
  - `fixing`: an area agent is on it.
  - `fixed`: changed and reviewed, waiting for retest.
  - `verified`: the retest rows and the regression ring passed.
  - `reopened`: the retest failed; the block says why in History.
  - `wont-fix`: the developer decided not to fix; History quotes their words and the date.
  - `later`: moved to the backlog by the developer; History says where.
- **Every block** has: ticket and criterion, found by (agent and row id), where (role, page, environment), numbered
  steps, expected, actual, evidence, suspected area (`path:line`, marked `(suspected)` until proven), fix owner, and
  retest rows plus the regression ring.
- **History** gets one dated line per status change (who and why). The top table and the block always agree.
- **A ticket closes only on SIGNED OFF**: no `MUST` item is `open`, `fixing`, `fixed` or `reopened` (a `wont-fix`
  MUST needs the developer's accepted-risk words).
- **Jira bugs** only when the developer asks; ask before creating one.
