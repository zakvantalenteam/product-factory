# Data standards (enterprise database design)

The data model is designed, explained and approved (G3) before any entity is written. It must hold up at
high volume and grow without redesign. "Store it as JSON in one column" is not a design.

## Modelling
- Start from the domain: entities, relationships, cardinality, lifecycle (created, changed, archived,
  deleted) and who owns each record. Draw it (Mermaid `erDiagram`) with example rows.
- Normalise to 3NF. Denormalise only with a written reason (a measured read path), in `decisions.md`.
- Reference data (statuses, types, countries) in lookup tables or enums with a decision for which; values
  that admins edit are tables.
- Many-to-many through a join table with its own key and audit columns.
- JSON/CLOB columns only for truly unstructured, never-queried payloads; say why per column.
- Multi-tenant: every business table has `tenant_id`, part of every unique key and every index that
  serves a tenant query. Decide and record: row-level tenant column vs schema per tenant.

## Naming
- Tables plural snake_case with a module prefix (`prj_projects`, `prj_tasks`), columns snake_case,
  FK columns `<entity>_id`, indexes `ix_<table>_<cols>`, unique `uq_<table>_<cols>`, FKs `fk_<table>_<ref>`.
- No reserved words, no quoted identifiers.

## Every business table has
- `id` (UUID or sequence-backed BIGINT - one choice per product, recorded), `tenant_id`.
- `created_at`, `created_by`, `updated_at`, `updated_by`, `version` (optimistic locking).
- Soft delete where users can delete: `deleted_at`, `deleted_by`; unique keys exclude deleted rows.
- Change history by default (see Audit). Opting a table out needs a written reason.

## Audit history (on by default)
- One generic audit design for the whole product: `aud_change_log` (id, tenant_id, entity_type,
  entity_id, action CREATE|UPDATE|DELETE|RESTORE, changed_by, changed_at, request_id) and
  `aud_change_field` (change_id, field, old_value, new_value), written by one entity listener, never by
  hand in services. Read API: `GET /api/v1/{resource}/{id}/history`. Retention period per product.
- Partition or archive the audit tables by time from day one (they are the biggest tables).

## Keys, constraints, indexes
- Every FK declared, with the delete rule chosen per relation (restrict / cascade / set null) and explained.
- NOT NULL by default; nullable needs a meaning. CHECK constraints for ranges and states.
- Index every FK and every column used in a filter, sort or join of a listed query; composite indexes
  match the query (`tenant_id` first). List the top queries and the index each uses.

## Volume and growth
- For each table: expected rows at go-live, after 1 year, after 5 years; growth per day; row size.
- Tables expected over ~10 M rows: partitioning strategy (by tenant or time), archiving, purge job.
- Paging on every list query; no `SELECT *` on wide tables; no N+1 (fetch plans named).
- Long-running work (imports, syncs) in background jobs with batch commits, not in request threads.

## Change and deploy
- Schema changes through the product's migration mechanism (named in the base spec); every change has
  a forward step, a backfill for existing rows and a rollback note. Never hand-edit generated DDL.
- Personal data: listed per column with purpose and retention; deletion/anonymisation path defined.

## Deliverable (`05-data-model.md`)
Diagram, table-by-table spec (column, type, length, null, default, key/index, meaning), example rows,
relationships and delete rules, top queries with indexes, volume table, partitioning/archiving, audit,
tenant isolation, personal data, migration plan, open questions.
