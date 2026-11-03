# Practice pack: n8n-expert

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## AWS GenAI Developer Pro: agents, RAG, fallbacks and evals inside n8n
- RAG: for Ask, run the vector store node in Get Many mode on every turn before the LLM; use the as-tool mode only when the model must decide whether to search.
- RAG: insert and query with the same embeddings model and dimensions; a new embeddings model means a full re-index into a new table, then a switch.
- RAG: set the metadata filter (tenant, language, active) in the vector store node itself, not in a later Filter or IF node.
- RAG: keep retrieval in its own sub-workflow so the recall@k eval runs on it without an LLM call.
- RAG: re-index changed courses only (content hash in metadata) and delete their old chunks first.
- Agent: set Max Iterations to the loop cap in ai.md; at the default a confused agent makes up to 10 model calls.
- Agent: few tools per agent; each a sub-workflow tool with a typed input schema and a description that says when to use it and when not.
- Agent: `$fromAI()` only for values the model may choose (query text, filters); user id, tenant and language come from the trigger payload.
- Agent: a tool sub-workflow returns an error item with a short reason instead of failing, so the agent can recover inside the loop cap.
- Agent: structured output through the agent's output-format option and a Structured Output Parser; the auto-fixing parser is one more model call per failure.
- Memory: session key from the app (user plus conversation id); in queue mode Postgres or Redis chat memory, never Simple Memory.
- Model sub-node: set max tokens, temperature, timeout and max retries (where the node offers them) to the budget in ai.md.
- Fallback: On Error "Continue (using error output)" on agent, LLM and tool nodes; the error branch returns the agreed fallback payload to the app.
- Fallback: Stop and Error with a code and a plain message when a guard fails, so the error workflow and the app see the cause.
- Webhook: Respond to Webhook as soon as the answer exists; a node that fails after it needs a callback, the app never sees that error.
- Webhook: Header Auth or JWT Auth on every webhook the app calls.
- Rate limits: the HTTP Request Batching option, or Loop Over Items with a Wait node, to stay under a provider's per-minute limits.
- (SAP) Generative AI hub calls: HTTP Request node with an OAuth2 client-credentials credential and the `AI-Resource-Group` header.
- Evals: n8n Evaluations: an Evaluation Trigger feeds the golden set, the Evaluation node records outputs and metrics, and its "check if evaluating" branch skips callbacks and writes.
- Evals: keep the golden set in the repo too; quote the run's metrics and the workflow revision in the handoff.
- Privacy: mask learner names and emails in a Code node before any LLM node; pass only the fields the answer needs.
- Privacy: executions save every node's input and output, learner questions included; for Ask, do not save successful production executions, keep failed ones.
- Queue mode: the main instance and every worker share one N8N_ENCRYPTION_KEY; binary data in database or S3 mode, not filesystem.
- Rollout: run the changed workflow on recorded inputs (pinned data is used in manual runs only), then switch the active version; rollback is the previous export.

## Traps
- Retries stacked: model Max Retries times node Retry On Fail times the app's retry; keep retries in one layer.
- Retry On Fail retries every error, 4xx included: for HTTP calls set the Never Error response option and branch on the status code.
- `.first()` in a multi-item run gives every item the first item's data: one learner's context in another learner's answer.
- A Code node that builds new items without `pairedItem` breaks `$('Node').item` downstream.
- Error workflows do not run for manual executions; test the error path with a production webhook call.
- Simple Memory in queue mode loses the conversation when the next call lands on another worker.
- Vector store insert appends: re-inserting a course duplicates its chunks and crowds the top k.
- A test webhook URL in app config answers only while the editor listens; the app needs the production URL.

## Numbers
- Retry On Fail defaults: Max Tries 3, Wait Between Tries 1000 ms; raise the wait for 429, 1 s is short against a per-minute limit.
- AI Agent Max Iterations default 10; our default cap 5 unless ai.md sets another.
- EXECUTIONS_TIMEOUT default -1 (no limit), EXECUTIONS_TIMEOUT_MAX default 3600 s: set a workflow timeout on Ask.
- Saved executions are pruned after EXECUTIONS_DATA_MAX_AGE, default 336 h (14 days), or past EXECUTIONS_DATA_PRUNE_MAX_COUNT, default 10,000.
- Queue mode worker concurrency default: 10 executions per worker.
- Turn defaults unless ai.md sets others: read-tool timeout 5 s, turn deadline 30 s, first words 5 s.
