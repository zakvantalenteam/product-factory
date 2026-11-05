# claude-setup-review Review of the Claude setup: skills, hooks, settings, rules, CLAUDE.md, plugin (read-only)

Size M, claude, task mode. Live view: work/live.html
Risk: medium

| stage | state | evidence |
|---|---|---|
| Spec | todo |  |
| Design | todo |  |
| Build | done | core 1.11.0 (pf-agent-core): M1-M5, S1, S3-S9 built and installed in 3 repos; Blend AGENTS.md 22.5 KB to 11.8 KB |
| Review | done | 5 MUST, 9 SHOULD, 7 COULD; merged in findings.md (M1, M2, M4 re-checked) |
| Test | todo |  |
| Verify | done | 3 repos 1.11.0, 126 core files identical, install + cursor checks ok; no-project guard passes Edit and merge; guard onFailure block; sdlc YAML valid |
| Release | skip |  |
| Wrap-up | done | product-factory 6c5c91e pushed; plugin 1.11.0 installed, 130 files identical to repo; Blend and TalentBox commit commands given |

Over budget (working time, gate waits left out):
- Build: ran over by 4 min (48 of 45 min)

## Notes

For release:
