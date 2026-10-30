# Product factory

One shared team of AI agents and one delivery flow for Claude Code and Cursor, used by every TalenTeam product
repo. It is also where new products are made. Change the core here and push to `main`: every product repo gets the
new version, and Claude users get it as a plugin.

## What is in this repo

| Path | What |
|---|---|
| `core/` | The agent core source: agents, skills, hooks, scripts, reference, templates. `core/core-plan.md` is its design and change log. |
| `plugin/` | The Claude Code plugin `agent-core`, built from `core/` by `core/scripts/build_plugin.py`. Do not edit by hand. |
| `.claude-plugin/marketplace.json` | Makes this repo a Claude Code plugin marketplace (`talenteam`). |
| `.github/workflows/core-sync.yml`, `.github/core-sync/` | The sync bot that installs the core into each product repo. |
| `.claude/`, `.cursor/`, `AGENTS.md`, `CLAUDE.md` | The core installed for this repo itself. |
| `work/<slug>/` | One folder per product or task: documents, questions, decisions and live status. |
| `base/`, `standards/`, `scripts/`, `prototypes/` | Older copies and prototypes; the core's own copies live in `core/`. |

## How people get it

**Product repos (Claude Code and Cursor, nothing to install).** On each push to `main` that changes the core,
the `core-sync` workflow installs it into every repo in `.github/core-sync/targets.json` (SkillsOS on GitHub,
Blend and TalentBox on AWS CodeCommit). It runs the checks and pushes one commit to `dev`. When a person must look,
it opens a pull request instead: a first install, a core file edited by hand in that repo, a failed check, or a
protected branch. Developers get the update with their normal `git pull`.

**Any other repo (Claude Code only): the plugin.** Each person sets it up once (steps below). Repos that carry the
core switch the plugin off in their own settings, so nothing runs twice. To give a repo the core for the whole team
(Cursor too), run `python <plugin or core>/scripts/install.py <repo> --write-settings` once and commit the result.

### Set up the plugin (each Claude Code user, once)

1. Get read access to `talenteam/product-factory` from a GitHub org owner. The repo is private; nobody outside
   the org can see it.
2. Check that git reaches it over HTTPS without asking for a password:
   `git ls-remote https://github.com/talenteam/product-factory.git HEAD` must print one line. On Windows, Git
   Credential Manager asks you to sign in to GitHub the first time; after that it remembers you.
3. Add the marketplace and the plugin. Either type in Claude Code (terminal, desktop app or IDE):

   ```
   /plugin marketplace add https://github.com/talenteam/product-factory.git
   /plugin install agent-core@talenteam
   ```

   then `/plugin` > Marketplaces > talenteam > Enable auto-update. Or add these two keys to your user settings
   (`~/.claude/settings.json`), which also turns on auto-update:

   ```json
   "extraKnownMarketplaces": {
     "talenteam": {"source": {"source": "git", "url": "https://github.com/talenteam/product-factory.git"}, "autoUpdate": true}
   },
   "enabledPlugins": {"agent-core@talenteam": true}
   ```

4. Start a new session in a repo that does not carry the core. `/agents` lists `agent-core:explorer` and the
   others, and the skills show as `/agent-core:sdlc` and so on.
5. Updates: a new version reaches you within about 10 minutes of starting a session; `/reload-plugins` applies it.
   Nothing changes until the version in `core/VERSION` is raised.

## The agents

Every agent runs on Opus. The agents that decide get about 35 tool calls, the others about 20.

| Team | Agents |
|---|---|
| Lead | the main session (triage, briefs, gates, builds in task mode) |
| Product | `spec-analyst`, `product-critic`, `story-sizer` |
| Design | `ux-designer` |
| Architecture | `solution-architect`, `data-architect`, `security-architect` |
| Engineering | `base-builder`, `backend-developer`, `frontend-developer`, `integration-engineer` |
| Domain experts | `sf-expert` (SuccessFactors), `ai-engineer` (AI behaviour, orchestration, cost), `n8n-expert` (n8n workflows) |
| Quality | `code-reviewer`, `qa-engineer`, `verifier`, `performance-engineer`, `bug-investigator` |
| Audit | `audit-expert` |
| Operations | `devops-engineer`, `release-manager` |
| Helpers | `explorer` |

Each repo's own facts for the domain experts live in its `.claude/experts/<sf|ai|n8n>.md`.
Skills: `sdlc` (triage and task mode), `factory` (new products), `prototype`, `dev-handoff`, `commit-msg`, `verify-push`, `live-check`.

## How work flows

Every request is triaged first:
- **Answer**: a question is answered directly.
- **Quick fix**: a small, obvious change is made and recorded.
- **Setup work**: changes to the AI setup only.
- **Task**: a change to an existing product. A context pack comes first, the risk is set from evidence, only the agents the work needs join, and a safety net is scaled by risk.
- **Product**: a new product runs through intake, base, requirements, product review, prototype, stories, design, build, review, audit and release.

The developer decides at fixed gates: gaps, decision cards D1-D8, prototype picks.

