# Practice pack: data-architect

Read once at the start, in the same message as common.md. The practical knowledge behind your credentials: what a holder does differently on the job. Lines marked (SAP) apply only when `stack.platform` is `sap-btp`.

## DAMA CDMP: ownership, meaning, quality and lifecycle per table
- Name the system of record per business object: SuccessFactors for employee master data (our copy is read-only, keyed by its id plus the tenant), this product for its own objects; a copy never becomes a second master.
- Every table has a data owner (decides what it means and who may see it) and a steward (fixes bad rows); name both roles in the model.
- One line per column in the model: business meaning, unit, allowed values, source (entered here, or `entity.field` of the outside system) and class (public, internal, confidential, personal, special category).
- Reference data (statuses, languages, countries, levels) as code lists with labels by translation key; master data (people, org units, skills) with the source key.
- A quality rule per critical column, by dimension (completeness, validity, uniqueness, consistency, timeliness, accuracy), and where it is enforced: database constraint, service validation or sync-job reject.
- History per attribute: overwrite when only today matters; a new row with valid-from and valid-to when a report or rule must answer "as of a date" (effective-dated HR data is this kind).
- Lifecycle per table: create, use, archive, delete. Name the retention period and the job that enforces it; when security-architect has not set one, propose a period (for example 24 months after last use) marked to confirm, never an open question.
- Per personal column, delete or anonymise: hard delete when nothing depends on the row; otherwise replace identifiers and free text and keep the non-personal facts for totals.
- Model in three steps: conceptual (objects and links in plain words), logical (3NF, database-neutral), physical (types, indexes, partitions); when a product runs on two databases (for example PostgreSQL and, under (SAP), HANA), write the differences as a mapping, not two models.

## Google Data Engineer: loads, pipelines and reporting
- Batch delta on a schedule until the freshness criterion is shorter than the schedule; streaming only below that.
- Loads are idempotent: upsert on the natural key (source id plus tenant), so a rerun or a duplicate delivery gives the same rows.
- Exactly once is at-least-once delivery plus an idempotent write; plan for duplicates and late rows.
- Every load reconciles its counts (read, inserted, updated, rejected); rejected rows land in a reject table with the reason.
- Feed schema changes are additive first: a new source field becomes a new nullable column; a dropped one stays until no reader uses it.
- Reports and exports read a view, a projection or a replica sized for scans, not the hot transactional tables at peak; name which one.
- Append-only big tables (audit, events, sync logs) are partitioned by time, so retention drops a partition instead of running a mass delete.
- Personal columns are masked or replaced in every non-production copy; a support copy of production data is a named, time-limited exception.

## EDB Advanced for PostgreSQL: changes that do not lock or bloat
- Online index: `CREATE INDEX CONCURRENTLY` on live tables; it cannot run inside a transaction block, and a failed run leaves an INVALID index to drop and rebuild.
- New foreign key or CHECK on a big table: add it `NOT VALID`, then `VALIDATE CONSTRAINT` in a later step, which does not block writes.
- `SET NOT NULL` scans the table under a strong lock; from PostgreSQL 12 a validated `CHECK (col IS NOT NULL)` lets it skip the scan.
- `ADD COLUMN` with a constant default is a metadata change from PostgreSQL 11; a volatile default or a column type change rewrites the table.
- Every migration sets `lock_timeout` (for example 5 s), so a blocked ALTER fails fast instead of queueing all traffic behind it.
- MVCC: an UPDATE writes a new row version; often-updated tables get per-table autovacuum settings and a fillfactor below 100, so updates that change no indexed column stay on the page.
- Long or idle-in-transaction sessions block vacuum and hold locks: set `idle_in_transaction_session_timeout` and a `statement_timeout` for the app role.
- Index type by query: B-tree by default; GIN for jsonb, arrays and full text; BRIN for very large tables written in time order; an expression index for `lower(email)`.
- Range partitioning (for example by month): every primary and unique key must include the partition key; old partitions are detached and dropped.
- Read a plan for estimated vs actual rows: a large gap means stale statistics (`ANALYZE`); a sequential scan of a big table under a selective filter means a missing index.
- Each connection is a server process: pool size per instance times instances stays under `max_connections` minus a reserve for admin and migrations.
- Point-in-time restore needs a base backup plus archived WAL; `pg_dump` is a logical copy, not a recovery plan; test the restore.
- Replicas are read-only and lag: a read that must see the user's own write goes to the primary.

## SAP HANA Data Engineer (C_HAMOD): HANA models and data access
- (SAP) Tables come from JPA (settled); HDI artefacts only for reporting views or synonyms, and never two owners for one table.
- (SAP) Business logic stays in the Java service; SQLScript table functions only feed reporting views.
- (SAP) Calculation views are for reporting: dimension views for master data, cube views with a star join for measures; filter early with input parameters and aggregate before joining.
- (SAP) No calculated column on a join key or a filter column in a calculation view: it stops the filter being pushed down.
- (SAP) Row-level reporting access through analytic privileges on the view; the app's technical user holds object privileges on its own schema only.
- (SAP) Remote data: a virtual table (Smart Data Access) when queries are rare and latency is fine; replicate only when query speed or availability needs a local copy.
- (SAP) Memory drives HANA Cloud cost: size from the compressed column-store data; large cold tables (audit, history) as page loadable (Native Storage Extension) to keep them out of memory.
- (SAP) Column store by default; row store only for a small table written very often and always read as whole rows.
- (SAP) Text longer than 5000 characters needs `NCLOB`; keep LOB columns out of keys, WHERE and ORDER BY.

## Traps
- A NOT NULL column or unique key added with its backfill in one PostgreSQL migration on a big table: a long lock; fix: add, backfill in batches, validate, then enforce.
- Exact `COUNT(*)` for every page of a big PostgreSQL list scans the table each time; fix: "has next page" or a capped count.
- An index on a low-selectivity column alone (status, flag) is rarely used; fix: put it after the tenant and a selective column, or a partial index for the rare value (PostgreSQL).
- Source times stored as local time: deltas skip or repeat rows around a daylight-saving change; fix: store the source's UTC instant.
- Generated index or constraint names longer than one database allows fail only there; fix: name them explicitly, within both limits.
- A month-end report on the live tables slows every user; fix: a reporting view or replica and a time window.

## Numbers
- PostgreSQL: default `max_connections` 100; page size 8 kB; rows over about 2 kB get large values compressed or moved to TOAST.
- Identifier length: PostgreSQL 63 bytes; (SAP) HANA 127 characters.
- (SAP) HANA: `NVARCHAR` up to 5000 characters; a column-store table or partition holds at most about 2.1 billion rows, so partition well before that.
