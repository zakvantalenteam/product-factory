# AI engineering reference (generic)

Read by `ai-engineer`. It holds what holds for any LLM feature. Where this repo calls models (clients,
deployments, prompts, tools, quota, eval commands) lives in `.claude/experts/ai.md`. Numbers are measured or
computed with the method stated; a price, limit or model name is read from the provider's own page on the
day and dated (never from memory). This file is core-owned: the expert proposes additions in its output file.

## 1. The AI job first
Who asks what, what a good answer contains, what must never happen (another person's data, an invented fact, a
write without a user action, personal data leaving the product, a blank or endless wait). Write it in 2-3 lines
before any model talk. Ask whether a template, a query or a rule gives the answer without a model.

## 2. Model per step
- One model per step, chosen by what the step needs: a small, fast model for routing, extraction,
  classification and short summaries; a larger one only where an eval shows it wins.
- Temperature low for planning and JSON; max output tokens sized to the real output; structured output
  (a schema) for anything a program parses; a stable system prefix first so provider prompt caching applies.
- Pin model and version per step in config, not in code; changing one is a change with an eval run.

## 3. Prompts
- One job per prompt. Rules stated once; no prompt contradicts or duplicates another (own-data rule, language,
  output format, tone). Say the size change in tokens when a prompt changes.
- Data is fenced as data: user text, titles, documents, comments, goals and database text sit in a delimited,
  length-capped block the model is told to treat as content, never as instructions. A prompt change never
  drops an own-data or safety rule.
- Few-shot examples only when an eval case proves they help. Version prompts so a regression can be traced.

## 4. Tool design
- The planner picks tools from their descriptions, so a description is a prompt: what it returns, when to use
  it, when not, the real argument defaults, limits and formats. No two tools claim the same question.
- Arguments the model builds are validated server-side (type, enum, range, limit, date format, ids owned by the
  caller) and a bad value returns a clear error object, not a stack trace.
- A tool that changes data cannot be fired from free text alone: an explicit user action (confirm click, card
  action) is part of the path; writes are idempotent and audited.
- Return only the fields the answer needs, with a row and text cap that fits the token budget and a truncation
  flag; an empty result and a failed read are different outcomes.

## 5. Context and token budgets
- Tokens in and out per call, calls per turn, turns per user per day. Cut: drop fields no answer uses, cap
  history, summarise old turns, retrieve fewer and better chunks, shorten tool results.
- Cost per turn = sum over calls of (input tokens x input price + cached input tokens x cached price + output
  tokens x output price) / 1,000,000. Cost per month = cost per turn x turns per day x working days x active
  users. State the volume, the price page URL and the date next to every figure.
- Estimates say how they were made (counted from a capture, or tokens ~ characters / 4 for English text).

## 6. Caching
- Provider prompt caching: keep the long stable part first and byte-identical; put per-user data last.
- Result caching: key by everything that scopes the answer (user, role, language, tenant, data version), with a
  size bound and a time limit, safe with more than one instance. A key without the user can serve one person's
  answer to another.
- Deterministic shortcuts: answer from a template or a query when the question is fully structured.

## 7. Latency
- Budget: first words of an answer (default 5 s) versus the full answer. Stream the narrative; run independent
  tool and model calls in parallel; never an LLM call on a request thread without a timeout; long or bulk
  generation runs as a job with status; skip the model when a template is enough.
- Per step seconds are measured from timings or a capture; mark estimates.

## 8. Quality and evals
- "Smarter" needs a number. Build an offline case set (intent x role, plus the failure that motivated each
  case) with an expected outcome: intent, tools called, widgets or fields returned, `mustNot` lines, a latency
  ceiling. Add a replay against the live pipeline for a sample, and an LLM judge with a written rubric whose
  agreement with a human sample is measured before it is trusted.
- Pass bar: no high-priority case lost, judge score not lower, latency not worse. Quote the run in the handoff.
- A new intent or route has at least one case before it ships.

## 9. Guardrails and fallbacks
- Input checks (policy, injection) and output checks (grounding, privacy) on every route; a new route or branch
  never skips them.
- Grounded answers only: no invented records, dates, people, links or numbers; counts and names in the text
  equal those in the card; an empty tool result is said so.
- Failure: every outside call has a timeout, a bounded retry and fallback text that says what is missing; a kill
  switch turns the feature off without a restart; a quota hold is released on every failure path.

## 10. Memory and personalisation
State what is stored, for whom, for how long, how a user sees and clears it, and that it is covered by the
retention job and leaver erasure. Never store more than the feature uses.

## 11. Observability and privacy
- Record per turn: model, tokens in and out, seconds per step, tool calls, outcome, error. Every LLM call writes
  its token row to the usage or quota ledger.
