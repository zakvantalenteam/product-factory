# Practice pack: backend-developer

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## OCP Java SE 17: types chosen by access pattern, data immutable, threads bounded
- Sorted output or range lookups (`floorKey`, `ceilingEntry`, `subMap`): `TreeMap`/`TreeSet` at O(log n); plain lookups stay on `HashMap` at O(1).
- Top k of n rows: a `PriorityQueue` capped at k is O(n log k) and holds k items; sorting all n is O(n log n) and holds n.
- `ArrayList` reads by index in O(1) but `remove(0)` or an insert in the middle is O(n): a queue is an `ArrayDeque`; `LinkedList` is almost never right (O(n) `get(i)`).
- Read-mostly lists shared between threads (listeners, rules loaded at start): `CopyOnWriteArrayList`; every write copies the array, so never for per-request data.
- Expose collections as `List.copyOf(...)`; `Collections.unmodifiableList(x)` is only a view and still shows later changes to `x`.
- Records are shallow: copy list and array components in the compact constructor and validate there, so the record is really immutable and safe as a map key.
- A stream is single-use and runs only at the terminal call; keep lambdas free of side effects on shared state (`collect`, never `forEach` into an outside list).
- Switch expressions over an enum without `default`: adding a constant then breaks the compile instead of falling through silently.
- Java 17 has no switch on types: put the behaviour on the sealed interface (one method per subtype) or end an `instanceof` chain with `throw`.
- Elapsed time is a `Duration`, calendar time a `Period`: across a DST change `plusDays(1)` and `plusHours(24)` give different instants.
- Codes, keys and ids use `Locale.ROOT` (`toUpperCase(Locale.ROOT)`); text for people uses the user's `Locale` and `ResourceBundle` keys.
- A user-given file name: `base.resolve(name).normalize()` must still `startsWith(base)`, else reject it (path traversal).
- `Files.lines` and `Files.list` hold an open file handle: try-with-resources; `Files.readAllLines` loads the whole file, so stream big files.
- `volatile` gives visibility only: `count++` on it loses updates; a shared counter is an `AtomicLong` or `LongAdder`.
- A `ThreadPoolExecutor` starts threads above core only when its queue is full: with an unbounded queue max size is never reached; bound the queue and size core from the load.
- Pick the rejection policy on purpose: `CallerRunsPolicy` slows the producer (back-pressure), `AbortPolicy` fails fast and maps to 503.
- `orTimeout` fails the future but does not stop the running call: the HTTP client still needs its own connect and read timeouts.
- `ThreadLocal` values (tenant, user, MDC) stay on pooled threads: set and clear them in `try/finally`, or copy them with a `TaskDecorator`.

