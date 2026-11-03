# Product factory

One shared team of AI agents and one delivery flow for Claude Code and Cursor, used by every TalenTeam product
repo. It is also where new products are made. Change the core here and push to `main`: every product repo gets the
new version, and Claude users get it as a plugin.

## What is in this repo

| Path | What |
|---|---|
| `core/` | The agent core source: agents, skills, hooks, scripts, reference, templates. `core/core-plan.md` is its design and change log. |
| `plugin/` | The Claude Code plugin `product-factory`, built from `core/` by `core/scripts/build_plugin.py`. Do not edit by hand. |
| `.claude-plugin/marketplace.json` | Makes this repo a Claude Code plugin marketplace (`talenteam`). |
| `.github/workflows/core-sync.yml`, `.github/core-sync/` | The sync bot that installs the core into each product repo. |
| `.claude/`, `.cursor/`, `AGENTS.md`, `CLAUDE.md` | The core installed for this repo itself. |
| `work/<slug>/` | One folder per product or task: documents, questions, decisions and live status. |
| `base/`, `standards/`, `scripts/`, `prototypes/` | Older copies and prototypes; the core's own copies live in `core/`. |

## How people get it

**Product repos (Claude Code and Cursor, nothing to install).** Each repo carries its own copy of the core in
`.claude/`, `.cursor/` and `AGENTS.md`. After each core release the maintainer installs it into every product repo
and commits it there (step 5 of "Releasing a change to the core"); developers get it with their normal `git pull`.
The optional sync bot does this by itself for the repos in `.github/core-sync/targets.json` (Blend and TalentBox on
AWS CodeCommit, once AWS is set up): it runs the checks and pushes one commit to `dev`, or opens a pull request
when a person must look (a first install, a core file edited by hand, a failed check, a protected branch).

**Any other repo (Claude Code only): the plugin.** Each person sets it up once (steps below). Repos that carry the
core switch the plugin off in their own settings, so nothing runs twice. To give a repo the core for the whole team
(Cursor too), run `python <plugin or core>/scripts/install.py <repo> --write-settings` once and commit the result.

### Set up the plugin (each Claude Code user, once)

The repo `zakvantalenteam/product-factory` is public, so no GitHub access or sign-in is needed.

1. Add the marketplace and the plugin. In the Claude desktop app, use the settings keys below. In a terminal
   `claude` session you can instead type:

   ```
   /plugin marketplace add https://github.com/zakvantalenteam/product-factory.git
   /plugin install product-factory@talenteam
   ```

   then `/plugin` > Marketplaces > talenteam > Enable auto-update. Or add these two keys to your user settings
   (`~/.claude/settings.json`), which also turns on auto-update:

   ```json
   "extraKnownMarketplaces": {
     "talenteam": {"source": {"source": "git", "url": "https://github.com/zakvantalenteam/product-factory.git"}, "autoUpdate": true}
   },
   "enabledPlugins": {"product-factory@talenteam": true}
   ```

   If adding the marketplace fails with a network error on Windows, and
   `git ls-remote https://github.com/zakvantalenteam/product-factory.git HEAD` says "unable to get local issuer
   certificate", the company network checks HTTPS traffic with a certificate that Windows trusts but Git's own list
   does not. Let Git use the Windows certificate store, then add the marketplace again:

   ```bash
   git config --global http.sslBackend schannel
   ```

   Installed it before 1.4.0 as `agent-core@talenteam`? Uninstall that one and install `product-factory@talenteam`
   (in settings: replace the key in `enabledPlugins`).

2. Start a new session in a repo that does not carry the core. `/agents` lists `product-factory:explorer` and the
   others, and the skills show as `/product-factory:sdlc` and so on.
3. Updates: a new version reaches you within about 10 minutes of starting a session; `/reload-plugins` applies it.
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

## Certified agents

Each agent is tagged with the most respected credentials for its role: general ones first (valid at any software
company, startup to enterprise), then SAP ones, because TalenTeam builds on SAP BTP and SuccessFactors. What this
means: the agents work to the practical knowledge those exams test (one practice pack per agent in
`core/reference/practice/`); they do not hold the credentials. SAP rules apply only when `.claude/project.json`
`stack.platform` is `sap-btp`.

How to read the exam scores: each examined agent answered the same 3 tasks taken from our own code (5 points each,
15 in all), once on the previous core (1.6.0) and once on this one (1.7.0). A separate grader marked both answers
against a fixed answer key without knowing which version wrote which. A higher score means the agent caught more of
what an expert would catch. "-" means the agent has not taken the exam yet. Scores live in `core/exam-scores.json`.

