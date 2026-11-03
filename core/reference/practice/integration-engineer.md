# Practice pack: integration-engineer

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## MuleSoft Integration Architect and EIP: style, reliability and the pattern per flow
- Pick the style from the need: request-reply when the user waits and the target answers inside the budget; a scheduled batch delta for bulk sync; events when two or more consumers react to the same change.
- Layers (system, process, experience) in our size: one adapter class per outside system hides its API, paging and quirks behind our own types; a separate deployable per layer only when two or more consumers reuse it.
- A canonical data model only when three or more systems exchange the same object; with two, map directly (message translator).
- Reliable acquisition: an inbound webhook or callback is stored durably before the 2xx reply and processed afterwards, so a crash after the reply loses nothing.
- No distributed transaction: write the business change and the outgoing message in one local transaction (outbox table); a job sends it and marks it sent; the receiver is idempotent.
- Delivery: at-least-once plus an idempotent receiver; at-most-once only for messages we can afford to lose (a notification).
- Keep processed message ids at least as long as the sender may retry, under a unique constraint, with a cleanup job.
- Ordering: apply an update only when its source modified time is newer than the stored one; arrival order is not source order.
- Splitter and aggregator: a correlation id and a completion rule (expected count or a timeout).
- Claim check for big payloads: store the file or text and pass its id between steps (workflow callbacks, AI flows).
- Content enricher: fetch the extra data in one batched call per page, never one call per record.
- Process manager for multi-step flows with waits: the state lives in a table with a status per step, never in memory.
- Wire tap for audit or debug copies without changing the flow; the copy follows the same personal-data rules.
- Batch: chunk, commit per chunk, error per record, resume from the checkpoint, report the counts at the end.
- Stream large responses and files; never hold a full export in memory.
- Our API for a third party: contract first, a client id or OAuth client per consumer, a rate limit and quota per consumer, payload size limits.
- Contract changes are additive; a breaking change gets a new version that runs side by side until every consumer has moved.
- Operations: endpoints and credentials per environment as config, a test-connection action, and a replay of parked messages once the cause is fixed.

## SAP Integration Developer (C_CPI): Cloud Integration and API Management
- (SAP) Use Cloud Integration when a flow routes or maps between several systems, or the customer's integration team must run and monitor it; one backend calling one system goes straight through a destination.
- (SAP) Every integration process has an exception subprocess that sets a clear error, parks the message and alerts; no silent end.
- (SAP) Guaranteed delivery and retry through JMS queues (JMS adapter) with a retry interval and a maximum; queue capacity comes with the tenant's licence, so count the queues you add.
- (SAP) Idempotent Process Call with the message id to skip duplicates; Write Variables to keep the last delta timestamp.
- (SAP) Externalise every address, credential alias and schedule, so one iFlow moves from dev to test to prod by transport without edits.
- (SAP) Credentials as security material (user credentials, OAuth2 client credentials, keystore entries) referenced by alias; never in a parameter or a script.
- (SAP) Mapping: graphical message mapping for field to field; XSLT for XML restructuring; a short Groovy script only for logic the others cannot express, with a test.
- (SAP) Never attach full payloads to the message processing log in production: it puts personal data into monitoring; trace only for a short, named investigation.
- (SAP) API Management policies in front of APIs exposed to third parties: API key or OAuth check, spike arrest, quota, JSON or XML threat protection; not for internal app-to-app calls.
- (SAP) On-premise targets through Cloud Connector, with a location id when one subaccount has several connectors.

## Traps
- Retrying a non-idempotent POST after a timeout: the first call may have worked; fix: an idempotency key, or look up by natural key before creating.
- Delta checkpoint taken from our clock or the run start misses rows changed during the run; fix: the highest source modified time read, minus an overlap window, with idempotent upserts.
- Deletes and leavers are invisible to a modified-since delta; fix: a deletion feed, an end-date check, or a periodic full id reconciliation.
- Paging by `$skip` over a set that changes during the run skips or repeats rows; fix: a stable sort on a unique key, the server's next link, or snapshot paging.
- Building the next page URL yourself next to the server's next link double-skips; fix: follow the next link exactly as given.
- `$expand` on a large navigation multiplies payload and time; fix: `$select` inside the expand, or a second batched query.
- An OData `$batch` changeset is all or nothing, the batch as a whole is not; fix: read the result of every part.
- OData v2 lists sit in `d.results` with `$inlinecount=allpages`; v4 uses `value` and `$count=true`; a parser written for one breaks on the other.
- An aggregator or wait step without a timeout: one lost message blocks the flow forever.
- A 401 from an expired token counted as a transient error burns the retries; fix: refresh the token once, retry once.

## Numbers
- Never retry 400, 403, 404, 409 or 422; 408 counts as transient; 401 gets one retry after a token refresh.
- Backoff example: about 1 s, 2 s, 4 s with random jitter, capped by the caller's wait budget.
- Delta overlap window: a few minutes (for example 5 min), more than the largest expected clock skew between systems.
