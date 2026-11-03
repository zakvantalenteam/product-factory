# Stack pack: Java 17, Spring Boot 3, JPA with EclipseLink, SAP HANA or PostgreSQL

Read once, at the start, by the agents that design, write, test or review Java. Versions come from
`.claude/project.json` `stack`; they are a ceiling. The repo's own rules and checklists win over this pack.

## Java 17: use, and never above it
- Use: records (value carriers, DTOs, keys), sealed interfaces for closed hierarchies, switch expressions with
  `->` and `yield`, `instanceof` patterns (`if (o instanceof Foo f)`), text blocks, `var` for obvious local types,
  `Stream.toList()` (unmodifiable), `List.of`/`Map.of`/`Set.of`, `List.copyOf`, `String.isBlank`/`strip`/`lines`,
  `Objects.requireNonNullElse`, helpful NPE messages.
- Never (Java 21 and later): virtual threads, record patterns, pattern-matching `switch` on types or `case null`,
  `SequencedCollection` (`getFirst`, `reversed` on lists), `StringTemplate`, unnamed variables `_`, scoped values.

## Correctness traps
- `==` on `Long`, `Integer` or `String` compares references; boxed values are cached only for -128..127. Use
  `Objects.equals` or compare primitives. Constant first: `"N".equals(status)`.
- `equals` and `hashCode` together, over the same fields; JPA entities: by id with a stable `hashCode`, never by
  every field. Records give both for free.
- `Stream.toList()` and `List.of` are unmodifiable: `removeIf`, `add`, `sort` throw. Filter in the stream instead.
- `SimpleDateFormat`, `Date`, `Calendar` are mutable and not thread-safe: use `java.time` (`Instant`,
  `LocalDate`, `ZonedDateTime`) and a static final `DateTimeFormatter`; store and compare in UTC; inject `Clock`.
- Money and exact numbers: `BigDecimal` with an explicit scale and `RoundingMode`; never `double`.
- I/O: try-with-resources for every stream, reader, connection; `getResourceAsStream` may return null; always name
  the charset (`StandardCharsets.UTF_8`).
- Exceptions: never swallow; catch the narrowest type, add context, rethrow or map; a failed read is an error,
  never an empty list (that fails open).
- Generics: no raw types; `List<? extends T>` to read, `? super T` to write (PECS). `Optional` as a return type
  only, never a field or parameter; never `Optional.get()` without a check.

## Collections and performance
- Lookup or dedupe: `HashSet`/`HashMap` (O(1)), never `List.contains` in a loop (O(n^2)); keep first-seen order with
  `LinkedHashSet`/`LinkedHashMap`; `EnumMap`/`EnumSet` for enum keys; `ArrayDeque` for stacks and queues; presize
  when the size is known.
- Hot paths: no boxing in loops (`long`, `IntStream`), no `Pattern.compile` or formatter per call (static final),
  `StringBuilder` in loops, no logging string concatenation (use `{}` placeholders).
- Sort with `Comparator.comparing(..., String.CASE_INSENSITIVE_ORDER)` and `nullsLast` when values may be null.
- Batch outside calls: one call with a set of ids, then a map by id; never one call or query per row.

## Concurrency (Spring beans are singletons)
- A bean holds no mutable state unless it is thread-safe: `ConcurrentHashMap` with atomic `compute`, `merge`,
  `remove(key)` (use its return value, never get-then-remove); `AtomicLong` or `LongAdder` for counters.
- Every map or cache that grows has a bound (size and expiry, for example Caffeine) or a sweeper.
- Executors bounded and named (`ThreadPoolTaskExecutor` with queue capacity); never `newCachedThreadPool` for
  request work. `CompletableFuture` with an explicit executor and `orTimeout`.
- Immutable shared objects: records or final fields; never mutate an object another thread can see.

## Spring Boot 3
- Constructor injection with `final` fields; no field `@Autowired`. `jakarta.*` imports, not `javax.*`.
- Proxies: `@Transactional`, `@Async`, `@Cacheable`, `@Retryable` work only through the proxy, on a method called
  from another bean; self-invocation and private methods are silently ignored. Keep them on public methods (Spring 6
  also intercepts protected and package-private `@Transactional` methods on class proxies, never on interface ones).
- `@Transactional(readOnly = true)` for reads; no remote, n8n or AI call inside a transaction; the transaction on
  the service, never on the controller.
- Controllers thin: `@Valid` on request bodies, problem-details errors (`ProblemDetail`), no entity returned
  directly (map to a DTO or record with only the fields the role may see).
- Config: `@ConfigurationProperties` records with defaults in code; a new key only with a stated need.
- Retries: `spring-retry` or a loop with a bound (2-3), backoff with jitter, transient errors only; never unlimited.
- Logging: SLF4J with placeholders; the request id in MDC; no secrets or personal data (mask user ids).

## JPA with EclipseLink (Hibernate is not on the classpath in these repos)
- Queries in the repository with the tenant in the WHERE: derived queries, `@Query` JPQL with bound parameters, or
  the Criteria API; never `findAll()` then filter in Java; never string-built JPQL or SQL.
- `FetchType.LAZY` for every collection (EclipseLink honours LAZY on `@OneToMany` and `@ManyToMany`; `@ManyToOne`
  LAZY needs weaving, which the repo's setup decides); name the fetch plan: `JOIN FETCH`, `@BatchFetch(BatchFetchType.IN)`
  or a query hint `eclipselink.batch` for collections read in a loop.
- Count with a COUNT query or a projection, never `getCases().size()`; read lists with `Pageable`, a sort and a max
  page size (for example 200).
- Projections (interface or record constructor expressions) for list screens, not whole entities.
- Writes: batch with `eclipselink.jdbc.batch-writing=JDBC` and a batch size; flush and clear in long loops; bulk
  `UPDATE`/`DELETE` queries bypass the cache, so refresh or evict after them.
- EclipseLink shared cache (L2) is on by default: data changed outside JPA (raw SQL, another node, n8n) can be stale;
  the repo's cache settings decide (`@Cache(isolation = ISOLATED)` or a refresh hint).
- `@Version` on business tables for optimistic locking; handle `OptimisticLockException` as a 409.
- Native queries only for what JPQL cannot do; mark them, because column renames break them silently.

## SAP HANA and PostgreSQL
- HANA: identifiers are upper case unless quoted; `NVARCHAR` for text; `LIMIT ? OFFSET ?` paging is fine to a few
  thousand rows, then keyset paging (`WHERE created_at < :t OR (created_at = :t AND id < :id)`, a form JPQL and both
  databases accept); a function on an indexed column in WHERE (`UPPER(col)`) stops the index; column store for
  read-heavy tables; `EXPLAIN PLAN` and `M_SQL_PLAN_CACHE` (hash, counts and times; never print the statement text,
  it may hold data) to prove a plan.
- PostgreSQL: `EXPLAIN (ANALYZE, BUFFERS)` to prove a plan; partial indexes for soft delete; `text` over
  `varchar(n)` unless a limit is a rule; `timestamptz` in UTC.
- Both: an index for every new WHERE, JOIN and ORDER BY (tenant column first, equality before range); IN-lists
  bounded: chunk long id lists (for example 500 per query) to keep statements and plans small; this is a
  guideline, not a database limit.

## Tests
- JUnit 5, Mockito and AssertJ as the repo uses them; `@WebMvcTest` or `@DataJpaTest` slices before a full
  `@SpringBootTest`; no real network; a fixed `Clock`.
- Cases from the boundaries: null, empty, one, many, duplicates, the page limit, another tenant with the same user
  id, an id above 127, a time on the overdue boundary.
