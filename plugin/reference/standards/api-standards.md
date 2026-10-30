# API standards

Contract first: `work/<slug>/05-openapi.yaml` is written and approved (G3) before any endpoint or screen is
built. Backend implements it; frontend codes against it (generated types, mock server until the backend is
ready). A change to an endpoint changes the contract first, in the same change.

## Contract
- OpenAPI 3.1, one file per product, `info.version` semver. Every operation has `operationId`
  (`verbNoun`, e.g. `listProjects`), `summary`, `tags` (one per module), every response code it can return,
  and request/response schemas in `components/schemas` (no inline object schemas).
- Every schema property has `type`, `description`, constraints (`maxLength`, `minimum`, `enum`, `format`),
  and `required` lists. Ids are `string` `format: uuid`. Dates `format: date-time`, UTC, ISO 8601.
- Examples for every request body and every 2xx response.
- Security schemes declared; every operation lists the scopes/roles it needs (`x-roles: [ADMIN]`).
- Lint clean: `npx @redocly/cli lint 05-openapi.yaml` (or Spectral `spectral:oas`) with zero errors.

## Resources and paths
- `/api/v1/<plural-noun>` and `/api/v1/<plural-noun>/{id}`; child resources one level deep
  (`/projects/{projectId}/tasks`). kebab-case paths, camelCase JSON fields. No verbs in paths, except
  actions that are not CRUD: `POST /projects/{id}:archive` or `POST /projects/{id}/archive` - pick one style
  per product and record it in `decisions.md`.
- Methods: GET read (safe), POST create (201 + `Location`), PUT full replace, PATCH partial
  (`application/merge-patch+json`), DELETE (204). Idempotency key header for POSTs that create money or
  side effects outside the system.

## Responses
- Success body is the resource or `{ "items": [...], "page": {...} }` for lists. No generic wrapper with
  `success: true`.
- Errors: RFC 9457 problem details (`application/problem+json`): `type`, `title`, `status`, `detail`,
  `instance`, plus `code` (stable machine code, e.g. `PROJECT_NAME_TAKEN`), `traceId`, and `errors[]`
  (`field`, `code`, `message`) for validation. 400 validation, 401 not signed in, 403 not allowed,
  404 not found (also for "exists but not yours"), 409 conflict / stale version, 422 business rule,
  429 rate limit, 500 with no internals.
- Concurrency: every updatable resource returns `version` (or `ETag`); PUT/PATCH require it
  (`If-Match`), mismatch = 409.

## Lists
- Paging: `?page=0&size=20` (max size 100) or cursor (`?cursor=&limit=`) for large or live data; response
  `page: { number, size, totalElements, totalPages }` or `{ nextCursor }`.
- Sorting `?sort=name,asc`; filtering by named params (`?status=OPEN&ownerId=`); free search `?q=`.
- Every list endpoint is bounded: no endpoint returns an unbounded collection.

## Versioning and change
- `/v1` in the path. Additive changes (new optional field, new endpoint) stay in v1. Breaking changes
  (removed/renamed field, new required field, changed meaning) need v2 and a deprecation note
  (`deprecated: true`, `Sunset` header).

## Cross-cutting
- Auth on every endpoint except health; authorization checked in the backend per operation and per record
  (the frontend hiding a button is not security).
- Audit: every write records who, when, what changed (see data standards).
- Correlation: accept/return `X-Request-Id`; logs carry it.
- No personal data in URLs or query strings.
