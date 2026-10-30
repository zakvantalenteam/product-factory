# n8n - generic knowledge for `n8n-expert`

Read by `n8n-expert` (and by any agent planning work on an n8n workflow). Where this repo uses n8n (workflows,
owners, the node tool, eval commands, contracts, checklist ids) lives in `.claude/experts/n8n.md`. Facts that depend
on the n8n version or a node option are checked on docs.n8n.io before they go in a plan.

## Items and data
- A node runs on a list of items; each item is `{json, binary}`. Paired items link an output item to its input
  item; a Code node that builds new items must keep `pairedItem` or later `$('Node').item` lookups break.
- Code node modes: run once for all items (`$input.all()`) or once for each item (`$input.item`). Work per item in
  a loop of LLM or HTTP calls multiplies time and cost.
- Expressions: `$json` (current item), `$('Node').item` / `.first()` / `.all()`, `$input`, `$vars` (instance
  variables, the place for hosts and settings) versus `$env` (often blocked on cloud plans). An expression runs once
  per item.
- Static data persists between executions of one workflow (production only, not in manual runs); pinned data is for
  testing and must not stay on a production workflow.

## AI nodes
- AI Agent (tools agent) calls tools in a loop; each turn is an LLM call. Basic LLM Chain is one call. Chat model
  sub-nodes carry the model, temperature, max tokens, timeout and retries; a structured output parser validates the
  shape (and may retry with the model).
- Tools: MCP Client tool, HTTP Request tool, Call n8n Workflow tool. Tool arguments come from the model: validate
  them in the tool (type, range, the caller's own data) before use.
- Memory sub-nodes keep chat history per session key; the key must come from the session, never from the model.
- Token use is read from the model's response metadata; log one usage row per LLM call where the repo tracks quota.

## Flow control and sub-workflows
- Execute Workflow (sub-workflow): wait for it or not, input mapping, the sub-workflow's own timeout and error path.
- Merge (append, combine by key or position, wait for both inputs), Switch, If, Loop Over Items (batch size),
  Wait (time or webhook resume), Respond to Webhook (when the caller gets the answer).
- Calls that do not depend on each other can run in parallel branches and merge; in series they add up.

## Reliability
- Node settings: Retry On Fail (tries, wait between), On Error (stop workflow, continue, continue with error
  output). Retries must be bounded; a non-idempotent call (a write, a message) must not be retried blindly.
- Workflow settings: timeout, error workflow (Error Trigger) for alerts, save execution data on error.
- A failed tool or model call must end in fallback text the user can read, never an empty reply or a raw error.

## Runtime
- Webhooks: production versus test URL (the test URL works only while the editor listens), header auth, response
  mode (immediately, when the last node finishes, Respond to Webhook node), streaming responses where the version
  supports it.
- Queue mode: a main instance, workers and Redis; concurrency per worker and plan limits on n8n Cloud. Long
  executions hold a worker slot.
- Execution data: saved per workflow setting (success, error, manual) and pruned by age; saved executions hold every
  item, so personal data and prompts in them need a retention rule.
- Credentials are referenced by name and id in the export, never by value; exports kept in git need the ids
  scrubbed or mapped per environment. Workflow history keeps earlier versions in n8n for rollback.

## Speed
- Where time goes: LLM calls in series, tool calls in series that could run in parallel, a large prompt, a large
  model for a simple step, high max tokens, Code node work per item, waiting on slow outside calls without a timeout.
- First words: stream the final answer when the caller supports it; send a short early status when it does not.
- Measure with execution timings per node (the execution log) before and after; never guess.

## Traps to check in a review
- Input that is null, empty or an error object from the previous node; `$('Node')` on a node that did not run.
- No timeout or unbounded retries; retries on a write; no fallback text.
- Secrets, hosts, workflow ids or user ids as literals in node code or parameters; `$env` where `$vars` is meant.
- User id or tenant taken from the model or the request body instead of the session context.
- A new route that skips the repo's guardrail step; tool arguments from the model used unchecked.
- An LLM call without its usage row; personal data in prompts or saved executions without need.
- Callback field names or payload shape changed without the app side; a revision stamp not updated.
- An export reformatted (whole-file diff) instead of a node change; pinned data left on.
