# factory skill: S1 Base (new products; runs alongside S2-S4)

Part of the `factory` skill (SKILL.md next to this file), read when its step comes. Read it when the stage starts.

## S1 Base (new products; runs alongside S2-S4)
Starts only after G0 approved the platform in `00-infra.md`: the base is built for it (another platform than the
base default needs its D6 card first). `stage <slug> base start` opens code writes for the product root. Run `base-builder` (it builds the base from
`${CLAUDE_PLUGIN_ROOT}/reference/base/BASE-SPEC.md`, runs `check_base.py <root>` until 100 % and installs the core into
the product root). `devops-engineer` checks it deploys. `stage <slug> base done` closes writes again.
