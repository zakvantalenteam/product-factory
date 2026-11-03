# Practice pack: devops-engineer

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## CKA: workloads that start, stop and fail cleanly
- Three probes, three jobs: startup covers the slow JVM start, readiness takes the instance out of traffic, liveness restarts a stuck process.
- Probe defaults are tight (1 s timeout, 10 s period, 3 failures): set them from the measured health response time and start time.
- JVM memory: the container limit covers heap, metaspace, thread stacks and direct buffers; set heap as a share (`-XX:MaxRAMPercentage`, for example 70-75), since the Java default is 25%. (SAP) On Cloud Foundry the Java buildpack's memory calculator sets heap, metaspace and stacks from the app memory: tune its settings, not MaxRAMPercentage.
- On Kubernetes, memory request equals limit for JVM workloads; exit code 137 means killed (often out of memory), 143 means stopped by SIGTERM.
- Graceful stop: on SIGTERM stop taking requests, finish in-flight work and exit inside the platform's grace period; Spring `server.shutdown=graceful` with a phase timeout below that period.
- Zero-downtime rolling update on Kubernetes: max unavailable 0, max surge 1, and a disruption budget that keeps at least one instance during node maintenance.
- On Kubernetes, config in ConfigMaps and secrets in Secrets backed by encryption at rest or an external store; base64 is encoding, not protection.
- On Kubernetes, a service account per app with only the rights it uses and a network policy that denies by default and allows the paths the design names.
- Troubleshoot in order: events and status, logs (also of the previous crashed run), exit code, probes, resources, then networking (selectors, endpoints, DNS).
- Scheduled jobs on two or more instances run twice unless the job framework takes a database lock; check before scaling out.

## AWS DevOps Pro: pipelines, release strategies and incidents
- Deploy strategy by rollback speed and spare capacity: rolling (cheap, slow rollback), blue-green (instant switch back, double capacity during the switch), canary (small share first, needs traffic splitting and a metric to judge it).
- Every deploy has a bake time with a rollback trigger, automatic or in the runbook: error rate or p95 latency above a stated threshold, compared with the previous version.
- Artifact version is the commit id; the deploy names that version.
- Pipeline credentials are short-lived (OIDC federation from the CI system to a cloud role) where the platform supports it; otherwise one technical user per space with deploy rights only, its secret stored in CI and rotated.
- Platform config as code (deploy descriptor, security descriptor, routes, service definitions); a console change not in code is drift and gets written back.
- Gates before deploy: unit tests, static analysis, a dependency scan that fails on a critical or high finding with a fix available, and a licence check.
- A database migration runs once per deploy, by one process, before the new build takes traffic; instances racing the same migration is a finding.
- Incident: declare, set severity by user impact, mitigate first (roll back, switch the feature off, scale), then find the cause; a blameless review with owned, dated actions.
- A synthetic check of the main journey from outside every few minutes, so an outage shows before a user reports it.
- Restore drills on a schedule, with the measured restore time compared with the RTO.

## Google Cloud DevOps Engineer: SLOs, error budgets and toil
- SLI = good events / valid events, measured as close to the user as you can (the gateway), for example requests answered without a 5xx in under 1 s.
- SLO below 100%; error budget = 1 - SLO over a rolling window (often 30 days); an error budget policy says what happens when it runs out (feature freeze, reliability work).
- The SLA (the contract) is looser than the SLO, so we miss the SLO and fix it before we owe a penalty.
- Alert on symptoms with multi-window burn rates, not on causes; every page is actionable and links its runbook.
- Watch the four golden signals per service: latency, traffic, errors and saturation (pool use, memory, queue depth).
- Toil (manual, repetitive, automatable, grows with load) is measured and automated away; keep it under half of operations time.
- Capacity: load test to a stated multiple of measured peak, with one instance of headroom (N+1).
- Cost: right-size from measured use, scale non-production down when idle, tag every resource with product and environment.

## SAP BTP Administrator (C_ADBTP): accounts, spaces, trust and roles
- (SAP) Account model: global account, optional directories, subaccounts (region fixed at creation), Cloud Foundry org, spaces; entitlements and quotas are set per subaccount.
- (SAP) Production gets its own subaccount (own trust, admins and entitlements); spaces only split apps, not identity or admins.
- (SAP) Cloud Foundry roles: people get Space Developer in dev and Space Auditor in production; production Space Developer is the pipeline's technical user only.
- (SAP) Trust to IAS per subaccount for business users; keep at least two platform admins in the SAP ID service, so a broken custom identity provider cannot lock everyone out.
- (SAP) Service keys are long-lived credentials: prefer bindings; rotate by creating a new key, switching, then deleting the old one; delete unused keys.
- (SAP) Spare memory quota: a rolling deploy needs one extra instance, blue-green a full second set; check the space quota before the release.
- (SAP) Zero downtime: `cf push --strategy rolling` for one app, or a multi-target archive with `cf deploy --strategy blue-green`.
- (SAP) Cloud Foundry sends SIGTERM and kills the app 10 s later; keep Spring's shutdown phase timeout under that.
- (SAP) Platform as code where the team agrees: the Terraform provider for SAP BTP for subaccounts, entitlements and role collections.
- (SAP) Compare the global account's monthly usage with the cost estimate; a consumption contract bills every extra instance and plan.
- (SAP) Alerts through the Alert Notification service or the team's on-call tool; logs through the logging service the subaccount is entitled to.

## Traps
- Heap set to the full container memory: the process is killed under load; fix: leave room for non-heap memory.
- A 1 s probe timeout on a busy JVM: restarts under load make it worse; fix: a cheap endpoint and a timeout from measurement.
- Autoscaling a JVM app on CPU when the database pool is the limit: more instances open more connections and the database saturates; fix: scale on the real bottleneck and cap instances by the pool sums.
- Blue-green switch with a migration the old build cannot read: the rollback fails; fix: expand first, switch, contract in a later release.
- Rollback never practised: the first try happens during an incident; fix: rehearse it on test for each kind of release.
- One deploy user with admin rights in every space: a leaked CI secret owns production; fix: one technical user per space with deploy rights only.

## Numbers
- Allowed downtime per 30 days: 99.5% = 3.6 h, 99.9% = 43.2 min, 99.95% = 21.6 min.
- Burn-rate alerts on a 30-day SLO: page at 14.4x over 1 h (2% of the budget) and 6x over 6 h (5%); ticket at 1x over 3 days (10%).
- Kubernetes defaults: termination grace 30 s; probe timeout 1 s, period 10 s, failure threshold 3. Spring Boot shutdown phase timeout default: 30 s.
- Java default max heap: 25% of container memory.
