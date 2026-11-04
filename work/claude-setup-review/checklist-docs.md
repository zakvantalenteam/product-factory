# Claude Code docs checklist (claude-code-guide, read from code.claude.com 2026-11-04)

Decision-relevant facts only. [F] doc fact, [R] recommendation.

## Plugin end state
- [F] A plugin can ship skills, agents, commands, hooks (`hooks/hooks.json`), MCP, LSP, output styles, workflows, `bin/`. Its `settings.json` only takes `agent` and `subagentStatusLine`.
- [F] A plugin can't ship CLAUDE.md or AGENTS.md, `.claude/rules/`, permissions, env or statusLine. These stay in the repo or in user settings. A CLAUDE.md at the plugin root is not loaded.
- [F] Plugin agents ignore the frontmatter fields `hooks`, `mcpServers`, `permissionMode` and `initialPrompt`.
- [F] Names are namespaced: `/product-factory:sdlc`, `product-factory:qa-lead`.
- [F] Hooks from every source merge and run in parallel. No order is documented.
- [F] `${CLAUDE_PLUGIN_ROOT}` is substituted in hook command/args and in SKILL.md and agent bodies. `${CLAUDE_PLUGIN_DATA}` survives updates.
- [F] Files outside the plugin root are not copied into the cache.
- [F] `defaultEnabled: false` in plugin.json. A project opts in with `enabledPlugins: {"product-factory@talenteam": true}` in `.claude/settings.json`. Project beats user.
- [F] Committing `enabledPlugins` does not install the plugin. Each teammate installs it once.
- [F] Project `extraKnownMarketplaces` and `enabledPlugins` apply after the workspace is trusted.
- [F] Auto-update is off for custom marketplaces. Turn it on with `autoUpdate` on the marketplace entry. A running session needs `/reload-plugins` to pick up an update.
- [F] The plugin.json `version` pins users to that version. Old cache folders are removed 14 days after they are orphaned.
- [R] Run `claude plugin validate --strict` in CI.

## Skills
- [F] Frontmatter fields: name, description, when_to_use, argument-hint, arguments, disable-model-invocation, user-invocable, allowed-tools, disallowed-tools, model, effort, context: fork, agent, background, hooks, paths, shell (bash|powershell), metadata.
- [F] The listing cuts description plus when_to_use at 1,536 characters. Keep SKILL.md under 500 lines and put detail in supporting files.
- [R] Lead the description with the use case and put trigger phrases in `when_to_use`. Set `disable-model-invocation: true` on skills with side effects.

## Rules and memory
- [F] `.claude/rules/*.md` is native, and only `paths` is read. Rules without `paths` load at launch.
- [F] Keep CLAUDE.md under 200 lines. An `@import` loads with its file and saves no tokens. It can go 4 hops deep.
- [F] Auto memory loads the first 200 lines or 25 KB of MEMORY.md.

## Hooks
- [F] There are 33 events.
- [F] The `"if": "Bash(git *)"` field (one permission-rule expression) on PreToolUse, PostToolUse and PermissionRequest stops the process from starting when a call doesn't match.
- [F] Exit 2 blocks. Any other non-zero exit, including an uncaught Python traceback (exit 1), does not block, so the hook fails OPEN.
- [F] `"onFailure": "block"` makes a hook fail closed (v2.1.295+). It is not available on Stop, SubagentStop or async hooks.
- [F] A hook can only tighten permissions. A permission deny always wins.
- [F] Default timeout is 600 s for command hooks. Async hooks have no timeout.
- [R] Use one dispatcher per event, `if` conditions, narrow matchers, and a light SessionStart.

## Subagents
- [F] Model precedence: invocation `model`, then frontmatter `model`, then `CLAUDE_CODE_SUBAGENT_MODEL`, then the main model. Since v2.1.251, frontmatter beats the env var. `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` overrides everything.
- [F] Frontmatter fields include tools, disallowedTools, maxTurns, skills (up to 32 preloaded), memory, effort, isolation, omitClaudeMd, autoCompactWindow and background.

## Permissions and settings
- [F] Precedence: managed > --settings > local > project > user. Lists merge, and a deny anywhere wins.
- [F] `defaultMode: auto|bypassPermissions` is ignored in project and local files.
- [F] There is no Bash sandbox on native Windows, so deny rules and hooks are the protection.
- [F] Windows deny paths use `//**/.env`. Bash rules match command text and are not a security boundary.
- [F] `includeCoAuthoredBy` is deprecated. Use `attribution`.
- [F] statusLine is set in user or project settings.
