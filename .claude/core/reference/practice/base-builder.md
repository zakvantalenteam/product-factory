# Practice pack: base-builder

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## OCP Java SE 17 and Spring Professional: the patterns every story copies
- Every story copies the base: one way per concern (errors, paging, tenant scope, audit, jobs, outbound calls), written once and named in B9.
- `@SpringBootApplication` sits in the root package: component scan and entity scan cover only that package and below.
- `@ConfigurationProperties` records with `@Validated` constraints: a missing or wrong key stops the start, not the first request.
- Property order: command line, then environment variables, then profile files, then `application.yml`; `app.jobs.pool-size` binds from `APP_JOBS_POOLSIZE` (dots to underscores, dashes dropped).
- Profiles come from the environment (`SPRING_PROFILES_ACTIVE`), never fixed inside the packaged `application.yml`.
- Problem details on: `spring.mvc.problemdetails.enabled=true` plus one `@RestControllerAdvice` that maps our exceptions to codes (RFC 9457).
- Jackson through `spring.jackson.*` or a `Jackson2ObjectMapperBuilderCustomizer`; an own `ObjectMapper` bean switches Boot's setup off.
- Security from the first file: one `SecurityFilterChain`, stateless (`SessionCreationPolicy.STATELESS`), deny by default, `@EnableMethodSecurity`; the health path is the only public one.
- The tenant comes from the validated token, never from a header, parameter or body the client sets.
- One named, bounded executor for jobs and one for outbound calls, defined in the base with a `TaskDecorator` that carries the request id and tenant.
- One outbound client builder with connect and read timeouts, a bounded retry for transient errors and the request id header; stories never build their own.
- `@Scheduled` runs on every instance: with 2 instances each job runs twice unless the job framework takes a database lock or lease first.
- Liveness without database or outside calls (`management.endpoint.health.probes.enabled=true` gives `/actuator/health/liveness`); readiness may add `db` to its group.
- Actuator over HTTP: `health` only, details hidden from anonymous callers; never `env`, `heapdump` or `*`.
- EclipseLink in Boot: Hibernate excluded from the JPA starter, `EclipseLinkJpaVendorAdapter` configured, the weaving choice (static in the build, or off) written down; `spring.jpa.open-in-view=false`.
- Pool, executor, page and timeout sizes set explicitly in config with a comment on how they were sized; no library default left implicit.
- Logs as JSON to stdout with the request id and tenant in MDC (Boot 3.4+ `logging.structured.format.console`); no personal data.
- A context-loads test plus one slice test per layer (`@WebMvcTest`, `@DataJpaTest`) for the demo flow, so stories have a pattern to copy.
- Repository tests on the real database engine where possible (PostgreSQL in a container): H2 hides case, function and locking differences.
- Twelve-factor: config in the environment, backing services as bindings, stateless processes, fast start and graceful stop, logs to stdout, one build for every stage.

## SAP BTP Administrator: the account, security and services the base needs
- (SAP) Account model: global account, directory, subaccount (one region, one stage), Cloud Foundry org and spaces; never dev and prod in one subaccount.
- (SAP) Choose the subaccount region by data residency before creating anything (EU customers: an EU region such as `eu10`); moving later means a new subaccount.
- (SAP) Entitlements come first: a service plan must be entitled to the subaccount before an instance can be created.
- (SAP) People get role collections through identity provider groups (trust to SAP Cloud Identity Services), not one by one.
- (SAP) Space Developer can read every binding credential (`cf env`): in production keep it to the deploy pipeline's technical user and named admins; others get Space Auditor.
- (SAP) `xs-security.json`: `tenant-mode` `dedicated` for a single-tenant app; `token-validity` set explicitly (seconds); one role template per product role.
- (SAP) Service keys are standing credentials for tools outside the app: one per named user and purpose, deleted when done; apps use bindings.
- (SAP) Destinations hold outside URLs and credentials at subaccount level; pick the authentication type per call: a technical user (`OAuth2ClientCredentials`) or the user's identity (`OAuth2SAMLBearerAssertion`, `OAuth2UserTokenExchange`).
- (SAP) On-premise systems are reached only through the Connectivity service and a Cloud Connector, never a public route.
- (SAP) With JPA owning the schema, bind the `hana` service `schema` plan; `hdi-shared` is for HDI deployer artifacts.
- (SAP) MTA (`mta.yaml`, `mbt build`, `cf deploy`) deploys apps, services and bindings as one versioned unit and supports blue-green; `cf push` with `manifest.yml` leaves services to be created by hand; the base spec decides, write the choice down.
- (SAP) Security events (role changes, personal data read or changed by admins) go to the SAP Audit Log service; the table audit history does not replace it.
- (SAP) `default-env.json` for the local approuter holds real credentials: git-ignored from the first file, with a placeholder copy in the repo.

## Traps
- (SAP) Cloud Foundry kills the app 10 s after SIGTERM, while Boot's graceful shutdown waits up to 30 s per phase: set `spring.lifecycle.timeout-per-shutdown-phase` below 10 s.
- A health check that calls the database restarts every instance when the database is slow: keep liveness local.
- Leftover names of the source product in packages, i18n keys, `xsappname`, routes, bean names or comments fail the base check (B10).
- A secret copied from a reference repo is a leak even inside a placeholder file: key names only.
- `APP_JOBS_POOL_SIZE` binds to `app.jobs.pool.size`, not `app.jobs.pool-size`: the value is silently ignored.

## Numbers
- (SAP) Cloud Foundry: 10 s from SIGTERM to SIGKILL; Boot `timeout-per-shutdown-phase` defaults to 30 s.
- JVM default max heap: 25% of the container memory limit; set it from the app memory on purpose. (SAP) On Cloud Foundry the Java buildpack's memory calculator sets it from the app memory: tune its settings, not MaxRAMPercentage.
- HikariCP default 10 connections; Tomcat default 200 threads; Boot task executor default 8 core threads with an unbounded queue.
- Pool size x instances stays below the database connection limit (PostgreSQL default `max_connections` 100).
- Spring Data web paging caps a page at 2000 rows by default: set the product maximum in the base.
