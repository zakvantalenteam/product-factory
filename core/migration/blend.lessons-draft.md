# Blend lessons from fixed Ask + Pulse review findings (DRAFT for review, nothing changed in Blend)

Sources: work folders review-02-set, review-next5, review-next8, review-next16 (review*, spec, design, fixes-1, items, test, status), the tracker artifact (304 findings in state fixed or verified, read through ArtifactData), Blend `review/checklist.md` and `rules/*.md`, core `reference/review/checklist.md`.
review-next8 is design only (nothing built or fixed yet), so it gives no lessons. Open findings, open security items and LATER items are skipped.
Date = the task's date or the finding's fix date in the tracker. `Fxx-yyy` ids are tracker findings. Line numbers in "Already covered": `checklist.md` = `D:\blend\repo\LearningContentPack\.claude\review\checklist.md`; `core:` = `D:\product-factory\core\reference\review\checklist.md`.

## Lessons

### n8n workflows
- 2026-10-28 review-02-set + F-A3-072/F-A3-021/F-A3-023 + review-next5 F-A3-119: A list, regex set or constant that lives in several n8n nodes or workflows, or in n8n and Java (identity keys, PII patterns, guardrail rules, parked tool names, max tools per turn), has one source and is changed in all copies in the same change, then checked by a script that diffs the copies (n8n_workflows/**, mcp/ParkedMcpToolNames).
- 2026-10-28 review-02-set + F-A1-043/F-A3-059/F-A3-083: Data sent to an LLM, a card or an execution is chosen by an allow-list of field names; a deny-list that stays matches key suffixes (...By, ...Id, ...GUID) and nested values, and both are run over the real field names the tools emit before shipping (02 Pack Narrative Context, 03/04 connectors).
- 2026-10-22 F-A3-006/007/015/016/018/031/032/064/124/126/127/129/139 + F-A1-048: A keyword or regex rule that refuses, reroutes, overrides or rewrites a learner question needs context words (verb plus object), anchored phrases instead of bare words, no blanket "learning word" exemption, and eval cases with real learning questions, idioms and non-English text (n8n 01/02/05).
- 2026-10-22 F-A3-070/073/080/123/061: Text matching in Code nodes uses Unicode letters (\p{L}) and case-insensitive tests: a non-English gate counts non-Latin letters only, emoji strips keep dingbats and ZWJ sequences, title dedupe works for non-Latin titles, text without spaces is clamped by characters (n8n 01/02/04).
- 2026-10-28 review-02-set + F-A1-051/F-A3-097: A new PII or redaction regex is first run over catalog titles, course codes, years and tool ids (bare 00-prefixed digit runs, plain numbers), and covers non-US phone formats and non-English wording (02/05 guardrail copies).
- 2026-10-28 review-next5 (F-A4-025): A guard on writer output (emoji or markup, instruction words, name check, length) is first run against real catalog titles ((c) (R) TM match Extended_Pictographic; "system prompt" is a real course), and each drop reason names the condition tested (placeholder_missing, not real_name) so the live drop rate can be read (03 Read Compose).
- 2026-10-22 F-A3-086/F-A3-105/F-A9-018/F-A9-026: A guardrail, validator or summariser that throws, times out or returns an error body fails closed with a named failure envelope (GUARDRAIL_FAILURE, ASK_FAILED, MCP_UNAVAILABLE) that still carries execution id and token usage; it never passes content on unchecked, kills the turn or streams the raw n8n error (01/02/05, AISearchStreamController).
- 2026-10-20 F-A1-047/F-A3-008/F-A3-011/F-A3-028/F-A3-122/F-A7-025/F-A9-004: A tenant switch (general knowledge, data source, agent, intent, AI off) is enforced where the call or data read happens and on every path a classifier or retry can pick, in Java and in n8n; a check by an English regex at the router alone is not enforcement (01-05, aisearch, mcp).
- 2026-10-20 F-A3-095/F-A3-125/F-A3-134: A write-claim rewrite treats a write as blocked only when it did not run and never rewrites a correct read-only answer; the narrator may say a change was made only when the facts show the write succeeded (02/05).
- 2026-10-22 F-A3-010/F-A3-056/F-A3-068/F-A3-082 + review-next5 item 5: Never spread an inbound or upstream object into a trusted one (userContext, agent output, reply): copy named fields, set trusted fields after any spread, and never let a request-body flag grant trust (n8n 01-05, Java reply builders).
- 2026-10-22 F-A3-130/131/132/138/051: A branch or early return in a prompt-building node still appends the mandatory blocks (safety policy, mode guide, learner preferences); a notice line is added to the mode guide, never replaces it; test every branch (02 Pack Narrative Context).
- 2026-10-20 F-A3-049/F-A3-050: What the narrator is told (widget inventory, omitted fact rows) is decided from the cards actually built, not from the plan (02).
- 2026-10-22 F-A3-029/F-A3-058: A step that drops rows or skips a planned call leaves a counted reason in the item (data.dropped, ID_NOT_RESOLVED) so the answer and meta can say it (02 Build Widgets, Run MCP Plan).
- 2026-10-29 review-next16 F-A3-057: Learner-visible fixed text in n8n Code nodes (fallback titles, thought lines, refusal tables) goes out as a label key `label.aisearch.*` with English only as the fallback, and a refusal table exists once, not copied across 05/02/03 (n8n 01-05).
- 2026-10-23 F-A8-017 + 2026-10-29 review-next16 F-A3-116: After merging or deleting nodes or functions, search all workflows for references (`n8n_node.py find`, a refcheck script); leave no `$('Node')` read of a removed node and no stale sticky (n8n_workflows/**).
- 2026-10-22 F-A3-065: Workflow static data is not per-turn scratch space; state kept across hops is pruned by age and size so concurrent turns do not overwrite each other (02).
- 2026-10-22 F-A3-067: n8n date logic ("today", due, this week) uses the learner's zone from userContext, not the n8n server's UTC clock (02/03; JV7 names Java only).
- 2026-10-22 F-A3-078: A workflow with no userId (or mcpUrl) stops right after Build Context with a VALIDATION_ERROR envelope, before any LLM or tool call, and never guesses a mode (02/04).
- 2026-10-20 F-A3-001/F-A3-113/F-A3-115: Every n8n webhook trigger checks the shared key; orphan workflows (08) are removed or kept off, and test triggers and test workflows are not in production exports (n8n_workflows/**).
- 2026-10-22 F-A3-103/F-A9-001/F-A8-002/F-A8-026/F-A3-106: Per-call timeouts, retries and waits add up to less than the turn deadline (140 s) and the approuter timeout; past a soft deadline optional LLM steps are skipped for a rule-based answer; a tool slower than the default is listed in SLOW_TOOLS with its own timeout (02, aisearch, mcp, approuter).
- 2026-10-22 F-A3-107/F-A8-020/F-A9-017/F-A3-110/F-A5-016: Progress callbacks, usage lookups and optional AI text stay off the critical path: short timeout (800 ms), stop after two failures, estimate on failure, AI text queued after the scan (02/03, aipulse/scan).
- 2026-10-20 F-A4-017/F-A4-021: Guardrail rules cover self-harm, violence and abuse with a supportive reply (not left to the model) and other people's pay and ratings (05).
- 2026-10-22 F-A3-092/F-A3-093/F-A3-099: The output guard runs over every learner-visible string (narrative, card text, follow-ups, progress lines, error text), and Pulse cards pass it (02/03/05).
- 2026-10-29 review-next5 SHOULD 1-2 + review-next16 phase 2 (item 14): A script that patches several workflows or pins hashes runs entirely under the n8n lock, analyses all nodes first, writes nothing when one check fails, and re-pins only with an explicit `--repin` (n8n_workflows/eval/*.py).
- 2026-10-28 review-next5: After patching a Code node the offline harness does not load (03), run `node --check` on the extracted code and grep for duplicate top-level declarations (n8n_workflows/**).

### Java, MCP tools and Pulse backend
- 2026-10-29 review-next16 F1/F2 (F-A2-004): `truncated` is true only when more rows exist: read limit+1 and cut back to limit; where a query class clamps at the tool maximum raise that inner clamp by one; with a filter, `truncated` follows the filtered count (mcp/tool/**, mcp/data/**).
- 2026-10-29 review-next16 F3 (F-A10-004): A WARN with a stack inside a per-card, per-learner or per-label path is rate-limited: first failure WARN with the exception, then at most one per 60 s per site, the rest DEBUG (aipulse/scan/**, aisearch/**, aiconfig/**).
- 2026-10-29 review-next16 F4 (F-A8-031): A cache key uses a bucketed time argument (the day in the learner's zone), never raw epoch ms; a partial or failed read is not stored; on overflow drop expired entries first; a cache over a read that a write changes is short-lived or cleared after that write (mcp/tool/**).
- 2026-10-29 review-next16 (F-A10-006): When merging copies of a helper into a shared one, diff their behaviour first (null, blank, trim vs strip), keep variants that differ, state the rule in the shared Javadoc and pin each replaced copy with a test case (aicommon AiText, McpRows).
- 2026-10-29 review-next16 (F-A10-004): Never put `e.getMessage()` straight into `Map.of(...)` (a null message throws); use `AiText.messageOr` (`**/*Controller.java`).
- 2026-10-22 F-A2-026: Every MCP tool declares readOnlyHint, destructiveHint and openWorldHint (writes marked destructive or idempotent), so n8n does not guess writes from a name prefix (mcp/tool/**).
- 2026-10-20 F-A2-025: A tool that truncates or prunes input says so in its result; never report success for a pruned or cut row (mcp/tool/MemoryMcpTools).
- 2026-10-22 F-A2-040/F-A2-045: Every row a card can act on (enrol, start, open) carries kind, openUrl, launchMode and userAction through `RecommendationOpenLinks` (mcp/tool/**).
- 2026-10-23 F-A2-028/F-A9-015: Tool and client timeouts come from one place (`McpDeadline`, the RestClient config) and a client config never drops its configured timeouts (mcp/**, config).
- 2026-10-22 F-A9-006/F-A9-024/F-A9-005/F-A8-006: A new shared in-memory resource (SSE hub, queue, bulkhead, pool share) has per-user and global caps, a bounded queue, expiry for unused entries, a 429 with Retry-After, and its own executor, never the shared Spring scheduler thread (aicommon, aisearch).
- 2026-10-29 review-next16 phase 2 (F-A5-004): A date-only input (picked end day) is stored and shown as that calendar day, not as an exclusive end instant read back in another zone; background scans resolve the zone from config once per run, never from `UserSessionBean` (aipulse/**).
- 2026-10-20 F-A5-009: A card fingerprint hashes the identity of the item, not volatile counts or text, so a dismissed summary card does not come back as new (aipulse/**).
- 2026-10-28 review-next5 (F-A7-016): A paged list endpoint clamps `page` so page times size fits an int, not only the size (`**/PulseAdminController`, `**/*Controller.java`).
- 2026-10-20 F-A7-011/F-A7-013: Viewing or exporting captured prompts and answers writes an access-log row (who, when, what) and obeys retention (aimonitoring, debug viewer).
- 2026-10-22 F-A7-014: Test connection sends a stored key only to the saved URL, never to one typed in the same request; integration changes write an audit row with secrets recorded as set, none or changed only (aiconfig).
- 2026-10-22 F-A7-021: Monitoring queries count call rows only (CALL_ROWS: USAGE, no parent, not RESERVED, not eval); per-node step rows are summed into their call (aimonitoring).
- 2026-10-27 F-A1-035: A dev-mode or profile switch cannot turn off login or grant a super-admin unless an explicit local profile is active; test and production profiles ignore it (config, security).
- 2026-10-23 F-A9-027: An SSE endpoint sends `Cache-Control: no-cache, no-transform` and `X-Accel-Buffering: no`, keeps the stream alive and honours `Last-Event-ID` (aisearch/AISearchStreamController).

### Widgets and admin UI
- 2026-10-22 F-A5-006/F-A6-004: Widget CSS has no box-shadow and no weight above 600; keyboard focus uses `:focus-visible` (body.ai-kbd), never `:focus` or a JS-driven ring (css/Pulse.css, css/AISearch*.css).
- 2026-10-22 F-A6-001: Every card renderer runs through `Widgets.safeRender`, so one throwing renderer skips only its card and shows a note (static/js/AISearch/**, Pulse/**).
- 2026-10-27 F-A6-025: A widget `fetch` or `EventSource` goes through the shared wrapper that adds token auth, rewrites jsessionid and maps 401 or a login page to SESSION_EXPIRED; no bare `fetch` (static/js/AISearch/**, Pulse/**).
- 2026-10-23 F-A6-013/F-A6-014: Ask and Pulse use their own `label.aisearch.*` keys, never Blend's labels (corrupt in up to 19 locales) (static/js/**, messages.properties).
- 2026-10-23 F-A6-015: Widget CSS uses logical properties (margin-inline-start) and the page sets `dir` from the locale, so Arabic layouts mirror (css/AISearch*.css).
- 2026-10-29 review-next16 F5 (F-A6-020): A button's accessible name starts with its visible label text (label in name); reuse `a11y.labelAndName`, no new key per button (static/js/AISearch/**).
- 2026-10-29 review-next16 (F-A6-020, ui.md): A programmatic focus target (a `tabindex="-1"` heading) gets its own `:focus-visible` ring with higher specificity than Bootstrap's `[tabindex="-1"]:focus{outline:0!important}`; announce an error through the assertive live region and move focus to the heading after retry (static/css/AISearch.css, AISearch.profile.js).
- 2026-10-28 review-next5 (F-A7-016): In a growing or paged UI5 table, Save reads the model, not the rendered rows (static/view/**, static/controller/**).
- 2026-10-29 review-next16 phase 2 (item 15): A paged admin list sorts by last changed and returns to page 1 after save, so the edited row is row 1 and is not lost on another page (AIPulse.controller.js, PulseOrgMessageService).

### Work process
- 2026-10-28 review-02-set (MUST 2, SHOULD 1): Every key or field an acceptance criterion names (tenantid, tenant_id) is implemented, or its omission is recorded in a change card; when a fix lands in a different node or file than the spec or design names, record it in decisions.md or status.md (.claude/work/**).
- 2026-10-28 review-02-set (F-A2-042, F-A3-072): Tracker findings go stale (cited nodes, lines and premises moved after the Ask-smarter merge); re-check each location and premise at HEAD before building and close stale ones with evidence (.claude/work/**).
- 2026-10-29 review-next16 phase 2 (review-p2 SHOULD 2): Update or remove a comment or Javadoc the change makes false; no stacked Javadocs, no "A new message goes to the first page" left above code that now does the opposite (all code).

## Already covered
- F-A1-011, F-A1-012 monitor and remarks endpoints without a role check -> checklist.md:83 (RE2)
- F-A1-013 no CSRF defence on AI write endpoints -> checklist.md:209 (CF3)
- F-A1-018/019/021/022, F-A2-022, F-A2-036 SQL literals, LIKE and CONTAINS not escaped or bound, unbounded readers -> checklist.md:101-102 (MC2, MC3), rules/mcp-tools.md:11
- F-A1-020 IN-lists not chunked -> checklist.md:102 (MC3)
- F-A1-024 raw-HTML helper parameters -> checklist.md:150 (WG1); F-A6-018 card type and label template in HTML -> checklist.md:150 (WG1)
- F-A1-025, F-A3-060, F-A6-002 link sinks without scheme check -> checklist.md:151 (WG2)
- F-A1-028 webhook key readable in the config feed -> checklist.md:69 (JV6), :207 (CF1)
- F-A1-005, F-A1-045, F-A1-052, F-A2-031 learner text or ids in logs; review-next16 SHOULD 1 (ids in new WARNs) -> checklist.md:52 (AL4)
- F-A1-009, F-A3-059 other people's ids to n8n and the LLM -> checklist.md:91 (RE10), :100 (MC1), :189 (NW9)
- F-A1-016 card actions not audited -> checklist.md:108 (MC9); F-A1-017 duplicate protection per instance -> :55 (AL7), :89 (RE8)
- F-A1-023, F-A3-036, F-A3-037, F-A3-071 data text not fenced in prompts -> checklist.md:184 (NW4); core:158 (LL1)
- F-A1-055 role read from model arguments -> checklist.md:50 (AL2), :85 (RE4), :182 (NW2)
- F-A2-003 enums ignored silently -> checklist.md:103 (MC4); F-A3-022 argument validation fails open -> :183 (NW3)
- F-A2-005 overlapping tools -> checklist.md:110 (MC11); F-A2-007, F-A2-009 description size -> rules/mcp-tools.md:10
- F-A2-012 server clock instead of user zone (Java) -> checklist.md:70 (JV7)
- F-A2-014, F-A2-015, F-A5-008 hidden or inactive content (MCP and Pulse sources) -> checklist.md:104 (MC5)
- F-A2-016, F-A10-016, review-next16 AC6.1 scans (empty catch, Map.of with message) -> checklist.md:51 (AL3), rules/mcp-tools.md:12
- F-A2-021, F-A2-029 result sets without a cap -> checklist.md:105 (MC6), :120 (DA3); review-next5 SHOULD 9 (DISTINCT list without cap) -> :120 (DA3)
- F-A2-023, F-A5-010 team check missing, manager cards name wrong people -> checklist.md:100 (MC1)
- F-A3-002, F-A3-005, F-A9-020 hard-coded workflow ids, hosts from the request -> checklist.md:188 (NW8), :210 (CF4)
- F-A3-003 deployed workflows vs repo -> rules/n8n.md:10 (wfrev)
- F-A3-035, F-A3-090, F-A6-006, F-A5-013 product name reaches learners -> rules/ask-pulse-widgets.md:18
- F-A3-045, F-A3-047 personal data in executions or Wikipedia call -> checklist.md:189 (NW9); core:163 (LL6)
- F-A3-013, F-A3-061, F-A3-084 LLM output parsed by substring or clamped -> core:161 (LL4), :162 (LL5)
- F-A3-054, F-A3-104 no error boundary, planner error becomes a direct answer -> checklist.md:181 (NW1), :185 (NW5), :51 (AL3)
- F-A3-076 incoming message length cap -> checklist.md:87 (RE6)
- F-A3-102, F-A3-109 token metering gaps -> checklist.md:187 (NW7)
- F-A3-041, F-A3-100, F-A4-015 reply language -> checklist.md:193 (NW13), :161 (WG12)
- F-A4-002 harness reads other key names than 07 returns -> checklist.md:53 (AL5)
- F-A4-013, F-A4-014 grounding, counts and dates equal the card -> checklist.md:186 (NW6)
- F-A4-022 quota error blames the organisation -> checklist.md:90 (RE9)
- F-A5-002 late AI text write overwrites a dismiss -> checklist.md:122 (DA5)
- F-A5-003 failed "done" save is silent -> checklist.md:154-155 (WG5, WG6)
- F-A6-003 CSV formula injection -> core:148 (IN6)
- F-A6-007 plurals follow English -> checklist.md:203 (LB5); F-A6-016, F-A6-017, F-A7-028 English strings -> :201-202 (LB3, LB4)
- F-A6-019, F-A6-022 script not loaded, stale ?v= tags -> rules/ask-pulse-widgets.md:13-14
- F-A6-026, F-A10-012, review-next5 SHOULD 11 (LF in a CRLF file) -> checklist.md:57 (AL9)
- F-A7-002, F-A7-004, F-A7-005, F-A7-006 history atomic, double submit, quota races -> checklist.md:122-123 (DA5, DA6), :125 (DA8), :133 (DA16)
- F-A7-007 ledger without indexes -> checklist.md:129 (DA12); F-A7-030 120-minute cache -> :212 (CF6); F-A7-032 plan code to every user -> :91 (RE10)
- F-A8-012, F-A8-013, F-A8-015 query per row -> checklist.md:121 (DA4); F-A8-028 unbounded goals cache -> :73 (JV10); F-A8-022 dossier on another node -> :55 (AL7)
- F-A9-007 job without cluster lock -> checklist.md:137 (JB1); F-A9-008 unbounded pools -> :141 (JB5); F-A9-025 STREAMABLE mode -> rules/mcp-tools.md:14
- F-A9-015 RestClient drops timeouts -> checklist.md:54 (AL6)
- F-A10-013/014/015 JSON column, hand-written DDL, native-SQL writes -> rules/java-backend.md:11-12, rules/mcp-tools.md:11
- review-next16 SHOULD 2 (clamp edits in Yogesh's data package missing from D7) -> AGENTS.md hard rule 10 as cited in review-next16/review-rules.md (Blend AGENTS.md not re-read; line not checked)
- review-next16 rules 6 (tools-inventory.md not updated) -> rules/mcp-tools.md:16. Conflict to settle: the rule says same commit, Zakvan's standing rule says docs in one pass at release.
- review-next16 rules 7 (no test run on record) -> checklist.md:56 (AL8)
- review-02-set F-A3-108 (Greeter without JSON format) and F-A3-069 (no consumer for failFast) went to Yash as exact node diffs -> rules/n8n.md:12; model settings in the handoff -> checklist.md:192 (NW12). Not yet closed, so no lesson.

## Checklist candidates
Five lessons that cost the most findings, or the most serious ones, and are general. Proposed new MUST items:
1. n8n workflows, NW14 MUST: a tenant switch (general knowledge, data source, agent, intent, AI off) is enforced where the call or data read happens and on every path a classifier or retry can pick, in Java and n8n. (7 fixed findings, 3 high or critical.)
2. n8n workflows, NW15 MUST: a keyword or regex rule that refuses, reroutes, overrides or rewrites a learner question needs context words, anchored phrases and eval cases with real learning questions, idioms and non-English text. (13 fixed false-refusal and false-route findings.)
3. Always, AL11 MUST (extends AL10): a list, regex set or constant copied across n8n nodes, workflows, or n8n and Java has one source and is changed in all copies in the same change, checked by a diff script. (identity keys, PII rules, parked tool names, guardrail rules.)
4. MCP tools, MC14 MUST: `truncated` is true only when more rows exist (read limit+1, cut back to limit; with a filter, follow the filtered count). MC10 only says "truncation flag matches siblings". (13 tools fixed; the planner tells the learner a list is partial.)
5. Java backend, JV14 MUST (extends JB5): a new shared in-memory resource (SSE hub, queue, bulkhead, pool share) has per-user and global caps, a bounded queue, expiry for unused entries and its own executor. (One user could lock everyone out of the live-progress hub.)
