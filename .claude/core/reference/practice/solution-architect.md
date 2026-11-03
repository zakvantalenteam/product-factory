# Practice pack: solution-architect

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## AWS SA Pro and Google Cloud Architect: the Well-Architected trade-off per choice
- Turn each business need into a number before you pick a part: users, peak calls per minute, data size, wait budget, RTO, RPO, monthly cost cap.
- For each real choice write one line per pillar it moves (operational excellence, security, reliability, performance, cost, sustainability) and name the pillar it gives up.
- Read how the criteria rank: "least operational effort", "lowest cost" and "highest availability" pick different answers; say which one wins when they clash.
- A managed platform service beats self-run software unless a stated need (control, licence, cost at measured volume) says otherwise.
- Split the user's wait budget over the hops (gateway, backend, database, each outside call); each call's timeout comes from its share.
- Monthly cost estimate as a table: item, unit, quantity, price source, cost now, cost at 1-year volume; include every environment, log volume, egress, backups and AI tokens; name the top driver.
- Failure-mode table per component: down, slow, wrong data; who is hit (one user, one tenant, all tenants); how we detect it; what the user sees; how it recovers.
- Shrink the blast radius: per-tenant limits, a separate bounded pool per outside system, jobs apart from user requests, so one slow dependency cannot take every request thread.
- Pick the cheapest recovery tier that meets RTO and RPO (backup and restore, pilot light, warm standby, active-active) and write why the next tier up is not needed.
- High availability across zones in one region is the default; a second region only when an RTO or a regulation demands it, and for EU customers that region is in the EU too.
- Tenancy model per product: pool (shared tables, tenant column) by default; silo (own schema or database) only when a contract or regulation requires it; bridge mixes them per tier.
- Noisy neighbour: one tenant's import or report must not slow the others; name the quota or the queue that stops it.
- Caching only for a measured read-heavy path; name the key (tenant in it), the expiry and who invalidates it.
- Moving an existing system: per part pick retire, retain, rehost, relocate, replatform, repurchase or refactor; refactor only the part the criteria need.
- An AI call is an outside call with a price per token: a budget per request and per month, a hard cap, and the behaviour when the model is down.

## TOGAF Practitioner: deciding, recording and slicing the architecture
- Map the work to the ADM without ceremony: A is scope, stakeholders and constraints; B to D are the business, data, application and technology views; E and F are the release slices; G checks the build against the design; H is a change request.
- Gap table per domain: baseline, target, and each gap as new, changed or removed; every removed item names its migration path.
- Each view answers one stakeholder's concern: journeys for the product owner, modules and contracts for developers, deploy units for operations, trust boundaries for security.
- Building blocks: reuse a platform or base service before a custom one, and name the one you reuse.
- Principles in four parts (name, statement, rationale, implications); a design that breaks one gets a recorded exception, never a quiet workaround.
- A choice is irreversible, so it needs an ADR, when undoing it costs more than one sprint, needs a data migration, breaks a contract or binds us to a vendor or licence.
- ADR content: context, options including "do nothing", decision, consequences, cost to reverse, and the trigger that reopens it.
- An accepted ADR is never edited; a new ADR supersedes it and the two link to each other.
- Transition architectures: when the target cannot ship at once, define the smallest first slice that meets this release's criteria and stop there.
- Architecture contract at the build gate: list what the build must conform to (modules, contracts, access, data) so the review can tick it item by item.

## SAP BTP Solution Architect (P_BTPA): fitting the design to BTP
- (SAP) Keep the core clean: extend SuccessFactors side by side on BTP through its public APIs and events; never change the SuccessFactors system itself.
- (SAP) Map each need to a BTP service the base already binds (XSUAA, destination, database, logging) before adding a service or an entitlement.
- (SAP) Subaccount in an EU region for EU customers, with the database, destinations and AI services in the same region; a service missing there is a finding.
- (SAP) Single-tenant (a subaccount per customer) is simpler to run per customer; a multitenant SaaS app needs subscription callbacks and per-tenant routes; choose by customer count and operations cost, with an ADR.
- (SAP) Cloud systems through the destination service; on-premise systems through Cloud Connector and the connectivity service; principal propagation only when the user's identity must reach the target.
- (SAP) IAS as the proxy to the customer's corporate identity provider; XSUAA holds the app's scopes.
- (SAP) Cost: price each service plan in the SAP Discovery Center estimator and name the contract model (consumption credits or subscription), since it changes what one more instance costs.
- (SAP) Start from an SAP reference architecture when one matches the scenario, and say what you leave out of it.

## Traps
- Active-active across regions for a 99.9% target: double cost and complexity for no criterion; fix: zones in one region plus a tested restore.
- Retries at every layer multiply: 3 tries at 3 layers is up to 27 calls on the last system; fix: retry at one layer only.
- A cost estimate for production only misses test and dev spaces, logs and backups; fix: one row per environment.
- A shared dependency nobody lists (identity provider, gateway, database) sits in every blast radius; fix: name it and accept the risk in writing.
- Availability claimed for the app alone: the user feels the product of every serial dependency; fix: multiply them.
- ADR written after the build records, it does not decide; fix: write it at the design gate.
- "Future scale" used to justify a queue, a cache or a new service with no number; fix: write the threshold that would trigger it, and stop.

## Numbers
- Cost per month: about 730 hours per month.
- Allowed downtime per 30-day month: 99% = 7.2 h, 99.5% = 3.6 h, 99.9% = 43.2 min, 99.95% = 21.6 min, 99.99% = 4.3 min.
- Serial availability multiplies: three dependencies at 99.9% each give about 99.7%.
- Recovery tiers, typical RTO: backup and restore hours; pilot light tens of minutes; warm standby minutes; active-active near zero.
