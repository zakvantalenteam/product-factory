# Practice pack: bug-investigator

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## OCP Java SE 17: reading the failure
- Stack trace: the root cause is the last `Caused by`; start at the first frame in our own package under it; `... 12 more` repeats frames shown above.
- Helpful NPE messages name the null part (`because the return value of "...getManager()" is null`): start from that call, not from the line number alone.
- The first error in the log wins: `ExceptionInInitializerError` comes once, later uses of the class only say `NoClassDefFoundError`.
- `NoSuchMethodError` or `NoClassDefFoundError` with clean code: two versions of a library on the class path; compare them in the dependency tree.
- `ClassCastException` far from any cast: a raw type or unchecked cast put the wrong element into a collection earlier; find where it was added.
- `ConcurrentModificationException`: a collection changed while it was iterated, often the same thread removing inside a for-each.
- `UnsupportedOperationException` on `add` or `remove`: an unmodifiable list (`List.of`, `Stream.toList()`, `Arrays.asList`) reached code that changes it.
- `IllegalStateException: Duplicate key` from `toMap`: the data holds a duplicate the code did not expect; the defect is the data or the rule.
- Works in tests, fails in production with real ids: `==` on boxed ids, which holds only up to 127.
- Wrong day near midnight or once a year: the server zone (UTC on cloud) instead of the user's, `YYYY` instead of `yyyy`, or a DST change.
- `Ã¼` instead of `ü`: UTF-8 bytes read as ISO-8859-1 or Windows-1252; find the reader or writer without a named charset.
- Negative or tiny totals: `int` overflow; cents off: `double` used for money.
- A duplicate in a `HashSet` or a lost entry in a `HashMap`: missing `equals`/`hashCode`, or a key changed after insert.
- Order differs between runs: output depends on `HashMap`, `HashSet`, `Map.of` or `Set.of` iteration order.
- A write that did not roll back, or a cache or permission check that did not apply: the annotated method is private, final or called from its own class; or a checked exception (commits by default); or a `catch` swallowed it.
- Data changed outside the app (n8n, a SQL script) shows only after a restart: the EclipseLink shared cache.
- A hang: ask the main session for 3 thread dumps a few seconds apart (`jcmd <pid> Thread.print`); "Found one Java-level deadlock" names both locks.
- The Java and Spring traps behind these symptoms are in the stack pack `java17-spring-boot3.md`: read only the matching section.

## ISTQB TTA: analysis that finds the defect
- Data flow along the failing path: a value set and overwritten before use, used before it is set, or computed and never used (a filter built but not passed to the query).
- Control flow: an early `return`, `continue` or `break` that skips a step; a branch nothing can reach; `&&` where `||` was meant.
- A wrong decision with several conditions: for each condition find the input that flips the result alone (MC/DC thinking); the one that does not behave is the defect.
- Boundaries: the value at, just below and just above each limit (page size, end of a date range, 127 and 128, empty string).
- Coverage is not proof: a covered line was not tested both ways; check that the existing tests take the failing branch with the failing data.
- Read the test that should have caught it: mocked away, wrong data or a loose assert; that goes into the lesson.
- Compiler warnings and static analysis findings (SpotBugs, Sonar) on the suspect file are cheap evidence: read them before guessing.
- Intermittent failures are usually timing (race, timeout), order (iteration or test order), time (midnight, month end, DST), data (one record's shape) or environment (one instance of two, a node-local cache): name the kind and the test that shows it.
- A memory leak shows as a rising heap floor after GC over hours, then out-of-memory after days: look for growing maps, caches, `ThreadLocal`s and listeners.
- A retry that is not idempotent duplicates rows or messages: check what a timeout followed by a retry does.
- A 502 or 504 from the router with no app error: the app crashed, restarted or passed the router timeout; a 500 comes from the app.
- Classify the root cause (requirement, design, code, data, configuration, environment) for the lesson; severity is impact, priority is when to fix.
- Defects cluster: search the same module and the same change for the same construct.
- A regression test is proof only when it asserts the exact wrong value from the reproduction and fails with the fix reverted.
- Read-only history: `git log -S <text>` finds commits that change how often a text occurs; `git log -G <regex>` finds commits whose changed lines match, even when the count stays; `git log --follow` crosses renames; `git blame -w` ignores whitespace.
- (SAP) Ask the main session for `cf logs <app> --recent` right after the reproduction (only a short buffer is kept) and `cf events <app>` for crashes and restarts.

## Numbers
- Exit code 137 is SIGKILL (128 + 9), often the memory limit; 143 is SIGTERM (128 + 15), a normal stop.
- Cyclomatic complexity above 10 (McCabe): write the path table and mark the path the failing input takes before guessing.
