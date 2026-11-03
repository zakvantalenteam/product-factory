# Practice pack: code-reviewer

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## OCP Java SE 17: defects to spot in a Java diff
- A getter that returns the internal list, or a `Collections.unmodifiableList` view of it, leaks later changes: return `List.copyOf`.
- A record with a list or array component and no copy in the compact constructor can be changed from outside.
- A `Comparator` written as `a - b` overflows for large or negative values: `Integer.compare` or `Comparator.comparingInt`.
- `list.remove(i)` on a `List<Integer>` removes by index, not by value: `remove(Integer.valueOf(i))`.
- A ternary that mixes `int` and `Integer` unboxes: `flag ? map.get(k) : 0` throws NPE when the key is missing.
- `Optional.orElse(load())` always runs `load()`: `orElseGet` for anything costly or with side effects.
- `String.split(".")` and `split("|")` take a regex: escape with `Pattern.quote` or the result is wrong.
- A `catch` of `InterruptedException` (or of `Exception` around blocking code) without `Thread.currentThread().interrupt()` loses the interrupt and blocks shutdown.
- An old-style `switch` without `break` falls through: ask for the arrow form.
- `Integer.parseInt`, `UUID.fromString` or `LocalDate.parse` on request input throws: the controller must answer 400, not 500.
- `equals` in a non-final class that a subclass extends with a new field breaks symmetry: make the class final or a record.
- A `TreeSet` or sorted map whose comparator ignores the id silently merges distinct rows.
- Lazy init of a shared field without synchronisation (`if (cache == null) cache = load()`) races: initialise in the constructor or use a holder class.
- A diff that swaps `Collectors.toList()` for `Stream.toList()` changes behaviour: any later `add`, `sort` or `removeIf` on the result now throws.

## CSSLP: secure design, code and supply chain in review
- Complete mediation: every request checks permission on the server, per record (its tenant and owner); a hidden button is not a control.
- IDOR: an id from the path or body loads a record with no owner or tenant check: MUST, with a cross-tenant test as the fix proof.
- Mass assignment: a request body bound straight onto an entity lets the client set `tenantId`, `role`, `id` or `version`: bind to a DTO with only the allowed fields.
- Least privilege: a new scope, role, database grant or technical user gets only what the criterion needs; a wildcard scope or an admin user is a finding.
- Attack surface: a new endpoint, public route, webhook, file upload or query parameter gets a closer look (auth, size limit, validation, rate limit).
- Fail secure: a `catch` in an auth, permission, signature or validation path that returns true, a default or an empty filter is a MUST.
- Errors to clients carry a code, never a stack trace, SQL, class name, internal id or another user's data.
- Untrusted deserialization: no `ObjectInputStream.readObject` on outside data; no Jackson default typing or `@JsonTypeInfo(use = Id.CLASS)` on input.
- XML from outside: DTDs off (`disallow-doctype-decl`) on every parser factory, or XXE reads local files.
- Zip and file input: entry names normalised and checked to stay inside the target folder (zip slip); upload size and type limited.
- An outbound URL built from input (SSRF) or a redirect target from a parameter (open redirect): allowlist the hosts.
- Crypto: no own algorithms; `SecureRandom` for tokens, never `Random` or `Math.random`; never MD5 or SHA-1 for security.
- TLS checks never disabled: a trust-all `TrustManager` or a `HostnameVerifier` that returns true is a MUST.
- A regex with nested quantifiers (`(a+)+`) on user input can hang a thread (ReDoS): simplify it or bound the input length.
- CR or LF from user input written to a log forges log lines: log through the structured logger or strip line breaks.
- Personal data (GDPR): a new field, log line, export, cache, AI prompt or n8n payload with personal data needs a purpose, the fewest fields, a retention rule and a deletion path.
- A secret in the diff stays leaked after it is removed: the finding says rotate it, not only delete it.
- Each security MUST names the test that keeps it fixed: 403 for the wrong role, 403 or 404 for another tenant, 400 for bad input.
- New dependency: needed (nothing in the repo does it), maintained (recent release, more than one maintainer), licence fits (no GPL or AGPL in shipped code without approval), no known High or Critical CVE, transitive dependencies checked.
- Exact names: compare the groupId and artifactId, or the npm name and publisher, with the official ones (typosquatting); AI-suggested packages that do not exist are a known attack (slopsquatting).
- Pinned versions: no Maven version ranges, `LATEST`, `RELEASE` or SNAPSHOT in a release; the npm lockfile is committed and CI installs with `npm ci`.
- A new `<repository>` in the pom or a registry in `.npmrc` is a finding unless approved: only the central registry or the company mirror.
- npm `postinstall` and other install scripts run code on every machine: a new package with one needs a reason.
- Override a version managed by the Spring Boot BOM only to fix a CVE, with a comment that names it.
- CI actions and build plugins pinned (GitHub Actions to a commit SHA); an SBOM (CycloneDX or SPDX) per release lists what ships.
- An n8n community node is a third-party dependency with access to the workflow's credentials: the same review as a library.
- (SAP) A new approuter route with `authenticationType: none` or a new scope in `xs-security.json` is a security decision: it must match an approved card.

## Traps
- A test that mocks the repository cannot catch a missing tenant filter: ask for a `@DataJpaTest` with two tenants and the same user id.
- `@PreAuthorize` on a private or self-invoked method never runs: the permission check is silently absent.
- `requestMatchers` order: a broad `permitAll()` before a specific rule makes that path public.
- `@Valid` on a request body does not reach nested objects or list items unless those fields carry `@Valid` too.
- CORS with credentials and `allowedOriginPatterns("*")` lets any site call the API as the user: list the origins.
- CSRF switched off on an app that uses a session cookie is a MUST; only token-only APIs may switch it off.
- A record's generated `toString` prints every component: logging a record DTO logs its personal data and secrets.
- A record or DTO serialised to JSON exposes every component: a field the role may not see needs its own DTO, not a later `@JsonIgnore`.
- Comparing tokens, HMACs or signatures with `equals` leaks timing: `MessageDigest.isEqual`.

## Numbers
- CVSS v3 bands: Critical 9.0-10.0, High 7.0-8.9, Medium 4.0-6.9, Low 0.1-3.9; a reachable High or Critical is a MUST.
- Password storage (OWASP): Argon2id with at least 19 MiB memory, 2 iterations, parallelism 1; or bcrypt with work factor 10 or more.
- Random tokens: at least 128 bits from `SecureRandom`.
- AES-GCM: a 12-byte nonce, never reused with the same key; RSA keys at least 2048 bits; TLS 1.2 minimum, 1.3 preferred.
