# core-1-10-0 core 1.10.0: harden the setup for the plugin switch (M1-M5, S1 S3 S4 S6 S7 S9)

Size L, claude, task mode. Live view: work/live.html
Risk: medium

| stage | state | evidence |
|---|---|---|
| Spec | todo |  |
| Design | todo |  |
| Build | done | M1-M5, S1 S3 S4 S6 S7 S9 built in core/; installed with --write-settings in product-factory, Blend, TalentBox; plugin rebuilt at 1.10.0 |
| Review | todo |  |
| Test | done | test_v1100 31/31 pass (M1 edit+merge pass without project.json, M2 headers, M3 crash blocks, S9); timing Read 254 ms -> no hook, Bash 245 -> 229; switch tested on a scratch Blend copy only; install/cursor_sync/plugin/version checks clean in 3 repos |
| Verify | todo |  |
| Release | todo |  |
| Wrap-up | done | report and commit messages in the shared notes folder (core-1-10-0-report.md) |

## Notes

For release:
