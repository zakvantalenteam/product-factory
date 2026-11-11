---
name: release
description: "Use when the developer types /release, asks for a go or no-go, release notes or a release check for a release branch (for example OCT2026) or a list of tickets, or the sdlc triage routes a release here. Owns the go or no-go of one release: the tickets in it (the branch's git log against the last release, plus the work folders), each ticket's QA sign-off (a missing one is a NO-GO item), migrations and upgrade jobs, config keys, labels and the translation pass, restarts, the smoke pack's P1 items on the release candidate (through /test smoke), release notes in plain words for the business plus technical notes, rollback triggers and steps, and one gate with the developer. release-manager leads, qa-lead checks the sign-offs and the smoke run, devops-engineer writes the deploy plan. Never deploys, merges, tags or pushes."
---
# Release (go or no-go)

Paths: `<work>` is `work_dir` in `.claude/project.json` (default `.claude/work`); `live_status.py` is
`python .claude/core/scripts/live_status.py`. The shared rules live once, in the `sdlc` skill: briefing.md, gates
and decision cards (section 7), live status (section 6) and the lessons loop (section 9). Every rule in them applies;
this file adds only what is particular to a release.

You are the Tech Lead of this run. You find what is in the release, start the agents, run the smoke on the release
candidate through `/test smoke`, and stop at one gate. You never deploy, merge, tag, push or edit code.

## One job
| The request | Whose |
|---|---|
| A release branch or a ticket list to ship: go or no-go, release notes, rollback | yours |
| Testing one ticket, a retest | `/test` |
| A NO-GO item to fix | `/fix` (the developer starts it) |
| Something broken in production now | `/fix --hotfix <ticket>` |

## Commands
| Command | What runs |
|---|---|
| `/release OCT2026` | the release branch against the last release before it |
| `/release OCT2026 --base SEP2026` | the same, with the base named |
| `/release BLEN-1 BLEN-2` | a ticket list with no branch: the same checks for those tickets |
| `/release OCT2026 notes` | the release notes again from a finished go or no-go |

## 1. Start
1. `live_status.py init release-<branch> --mode task --skill release --title "Release <branch>"` (a ticket list:
   `release-<date>`). The folder is `<work>/release-<branch>/`; an existing one goes on from where it stopped.
2. Scope, with read-only git only (`git log`, `git branch --list`, `git diff --stat`; never fetch, pull, checkout or
   switch): `git log --oneline <base>..<branch>`. The base is the release the developer names, else the newest
   earlier release branch; ask once when it is not clear, with your recommendation. A branch that is not local: ask
   the developer to fetch it.
3. Write `<work>/release-<branch>/tickets.md`: one row per ticket (from the commit subjects and `ticket_prefix` in
   project.json): `| Ticket | Title | Commits | Work folder | QA verdict | Open MUST | Data | Smoke |`, read from each
   `<work>/<id>/status.json` and `qa-signoff.md`. Commits with no ticket get their own rows (`no ticket`).

## 2. The evidence (in one message)
- `qa-lead` (mode `release`): every ticket's sign-off and fix list into `qa-release.md`; a ticket with no SIGNED OFF
  is a NO-GO item; the smoke scope for the release candidate (every P1 item, plus the areas the release touches).
- `devops-engineer` (mode `deploy-plan`, release folder): `deploy-plan.md` with the environments in order,
  migrations and upgrade jobs, config keys per environment by name (never values), restarts, health checks and the
  rollback steps.

## 3. Smoke on the release candidate
Ask where the release candidate runs (a test host, never production). Then the `/test smoke` steps of the test skill
(`skills/test/data-and-smoke.md`) with the run titled `smoke <branch>`, briefed with the scope from `qa-release.md`.
A P1 FAIL is a NO-GO item. The release candidate is not running: the smoke stays `not run`, which is a NO-GO item
unless the developer accepts the risk in their own words.

## 4. Go or no-go
`release-manager` (mode `release`, release folder) reads `tickets.md`, `qa-release.md`, `deploy-plan.md` and the
smoke result and writes `release.md`:
- `## Go / no-go`: the verdict line, then `### NO-GO items` first (each with its owner and the skill that clears it);
- `## What ships`: the tickets in plain words;
- `## Release notes`: `### For the business` (what users and admins will see, per area, plain words, no ticket jargon)
  and `### Technical notes` (migrations, upgrade jobs, config keys by name, labels and the translation pass, contract
  changes, restarts);
- `## Rollback`: the triggers table and the steps;
- the go-live card `decisions/D8-go-live.md` (sdlc section 7).
Then `python .claude/core/scripts/md_to_html.py <work>/release-<branch>/release.md` for an offline copy to share.

## 5. The gate (one)
`live_status.py gate release-<branch> release "Go for <branch>?" --file <work>/release-<branch>/release.md
--decision D8`. Show the NO-GO items first, then the notes in short, and ask (Claude desktop app: Go and No-go).
- Go: `ok release-<branch> release --note "<their words>"`, then `live_status.py next release-<branch> "deploy
  <branch> (developer)"`. The developer or the pipeline deploys.
- No-go: each NO-GO item goes to its skill (a missing sign-off to `/test <id>`, a failure to `/fix <id>`); the
  developer starts them. Run `/release <branch>` again afterwards: finished checks are reused.

## Rules
- Read-only on code; git read-only; never production; no personal data, secret values or internal names in the
  release notes.
- A ticket closes only on SIGNED OFF (`/test`); this skill reads sign-offs, it never writes one.
- Keep the live page current: the stage lines, the gate and `next`.
