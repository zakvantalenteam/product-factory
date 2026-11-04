# Where this repo uses n8n

Read by `n8n-expert` next to the generic reference (`${CLAUDE_PLUGIN_ROOT}/reference/domains/n8n.md`). Keep it to facts with
`path:line`. No secrets, hosts, workflow ids, user ids or personal data: name the key or variable only.
Delete this line and the hints in brackets when you fill it in.

## Workflows
| Workflow | Export file | Trigger (webhook, schedule, sub-workflow) | Job | Owner |
|---|---|---|---|---|
| (for example the chat router) | `<path>` | webhook | (routes a question to the right workflow) | (the person who changes it) |

## Split between the app and n8n
- What the app does (for example: tool server, stores results) and what n8n does (orchestration, LLM calls, routing).
- Calls from the app to n8n (`path:line`, payload shape) and callbacks from n8n to the app (endpoint, field names,
  auth header name).
- Models per workflow step (model sub-nodes) and where token usage is recorded.

## Tools and commands
- Node tool (read and change one node without opening the export): `<command>` with its list, find, show, extract,
  patch and diff forms; or "none: read node line ranges".
- Revision stamp: `<command>` (write and check).
- Offline eval: `<command>`; cases in `<path>`. Live replay for the main session: `<command>`.
- What the guard blocks (for example reading or editing the export JSON directly).

## Rules and checklist ids
- The repo's n8n rules file and skill: `<path>`.
- Checklist ids for an n8n review (for example NW1-NW10) and where they are defined: `<path>`.
- Who may change which workflow, and when a D7 card and a handoff are needed instead.

## Rollout
- Import order between workflows, the app side that must ship first, rollback (previous export, workflow history).
- Never run: `<deployment scripts>`.

## Known traps and weak spots
- (for example calls in series that could run in parallel, a missing timeout, personal data in saved executions)
