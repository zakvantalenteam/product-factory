# Platform facts: SAP BTP, Cloud Foundry

Read by `devops-engineer` only when `AGENTS.md` says the repo runs on SAP BTP Cloud Foundry. Names in angle
brackets are placeholders: a real value (host, service name, org, space, company id, key) never goes into a
document, a committed file or chat. Anything marked *verify* depends on the account's CLI or service plan.

## Shape of an app on Cloud Foundry
| Part | What it is | Notes |
|---|---|---|
| Backend app | the server (for example a Java WAR or JAR on the Java buildpack) | stateless; session and cache state must work with several instances |
| Approuter app | `@sap/approuter` on the `nodejs_buildpack` | the only public entry; authenticates, then forwards to the backend |
| Frontend build | static files | copied into `approuter/resources` by the build or CI, never committed |
| Services | xsuaa, destination, database, logging (and optional autoscaler) | bound by name; credentials arrive in `VCAP_SERVICES` |

Deploy order: database migration, backend, approuter. A change that adds a role or scope also needs the
security service updated (below) before the backend starts using it.

## manifest.yml
- One entry per app: `name`, `hostname` or `routes`, `memory`, `disk_quota`, `instances`, `buildpack`, `path`
  (artifact), `env`, `services`. Production runs at least 2 instances; set memory from measured use.
- Per-environment values (hosts, service names, profile) use manifest variables (`((var))` with
  `--vars-file` per environment) or `cf set-env` by the developer; never one committed value for all
  environments, never a real service name in a shared template.
- Health check: `health-check-type: http` and `health-check-http-endpoint` pointing at the public health
  endpoint; `timeout` sized to startup (a cold Java app can need 60-120 s). The endpoint needs no login and
  does no database call, so a database outage does not restart every instance. *verify* readiness checks on
  the CLI version in use.
- Typical env keys, by name only: the active profile (`cloud`), JVM options, node roles, schema-validation
  switch, company or tenant id, frame-options switch, logout switch. Secrets are never env literals in the file.

## Approuter (`approuter/xs-app.json`, `package.json`)
- `authenticationMethod: route`; `welcomeFile`; `logout` endpoint and page. Routes are matched in order, so the
  most specific first: webhook routes (`authenticationType: none`, `csrfProtection: false`, no cache), public
  routes such as health and public APIs (`none`), the application routes (`xsuaa`, csrf per the design), and
  last the static `localDir: resources` route. Every `none` route is a security decision: list it in
  `05-security.md` or the design section.
- Destination: backend routes name a destination; the destination points at the backend URL with
  `forwardAuthToken: true` (in the `destinations` env JSON or the destination service).
- Env keys: `TENANT_HOST_PATTERN` (multitenant), `COMPRESSION`, `REQUEST_TRACE` (off in production),
  `SEND_XFRAMEOPTIONS`, `INCOMING_CONNECTION_TIMEOUT`, `CF_NODEJS_LOGGING_LEVEL`, session timeout.
- Frame embedding (a portal or work zone) needs the frame-options and CSP settings decided on purpose.

## Security descriptor (`xs-security.json`) and roles
- `xsappname`, `tenant-mode`, `scopes`, `role-templates` (each lists `scope-references`), `role-collections`
  (each lists `role-template-references`), `oauth2-configuration` (`token-validity`, `redirect-uris` with
  `https://<approuter-host>/login/callback`), `grant-as-authority-to-apps` when another app calls this one.
- Chain: scope -> role template -> role collection -> user. One role template per product role in the access
  matrix; the code checks scopes or roles, never user names.
- Changing the file means updating the bound xsuaa service (`cf update-service <xsuaa> -c xs-security.json`,
  a developer step). Role collections are assigned to users in the cockpit or the identity provider (manual
  step); roles needed by existing tenants are granted by an upgrade job, not by hand.
- Tokens: keep the validity short enough for the risk, refresh in the approuter, never put a token in a URL
  or a log.

## Service bindings, secrets and profiles
- Bind by service instance name in `manifest.yml`; read credentials from `VCAP_SERVICES` or the platform
  library. No credential in the repo: placeholders (`<set-me>`), user-provided services, or the CI credential
  store. `cf env` and `cf service-key` print secrets: agents never run them.
- Profiles: `local` (default on a laptop, mock login, local database), `test`, `cloud` (set by the manifest).
  A build profile such as `production` marks container-provided libraries as `provided` for a WAR. The app must
  start under each profile with a clear message when a required value is missing.
- Environments are separate CF spaces (for example dev, test, prod) with the same artifact and different
  variables; promote the artifact, do not rebuild it per environment.

## CI pipeline
Steps in order: build backend and frontend, unit tests, lint and type check, contract lint (OpenAPI), static
analysis (Sonar), package, store the artifact, deploy to dev automatically and to higher spaces by an approval.
The pipeline reads secrets from its own store. A failing test, lint error or quality gate stops it.
- Sonar: `sonar.projectKey`, source and test paths, coverage report paths, exclusions for generated code and
  the frontend build output, quality gate on new code (no new blocker or critical issue, coverage floor from
  the spec).

## Logging and monitoring
- Log to stdout; one line per event; a request id on every line (a `requestId` mapped diagnostic value set by a
  filter, also returned in the response header); no personal data, token or prompt text at INFO and above.
- Levels per package come from env. Read logs with `cf logs <app> --recent` or the logging service.
- Watch: health endpoint, 5xx rate, response time p95 per main operation, job failures (a job records status and
  errors), memory and restarts. Alerts go to the on-call route the spec names.
- Backups and restore come from the database service plan: state the schedule and a restore test in the ops plan.

## Rollback and manual steps
- Application: push the previous artifact, or `cf rollback <app>` to a previous revision (*verify* CLI version).
- Database: migrations go forward only; each has a down note, and a destructive step is split over two
  releases (expand, then contract).
- Security descriptor: update the service again with the previous file.
- Manual cockpit steps to list in the deploy plan: role collection assignment, destinations, trust to the
  identity provider, subscriptions, custom domains and certificates, scaling rules.

## What an agent never does
Run `cf push`, `cf set-env`, `cf update-service`, `cf delete` or any `cf` command that changes something;
run `cf env` or `cf service-key`; start a server; push to git. It writes the plan and the exact commands
for the developer to run.
