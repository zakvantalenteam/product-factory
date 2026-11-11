# Your first day with the agent team

A team of AI agents helps you write requirements, build, fix, test and release. You give the request and make the
decisions; the agents do the work and stop when something needs you. This page takes about 10 minutes.

## 1. Install (once)
1. Install Claude Code: the Claude desktop app (Code tab) or the `claude` command in a terminal.
2. Add the plugin. In a terminal `claude` session type:
   ```
   /plugin marketplace add https://github.com/zakvantalenteam/product-factory.git
   /plugin install product-factory@talenteam
   ```
   In the desktop app, add these two keys to your user settings (`~/.claude/settings.json`) instead:
   ```json
   "extraKnownMarketplaces": {
     "talenteam": {"source": {"source": "git", "url": "https://github.com/zakvantalenteam/product-factory.git"}, "autoUpdate": true}
   },
   "enabledPlugins": {"product-factory@talenteam": true}
   ```
   The repository is public, so no sign-in is needed. On a company network that fails with "unable to get local
   issuer certificate": run `git config --global http.sslBackend schannel` and add it again.
3. Start a new session. Typing `/product-factory:` lists the commands. Updates arrive by themselves.

Developers and QA also need the product's code: clone the product repo and open Claude Code in it. A product owner
or analyst does not: any folder works (step 2).

## 2. Your first command
| You are | Open Claude Code in | Type |
|---|---|---|
| Product owner or analyst | any folder (a new empty folder is fine) | `/product-factory:review-spec` and paste the ticket text, attach the document, or give a Jira key |
| Developer | the product repo | `/product-factory:develop BLEN-123` (a feature or change) or `/product-factory:fix BLEN-123` (a bug) |
| QA | the product repo | `/product-factory:test BLEN-123`; later `/product-factory:test retest BLEN-123` |
| Release manager | the product repo, on the release branch | `/product-factory:release OCT2026` |
| On call | the product repo, on the release branch | `/product-factory:fix --hotfix BLEN-123` |
| Engineering manager | the product repo | `python .claude/core/scripts/live_status.py share --all` |

Not sure which one? Describe what you need in plain words; the team picks the right command and says which.

In a product repo that carries its own copy of the core, the same commands also show without `product-factory:` and
are marked "(repo copy)". With the plugin on, use the `product-factory:` ones.

## 3. Where things land
- **Everything about one ticket:** in the work folder, `.claude/work/<ticket>/` in a product repo, or `requirements/<ticket>/` in a folder with no code. That covers requirements (`spec.md`), the size (`estimate.md`), designs, reviews, the test results (`qa-signoff.md`), the fix list (`fix-list.md`) and the release notes (`release.md`).
- **To follow a ticket live:** the live page shows every agent at work, its steps, and its tokens with an estimated cost. Open it with `python .claude/core/scripts/live_status.py open <ticket>`.
- **To send a ticket's status to someone:** `live_status.py share <ticket>` writes `share.html`, one file that opens without internet. Sending it is up to you.
- **To share requirements:** an approved requirement also gets an HTML copy you can send.

## 4. What needs your approval
The agents stop and ask; nothing goes past these points without your yes:
- **Product owner or analyst:** the requirements and the size, at one gate. Posting to Jira needs a separate yes.
- **Developer:**
  - gaps in the request;
  - design decisions (decision cards D1-D8: data, API, access, dependencies, go-live);
  - the pick between prototype variants of a new screen;
  - starting a fix.
- **QA:** creating test data (the data map is approved once), and deleting test data.
- **Release manager:** go or no-go, at one gate.

## 5. What the agents never do
- They never commit, push, pull or merge: you do all git.
- They never start or restart servers. They say what needs a restart.
- They never deploy anything, and never touch production data.
- They never copy secrets, passwords or personal data into files or chat.

Questions about how it works: ask in the session ("how does /test work?"). The full detail is in
`.claude/core/reference/how-work-flows.md`.