<!-- certified-agents:start (build_plugin.py writes this table from the agent files) -->
| Agent | Role | Certifications (general) | SAP | Exam 1.6.0 | Exam 1.7.0 |
|---|---|---|---|---|---|
| `ai-engineer` | AI engineer (LLM features, retrieval, agents, evals, cost) | AWS Certified Generative AI Developer - Professional (AIP-C01)<br>Google Cloud Professional Machine Learning Engineer | SAP Certified - SAP Generative AI Developer (C_AIG) | 15/15 | 15/15 |
| `audit-expert` | Go-live auditor | ISACA Certified Information Systems Auditor (CISA)<br>PECB Certified ISO/IEC 27001 Lead Auditor | - | - | - |
| `backend-developer` | Backend engineer (Java 17, Spring Boot) | Oracle Certified Professional: Java SE 17 Developer (1Z0-829)<br>Spring Certified Professional (2V0-72.22) | - | 15/15 | 14/15 |
| `base-builder` | Base project builder | Oracle Certified Professional: Java SE 17 Developer (1Z0-829)<br>Spring Certified Professional (2V0-72.22) | SAP Certified - SAP Business AI Platform Administrator (C_ADBTP) | - | - |
| `bug-investigator` | Root-cause investigator | Oracle Certified Professional: Java SE 17 Developer (1Z0-829)<br>ISTQB Certified Tester Advanced Level Technical Test Analyst (CTAL-TTA v4.0) | - | - | - |
| `code-reviewer` | Code reviewer | Oracle Certified Professional: Java SE 17 Developer (1Z0-829)<br>ISC2 Certified Secure Software Lifecycle Professional (CSSLP) | - | 14/15 | 15/15 |
| `data-architect` | Data architect | DAMA Certified Data Management Professional (CDMP Practitioner)<br>Google Cloud Professional Data Engineer<br>EDB Advanced for PostgreSQL | SAP Certified - Data Engineer - SAP HANA (C_HAMOD) | 15/15 | 15/15 |
| `devops-engineer` | Build, deploy and operations engineer | CNCF Certified Kubernetes Administrator (CKA)<br>AWS Certified DevOps Engineer - Professional (DOP-C02)<br>Google Cloud Professional Cloud DevOps Engineer | SAP Certified - SAP Business AI Platform Administrator (C_ADBTP) | - | - |
| `explorer` | Code search and impact analysis | Oracle Certified Professional: Java SE 17 Developer (1Z0-829) | - | - | - |
| `frontend-developer` | Frontend engineer (UI5, plain JS, React) | IAAP Web Accessibility Specialist (WAS) | SAP Certified - SAP Fiori Application Developer (C_FIORD) | 15/15 | 15/15 |
| `integration-engineer` | Integration engineer | Salesforce Certified MuleSoft Platform Integration Architect | SAP Certified - Integration Developer (C_CPI) | - | - |
| `n8n-expert` | n8n workflow engineer | AWS Certified Generative AI Developer - Professional (AIP-C01) | - | - | - |
| `performance-engineer` | Performance engineer | Oracle Certified Professional: Java SE 17 Developer (1Z0-829)<br>ISTQB Certified Tester Performance Testing (CT-PT) | - | - | - |
| `product-critic` | Product reviewer | Pragmatic Institute Certified Product Manager<br>Scrum.org Professional Scrum Product Owner II (PSPO II)<br>ATD Certified Professional in Talent Development (CPTD) | - | - | - |
| `qa-engineer` | Test engineer | ISTQB Certified Tester Advanced Level Test Analyst (CTAL-TA v4.0)<br>ISTQB Certified Tester Advanced Level Technical Test Analyst (CTAL-TTA v4.0)<br>ISTQB Certified Tester Advanced Level Test Automation Engineering (CTAL-TAE v2.0) | - | 14/15 | 15/15 |
| `release-manager` | Release manager | ITIL Managing Professional (ITIL Version 5) | SAP Certified - Solution Transformation Consultant with SAP Cloud ALM (C_STC) | - | - |
| `security-architect` | Security and privacy architect | ISC2 Certified Information Systems Security Professional (CISSP)<br>ISC2 Certified Cloud Security Professional (CCSP)<br>IAPP Certified Information Privacy Professional/Europe (CIPP/E) | - | 14/15 | 15/15 |
| `sf-expert` | SAP SuccessFactors consultant | SHRM Senior Certified Professional (SHRM-SCP) | SAP Certified - SAP SuccessFactors Employee Central Core and Position Management (C_THR81)<br>SAP Certified - SAP SuccessFactors Learning (C_THR88) | - | - |
| `solution-architect` | Lead solution architect | AWS Certified Solutions Architect - Professional (SAP-C03)<br>Google Cloud Professional Cloud Architect<br>TOGAF Enterprise Architecture Practitioner | SAP Certified Professional - Solution Architect - SAP BTP (P_BTPA) | 15/15 | 15/15 |
| `spec-analyst` | Business analyst (requirements and specs) | IIBA Certified Business Analysis Professional (CBAP)<br>IREB CPRE Practitioner (Requirements Elicitation, Requirements Modeling)<br>ATD Certified Professional in Talent Development (CPTD) | SAP Certified - Project Manager - SAP Activate (C_ACT) | - | - |
| `story-sizer` | Backlog and sizing (Scrum) | Scrum.org Professional Scrum Master II (PSM II)<br>Scrum.org Professional Scrum Product Owner II (PSPO II) | SAP Certified - Project Manager - SAP Activate (C_ACT) | - | - |
| `ux-designer` | UX and screen designer | Nielsen Norman Group UX Certification (Interaction Design specialty)<br>IAAP Certified Professional in Accessibility Core Competencies (CPACC) | - | 14/15 | 15/15 |
| `verifier` | Independent verifier | ISTQB Certified Tester Advanced Level Test Analyst (CTAL-TA v4.0)<br>ISTQB Certified Tester Advanced Level Technical Test Analyst (CTAL-TTA v4.0) | - | - | - |
| **Total (9 examined)** | | | | **131/135** | **134/135** |
<!-- certified-agents:end -->

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
4. Commit and push to `main`. The workflow stops a push whose versions differ or whose `plugin/` is stale. Plugin
   users get the new version by themselves.
