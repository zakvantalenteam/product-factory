# Frontend / backend responsibilities

The architect assigns every story task to exactly one side, using this split. A task that needs both sides
is two tasks joined by an OpenAPI operation id.

| Concern | Backend owns | Frontend owns |
|---|---|---|
| Business rules | all rules, calculations, state transitions, validation that matters | nothing authoritative; may repeat simple validation for fast feedback |
| Security | authentication, authorization per operation and per record, tenant isolation, rate limits | hiding what the user cannot do (UX only), never storing secrets |
| Data | persistence, transactions, audit, consistency, paging, sorting, filtering, search | caching server data (query library), optimistic UI, no business data in local storage |
| Contract | implements `05-openapi.yaml` exactly; contract tests | uses generated types/clients from the contract; mocks until ready |
| Errors | problem-details with stable codes | maps codes to translated messages; empty, loading, error, no-permission states |
| Text | stable codes and data, never UI sentences | all labels, i18n, formatting of dates/numbers per locale |
| Integrations | every external system call (SAP, Azure, AI), secrets, retries | never calls third parties directly |
| Background work | jobs, schedules, imports, notifications | shows job status and results |
| Look and feel | - | theme tokens, layout, accessibility (keyboard, contrast, screen reader), responsive |

Rules
- No endpoint shaped for one screen's convenience if it leaks business logic to the UI; screen-specific
  read models are fine when the backend computes them.
- No direct database access from anything but the backend's repository layer.
- Feature folders mirror each other: backend `<module>/controller|service|repository|domain|dto|mapper`,
  frontend `features/<module>/api|components|hooks|types|queryKeys`.
