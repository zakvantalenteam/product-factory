# Blend text moves (30 Oct 2026) - DONE

Files changed (all CRLF, UTF-8, no trailing whitespace, core block byte-identical, rule front matter kept):
`D:\blend\repo\LearningContentPack\AGENTS.md`, `.claude\rules\{java-backend,mcp-tools,n8n,ask-pulse-widgets,ui5-admin,labels}.md` (lines appended), `.claude\experts\sf.md` and `ai.md` (new).
Copies of AGENTS.md and the six rules before my edit: `scratchpad\blend\before\`. Script used: `scratchpad\blend\apply_text_moves.py`.
No git, no servers. No secret values (key names and `path:line` only).

## 1. AGENTS.md (outside the core block)
| Change | Result |
|---|---|
| Rule 9 (was line 38) | agents never run repo-changing git, read-only git fine, `git pull` only on the developer's own request, developer commits, `commit-msg` gives the message, subject starts `BLEN-5818 ...` |
| Worktrees line (was 47) | developer runs `git merge --ff-only dev` in the worktree; agents never run it |
| `crlf_edit.py`, `codemap.py`, `cursor_sync.py` | -> `.claude/core/scripts/` (cursor_sync now in "Blend flow notes") |
| "reuse `.claude/scripts/`" (line 45) | now also names `.claude/core/scripts/` |
| Lines 49-59 (triage, team, agents, flow) | replaced by `## Blend flow notes` (5 bullets, Blend-only): work folder + gitignored, Blend review checklist, area skills + `n8n-expert` + experts files, spec team rows, path rules, Cursor equivalent rule |
| Rule 8 (HANA) | added: one SELECT, small `--max-rows`, counts and ids not names or e-mail, `M_SQL_PLAN_CACHE` hash/counts/times only, never `STATEMENT_STRING` (performance-engineer, bug-investigator) |
| New `## Live check and verify notes` | `### Live check`, `### Verify`, `### Sdlc team rows and stages`, `### Release`, `### Search tips (explorer)` |

Facts moved into the new notes section (fact -> subsection):
- Ask `/lxp/widget/ai/search` + `?debug=true`, compact, Pulse, admin `/lxp/`; `app_status.py --asset` first -> Live check
- Ask turn about a minute, wait on the element, no screenshot polling; visible pane -> Live check
- 360/375 px, 200 % zoom, long German/Finnish labels, short Work Zone frame, light and dark tenant colour -> Live check (and widget/ui5 rules)
- repro capture list (role, page, input, console, network call, SSE events, screenshot) -> Live check
- five-point Definition of Done (blend-verifier) -> Verify
- verify-push n8n diff + `run_offline.mjs`, surefire, UI via live check -> Verify
- area owners Zakvan / Yash / Yogesh (also still in line 5) -> Verify
- sdlc rows: n8n (Yash OK else D7 + handoff; review only if mostly n8n), SF/AI review only if mostly theirs, area skills -> Sdlc team rows
- Test stage (`blend-build`: surefire, n8n eval; app UP/DOWN rules from test-runner; eval cases only under `n8n_workflows/eval/`) -> Sdlc team rows
- D3/D7 trigger meaning (display copy) -> Sdlc team rows
- "For release" notes, D8 list order, rollback triggers with Blend numbers (release-manager) -> Release
- explorer stack line, ~15 calls, codemap / n8n_node / props tips, trace-flow shapes -> Search tips

## 2. Rules: facts moved (fact -> file)
| Fact (source agent) | File |
|---|---|
| roles learner/manager/admin/n8n; manager = active direct reports only (spec-analyst, code-reviewer) | java-backend.md, mcp-tools.md |
| `roles.csv` loads only into an empty table (solution-architect, bug-investigator) | java-backend.md |
| EclipseLink shared cache does not see native-SQL writes in `cc/dao` (bug-investigator) | java-backend.md |
| bug suspects: missing user/`companyID` filter, lazy list outside transaction, "today" without time zone | java-backend.md |
| slow-code suspects (query per row, lazy lists, unbounded read, no index, n8n/LLM in series) (performance-engineer) | java-backend.md |
| D2 checks: legacy DAO reading a changed column, NOT NULL / unique index vs existing rows, column removal by `@UpgradeJob` (data-architect) | java-backend.md |
| new beans/endpoints/entities need restart, templates/static do not (solution-architect, release-manager) | java-backend.md |
| characterization tests: empty, one, many, other user, other language, deleted/expired course (test-runner, performance-engineer) | java-backend.md |
| run the five MCP guard tests; `McpToolRegistrationTest.EXPECTED` (test-runner, release-manager) | mcp-tools.md |
| tool losing active/deleted/expired filter as bug suspect (bug-investigator) | mcp-tools.md |
| `wfrev.py --check` clean before handoff, import order with WF_REV + node diffs, `promptrev.py` runs first (release-manager, ai-engineer) | n8n.md |
| eval cases only under `n8n_workflows/eval/`, `expect` fields, `run_replay.mjs`, `judge_agreement.mjs` (test-runner, ai-engineer) | n8n.md |
| field lost on a card -> diff Build Widgets / Deduplicate Ingredients (bug-investigator) | n8n.md |
| Pulse chain (scan -> fingerprint -> feed -> `Pulse.js`); `--plz-*` tokens (bug-investigator, ui-engineer) | ask-pulse-widgets.md |
| 375 px, 200 % zoom, German/Finnish labels, short Work Zone frame, light/dark tenant colour, AA on tenant colour (ui-engineer) | ask-pulse-widgets.md |
| no unit harness for widget JS: list live checks (test-runner) | ask-pulse-widgets.md |
| no internal ids or raw JSON to learner; SSE reconnect repeat, async race, missing label key (code-reviewer, bug-investigator) | ask-pulse-widgets.md |
| admin: long German/Finnish labels + 200 % zoom; no unit harness; slow-table suspects (ui-engineer, test-runner, performance-engineer) | ui5-admin.md |
| changed English value (not only new key) goes to release pass (release-manager) | labels.md |

