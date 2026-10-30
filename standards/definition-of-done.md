# Definition of Done (fixed MUST list)

Reviewers and the auditor check every item. A failed MUST blocks the gate. Anything else they find goes
to a LATER backlog in their report, never into this list. The list changes only when the developer asks.

## Product
- M1 Every story's acceptance criteria are met and shown (test or recorded check).
- M2 No open gap or product-critic issue marked "blocker" in `questions.md`.
- M3 Every screen has empty, loading, error and no-permission states.

## Contract and architecture
- M4 Implementation matches `05-openapi.yaml` (paths, methods, schemas, codes); lint has zero errors.
- M5 Every task sits on the side `fe-be-split.md` assigns; no business rule only in the frontend.
- M6 Errors are problem-details with stable codes; no stack traces or internals returned.

## Data
- M7 Schema matches `05-data-model.md`; every table has tenant, audit columns, version; FKs and indexes
  as designed; change history writes for every business table.
- M8 Every list is paged and bounded; no N+1 on listed queries.
- M9 Schema change goes through the migration mechanism with rollback note.

## Security and privacy
- M10 Every endpoint checks authorization in the backend, per operation and per record; tenant isolation
  tested.
- M11 No secrets in code, docs, logs or chat; no personal data in URLs or logs.
- M12 Input validated server-side; output encoded; dependencies have no known critical CVE.

## Quality
- M13 Unit tests for rules and services; contract/API tests for every operation; one end-to-end test per
  main journey. All pass.
- M14 No new lint/type errors; code follows the base conventions (B9 of the base spec).
- M15 All user-facing text is in the i18n files (English key set complete); theme tokens only, no fixed
  colours; keyboard focus visible.
- M16 Logs carry the request id; background jobs record status and errors.