Before anything is built, the flow asks what it needs to know:
- At intake, where and how a new product will run (`00-infra.md`).
- At requirements, every non-functional need with a number (`02-nfr.md`).
- In an existing repo, the deploy facts, asked once and kept in `.claude/project.json`.

Hooks enforce the rules in both tools. Agents never run git commands that change a repo, never start servers and
never copy secrets.

See the flow without real work: `python .claude/core/scripts/simulate.py --list`, then
`python .claude/core/scripts/simulate.py <request>`. This replays a sample request on the live status page.

## Releasing a change to the core

1. Change files in `core/` only.
2. Raise the version in `core/VERSION` and `core/.claude-plugin/plugin.json` (the same number). Plugin users are
   updated only when it changes.
3. `python core/scripts/install.py . --write-settings`: installs it here and rebuilds `plugin/`. Then
   `python .claude/core/scripts/install.py . --check` must print `ok`.
4. Commit and push to `main`. The workflow stops a push whose versions differ or whose `plugin/` is stale.

## One-time setup of the sync bot

Until these steps are done, a push to `main` gives a `core-sync` run whose summary names the missing step for each
repo. Nothing in the product repos changes. Steps 1, 2 and 4 need admin rights on this repo; step 3 needs an AWS
admin for the account that holds the CodeCommit repos (region `eu-west-2`).

**1. A GitHub token for SkillsOS.** Signed in as a person (or bot account) with write access to
`talenteam/SkillsOS`: picture > Settings > Developer settings > Personal access tokens > Fine-grained tokens >
Generate new token (https://github.com/settings/personal-access-tokens/new).
- Token name: any clear name (only the secret name in step 2 matters); Resource owner `talenteam`; Expiration at most a year (note the date: when it ends,
  the SkillsOS row fails until a new one is saved).
- Repository access: Only select repositories > `talenteam/SkillsOS`.
- Permissions > Repository permissions: Contents "Read and write", Pull requests "Read and write" (Metadata
  "Read-only" is added by itself).
- Generate token and copy it. If the org asks for approval, an org owner approves it under the org's Settings >
  Personal access tokens > Pending requests.

**2. Save the token in this repo.** Settings > Secrets and variables > Actions > New repository secret
(https://github.com/talenteam/product-factory/settings/secrets/actions/new): name `SYNC_GITHUB_TOKEN`, paste the
token, Add secret. GitHub never shows it again; to renew, save a new token under the same name.

**3. An AWS role the workflow may use (no AWS keys are stored).** Until steps 3 and 4 are done, the run skips the
CodeCommit repos (Blend, TalentBox) without failing; update those by hand with `install.py <repo> --write-settings`.
In the AWS console, IAM:
- Identity providers > Add provider: OpenID Connect, provider URL `https://token.actions.githubusercontent.com`,
  audience `sts.amazonaws.com`. Skip this if it is already listed.
- Roles > Create role > Web identity: that provider, audience `sts.amazonaws.com`, GitHub organization
  `talenteam`, repository `product-factory`, branch `main`. Attach no policies; role name `core-sync-bot`.
- Open the role > Trust relationships > Edit trust policy: paste `.github/core-sync/aws/trust-policy.json` with the
  12-digit account id in place of `<AWS_ACCOUNT_ID>`. Only runs on `main` of this repo may use the role.
- Permissions > Add permissions > Create inline policy > JSON: paste `.github/core-sync/aws/permissions-policy.json`
  with the same account id; name it `core-sync-codecommit`. It allows pull, push, branch read and pull requests on
  the two CodeCommit repos and nothing else.
- Copy the role ARN from the role's summary (`arn:aws:iam::<account id>:role/core-sync-bot`).

The same with the AWS CLI, on copies of the two files with the account id filled in:

```bash
aws iam create-open-id-connect-provider --url https://token.actions.githubusercontent.com --client-id-list sts.amazonaws.com
aws iam create-role --role-name core-sync-bot --assume-role-policy-document file://trust-policy.json
aws iam put-role-policy --role-name core-sync-bot --policy-name core-sync-codecommit --policy-document file://permissions-policy.json
```

**4. Save the role ARN in this repo.** Settings > Secrets and variables > Actions > Variables tab > New repository
variable (https://github.com/talenteam/product-factory/settings/variables/actions/new): name `AWS_SYNC_ROLE_ARN`,
value the role ARN. It is not a secret.

**5. Each product repo carries the core on `dev`.** Install it once by hand (`install.py <repo> --write-settings`)
and commit it. A repo without it gets a pull request from the bot instead of a direct push.

**6. Try it without changing anything.** Actions > core-sync > Run workflow, branch `main`, tick "Dry run", Run.
The run's summary has one row per repo: "dry run: would push to dev", "would open a pull request" or an error that
names the step to fix.

**7. Go live.** The next push to `main` that changes the core runs it for real, or Run workflow without "Dry run".
Tick "review" to get pull requests instead of direct pushes.

**Add or remove a repo:** edit `.github/core-sync/targets.json`. A GitHub repo also needs the token from step 1 to
cover it; a CodeCommit repo needs its ARN added to the inline policy from step 3.