## 3. Dropped as already covered
| Fact | Covered in |
|---|---|
| JPA only, no DDL, no quoted `@Column`, `LXP_` + UPPER_SNAKE, `@UpgradeJob` seeds, `TenantHelper.getTenantID()`, one company per deployment (data-architect) | AGENTS rules 1-2; java-backend.md lines 11, 12, 14 |
| `companyID` stamping, `LXP_` prefix, EclipseLink, Work Zone, wfrev --write | java-backend.md, ask-pulse-widgets.md:21, n8n.md:10 |
| surefire only while UP, never `./mvnw`, `app_status.py` first | AGENTS lines 9-11; project.json `guard` (mvnw block, block_while_app_up) |
| MCP guard tests named one by one; tool descriptions drive the n8n planner | mcp-tools.md lines 9-12 |
| Ask request chain (JS -> proxy -> n8n 01/05/02 -> MCP -> SSE) | ask-pulse-widgets.md:15 |
| `--primaryColor`, `--brand-*`, no fixed hex, focus-visible, no "Blend" for learners, labels as English keys | AGENTS rules 4-6; ask-pulse-widgets.md; ui5-admin.md |
| duplicate UI5 XML attribute truncates view | ui5-admin.md:15 |
| catalog only via `searchCatalog`, no embeddings | AGENTS rule 3; mcp-tools.md:15 |
| inventory update with tool changes; Jenkins `mvn clean package -DskipTests -P production` | mcp-tools.md:16; AGENTS line 11 |
| speed budgets 3/6/2/5 s, owner overlaps (sdlc:47-48) | core `sdlc:54-55` |
| design defaults (no shadows, 4/8/12/16, 13px, weights, tints), states, AA, Escape, skeleton rows, 150 ms, 375 px, 200 % zoom | core `reference/standards/ui.md:8-40` |
| cost per turn/month formula, price from provider page | core `reference/domains/ai.md:5,41-42` |
| `ui-engineer` / `test-runner` method text (critique, tokens, variants, review mode; test method) | agents already deleted from `.claude/agents`; generic parts in core `ux-designer`/`qa-engineer`; Blend parts moved above |
| `code-reviewer` focus passes, check mode, review-<focus> file names, finding format | core `code-reviewer` (reads `experts`) |
| D2/D4/D6 trigger text | already in project.json `decisions` |

## 4. Text for .claude/project.json (you edit; display text only, no guard trigger)
Add to `decisions`:
```json
"D3": { "what": "API and contracts (an MCP tool name or schema, an n8n payload, the answer envelope)" },
"D7": { "what": "other owners (n8n workflows: Yash; MCP tools: Yogesh)" }
```
If the schema needs `paths` or markers, leave them out: the hard guard on `n8n_workflows/*.json` stays in `no_read` / `no_write`. The same wording is in AGENTS.md under `### Sdlc team rows and stages`.

## 5. Found, not changed (not my files)
- `docs/agentic/` does not exist in the working tree (`docs/wiki/reference/mcp-tools.md` is the inventory). AGENTS.md repo-map row `docs/agentic/`, `.claude/rules/mcp-tools.md` `paths:` (`docs/agentic/tools-inventory.md`) and its last line point at it. Fix them or confirm the folder is elsewhere.
- `.claude/skills/blend-build` should carry the n8n eval / `wfrev.py --check` Test stage lines (also in AGENTS notes).
- `cursor_sync.py --check` not run by me (others are editing at the same time).