- Logs at INFO and above never hold prompts, answers, tokens or keys. A debug capture is admin-only, time-boxed
  and retained briefly.
- Send the provider only the fields the answer needs: no e-mail, phone, other people's ids or sensitive HR
  fields. Keys travel in headers from config, never in a URL or log.

## 12. Orchestration safety
- Deterministic or LLM, per step: code for whatever a rule, query, template or schema decides (routing on a known
  field, permission checks, totals, dates, formatting, every write); a model only for language, judgement or
  fuzzy matching, and its output is checked by code before anything uses it.
- Tool routing: one tool per kind of question; a model router has an eval case per route and a default route
  for "none fits".
- Structured outputs: a schema for every output a program reads; a parse failure gets one bounded repair try,
  then the fallback.
- Context propagation: user, role, tenant, language and request id travel explicitly through every step and
  async hop (never read from a thread-local on a worker thread); each step gets only the fields it needs.
- Timeouts per call and for the whole turn. Retries bounded in count and total time, only on retryable errors
  (timeout, 429, 5xx), with backoff; a retry never repeats a write.
- Idempotent writes: each write carries a key, so a retry or a replay cannot duplicate it.
- Loop limits: a cap on planner rounds, tool calls and tokens per turn; reaching it ends with a clear answer,
  not a silent stop.
- Human approval: a write, an outbound message or an irreversible action waits for an explicit user action;
  the model proposes, the person confirms.

## 13. Retrieval and grounding
The project's rules win over this section: where AGENTS.md or `.claude/experts/ai.md` says where content may
come from (one tool, no embeddings, no rows added or dropped), follow that and use only the parts below that fit.
- Search kind: keyword (exact terms, codes, names), vector (meaning, paraphrase) or hybrid (both, merged by
  rank), chosen by the query mix in the eval set.
- Chunking: by the document's own structure (heading, section, record), sized to the answer, with title and
  source kept on each chunk; overlap only when an eval shows answers lost at the cuts.
- Embeddings: one model and version per index, recorded; a model change re-embeds everything; never mix
  vectors from two models.
- Reranking: on the top N only when it lifts retrieval scores in the eval; count the latency it adds.
- Metadata filters (tenant, language, date, type, status) run in the query, before ranking.
- Permission-aware retrieval: the user's access is a filter in the query itself; never retrieve first and
  filter in the prompt.
- Grounding: the answer uses only retrieved items and can name them; a claim with no source is dropped or said
  as unknown; an empty retrieval is said so.
- Retrieval quality: recall@k and precision@k (or hit rate and MRR) on a labelled query set, measured before
  and after any change to chunking, embeddings, filters or ranking.

## 14. Eval types and thresholds
Baseline first: run today's version through the evals before changing anything, and compare every result with
it. Keep the types apart, because one blended score hides a regression:

| Type | Proves | Example threshold |
|---|---|---|
| component | one step does its job (router, extractor, retriever, prompt) | router accuracy not below baseline, 0 high-priority misroutes |
| end-to-end | the whole turn answers the case | pass rate not below baseline, judge score not lower |
| regression | nothing that passed now fails | 0 high-priority cases lost |
| safety | the never cases hold (other people's data, injection, invented facts, writes without a user action) | 0 failures |
| production | live numbers after release | error rate, P95 and cost per successful task within budget for 7 days |

Every material recommendation names the eval that validates it and its threshold, set before the run. Add no
eval that would not change the decision; reuse the project's existing eval commands and quality gates first.

## 15. Budget metrics
Mark every number: measured (capture, timing or monitoring; say where), calculated (from measured numbers by a
stated formula), estimated (by a stated method, for example characters / 4) or assumed (a stated guess to
confirm). A figure that mixes kinds says so.
- Latency: P50 and P95 per step and per turn (say how many runs), time to first token, total time.
- Tokens in and out per call; retries per turn and the cost and seconds they add.
- Cost per successful task = cost of all attempts (retries, failed turns, repair and judge calls) / tasks that
  succeeded. A cheaper call that fails more often can cost more per success.
- Cost per month at a stated volume (section 5).

## 16. Traps to check first
A model or max-token change with no numbers; no baseline before a change; a threshold set after the run; LLM
calls in series that could run in parallel; a model doing what code could decide; a prompt that drops the
own-data rule or duplicates another; unfenced data; parsed output with no schema; no token row; a cache without
user or language in its key; a tool description that misroutes; no fallback text; no eval for a new intent;
retrieval filtered after the fact instead of in the query; personal data in a prompt or a log; an unbounded tool
result; a retry loop with no bound; a write a retry can repeat.

## 17. Sources of truth
The provider's price page and model list (read on the day, date it), the provider's rate-limit and context
documentation, and the repo's own capture, monitoring and ledger numbers.