## Spring Professional: proxies, transactions, data access, outbound calls
- `@Transactional`, `@Async`, `@Cacheable` and `@PreAuthorize` act only through the proxy: a self-call or a private method silently skips them (no transaction, no new thread, no cache, a permission check that fails open). Say so whenever you add, keep or remove one.
- Fix a self-call by moving the annotated method to a second bean; injecting the bean into itself or `AopContext.currentProxy()` hides the coupling.
- CGLIB cannot override `final` classes or methods: annotations there are ignored with no error.
- `@PostConstruct` runs on the raw bean, outside the proxy, so with no transaction: do start-up data work in an `ApplicationReadyEvent` listener.
- Rollback is automatic only for `RuntimeException` and `Error`: a checked exception commits; set `rollbackFor` or throw an unchecked one.
- An inner `REQUIRED` call that throws marks the shared transaction rollback-only: catching it in the caller ends in `UnexpectedRollbackException` at commit.
- `REQUIRES_NEW` suspends the outer transaction and takes a second pool connection: under load it can drain the pool; keep it for a short audit or outbox write.
- Work after success (mail, n8n, calls to other systems): `@TransactionalEventListener(phase = AFTER_COMMIT)` or an outbox row; a write inside that listener needs `REQUIRES_NEW`.
- `@Bean` methods in a `@Configuration` class return the singleton when they call each other; in a `@Component` the same call builds a new object.
- Your own bean switches off Boot's matching auto-configuration (`@ConditionalOnMissingBean`): an own `ObjectMapper` drops every `spring.jackson.*` setting; customise with `Jackson2ObjectMapperBuilderCustomizer`.
- Name the executor in `@Async("<bean>")`: with no unique `TaskExecutor` Spring falls back to `SimpleAsyncTaskExecutor`, a new thread per call.
- `@Cacheable` keys on the method arguments only: add tenant, user and language when they come from the security context; cache immutable values, since every caller gets the same object.
- Set `spring.jpa.open-in-view=false` (Boot default true) so no query runs while the response is written.
- EclipseLink loads a LAZY relation even after the transaction ends (no `LazyInitializationException` as in Hibernate): an N+1 in mapping outside the service stays silent; map inside the service and count queries in a test.
- Fetch plan per use case, not per mapping: `JOIN FETCH` (one collection per query, with `DISTINCT`) or the hints `eclipselink.left-join-fetch` and `eclipselink.batch` with `eclipselink.batch.type` `IN` and `eclipselink.batch.size`.
- Paged parents: never JOIN FETCH a collection in the paged query (the limit then counts joined rows); page the parents, then batch-fetch children with type `IN`, which sends the page's ids (JOIN and EXISTS repeat the parent query).
- Spring Data `save()` on a detached entity merges and returns a new managed instance: keep working with the returned object.
- Entities with assigned ids look not-new to Spring Data (a SELECT before each insert): use a wrapper-typed `@Version` (null means new) or implement `Persistable`.
- `Page` adds a COUNT query per request: return `Slice` when the screen shows no total.
- `@Modifying` queries need a transaction; add `clearAutomatically = true` so the persistence context does not serve the old rows after the bulk update.
- Sequence ids: `allocationSize` equals the database sequence's INCREMENT BY, or two instances hand out the same ids; IDENTITY costs a round trip per insert and stops insert batching.
- Every outbound client (`RestClient`, `WebClient`, `RestTemplate`) gets explicit connect and read timeouts: the JDK-based request factories have no read timeout by default.
- Outbound time (timeout x attempts + backoff) fits inside the inbound call's budget, or the caller gives up while you are still retrying.
- Spring Security 6: one `SecurityFilterChain` bean, `requestMatchers` most specific first, ending in `anyRequest().authenticated()` or `denyAll()`; `@EnableMethodSecurity` for service-level checks.
- (SAP) The backend validates the XSUAA JWT itself even behind the approuter: its own Cloud Foundry route is reachable, so a call without a token must get 401.
- Tests on Boot 3.5: `@MockitoBean` (`@MockBean` is deprecated since Boot 3.4); each new set of mocked beans starts another context, so share one setup per slice.

## Traps
- `Collectors.toMap` throws on a duplicate key and on a null value: pass a merge function and decide what a duplicate means.
- `groupingBy` returns a `HashMap`: pass `LinkedHashMap::new` or `TreeMap::new` when the order is shown or asserted.
- `Map.of` and `Set.of` iterate in an order that changes between JVM runs: never depend on it in output or tests.
- `List.of(...).contains(null)` throws NPE; `Map.of` rejects null values and duplicate keys.
- `Arrays.asList` is fixed-size (`add` throws) and writes through to the array: copy it into a new `ArrayList` to grow it.
- A `TreeSet` or `TreeMap` treats `compare == 0` as the same element: a comparator on name alone drops a second person with the same name; end with `thenComparing` on the id.
- `BigDecimal.equals` compares scale (`1.0` vs `1.00` is false): use `compareTo`; build from a String or `BigDecimal.valueOf`, never `new BigDecimal(0.1)`.
- `int` arithmetic overflows silently: `Math.addExact`, `Math.multiplyExact`, `Math.toIntExact` for sums, sizes and ids.
- Pattern `YYYY` is the week-based year and prints the next year in late December: use `yyyy` or `uuuu`.
- A `return` or `throw` in `finally` discards the original exception: never do it; close failures sit in `getSuppressed()`.
- Never call the map from inside its own `computeIfAbsent` function: `ConcurrentHashMap` throws `IllegalStateException` (recursive update) or hangs.
- `HashMap.newHashMap(n)` is Java 19: presize with `new HashMap<>((int) (n / 0.75f) + 1)`.
- Parallel streams in request or job code share the common ForkJoinPool with the whole JVM and stall it on I/O: use a loop or the named executor.

## Numbers
- `HashMap`: load factor 0.75, so it resizes at 75% full; `ArrayList` starts at 10 and grows by half.
- Boot's default task executor: 8 core threads and an unbounded queue; set `spring.task.execution.pool.queue-capacity` and `max-size`.
- HikariCP (Boot's pool): 10 connections and a 30 s wait for one by default; a `REQUIRES_NEW` path holds 2 per request.
- Tomcat: 200 worker threads by default; an outbound call with no timeout can hold all of them.
- Spring Data web paging caps a page at 2000 rows by default (`spring.data.web.pageable.max-page-size`): set the product maximum.
- JPA `@SequenceGenerator` `allocationSize` defaults to 50.
- `@Transactional(timeout = ...)` is in seconds; keep it shorter than the inbound call's budget.
