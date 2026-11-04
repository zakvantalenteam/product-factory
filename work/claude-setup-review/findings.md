# Claude setup review: merged findings (4 Nov 2026)

Sources: `review-setup.md` (Opus reviewer, full evidence and target layout) and `checklist-docs.md` (claude-code-guide, read from code.claude.com).
"Checked" means the Tech Lead re-checked the finding.
End state: the plugin carries the core (agents, core skills, hooks, scripts, reference). Each repo keeps only its project layer.

## MUST: fix before the plugin switch
| # | Finding | Checked | Fix | Where |
|---|---|---|---|---|
| M1 | The plugin is on at user scope, so its guard runs in every repo. In a repo with no `project.json` the defaults turn routing on (`plugin/scripts/project.py`, routing.enforce True), and main-session edits and `git merge` are blocked. | defaults read | Set `defaultEnabled: false` in plugin.json and opt in per repo with `enabledPlugins: true`. Every hook exits 0 at once when `.claude/project.json` is missing. | core |
| M2 | The `sdlc` description is invalid YAML (an unquoted `: ` at column 346), so Claude lists it as "Delivery flow (agent core)" and triage never fires from its description. | yes (yaml parse fails; skill listing) | Quote the description. Make `build_plugin.py` and `install.py --check` parse every frontmatter and run `claude plugin validate --strict`. | core |
| M3 | Hooks fail open without a trace. The `python -c` wrapper exits 0 when the script is missing, and a crash exits 1, which does not block. Removing `.claude/core/` turns off the guard for Claude and Cursor. | wrapper read | Put `onFailure: "block"` on the guard (v2.1.295+). The guard exits 2 on an internal error. Cursor gets a vendored minimal guard runtime in the repo. | core |
| M4 | 28 plugin files still point at `.claude/core/...`. `build_plugin.py` rewrites only agent and skill text. | yes (grep 28) | Rewrite every reference to `${CLAUDE_PLUGIN_ROOT}/` (the docs say it is substituted in SKILL.md and agent bodies). Scripts find their files from their own folder. | core + AGENTS.md |
| M5 | A teammate on a fresh machine gets no plugin. The marketplace is known only in your user settings and sits on a personal GitHub account. | settings read | Add `extraKnownMarketplaces` (with `autoUpdate`) and `enabledPlugins` to each repo's `.claude/settings.json` at switch time. Host the marketplace in an org repo. | per repo + hosting |

## SHOULD
- **S1:** Switch each repo in one change, with `install.py --uninstall-core`. Otherwise hooks run twice and skills are listed twice.
- **S2:** Git rules are enforced twice, with different policies: your hook allows merge and the guard blocks it. Your hook starts Python on every Bash call. Add `"if": "Bash(git *)"` and give the policy one owner.
- **S3:** Python runs on every Read (about 170 ms). Move the secret-read checks to native `permissions.deny` (Windows `//**/` paths) and narrow the guard's matcher.
- **S4:** The plugin's SessionStart adds about 2.4k tokens to every session in every repo. Emit it only when `project.json` exists.
- **S5:** AGENTS.md is about 5.6k tokens. Trim it to about 2.5k and move the live-check and verify notes into a referenced file. All hard rules stay.
- **S6:** `sdlc` (27 KB) and `factory` (11 KB) load in full. Split them into SKILL.md plus supporting files that load on demand.
- **S7:** Log a one-line warning when a hook fails open (paired with M3).
- **S8:** Permission hygiene: stale `settings.local.json` entries, and personal versus team allow rules.
- **S9:** Plugin hooks should force UTF-8 on stdout and stderr; outside Blend `PYTHONUTF8` is not set.

## COULD
- **C1:** Remove the stale `.claude/core-backup/` and the 5 forwarder shims in `.claude/scripts/` after the switch.
- **C2:** Bump the plugin version with each release. Old cache folders are cleaned 14 days after they are orphaned.
- **C3:** Reword the user CLAUDE.md line on subagent models. Frontmatter `model:` already beats `CLAUDE_CODE_SUBAGENT_MODEL` (since v2.1.251); only `_FORCE=1` overrides it.
- **C4:** Add a statusline: task id, stage and branch.
- **C5:** Memory is fine: MEMORY.md is 81 lines, under the 200-line load limit.
- **C6:** Dropped: `bashOutputMaxChars` is a valid settings key according to the docs.
- **C7:** `effortLevel: low` is set at user scope. That is your cost choice; just be aware of it.

## Verified fine
- Rule files have valid `paths:`.
- The `@AGENTS.md` import is fine.
- No agent relies on frontmatter that plugin agents ignore (hooks, mcpServers, permissionMode, initialPrompt).
- Plugin hooks already use the exec form with `${CLAUDE_PLUGIN_ROOT}`.
- Blend has the plugin off while it uses the in-repo core.
