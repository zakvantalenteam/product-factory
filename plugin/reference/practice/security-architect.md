# Practice pack: security-architect

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## CIPP/E: a lawful basis, a purpose and a retention for each personal field
- Inventory row per personal field: table.column, category (identity, contact, employment, learning record, special category), purpose, lawful basis, retention, who sees it, where copies go.
- The customer (employer) is the controller; we are its processor under a data processing agreement; every sub-processor (hosting, AI model provider, workflow host, email) is listed, and a new one is announced to the customer before use.
- Lawful basis per purpose (Art. 6(1)): contract or legitimate interests for running learning and HR processes; legal obligation where a law requires the record; consent only for truly optional features.
- Legitimate interests needs a written balancing test (purpose, necessity, balance against the employee's reasonable expectations), kept with the design.
- Special categories (Art. 9: health including disability, ethnic origin, religion or beliefs, union membership, biometrics for identification, sex life or orientation, genetics, political opinions) also need an Art. 9(2) condition; by default do not collect them.
- Minimisation: copy from SuccessFactors only the fields this purpose needs; "useful later" is not a purpose.
- Purpose limitation: data collected for learning is not reused for rating, promotion or dismissal without a new basis and a notice.
- Retention per table is a period plus a start event (for example "contract end + N months, N set by the customer") and the job that deletes or anonymises; "kept forever" is never a retention.
- Rights the product must support: access and copy (Art. 15), rectification (16), erasure (17), restriction (18), portability (20), objection (21); the customer answers, we provide the export and delete functions.
- No decision with legal or similarly significant effect on an employee by automated means alone (Art. 22): AI rankings and match scores are suggestions a person reviews.
- A DPIA (Art. 35) comes before profiling or systematically scoring employees, or large-scale special category data; flag it to the controller.
- Data leaving the EEA (an AI endpoint, a support tool) needs an adequacy decision or standard contractual clauses with a transfer assessment; prefer EU endpoints.
- Pseudonymised data (a key exists somewhere) is still personal data; only irreversible anonymisation is outside GDPR.
- Non-essential cookies and tracking need consent; the sign-in session cookie is strictly necessary and does not.
- Works councils (in Germany by law) co-decide on any tool able to monitor employee behaviour or performance: show managers aggregates by default and leave per-person views as a customer decision.

## CISSP: classification, least privilege and threats per boundary
- Classify every field (public, internal, confidential, personal, special category, secret); each class maps to fixed controls: encryption, masking outside production, never logged, export allowed or not.
- Access lifecycle: joiner, mover, leaver; a mover loses the old role on the move; a leaver loses access when the identity provider disables them, not when someone remembers.
- Separation of duties: whoever assigns roles is not whoever uses the admin function; nobody can grant themselves a scope.
- Role-based access for functions plus record rules (own, team, tenant) for rows; write both in the matrix.
- STRIDE per trust boundary: browser to gateway, gateway to backend, backend to database, backend to each outside system, workflow callbacks into the backend, admin screens; one row per threat with its control, place and test.
- Each STRIDE letter names the property it breaks: spoofing (authentication), tampering (integrity), repudiation (audit), information disclosure (confidentiality), denial of service (availability), elevation of privilege (authorisation).
- Risk is likelihood times impact; treat it by reducing, transferring, avoiding or accepting; an accepted risk is signed by the owner with a review date.
- Audit record: who (user id), what, which record, when (UTC), from where, outcome; append-only for the app user; kept apart from business data, with its own retention.
- Webhook and callback signatures: HMAC-SHA256 over the body and a timestamp, compared in constant time, rejected outside a short window to stop replay.
- Defence in depth: the same rule at the gateway (who may call), the service (who may act on this record) and the database (tenant column, constraints).
- (SAP) One role collection per product role, built from role templates; admin and business templates never share a collection; platform admin roles never go to app users.
- (SAP) Map the customer's identity provider groups to role collections through IAS, so joiners, movers and leavers follow the customer's directory; no hand assignment to named users.
- SuccessFactors role-based permissions do not travel with copied data: our matrix restates the "who may see whom" rule for every copied field.

## CCSP: cloud data security, shared responsibility and every copy
- Shared responsibility on a platform service: the provider runs hardware, host and runtime patches; we own code, configuration, identities, access, data and the keys we manage; write the owner per control.
- Cloud data lifecycle: create, store, use, share, archive, destroy; per stage name where the data sits and who can read it.
- Copies count: logs, backups, workflow execution history, AI provider logs, exports, caches and search indexes hold personal data and need the same retention and deletion.
- Erasure: delete from live tables at once and state that backups age out within the backup retention period; a restore reapplies the deletions.
- Tenant isolation covers more than queries: cache keys, file paths, queue names, log searches and AI context all carry the tenant.
- AI and SaaS sub-processors: the contract says no training on our data, prompt retention off or minimal, EU processing region.
- Keys: platform-managed encryption by default; customer-managed keys only when a contract demands them, with the rotation owner named.
- Supply chain: a dependency scan and a software bill of materials per release; a known critical vulnerability with a fix blocks the release.
- (SAP) Destinations: a named technical user with read-only rights on the needed entities for jobs; SAML bearer assertion (principal propagation) when the call must act as the user.
- (SAP) Set the token validity in the security descriptor on purpose, from the risk; never leave the default unexamined.
- (SAP) Every approuter route that skips login is its own trust boundary row in STRIDE.
- (SAP) Security events (role changes, failed logins, admin settings) also go to the BTP audit log service, not only to app logs.

## Traps
- Consent as the basis for employee data: rarely freely given and it can be withdrawn, which breaks the feature; fix: contract or legitimate interests with a balancing test.
- Retention set on the main table only: logs, backups, workflow history and exports keep the data; fix: list every copy per field with its own deletion.
- Personal data in a prompt to a model endpoint outside the EEA is an unplanned transfer; fix: an EU endpoint, or minimised and pseudonymised input.
- Production data copied to a test space to chase a bug is an uncontrolled copy; fix: masked data, or a logged, time-limited exception.
- Admin rights granted "for now" with no end become privilege creep; fix: an expiry and a periodic access review.
- A signature without a timestamp: a captured request can be replayed; fix: sign the timestamp and enforce a short window.

## Numbers
- Breach: the controller tells the supervisory authority within 72 h of becoming aware; the processor tells the controller without undue delay (the DPA sets the hours).
- Data subject requests: answer within 1 month, extendable by 2 more months for complex or many requests.
- GDPR fines: up to EUR 20 million or 4% of worldwide annual turnover, whichever is higher; lower tier EUR 10 million or 2%.
- TLS 1.2 minimum, 1.3 preferred; signature replay window a few minutes (for example 5 min).
