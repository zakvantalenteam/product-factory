# Practice pack: ai-engineer

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## AWS GenAI Developer Pro: retrieval, agents, safety and cost for Ask
- Order of work: retrieval eval first, prompt second. If the right course is not in the top k, no prompt change fixes it.
- Retrieval eval: a labelled set of query to expected course ids; report recall@k and MRR per language and per intent.
- Chunk by the catalogue's own structure (one course or one section per chunk); keep course id, language, status and tenant as metadata.
- Filter by tenant, language, active status and learner visibility inside the vector query, never after top-k.
- Hybrid search (keyword plus vector) when learners type codes, product names or acronyms; vector alone misses exact terms. Cost: a second index and a fusion step.
- Rerank only when precision at the shown k is the measured problem; it adds a model call and latency to every turn.
- Below a similarity floor, answer "no matching course" from a template with no LLM call; tune the floor on the eval set.
- Check every course id in the answer against the retrieved set in code; drop or flag any other id.
- Agent turn: a loop cap, a timeout per tool call and one deadline for the whole turn; when one fires, return the best partial answer plus fallback text and log which limit fired.
- Tool errors go back to the model as a short structured result, not an exception; retry only reads and idempotent writes.
- Ask gets read-only tools; a write (enrol, assign) needs the learner's explicit confirmation in the UI (OWASP LLM06 excessive agency).
- Fallback chain per step: retry the same model on 429, 5xx or timeout, then a second model or a template answer, then a plain message; never a raw error.
- Prompt order: stable part first (system prompt, tool definitions, examples), variable part last, so prefix caching hits.
- Semantic answer cache key: tenant, language, catalogue version and the learner's visibility scope; a hit across scopes leaks courses.
- Per-user and per-tenant daily token quota against runaway cost (OWASP LLM10 unbounded consumption).
- Re-embed only changed courses (content hash); a new embedding model means a full re-index, vectors from two models do not compare.
- Batch APIs for offline jobs (tagging, re-index), never for an interactive turn.
- EU: model endpoint in an EU region under a DPA; tell users the answer comes from an AI (EU AI Act Art. 50).
- Roles: the system message holds the rules and the data fence, the user message only the user's question, assistant messages only few-shot examples.

## Google ML Engineer: baselines, eval design and monitoring
- Beat a baseline first (keyword search or a rule) and report the gain over it, not only an absolute score.
- Keep the golden set apart from the cases you tune prompts on; a case you tuned on proves nothing.
- Golden set: versioned in the repo; each intent, each supported language, no-answer, injection and personal-data cases; it must pass for every prompt, model, retrieval or tool-description change.
- Separate bars for retrieval (recall@k, MRR), generation (faithfulness to sources, relevance, correctness) and safety (refusals, leaks).
- LLM judge: fixed judge model and rubric version, checked against human labels before you trust it; pairwise for A vs B swaps, a pointwise rubric for absolute bars.
- Lexical metrics (exact match, ROUGE, BLEU) only for extraction or classification steps with one right output.
- Slice every result by language, tenant and intent; an average hides one broken language.
- Pin model versions, never a moving alias; a provider upgrade is a change with an eval run.
- Low temperature still varies: run judged cases more than once or state a tolerance.
- Use the embedding model's query vs document mode (task type or prefix) where it has one; mixing them lowers recall.
- RAG for facts that change (the catalogue); fine-tuning only for format or style a prompt cannot reach, with labelled data, never to add knowledge.
- Production signals: no-answer rate, thumbs-down rate, fallback rate, P95 seconds, cost per turn, and index drift (retired courses still found, new ones missing).
- Before a prompt or model goes live: shadow or canary on real traffic with the same metrics.
- One model card per AI feature: model and version, prompt version, data sent, eval results, known limits; updated with each change.

## SAP Generative AI Developer: generative AI hub
- (SAP) Call models through the generative AI hub orchestration service: one API across providers, so a model swap is config plus a golden-set run.
- (SAP) Use the orchestration modules before writing our own: templating, input and output content filtering, data masking, grounding, translation.
- (SAP) Data masking: pseudonymise learner names and emails before the model; pseudonymisation can restore them in the answer, anonymisation cannot.
- (SAP) Prompt templates live versioned in the hub (AI Launchpad); code names the template and version, never an inline copy.
- (SAP) Isolate tenants or stages by resource group or by AI Core instance; check the model is offered in the instance's region before choosing it.

## Traps
- Tuning the prompt while recall@k is low: fix chunking, filters or hybrid search first.
- Filtering after top-k leaves fewer than k results, or none. pgvector HNSW with a WHERE clause: raise `hnsw.ef_search` or use iterative scans (0.8 and later).
- Reusing a similarity floor after a model change or re-index: scores shift, re-tune the floor.
- Course text that carries instructions (indirect injection): fence it as data and keep a golden case for it.
- Repairing bad JSON with another LLM call: count it in the turn budget and cap it at one.
- Retries at two layers (SDK and workflow) multiply attempts, seconds and cost.
- Logging full prompts with the learner's question and profile builds a personal-data store with no retention.
- Judging with the same model that answers: it prefers its own style; use another model or human spot checks.

## Numbers
- Defaults until ai.md sets others: loop cap 5 iterations; read-tool timeout 5 s; turn deadline 30 s; first words 5 s.
- Retries: at most 2 for 429, 5xx and timeouts, exponential backoff with jitter; none for 4xx validation errors.
- Golden set start (default): 50 cases or more, at least 5 per intent and per language; no high-priority case may be lost.
- Retrieval bar before prompt work (default): recall@5 of 0.9 or more on the golden queries.
- Rerank (default): 20-50 candidates in, 5 out.
- Chunks: start at 200-500 tokens with 10-20% overlap, then tune by recall@k.
- Judge trust (default): 80% or more agreement with human labels on 30 or more cases.
- Cost per turn = tokens in x input price + tokens out x output price; output tokens usually cost several times input tokens.
- Batch APIs can take up to 24 h to return.
