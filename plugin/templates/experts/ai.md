# Where this repo uses AI

Read by `ai-engineer` next to the generic reference (`${CLAUDE_PLUGIN_ROOT}/reference/domains/ai.md`). Keep it to facts
with `path:line`. No keys, endpoints with secrets or personal data: name the config key only. Delete this line
and the hints in brackets when you fill it in.

## Areas and pipeline
| Feature or turn | Steps (model per step, tools called) | Prompt location | Code (`path:line`) | Owner |
|---|---|---|---|---|
| (for example answer a question) | (route, plan, tool calls, narrative) | `<file or node>` | `<path>:<line>` | |

## Clients, models and config
- Model clients and the one place that makes a call: `<path>:<line>`
- Models or deployments per step (names as in config), temperature and max tokens: `<where they are set>`
- Config keys for endpoints and keys (names only): `<keys>`
- Price list and volume assumptions in use (source URL and date): `<url> <date>`

## Tools and data
| Tool or data source | Returns | Caller-scoped? | Row and text cap | Code |
|---|---|---|---|---|

## Quota, cost and monitoring
- Where tokens are recorded per call (ledger table or service): `<path>:<line>`
- Quota or allowance rules and kill switch: `<path>:<line>`
- Monitoring, stage timings, debug capture and who can open them: `<where>`
- Retention of captured AI content and leaver erasure: `<path>:<line>`

## Evals
- Offline cases: `<command>`, cases at `<folder>`
- Replay against the live pipeline or a test lab: `<command or URL name>`
- Judge rubric and agreement check: `<where>`
- Pass bar the team uses: `<bar>`

## Guardrails and fallbacks
- Input and output checks, grounding rules, fallback text, kill switch: `<where>`

## Known traps and weak spots
- (for example prompts duplicated across routes, no token row on one path, unbounded tool result)
