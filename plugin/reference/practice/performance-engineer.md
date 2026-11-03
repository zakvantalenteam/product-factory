# Practice pack: performance-engineer

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## OCP Java SE 17: where Java time and memory go
- Big-O decides at volume: an O(n^2) dedupe is 160,000 steps at 400 rows and 1.6 billion at 40,000; check the 5-year row count, not the demo data.
- `ArrayList.remove(0)` or `LinkedList.get(i)` in a loop is O(n^2): an `ArrayDeque` or an index loop over an `ArrayList`.
- Boxed numbers in big maps (`Map<Long, Long>`) cost an object per value plus one per entry: primitive arrays or `long` streams for large numeric work.
- Exceptions as control flow are slow (the stack trace is filled on every throw): check first, throw only for errors.
- `synchronized` or one lock on a hot path shows as JFR "Java Monitor Blocked" events: shrink the locked section, or `ConcurrentHashMap` or `LongAdder`.
- A parallel stream in request code competes for the common ForkJoinPool with every other request: never the fix for a slow call.
- Allocation rate drives GC: entities, then DTOs, then a JSON string for a whole `findAll` is three copies in memory; page or stream.
- An array or object of half a G1 region or more is humongous and goes straight to the old generation: page large lists, no single huge `byte[]` per export.
- Read the heap after GC over time: a rising floor is a leak (a growing map, a `ThreadLocal`, a listener never removed); a sawtooth that returns to the same floor is normal.
- Hangs and slow requests: 3 thread dumps a few seconds apart (`jcmd <pid> Thread.print`, run by the main session); the same frame in all three is where the time goes.
- JMH: return the result or feed it to a `Blackhole`, or the JIT removes the work; `@Param` for the real sizes; never time a loop with `System.nanoTime`.
- In a container the JVM's default max heap is 25% of the memory limit: set `-XX:MaxRAMPercentage` or the buildpack's memory settings on purpose, leaving room for metaspace, thread stacks and direct memory.

## ISTQB CT-PT: load tests that answer a question
- Pick the test type from the risk: load (expected peak), stress (above peak, then recovery), spike (sudden burst), endurance or soak (hours at normal load), concurrency (many users on one record or job), scalability (do more instances add throughput), capacity (most users within budget).
- The operational profile comes from production data: the transaction mix and shares, think time and arrival rate at the busiest hour; guessed numbers are marked proposed.
- Open model (requests per second, for example k6 `constant-arrival-rate`) for APIs and jobs; a closed model (fixed virtual users) slows its own load when the system slows and hides queueing.
- Load profile: ramp-up, steady state, ramp-down; report only the steady state and drop the warm-up (JIT, caches, pools filling).
- Static testing first: review queries, indexes, payloads and timeouts on paper; it is cheaper than a run and often finds the cause.
- Environment like production: same database engine, instance count, memory and data volume; write every difference next to the result.
- Test data: realistic volume and spread, unique per virtual user so caches and locks behave as in production; synthetic or pseudonymised, never real personal data (GDPR).
- Scripts: parameterise inputs, correlate dynamic values (session, CSRF token, ids from earlier responses), check each response's content, not only its status.
- (SAP) Through the approuter: log in once per virtual user, fetch the CSRF token with `X-CSRF-Token: Fetch` on a GET, send it on every write.
- Outside systems (SuccessFactors, n8n, LLMs) are stubbed with a fixed, measured latency: never load a customer or shared system without written approval.
- Smoke run first (1 user, every script passes), then the baseline, then the load steps.
- Monitor every tier during the run and the load generator itself: a generator near its CPU limit measures itself.
- Find the knee: the load step where latency rises faster than throughput; capacity is the step before it.
- Stress: after the load drops, errors stop and latency returns to the baseline without a restart; if not, that is the finding.
- Endurance: heap floor, connections, threads and open files stay flat for the whole run.
- Concurrency: many users editing one record shows the 409 rate; the same job started twice runs once.
- Results per load step: p50, p95, p99, max, throughput, error rate and resource use, against the budget; never an average alone.
- Percentiles do not add or average across instances or time slices: merge the raw samples or histograms.
- Compare runs only with the same script version, data, environment and duration; report the spread across runs, not the best run.
- Report for the reader: one verdict line per budget (met or missed, by how much), then the evidence, with the bottleneck and its tier named.

## Traps
- Coordinated omission: a tool that waits for each response before the next request under-reports latency when the system stalls; use an open model.
- An empty or small database makes every query fast: load the 5-year volume first.
- Every virtual user asking for the same id gives a cache hit rate production never sees: vary the data.
- One load generator address can hit rate limits or stick to one instance: check how load spreads across instances.
- Debug logging or an attached profiler changes the result: same settings before and after.
- Error responses are fast: lower latency with more errors is not a fix; read the error rate first.
- A green average hides a red p95: budgets are percentiles.

## Numbers
- Core Web Vitals good: LCP up to 2.5 s, INP up to 200 ms, CLS up to 0.1, at the 75th percentile of page loads.
- Response time feel: 0.1 s feels instant, 1 s keeps the flow, 10 s loses attention.
- A p99 from 100 samples or fewer is just the maximum: collect enough requests per step for the percentile you report.
- HikariCP (Boot default): 10 connections, 30 s wait for a connection; Tomcat: 200 worker threads by default.
- PostgreSQL `max_connections` defaults to 100: pool size x instances x apps stays below it.
- JVM default max heap: 25% of RAM or the container limit; default thread stack 1 MB on 64-bit Linux.
- JFR with its default settings is built to run in production at about 1% overhead.
