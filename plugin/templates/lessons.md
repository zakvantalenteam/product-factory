# Lessons

Mistakes this repo has already made, one line each, so no agent makes them twice. Every review MUST (once fixed) and
every bug found later in a change adds one line; a repeat gets ` (again <date>)`. Agents read the lines for their area
and the reviewer fails a repeat. Rules that grow general move into `.claude/review/checklist.md`.

Format: `- <date> <task id> [<stage>]: <the rule, one line> (<area or path glob>)`
Stage tags: `[review-spec R<n>]` (requirements), `[develop review]` (code review; no tag means this),
`[test <type>]` (qa-lead's plan; types in `${CLAUDE_PLUGIN_ROOT}/reference/qa/test-types.md`).
