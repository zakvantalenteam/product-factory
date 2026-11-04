# Where this repo uses SuccessFactors

Read by `sf-expert` and `sf-skills-expert` next to the generic reference (`.claude/core/reference/domains/successfactors.md`). Keep it
to facts with `path:line`. No secrets, hosts, company ids, user ids or personal data: name the key only.
Delete this line and the hints in brackets when you fill it in.

## Areas
| Area (screen, job, tool or sync) | SuccessFactors API and entity | Read or write | Code (`path:line`) | Notes (select, filter, paging, delta) |
|---|---|---|---|---|
| (for example team members) | (for example OData v2 `User` by manager) | read | `<path>:<line>` | |

## Clients and authentication
- Client classes and the one place that builds the request: `<path>:<line>`
- Auth in use (API user, the user's own token, SAML bearer): `<how>`; where the token is cached and for how long: `<path>:<line>`
- Timeouts, retry, paging, delta and batch used today: `<what and where>`
- Config keys that hold hosts, company or tenant ids and credentials (names only): `<keys>`

## Data kept
| SuccessFactors field | Stored where (table, cache, log, LLM prompt) | Why needed |
|---|---|---|

## Known traps and weak spots
- (for example per-row calls in a loop, string-built `$filter`, a token in a log line, inactive users left out)

## Sister repos (read only when a task names them)
- `<repo path>`: what it calls and where (`path:line`)