5. Port it to each product repo the bot does not cover (SkillsOS today, and Blend and TalentBox until AWS is set
   up), from this repo:

   ```bash
   python core/scripts/install.py <product repo> --write-settings
   ```

   then, in that repo, `python .claude/core/scripts/cursor_sync.py` and both checks
   (`python .claude/core/scripts/cursor_sync.py --check`, `python .claude/core/scripts/install.py . --check`) must
   be clean. Files a repo edited by hand are kept and listed; review them. Commit the setup files there
   (`.claude/`, `.cursor/`, `AGENTS.md`, `CLAUDE.md`, `.gitignore`) and push to `dev`.

## One-time setup of the sync bot

The bot is optional; without it, port each release by hand (step 5 above). Until these steps are done, a push to
`main` gives a `core-sync` run whose summary names the missing step for each repo, and nothing in the product repos
changes. Steps 1, 2 and 4 need admin rights on this repo; step 3 needs an AWS admin for the account that holds the
CodeCommit repos (region `eu-west-2`).

**1. A GitHub token (only when `targets.json` lists a GitHub repo; none does today).** Signed in as a person (or
bot account) with write access to that repo: picture > Settings > Developer settings > Personal access tokens >
Fine-grained tokens > Generate new token (https://github.com/settings/personal-access-tokens/new).
- Token name: any clear name (only the secret name in step 2 matters); Resource owner: the org that owns the repo,
  for example `talenteam` (a token owned by your own account cannot reach org repos, and the run fails with 403).
  Expiration at most a year; note the date, because that repo's row fails until a new token is saved.
- Repository access: Only select repositories > the repos in `targets.json`.
- Permissions > Repository permissions: Contents "Read and write", Pull requests "Read and write" (Metadata
  "Read-only" is added by itself).
- Generate token and copy it. If the org asks for approval, an org owner approves it under the org's Settings >
  Personal access tokens > Pending requests.

**2. Save the token in this repo (only with step 1).** Settings > Secrets and variables > Actions > New repository secret
(https://github.com/zakvantalenteam/product-factory/settings/secrets/actions/new): name `SYNC_GITHUB_TOKEN`, paste the
token, Add secret. GitHub never shows it again; to renew, save a new token under the same name.

**3. An AWS role the workflow may use (no AWS keys are stored).** Until steps 3 and 4 are done, the run skips the
CodeCommit repos (Blend, TalentBox) without failing; update those by hand with `install.py <repo> --write-settings`.
In the AWS console, IAM:
- Identity providers > Add provider: OpenID Connect, provider URL `https://token.actions.githubusercontent.com`,
  audience `sts.amazonaws.com`. Skip this if it is already listed.
- Roles > Create role > Web identity: that provider, audience `sts.amazonaws.com`, GitHub organization
  `zakvantalenteam` (the repo's owner), repository `product-factory`, branch `main`. Attach no policies; role name `core-sync-bot`.
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
variable (https://github.com/zakvantalenteam/product-factory/settings/variables/actions/new): name `AWS_SYNC_ROLE_ARN`,
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
