# Bug test bench

How many real escaped bugs each stage of the team catches, measured again on every core release. Each miss
becomes one proposed agent or checklist change, applied only with the developer's yes. Script:
`scripts/bench.py`; skill: `/bench`. Claude Code only: it runs on `claude plugin eval`, which Cursor has no
equivalent for (Cursor users can add cases and read the reports; a run needs Claude Code 2.1.269 or later).

## A case

One folder per escaped bug, in the project's own repo: `.claude/bench/cases/<id>/` (committed there). The id is
kebab-case with the area first (`pulse-f3-chev-icon`); agents never see it.

| File | What |
|---|---|
| `case.json` | the ground truth (below) |
| `ticket.md` | what the developer had before the change: the ticket, the request or the acceptance criteria. Never the bug report. With no ticket, say so and quote the commit message: that is all the team had |
| `bug-report.md` | optional: the bug as reported, for people only; never given to an agent |
| `rubric-<stage>.md` | one per stage the case runs in: `The defect:` in 1-3 plain sentences, then `PASS if ...` and `FAIL if ...` lines a judge can decide from the agent's reply alone |

`case.json`:
```json
{
  "id": "pulse-f3-chev-icon",
  "title": "one plain line",
  "proof": ".claude/work/<task>/fix-proof.md#F3",
  "ticket": "BLEN-1234 or none",
  "introduced": "<sha of the commit that added the defect>",
  "fixed": "<sha of the commit that fixed it>",
  "files": ["the 1-3 files around the defect: the review and plan scope"],
  "context_files": ["optional: files the agent may read but that are not in the diff"],
  "defect": {"file": "path", "line": 1173, "mechanism": "one sentence: what is wrong and why"},
  "caught_at": "review-spec | code-reviewer | qa-lead | not-catchable",
  "caught_at_source": "fix-proof | judged",
  "caught_at_note": "the fix-proof 'Should have been caught at' line, or one line of reasoning",
  "not_applicable": {"review-spec": "why this stage cannot see it"},
  "layer_rev": "optional: the commit to take the project layer from"
}
```

## Stages

| Stage | Agent | Gets | PASS when |
|---|---|---|---|
| review-spec | spec-analyst, mode dor | `ticket.md`, today's code (the commit before the change) | the DoR check or the requirements review flags the gap |
| code-reviewer | code-reviewer | the review pack of the introducing change on `files` (`review_pack.py --base <introduced>~1 --head <introduced>`) | a MUST or SHOULD finding names the defect (file and mechanism) |
| qa-lead | qa-lead, mode plan | `ticket.md` and the diff of the introducing change on `files` | a matrix row would catch it |

Each run starts in an empty workspace. The case's scaffold fills it with read-only git: `git archive` of `files`
and `context_files` at the introducing commit, the project layer (`.claude/project.json`, `.claude/review/`,
`.claude/rules/`, `.claude/experts/`, `.claude/qa/`, `.claude/smoke.md`, `AGENTS.md`, `CLAUDE.md`) from the commit
before the fix (the newest project knowledge without this bug's own lessons), and the stage's input. The agents and
reference come from the plugin under test, without its hooks (they guard a live session, not the bench). The task
id is always `bench-1`. The agent cannot run commands or write files; it returns its result in its reply, and a
judge (Sonnet, 2 of 3 votes) grades the reply against the rubric.

## Rules that keep the bench honest
- No answer leaks: the bug report, the fix-proof, the fix diff and the case id never reach the agent. A lesson
  written because of this bug must not be in the layer: when the lessons at `<fixed>~1` already name it, set
  `layer_rev` to an older commit.
- `files` is the change the stage would have seen, not the whole combined commit; keep the diff under about 600
  changed lines.
- A rubric is specific to the bug: a generic "test everything" or "review carefully" must FAIL.
- `not-catchable`: nothing that existed before the bug (no ticket, no criterion, no visible defect in the diff)
  could have shown it, such as a capability nobody asked for. Kept for the record; `run` leaves it out unless
  `--all`.
- 3 runs per case and stage (always). A stage caught a bug when at least 2 of 3 runs pass. A run where the agent
  did not start (the `agent-ran` grader) is invalid, not a catch.
- Never real money: runs use the claude.ai subscription's tokens only; `bench.py run` refuses when the claude
  CLI is not signed in with claude.ai or an API key or cloud provider (Bedrock, Vertex, Foundry) is set. The $
  figures are list-price estimates of subscription usage. Every run has a usage ceiling (`--max-cost-usd`,
  required); `--dry-run` prints the projected usage first.

## Results
- `.claude/bench/history/<stamp>.json` (commit it): per case and stage the runs passed, the verdict and the cost,
  plus the plugin version, the models and the total cost.
- `.claude/bench/runs/<stamp>/` (gitignored): the eval report (`report.html`), the raw `aggregate-result.json`,
  the eval log and every reply (`replies/<project>--<case>--<stage>--<n>.md`).
- `bench.py report`: catch rate per stage and agent, the rate at the stage where each bug should have been caught,
  and every case whose verdict changed since the run before.
- `.claude/bench/proposals.md`: one row per miss with the proposed change and its state (proposed, approved,
  applied in core <version>, rejected).

## Projects
Every project keeps its own cases. From the home repo (product-factory), `--project all` runs every repo in
`release.local.json` that has `.claude/bench/cases/`; in a product repo, `bench.py` runs that repo only. No project
names live in the core.
