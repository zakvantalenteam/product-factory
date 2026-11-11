"""Hand-off check for the documents of a gate (agent core), for Claude Code and Cursor.

`live_status.py gate` runs it on the files of a spec or design gate (task mode) or of a requirements, product or
design gate (product mode) and opens the gate only when no problem is found. Problems are what the next agent or
the developer would trip over: a missing section, a gap without a recommended answer, a criterion no planned
change covers, a data-model card without its plain-English part, a task spec without its kind of work and team,
a bug spec without its root cause, an expert's notes without their sections.

Documents by name, in both modes (.claude/core/reference/flow-files.md):
  brief checks   brief.md, 02-gaps.md                 spec checks    spec.md, 02-spec.md
  design checks  design.md, 05-architecture.md        card checks    decisions/D*.md
  sections       ui.md / 05-ui.md, perf.md / 05-performance.md, sf.md / 05-sf-fields.md, ai.md / 05-ai.md,
                 n8n.md / 05-n8n.md,
                 review-<domain>.md, 07-sf-review.md
  task checks    triage.md (risk and its evidence, team, who is left out, planned files without a design),
                 context.md (the context pack), safety.md (the safety net); checked at every gate when present.
                 Tasks started before core 1.3 (no context.md and no Risk line) get hints only.
  hints only     05-data-model.md (the "Data model explained" parts) and every other document
Card layout: .claude/core/reference/review/decision-card.md. Hints are style points from
.claude/core/reference/review/plain-english.md; they never block. Glossary words and code words come from
`glossary` in .claude/project.json.

  fix-proof.md   (bug-investigator in /fix) one `## <ID>` or `## F<n>` block per bug, each with:
                 ### Reproduction (a numbered step), ### Root cause (`Proven: yes|no`; yes needs a `path:line` in
                 backticks; no needs a ### What would prove it section and is always a problem: the bug stays open),
                 ### Regression test (the test in backticks, and that it fails before the fix), ### Regression ring
                 (a bullet, or a line "none: reason"), ### Fix plan (a bullet naming a file in backticks).

  spec.md        with a ## Definition of Ready (review-spec, /develop dor): rows R1-R16 (R1-R11 on a spec made READY
                 before core 1.16), each pass, fail or n/a with a note; the vague words of R12
                 (.claude/core/reference/requirements/vague-words.md plus glossary.vague_words in project.json) in
                 the requirement part, above ## Technical appendix (quoted text, code, comments, questions, the
                 glossary and the table are skipped); in a review-spec task with context.md a ## Today vs asked
                 table (| AC | Today | Asked | Conflict | Also touches |, a Q<n> per conflict, plain words).
  fix-proof.md   also a line "Should have been caught at: <review-spec R<n> | develop review | test <type>> -
                 <the missing check>" or "not catchable: <why>" per block (the /fix escape check).
  test.md        with ## Acceptance tests (/develop, tests first): | AC | Test | Before build | Why it fails |
                 After build |, each test in backticks and seen FAIL before Build with a reason, none FAIL after;
                 ## Not automated | AC | Why | Owner | (ui-qa-expert or e2e-qa-expert); every AC of spec.md in one.
  test-plan.md   ## Test types names every type of .claude/core/reference/qa/test-types.md with rows or
                 "n/a: reason" (a plan without the section gets a hint).

  python .claude/core/scripts/handoff_check.py ID [FILE ...]   (files relative to <work>/ID; default: all; ID may
                 also be a folder path, for example requirements/<id> in a folder with no .claude/project.json)
  python .claude/core/scripts/handoff_check.py ID --fix [BLOCK ...]   only fix-proof.md, only these blocks (default all);
                 prints OK or the problems per block
  python .claude/core/scripts/handoff_check.py ID data.md   a ticket's test data (test-data-engineer; also in the default
                 run when the file exists): `Data: READY|PARTIAL|BLOCKED`, table | Row | Need | Record ids | Source |
                 Status | (ready, asked, blocked), every asked or blocked row under ## Ask list, created rows with
                 ids that contain QA-<ID>-, READY with a blocked row is a problem
  python .claude/core/scripts/handoff_check.py --data-map [PATH]   the test data map (default qa.data.map in
                 project.json, else .claude/qa/data-map.md): Approved:, Hosts:, Query: lines; ## Needs table
                 | ID | Need | Volume | Source | How | Cleanup | Status |; find rows read-only, create rows through an
                 API path, import or seed script with a Cleanup, ask rows listed under ## Ask list
  python .claude/core/scripts/handoff_check.py --smoke [PATH]   the smoke list (default .claude/smoke.md): each
                 ## <area> with a paths: line and `- ` items ([P1] allowed), optional ### Journey: <name> [P1] with
                 Role:, Steps: (numbered), Expected: and optional Data:; HTML comments ignored
Exit code 1 when there are problems.
"""
import glob
import json
import os
import re
import sys

sys.dont_write_bytecode = True
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:  # `python -I` leaves the script's folder off sys.path
    sys.path.insert(0, _HERE)
import project  # noqa: E402

ROOT = project.repo_root()
WORK = project.work_dir(ROOT)
CFG = project.config(ROOT)
CARD_LAYOUT = project.core_path("reference/review/decision-card.md")

SECRETISH = re.compile(r"(password|passwd|secret|token|api[_-]?key|client[_-]?secret)[\"']?\s*[=:]\s*[\"']?"
                       r"(?=[A-Za-z0-9_\-./+=]*\d)[A-Za-z0-9_\-./+=]{12,}|\bBearer\s+[A-Za-z0-9._\-~+/=]{16,}", re.I)
CODE_EXT = (r"java|kt|kts|scala|groovy|js|jsx|mjs|cjs|ts|tsx|vue|svelte|py|rb|go|rs|cs|php|swift|cpp|hpp|xml|"
            r"properties|json|ya?ml|toml|ini|css|scss|less|html?|sql|sh|ps1|gradle|csproj|cds|hdbtable")


def _code_words():
    words = ((CFG.get("glossary") or {}).get("code_words") or "").strip()
    if words:
        try:
            re.compile(words)
            return "|" + words
        except re.error:
            pass
    return ""


# File paths with a source extension, `Foo.java:12`, annotations such as @Entity, and the repo's own code words.
CODEY = re.compile(r"[\w/.-]+\.(?:" + CODE_EXT + r")\b|\b\w+\.(?:" + CODE_EXT + r"):\d+|(?<![\w.@])@[A-Z]\w+\b"
                   + _code_words())
# Words a newcomer may not know: explain once, in brackets or under "Words used here".
BASE_JARGON = ["foreign key", "nullable", "cascade", "orphan", "index", "schema validation", "backfill",
               "idempotent", "payload", "endpoint", "migration", "DTO", "tenant", "entity", "primary key",
               "unique constraint", "webhook", "SSE"]


def _words_file(relpath):
    """Glossary words from a file: the first cell of a table row, the part before ":" of a list item, else the line."""
    out = []
    try:
        with open(os.path.join(ROOT, relpath), encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
    except OSError:
        return out
    for line in lines:
        t = line.strip()
        if not t or t.startswith("#"):
            continue
        if t.startswith("|"):
            cell = t.strip("|").split("|")[0].strip()
            if cell and not re.match(r"^:?-{2,}:?$", cell) and cell.lower() not in ("word", "words", "term"):
                out.append(cell)
        else:
            t = re.sub(r"^[-*+]\s+|^\d+[.)]\s+", "", t)
            out.append(re.split(r":|\s-\s", t, 1)[0].strip(" *`"))
    return [w for w in out if w and len(w) <= 40]


def _glossary():
    words = (CFG.get("glossary") or {}).get("words") or []
    if isinstance(words, str):
        words = _words_file(words)
    return [w.strip() for w in words if isinstance(w, str) and w.strip()]


JARGON = BASE_JARGON + [w for w in _glossary() if w.lower() not in [j.lower() for j in BASE_JARGON]]
# A real person's e-mail in a document (query results pasted into a brief); example domains are fine.
EMAIL = re.compile(r"\b[\w.+-]+@(?!example\.(?:com|org|net)\b)(?=[\w-]*[A-Za-z])[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}\b")
IDS = {"AC": re.compile(r"\bAC(\d+)\b"), "Q": re.compile(r"\bQ(\d+)\b"), "A": re.compile(r"\bA(\d+)\b")}

# Document pairs per mode: task name, product name.
BRIEF_DOCS = {"brief.md": "spec.md", "02-gaps.md": "02-spec.md"}          # brief -> its spec
SPEC_DOCS = {"spec.md": "brief.md", "02-spec.md": "02-gaps.md"}           # spec -> its brief
DESIGN_DOCS = {"design.md": "spec.md", "05-architecture.md": "02-spec.md"}  # design -> its spec
PRODUCT_DOCS = ("02-gaps.md", "02-spec.md", "05-architecture.md")
STORIES = "04-stories.md"
REQUIRED = tuple(BRIEF_DOCS) + tuple(SPEC_DOCS) + tuple(DESIGN_DOCS)


def read(p):
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            return f.read().replace("\r\n", "\n")
    except OSError:
        return None


def sections(text):
    """{lower-case heading text: body} for every markdown heading below the title (## and deeper)."""
    out, cur, buf = {}, "", []
    fence = False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fence = not fence
        m = None if fence else re.match(r"^#{2,6}\s+(.*?)\s*#*\s*$", line)
        if m:
            out[cur] = "\n".join(buf)
            cur, buf = m.group(1).strip().lower(), []
        else:
            buf.append(line)
    out[cur] = "\n".join(buf)
    return out


def find(secs, *words):
    """Body of the first heading containing any of the words, else None."""
    for h, body in secs.items():
        if any(w in h for w in words):
            return body
    return None


def ids(kind, text):
    return {int(n) for n in IDS[kind].findall(text or "")}


def plain_hints(name, text, secs):
    """Style hints: long sentences and unexplained jargon in the human-facing parts."""
    hints = []
    prose = re.sub(r"```.*?```", " ", text, flags=re.S)
    prose = "\n".join(l for l in prose.split("\n") if not l.lstrip().startswith("|"))
    long = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n", prose) if len(s.split()) > 30]
    if long:
        hints.append("%s: %d sentence(s) over 30 words, e.g. \"%s...\"" % (name, len(long), " ".join(long[0].split()[:10])))
    words = (find(secs, "words used here") or "").lower()
    missing = [j for j in JARGON if re.search(r"\b" + re.escape(j) + r"s?\b", prose, re.I) and j.lower() not in words
               and not re.search(r"\b" + re.escape(j) + r"s?\b\s*\(", prose, re.I)]
    if missing:
        hints.append("%s: explain once (in brackets or under \"Words used here\"): %s" % (name, ", ".join(missing[:6])))
    return hints


def check_brief(text, name="brief.md"):
    p, secs = [], sections(text)
    spec = BRIEF_DOCS.get(name, "spec.md")
    need = [("what i understood", "what i understood"), ("gaps", "gaps i found"), ("assumption", "assumptions"),
            ("not doing", "not doing")]
    for key, label in need:
        if find(secs, key, "out of scope" if key == "not doing" else key) is None:
            p.append("%s: section \"%s\" is missing" % (name, label))
    under = find(secs, "what i understood") or ""
    if CODEY.findall(under):
        p.append("%s: \"What I understood\" is for the developer: move file, class or table names to %s" % (name, spec))
    gaps = find(secs, "gaps") or ""
    blocks = re.split(r"(?m)^\s*[-*]?\s*\**Q(?=\d+\b)", gaps)[1:]
    if not blocks and not re.search(r"\bnone\b", gaps, re.I) and find(secs, "gaps") is not None:
        p.append("%s: \"Gaps I found\" lists no Q1, Q2... items (write \"None found\" and what you checked if so)" % name)
    for b in blocks:
        n = re.match(r"(\d+)", b).group(1)
        if not re.search(r"recommend", b, re.I):
            p.append("%s: Q%s has no recommended answer" % (name, n))
    return p, plain_hints(name, text, secs)


KINDS = {"feature", "bug", "performance", "ui", "data", "config", "refactor"}
BUG_PARTS = ["Reproduction", "Likely causes", "Root cause", "Fix plan", "Regression test"]
PERF_PARTS = ["Scenario and budget", "Baseline", "Where the time goes", "Impact map", "Plan", "Behaviour unchanged", "After"]
PERF_DOCS = {"perf.md": "design.md", "05-performance.md": "05-architecture.md"}  # notes -> the design that adds parts
UI_PARTS = ["What the screen must do", "Today's screen", "Variants", "Improvements"]
UI_DOCS = {"ui.md": ("design.md", UI_PARTS),
           "05-ui.md": ("05-architecture.md", [x for x in UI_PARTS if x != "Today's screen"])}  # a new product has none
# the domain experts' notes (sf-expert, sf-skills-expert, ai-engineer, n8n-expert) in both modes, and their review files
SF_PARTS = ["SF areas touched", "Where this repo uses SF", "API plan", "Data and privacy", "Risks and tests", "Sources"]
AI_PARTS = ["AI behaviour", "Turn budget", "Model and prompt plan", "Evals", "Guardrails and fallbacks", "Observability"]
N8N_PARTS = ["Workflows touched", "Today's flow", "Plan", "Eval and rollout", "Handoff"]
EXPERT_PARTS = {"sf.md": SF_PARTS, "05-sf-fields.md": SF_PARTS, "sf-skills.md": SF_PARTS,
                "05-sf-skills-fields.md": SF_PARTS, "ai.md": AI_PARTS, "05-ai.md": AI_PARTS,
                "n8n.md": N8N_PARTS, "05-n8n.md": N8N_PARTS,
                "02-nfr.md": ["Needs", "Open questions"], "00-infra.md": ["Hosting and deployment", "Questions for the owner"]}
# a project's own expert documents and their required headings (`expert_docs` in project.json)
EXPERT_PARTS.update({k: list(v) for k, v in (CFG.get("expert_docs") or {}).items()
                     if k not in EXPERT_PARTS and isinstance(v, list)})
EXPERT_DOCS = tuple(EXPERT_PARTS)
REVIEW_PARTS = ["Findings", "Live checks for Verify"]
CONTEXT_PARTS = ["Impact map", "Key code", "Rules that apply", "Risk signals", "Gaps"]
TASK_DOCS = ("triage.md", "context.md", "safety.md")
RISK = re.compile(r"(?im)^[\s>*_-]*risk[\s*_]*:[\s*_]*(low|medium|high)\b")
DATA_MODEL_DOCS = ("05-data-model.md",)
ALL_DOCS = tuple(BRIEF_DOCS) + tuple(SPEC_DOCS) + tuple(DESIGN_DOCS) + tuple(PERF_DOCS) + tuple(UI_DOCS) + EXPERT_DOCS \
    + DATA_MODEL_DOCS + TASK_DOCS


def review_docs():
    """review-sf.md, review-sf-skills.md, review-ai.md, review-n8n.md, 07-sf-review.md and review-<x>.md for each domain expert in project.json."""
    shorts = {"sf", "sf-skills", "ai", "n8n"} | {str(e).split(":")[-1].split("-")[0].lower() for e in CFG.get("experts") or [] if e}
    return {"review-%s.md" % s for s in shorts if s} | {"07-sf-review.md"}


def missing_parts(name, secs, parts):
    return ["%s: section \"%s\" is missing" % (name, x) for x in parts if find(secs, x.lower()) is None]


def status(folder):
    try:
        with open(os.path.join(folder, "status.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def running_stages(folder):
    """Stage keys this task runs (not skipped for its size), from status.json; None when unknown."""
    try:
        return [s["k"] for s in status(folder)["stages"] if s.get("state") != "skip"]
    except (KeyError, TypeError):
        return None


def risk_of(folder):
    """low, medium or high from the "Risk:" line of triage.md; None when there is none."""
    m = RISK.search(read(os.path.join(folder, "triage.md")) or "")
    return m.group(1).lower() if m else None


def new_flow(folder):
    """A task started on core 1.3 or later (a context pack or a Risk line). Older tasks still in flight are not held
    to the 1.3 documents: they get hints instead of problems."""
    return os.path.isfile(os.path.join(folder, "context.md")) or risk_of(folder) is not None


def filled(secs, *words):
    body = find(secs, *words)
    return body is not None and re.search(r"\w", re.sub(r"<!--.*?-->", "", body, flags=re.S)) is not None


def check_triage(text, folder):
    """Risk with its evidence, the team with reasons, who is left out and, without a Design stage, the planned files."""
    p, hints, secs = [], [], sections(text)
    need = p if new_flow(folder) else hints
    risk = RISK.search(text)
    if not risk:
        need.append("triage.md: the line \"Risk: low|medium|high\" is missing")
    elif not filled(secs, "risk evidence"):
        need.append("triage.md: section \"Risk evidence\" (one bullet per signal, citing context.md) is missing or empty")
    if not filled(secs, "who will work on this"):
        need.append("triage.md: section \"Who will work on this\" (| Stage | Expert | Why |) is missing or empty")
    if find(secs, "not needed") is None:
        need.append("triage.md: section \"Not needed\" (one line per agent left out and why) is missing")
    stages = running_stages(folder)
    if stages is not None and "design" not in stages and not os.path.isfile(os.path.join(folder, "design.md")) \
            and not filled(secs, "planned files"):
        need.append("triage.md: no Design stage runs, so section \"Planned files\" (one bullet per file the build may "
                    "touch) is needed for the scope check")
    return p, hints


def check_context(text, folder):
    p, hints, secs = [], [], sections(text)
    need = p if new_flow(folder) else hints
    if not filled(secs, "impact map"):
        need.append("context.md: section \"Impact map\" (from impact.py: callers, endpoints, screens, each path:line) "
                    "is missing or empty")
    hints += ["context.md: section \"%s\" is missing" % x for x in CONTEXT_PARTS[1:] if find(secs, x.lower()) is None]
    return p, hints


def check_safety(text, folder):
    p, secs = [], sections(text)
    need = p if new_flow(folder) else []
    if not filled(secs, "before build"):
        need.append("safety.md: section \"Before build\" (compile, unit suite counts, characterization run) is missing "
                    "or empty")
    built = [s for s in (status(folder).get("stages") or []) if s.get("k") == "build" and s.get("state") == "done"]
    if built and not filled(secs, "after build"):
        need.append("safety.md: Build is done but section \"After build\" (compile, unit suite, characterization diff, "
                    "scope check) is missing or empty")
    return p, []


def check_task_design(folder, name):
    """design.md of a 1.3 task: the planned files, and the characterization tests at risk medium or high."""
    if name != "design.md" or not new_flow(folder):
        return []
    p = []
    if not filled(sections(read(os.path.join(folder, name)) or ""), "planned files"):
        p.append("design.md: section \"Planned files\" (one bullet per file the build may touch) is missing or empty")
    risk = risk_of(folder)
    if risk in ("medium", "high") and not os.path.isfile(os.path.join(folder, "safety.md")):
        p.append("safety.md: missing; risk is %s, so qa-engineer (characterize) locks today's outputs before Build"
                 % risk)
    return p


def check_team(text, folder, name="spec.md", product=False):
    """The "Kind of work" line and "Who will work on this" (one row per expert, a row for every stage that runs).
    Product mode starts with the factory's default team, so there both are hints."""
    from live_status import parse_team, NAMES
    p, hints = [], []
    kinds, rows = parse_team(text, "product" if product else "task")
    need = hints if product else p
    if not kinds:
        need.append("%s: the line \"Kind of work: ...\" (%s) is missing" % (name, ", ".join(sorted(KINDS))))
    odd = [k for k in kinds if k not in KINDS]
    if odd:
        hints.append("%s: unknown kind of work %s (known: %s)" % (name, ", ".join(odd), ", ".join(sorted(KINDS))))
    if not rows:
        need.append("%s: section \"Who will work on this\" (| Stage | Expert | Why |, one row per expert) is missing or empty"
                    % name + (" (the factory's default team is used)" if product else ""))
    else:
        have = {r["stage"] for r in rows}
        miss = [NAMES.get(k, k) for k in (running_stages(folder) or []) if k not in have and k != "release"]
        if miss:
            hints.append("%s: \"Who will work on this\" has nobody for %s: plan skips those stages (fine when the task "
                         "does not need them)" % (name, ", ".join(miss)))
        if any(not r["why"] for r in rows):
            hints.append("%s: give every expert a reason in the Why column" % name)
        who = {(r.get("agent") or r["expert"]).lower() for r in rows}
        if have & {"review", "test"}:  # code gets checked: the QA lead plans it and signs it off
            if "qa-lead" not in who:
                need.append("%s: no qa-lead in 'Who will work on this': every task that changes code gets qa-lead at Design "
                            "(test plan) and Test (sign-off); no task closes without the sign-off" % name)
            if "ui" in kinds and "ui-qa-expert" not in who:
                need.append("%s: kind of work ui but no ui-qa-expert at Test: every UI change is tested in the browser" % name)
    return kinds, p, hints


def check_spec(text, brief, folder="", name="spec.md", brief_name=None):
    brief_name = brief_name or SPEC_DOCS.get(name, "brief.md")
    product = name in PRODUCT_DOCS
    p, secs = [], sections(text)
    kinds, tp, th = check_team(text, folder, name, product)
    p += tp
    if "bug" in kinds:
        p += missing_parts(name, secs, BUG_PARTS)
    acs = find(secs, "acceptance criteria")
    if acs is None:
        p.append("%s: section \"Acceptance criteria\" is missing" % name)
    elif not ids("AC", acs):
        p.append("%s: acceptance criteria need ids AC1, AC2... so later stages can cite them" % name)
    if find(secs, "decisions this change needs", "decisions needed") is None:
        p.append("%s: section \"Decisions this change needs\" is missing" % name)
    if brief is None:
        p.append("%s: %s (what was understood, for the developer) is missing; the spec-analyst writes both" % (name, brief_name))
    else:
        for n in sorted(ids("Q", brief) - ids("Q", text)):
            p.append("%s: Q%d from %s is neither an open question nor a confirmed answer here" % (name, n, brief_name))
        for n in sorted(ids("A", find(sections(brief), "assumption") or "") - ids("A", text)):
            p.append("%s: assumption A%d from %s is missing here" % (name, n, brief_name))
    return p, th


def check_design(text, spec, name="design.md", stories=None, product=False):
    """A product-mode design may leave the criterion map to 04-stories.md: a criterion counts as covered when the
    design or the stories cite it, and the criteria come from 02-spec.md (else from the stories)."""
    p, secs = [], sections(text)
    left = text.count("<fill")
    if left:
        p.append("%s: %d place%s still say <fill> (the review_pack.py skeleton): fill or delete them"
                 % (name, left, "" if left == 1 else "s"))
    how = find(secs, "how it will work")
    if how is None:
        p.append("%s: section \"How it will work\" (plain English, for the developer) is missing" % name)
    if find(secs, "decisions") is None:
        p.append("%s: section \"Decisions\" is missing" % name)
    p += missing_parts(name, secs, ["Impact map", "Design patterns"])
    acs = ids("AC", find(sections(spec), "acceptance criteria") or "") if spec is not None else set()
    covered = ids("AC", text)
    if product and stories is not None:
        acs = acs or ids("AC", stories)
        covered |= ids("AC", stories)
    miss = sorted(acs - covered)
    if miss:
        p.append("%s: no planned change covers %s" % (name, ", ".join("AC%d" % n for n in miss))
                 + (" (cite it here or in %s)" % STORIES if product else ""))
    return p, plain_hints(name, how or "", sections(how or ""))


def explained(name, text, secs):
    """The "Data model explained" part (picture, relations, example rows, what happens, why) and its body."""
    p = []
    exp = None
    for h in secs:
        if "explained" in h:
            exp = h
    if exp is None:
        return ["%s: \"0. Data model explained\" is missing (picture, relations, example rows)" % name], text
    start = text.lower().find(exp)
    nxt = re.search(r"(?m)^##\s+1\.", text[start:])
    part = text[start:start + nxt.start()] if nxt else text[start:]
    sub = " ".join(h for h in sections(part))
    if "```" not in part:
        p.append("%s: the data-model picture (a text diagram in a ``` block) is missing" % name)
    for key, label in [("relate", "How the tables relate"), ("example", "Example rows"),
                       ("happens", "What happens when..."), ("why", "Why this shape")]:
        if key not in sub:
            p.append("%s: \"%s\" is missing from the data-model explanation" % (name, label))
    return p, part


def check_card(name, text):
    p, secs = [], sections(text)
    heads = [h for h in secs if h]
    for n, label in [(1, "Decision needed"), (2, "What changes"), (3, "Why"), (4, "Options"), (5, "Impact"),
                     (6, "Risks and rollback"), (7, "Questions and answers"), (8, "Decision")]:
        if not any(h.startswith("%d." % n) or h.startswith("%d " % n) for h in heads):
            p.append("%s: section \"%d. %s\" is missing (layout: %s)" % (name, n, label, CARD_LAYOUT))
    if not IDS["AC"].search(text):
        p.append("%s: no spec criterion (AC1...) is cited" % name)
    if re.search(r"\bsee (the )?(design|05-architecture)\.md\b", text, re.I):
        p.append("%s: the card must stand alone; copy the fact instead of \"see design.md\"" % name)
    if SECRETISH.search(text):
        p.append("%s: looks like a secret value; name config keys only" % name)
    human = text
    if re.search(r"(^|/)D2-", name):
        ep, human = explained(name, text, secs)
        p += ep
        if find(secs, "query speed") is None:
            p.append("%s: \"### Query speed\" (under 5. Impact: lookups, one-query-per-row loops, rows after a year) is missing" % name)
    return p, plain_hints(name, human, sections(human))


FIX_HEADER = "| ID | Sev | Title | Owner agent | Status |"
FIX_STATUS = ("open", "fixing", "fixed", "verified", "reopened", "wont-fix", "later")
FIX_OWNERS = ("backend-developer", "frontend-developer", "n8n-expert", "integration-engineer", "devops-engineer",
              "qa-engineer", "dev-handoff")
FIX_FIELDS = ("Ticket", "Found by", "Where", "Steps", "Expected", "Actual", "Evidence", "Suspected area", "Fix owner",
              "Retest", "History")
DOR_IDS = ["R%d" % n for n in range(1, 17)]
DOR_OLD = ["R%d" % n for n in range(1, 12)]  # a spec made READY before R12-R16 existed keeps its R1-R11 table


def table_rows(body):
    """[(header cells or None, rows)] is overkill here: the cells of every table line of a text, separators dropped."""
    out = []
    for line in body.split("\n"):
        t = line.strip()
        if t.startswith("|"):
            cells = [c.strip() for c in t.strip("|").split("|")]
            if not set("".join(cells)) <= set("-: "):
                out.append(cells)
    return out


def check_fixlist(text, name="fix-list.md"):
    """The fix list format (core/reference/qa/fix-list.md): header, Sev, Status, owner, a block per table row, the
    lines of each block, and no SIGNED OFF while a MUST is still to fix."""
    p = []
    lines = [l for l in text.split("\n")]
    head = next((l.strip() for l in lines if l.strip().startswith("|")), "")
    if head != FIX_HEADER:
        p.append("%s: the table header must be exactly \"%s\"" % (name, FIX_HEADER))
    rows, in_table = [], False
    for l in lines:
        t = l.strip()
        if t.startswith("|"):
            in_table = True
            cells = [c.strip() for c in t.strip("|").split("|")]
            if t != head and not set("".join(cells)) <= set("-: "):
                rows.append(cells)
        elif in_table:
            break
    open_must = []
    for c in rows:
        if len(c) < 5:
            p.append("%s: table row \"%s\" needs the 5 columns of the header" % (name, c[0] if c else ""))
            continue
        i, sev, status, owner = c[0], c[1], c[4].lower(), c[3]
        if sev not in ("MUST", "SHOULD"):
            p.append("%s: %s has Sev \"%s\" (MUST or SHOULD)" % (name, i, sev))
        if status not in FIX_STATUS:
            p.append("%s: %s has Status \"%s\" (%s)" % (name, i, c[4], ", ".join(FIX_STATUS)))
        if owner not in FIX_OWNERS:
            p.append("%s: %s has Owner agent \"%s\" (%s)" % (name, i, owner, ", ".join(FIX_OWNERS)))
        if sev == "MUST" and status in ("open", "fixing", "fixed", "reopened"):
            open_must.append(i)
    blocks, cur, fence = {}, None, False
    for l in lines:
        if l.lstrip().startswith("```"):
            fence = not fence
        m = None if fence else re.match(r"^##\s+(F\d+)\b", l)
        if m:
            cur = m.group(1)
            blocks[cur] = []
        elif cur and not fence:
            blocks[cur].append(l)
    tids = [c[0] for c in rows if c]
    for i in tids:
        if i not in blocks:
            p.append("%s: %s is in the table but has no \"## %s ...\" block" % (name, i, i))
    for i in blocks:
        if i not in tids:
            p.append("%s: block %s is not in the table" % (name, i))
    for i, body in blocks.items():
        b = "\n".join(body)
        for fld in FIX_FIELDS:
            if not re.search(r"(?im)(?:^[\s>*-]*|\|\s*)%s\s*:" % re.escape(fld), b):
                p.append("%s: %s has no \"%s:\" line" % (name, i, fld))
        if re.search(r"(?im)(?:^[\s>*-]*|\|\s*)Steps\s*:", b) and not re.search(r"(?m)^\s*\d+\.\s+\S", b):
            p.append("%s: %s Steps need numbered steps (1. 2. ...)" % (name, i))
    if open_must and re.search(r"(?im)Verdict:\s*\**\s*SIGNED OFF\b", text):
        p.append("%s: Verdict is SIGNED OFF but %s %s still to fix (open, fixing, fixed or reopened)"
                 % (name, ", ".join(open_must), "is" if len(open_must) == 1 else "are"))
    return p


def check_dor(text, name="spec.md"):
    """The Definition of Ready (core/reference/requirements/definition-of-ready.md) at the end of a spec."""
    p = []
    body = find(sections(text), "definition of ready")
    if body is None:
        return p
    got = {}
    for c in table_rows(body):
        if re.match(r"^R\d+$", c[0]):
            got[c[0]] = c
    settled = re.search(r"(?im)^[\s>*_-]*Requirements:\s*READY\b", text) and not any(i in got for i in DOR_IDS[11:])
    for i in (DOR_OLD if settled else DOR_IDS):
        if i not in got:
            p.append("%s: Definition of Ready has no row %s" % (name, i))
    failed = []
    for i, c in got.items():
        res = c[2].lower() if len(c) > 2 else ""
        note = c[3] if len(c) > 3 else ""
        if res not in ("pass", "fail", "n/a"):
            p.append("%s: Definition of Ready %s has Result \"%s\" (pass, fail or n/a)" % (name, i, res))
        elif res in ("fail", "n/a") and not note.strip():
            p.append("%s: Definition of Ready %s is %s: the Note column must say why" % (name, i, res))
        if res == "fail":
            failed.append(i)
    v = re.search(r"(?im)^[\s>*_-]*Verdict:\s*\**\s*(NOT READY|READY)\b", body)
    if not v:
        p.append("%s: Definition of Ready has no \"Verdict: READY\" or \"Verdict: NOT READY\" line" % name)
    elif v.group(1).upper() == "READY" and failed:
        p.append("%s: Definition of Ready verdict is READY but %s fail%s" % (name, ", ".join(failed), "s" if len(failed) == 1 else ""))
    if re.search(r"(?im)^[\s>*_-]*Requirements:\s*READY\b", text) and not (v and v.group(1).upper() == "READY"):
        p.append("%s: the \"Requirements: READY\" line needs the Definition of Ready verdict READY" % name)
    return p


# ---- R12 vague words (core/reference/requirements/vague-words.md + glossary.vague_words) ----------------------
VAGUE_FILE = project.core_path("reference/requirements/vague-words.md")
# headings of a requirements spec that are not requirements: questions, glossary, answers, the table, technical parts
VAGUE_SKIP = ("open questions", "smaller points", "gaps i found", "words used here", "glossary", "confirmed answers",
              "questions and answers", "confirmed by", "changes in revision", "definition of ready", "technical",
              "affected areas", "who will work", "not needed", "decisions", "lesson")
VAGUE_META = re.compile(r"(?i)^\s*[>*_-]*\s*(source|requester|requirements|size)\s*[*_]*\s*:")
# quoted text and inline code: the requester's own words, a question that quotes a word, a name in code
QUOTED = re.compile('``[^`\n]*``|`[^`\n]*`|"[^"\n]*"|“[^”\n]*”|„[^“”\n]*[“”]|'
                    '«[^»\n]*»|‘[^’\n]*’')
ESCAPE = re.compile(r"(?i)(review-spec\s+(?:dor\s+)?R\d+|develop review|test [\w-]+)\s*[-:–—]\s*\S"
                    r"|not catchable\s*:\s*\S")


def vague_words():
    """The core list (first column of the table under "The core list") plus the project's glossary.vague_words."""
    out = []
    try:
        with open(VAGUE_FILE, encoding="utf-8", errors="replace") as f:
            body = f.read().split("## The core list", 1)[-1]
    except OSError:
        body = ""
    for c in table_rows(body):
        if c and c[0].lower() not in ("word", "words"):
            out += [re.sub(r"\(.*?\)", "", w).strip(" *`") for w in c[0].split(",")]
    extra = (CFG.get("glossary") or {}).get("vague_words") or []
    if isinstance(extra, str):
        extra = _words_file(extra)
    out += [w.strip() for w in extra if isinstance(w, str)]
    seen, words = set(), []
    for w in out:
        if w and w.lower() not in seen:
            seen.add(w.lower())
            words.append(w)
    return words


def vague_pattern(word):
    w = re.escape(word.lower().rstrip("."))
    w = w.replace(r"\ ", r"\s+").replace(" ", r"\s+").replace(r"\/", "/").replace("/", r"\s*/\s*")
    tail = r"\.?" if word.endswith(".") else ""
    return re.compile(r"(?<![\w-])" + w + tail + r"(?![\w-])", re.I)


def vague_due(text):
    """A requirements spec gets the vague-word check unless it was made READY before R12 existed."""
    dor = find(sections(text), "definition of ready") or ""
    return bool(re.search(r"(?m)^\s*\|\s*R1[2-6]\s*\|", dor)
                or not re.search(r"(?im)^[\s>*_-]*Requirements:\s*READY\b", text))


def requirement_lines(text):
    """[(line number, heading, line)] of the requirement part of a spec: above the technical appendix, outside the
    question, glossary, answer and Definition of Ready sections, with quoted text, code and comments blanked."""
    text = re.sub(r"<!--.*?-->", lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)
    out, head, skip, fence = [], "", False, False
    for n, line in enumerate(text.split("\n"), 1):
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
            continue
        if fence:
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m:
            if len(m.group(1)) == 1:
                continue
            head = m.group(2).strip()
            if "technical appendix" in head.lower():
                break
            skip = any(w in head.lower() for w in VAGUE_SKIP)
            continue
        if skip or line.lstrip().startswith(">") or VAGUE_META.match(line):
            continue
        out.append((n, head, QUOTED.sub(" ", line)))
    return out


def should_ok(line, m):
    """'should' that is a priority label or part of a question, not a requirement."""
    if line.rstrip().endswith("?"):
        return True
    before, after = line[:m.start()], line[m.end():]
    if re.search(r"\(\s*\**$", before) and re.match(r"\**\s*\)", after):
        return True
    if re.search(r"(?i)priority\s*[:=-]?\s*\**\s*$", before):
        return True
    if re.match(r"^\s*(?:[-*+]|\d+[.)])?\s*\**$", before) and re.match(r"\**\s*:", after):
        return True
    if line.strip().startswith("|"):
        cell = before.rsplit("|", 1)[-1] + m.group(0) + after.split("|", 1)[0]
        if cell.strip(" *_").lower() in ("should", "should have"):
            return True
    return False


def check_vague(text, name="spec.md"):
    """R12: one PROBLEM per vague word and section in the requirement part (the line numbers listed)."""
    hits = {}
    pats = [(w, vague_pattern(w)) for w in vague_words()]
    for n, head, line in requirement_lines(text):
        for w, pat in pats:
            for m in pat.finditer(line):
                if re.search(r"(?i)\bhow\s+$", line[:m.start()]):
                    continue  # a label such as "how fast"
                if re.match(r"\s*\([^)\n]*\d[^)\n]*\)", line[m.end():]):
                    continue  # defined on the spot: fast (within 2 seconds)
                if w.lower() == "should" and should_ok(line, m):
                    continue
                hits.setdefault((head or "the top", w), []).append(n)
                break
    p = []
    for (head, w), lines in hits.items():
        p.append('%s: vague word "%s" in %s (line %s): replace it with a number or a concrete example, or quote it in '
                 'a question to the requester (R12, vague-words.md)' % (name, w, head, ", ".join(map(str, lines[:6]))))
    return p


def check_today(text, name="spec.md"):
    """review-spec with code there (context.md): a ## Today vs asked table, a Q per conflict, no code terms in it."""
    secs = sections(text)
    body = find(secs, "today vs asked")
    if body is None:
        return ["%s: code is here (context.md) but \"## Today vs asked\" is missing: per criterion what exists today, "
                "any conflict as a question, and what else it touches" % name]
    p = []
    rows = [c for c in table_rows(body) if c and re.match(r"^(AC\d+|in scope)", c[0], re.I)]
    if not rows:
        p.append("%s: \"Today vs asked\" has no row (one per criterion: | AC | Today | Asked | Conflict | Also touches |)" % name)
    qs = ids("Q", find(secs, "open questions") or "") | ids("Q", find(secs, "confirmed answers") or "")
    for c in rows:
        conflict = c[3] if len(c) > 3 else ""
        if len(c) < 5:
            p.append("%s: Today vs asked %s needs 5 cells (AC, Today, Asked, Conflict, Also touches)" % (name, c[0]))
        if conflict and not re.match(r"(?i)^\s*(none|no|-|n/a)\b", conflict):
            named = ids("Q", conflict)
            if not named:
                p.append("%s: Today vs asked %s has a conflict but names no question Q<n>" % (name, c[0]))
            for q in sorted(named - qs):
                p.append("%s: Today vs asked %s names Q%d, which is not under Open questions or Confirmed answers"
                         % (name, c[0], q))
        if CODEY.search(" ".join(c[1:])):
            p.append("%s: Today vs asked %s has code terms; keep plain words here and put path:line in the technical "
                     "appendix" % (name, c[0]))
    return p


# ---- /develop acceptance tests first (test.md) and the plan's test types (test-plan.md) ------------------------
TEST_TYPES = ("unit", "api", "ui", "e2e", "exploratory", "accessibility", "speed", "security", "ai-quality",
              "languages", "data-upgrade", "browsers", "smoke")
TYPE_WORDS = {"unit": "unit", "api": "api", "ui": "ui", "e2e": "e2e|journeys?", "exploratory": "exploratory",
              "accessibility": "accessibility", "speed": "speed", "security": "security",
              "ai-quality": "ai-quality|ai answer quality", "languages": "languages|long labels",
              "data-upgrade": "data-upgrade|data upgrade|migration", "browsers": "browsers|devices", "smoke": "smoke"}
NOT_AUTO_OWNERS = ("ui-qa-expert", "e2e-qa-expert")


def check_acceptance(text, spec, name="test.md"):
    """test.md from /develop: every criterion has an acceptance test seen failing before Build, or a Not automated
    row with its owner. A test.md without ## Acceptance tests (older tasks, /fix) is not checked."""
    secs = sections(text)
    acc = find(secs, "acceptance tests")
    if acc is None:
        return []
    p, seen = [], set()
    for c in table_rows(acc):
        m = re.match(r"^AC(\d+)", c[0]) if c else None
        if not m:
            continue
        a = "AC" + m.group(1)
        seen.add(int(m.group(1)))
        before = (c[2] if len(c) > 2 else "").upper()
        why = c[3] if len(c) > 3 else ""
        after = (c[4] if len(c) > 4 else "").upper()
        if not re.search(r"`[^`]+`", c[1] if len(c) > 1 else ""):
            p.append("%s: acceptance test %s names no test in backticks" % (name, a))
        if "PASS" in before:
            p.append("%s: acceptance test %s passes before Build: it tests nothing new (fix the test, or say the "
                     "behaviour already exists)" % (name, a))
        elif "FAIL" not in before:
            p.append("%s: acceptance test %s was not seen failing before Build (Before build: FAIL, run with the safe "
                     "test command)" % (name, a))
        elif not why.strip():
            p.append("%s: acceptance test %s fails but does not say why (the right reason: the missing behaviour)"
                     % (name, a))
        if "FAIL" in after:
            p.append("%s: acceptance test %s still fails after Build: Build is not done" % (name, a))
    for c in table_rows(find(secs, "not automated") or ""):
        m = re.match(r"^AC(\d+)", c[0]) if c else None
        if not m:
            continue
        seen.add(int(m.group(1)))
        owner = (c[2] if len(c) > 2 else "").lower()
        if not (c[1] if len(c) > 1 else "").strip():
            p.append("%s: Not automated AC%s does not say why" % (name, m.group(1)))
        if not any(o in owner for o in NOT_AUTO_OWNERS):
            p.append("%s: Not automated AC%s needs its owner: ui-qa-expert or e2e-qa-expert" % (name, m.group(1)))
    if spec is not None:
        for n in sorted(ids("AC", find(sections(spec), "acceptance criteria") or "") - seen):
            p.append("%s: AC%d has no acceptance test and no Not automated row (never skipped silently)" % (name, n))
    return p


def check_test_types(text, name="test-plan.md"):
    """test-plan.md: ## Test types names every type of core/reference/qa/test-types.md, with rows or n/a: reason.
    A plan without the section (written before core 1.16) gets a hint only."""
    body = find(sections(text), "test types")
    if body is None:
        return [], ["%s: no \"## Test types\" section (each type with its rows or n/a: reason; test-types.md)" % name]
    p, lines = [], body.lower().split("\n")
    for ty in TEST_TYPES:
        pat = re.compile(r"(?<![\w-])(?:%s)(?![\w-])" % TYPE_WORDS[ty])
        line = next((ln for ln in lines if pat.search(ln)), None)
        if line is None:
            p.append("%s: Test types does not name %s (rows, or n/a: reason)" % (name, ty))
        elif re.search(r"\bn/a\b", line) and not re.search(r"\bn/a\b\s*[:(\-–]\s*\w", line):
            p.append("%s: Test types %s is n/a without a reason" % (name, ty))
    return p, []


def fix_blocks(text):
    """[(block id, {lower-case ### heading: body})] for each `## <ID>` or `## F<n>` block of fix-proof.md."""
    out, cur, sub, buf, fence = [], None, "", [], False

    def close():
        if cur is not None:
            cur[1][sub] = "\n".join(buf)
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fence = not fence
        m = None if fence else re.match(r"^(#{2,6})\s+(.*?)\s*#*\s*$", line)
        if m and len(m.group(1)) == 2:
            close()
            words = m.group(2).split()
            cur, sub, buf = (words[0].strip("`:*") if words else "", {}), "", []
            out.append(cur)
        elif m and len(m.group(1)) >= 3 and cur is not None:
            close()
            sub, buf = m.group(2).strip().lower(), []
        else:
            buf.append(line)
    close()
    return out


def check_fixproof(text, name="fix-proof.md", only=None, escape=True):
    """{block: [problems]} for fix-proof.md; only = the block ids to check (default all); escape: the escape line
    is a problem (the /fix proof step, --fix), else the caller reports it as a hint (older blocks, other gates)."""
    blocks = fix_blocks(text)
    res = {}
    if only:
        for b in only:
            if not any(x[0].lower() == b.lower() for x in blocks):
                res[b] = ["%s: no block ## %s in %s" % (b, b, name)]
    elif not blocks:
        res[""] = ["%s: no bug blocks (## <ID> or ## F<n>, one per bug)" % name]
    for bid, secs in blocks:
        if only and bid.lower() not in [o.lower() for o in only]:
            continue
        pr = []

        def sec(*w):
            for k, v in secs.items():
                if k and any(x in k for x in w):
                    return v
            return None
        rp = sec("reproduction")
        if rp is None:
            pr.append("%s: no ### Reproduction section" % bid)
        elif not re.search(r"(?m)^\s*\d+[.)]\s+\S", rp):
            pr.append("%s: Reproduction has no numbered step" % bid)
        rc = sec("root cause")
        if rc is None:
            pr.append("%s: no ### Root cause section" % bid)
        else:
            m = re.search(r"(?im)^[\s>*_-]*proven[\s*_]*:[\s*_]*(yes|no)\b", rc)
            if not m:
                pr.append('%s: Root cause has no line "Proven: yes" or "Proven: no"' % bid)
            elif m.group(1).lower() == "yes":
                if not re.search(r"`[^`\s]+:\d+(?:[-,]\d+)*`", rc):
                    pr.append("%s: Root cause is Proven: yes but names no `path:line` in backticks" % bid)
            else:
                pr.append("%s: cause not proven - stays open, not fixed" % bid)
                if sec("what would prove it") is None:
                    pr.append("%s: Proven: no needs a ### What would prove it section" % bid)
        rt = sec("regression test")
        if rt is None:
            pr.append("%s: no ### Regression test section" % bid)
        else:
            if not re.search(r"`[^`\n]+`", rt):
                pr.append("%s: Regression test names no test in backticks (a class, method or test file)" % bid)
            if not re.search(r"(?i)fails?\b.{0,40}\b(before|on today|on the current)|before\b.{0,40}\bfail", rt):
                pr.append("%s: Regression test does not say it fails before the fix" % bid)
        ring = sec("regression ring")
        if ring is None:
            pr.append("%s: no ### Regression ring section" % bid)
        elif not (re.search(r"(?m)^\s*(?:[-*+]|\d+[.)])\s+\S", ring) or re.search(r"(?im)^\s*none\s*:\s*\S", ring)):
            pr.append('%s: Regression ring has no bullet and no "none: reason" line' % bid)
        fp = sec("fix plan")
        if fp is None:
            pr.append("%s: no ### Fix plan section" % bid)
        elif not any(re.search(r"`[^`\n]+`", ln) for ln in fp.split("\n") if re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", ln)):
            pr.append("%s: Fix plan has no bullet naming a file in backticks" % bid)
        if escape:
            pr += escape_problems(bid, secs)
        res[bid] = pr
    return res


def escape_problems(bid, secs):
    """The /fix escape check: one line naming the stage that should have caught the bug and the missing check."""
    esc = re.search(r"(?im)^[\s>*_-]*should have been caught at[\s*_]*:[\s*_]*(.+)$", "\n".join(secs.values()))
    if esc is None:
        return ['%s: no line "Should have been caught at: <stage> - <missing check>" (escape check)' % bid]
    if not ESCAPE.match(esc.group(1).strip().strip("`*")):
        return ["%s: Should have been caught at names no stage (review-spec R<n>, develop review, test <type>, "
                "or not catchable: <why>) and the missing check" % bid]
    return []


def fixproof_report(text, name="fix-proof.md", only=None, escape=True):
    """(problems, lines to print) for fix-proof.md."""
    res = check_fixproof(text, name, only, escape)
    problems, lines = [], []
    for b, pr in res.items():
        problems += pr
        lines.append("%s: %s" % (b or name, "OK" if not pr else "problems"))
        lines += ["  PROBLEM " + x for x in pr]
    return problems, lines


SQL_WRITE = re.compile(r"\b(INSERT|UPDATE|DELETE|MERGE|UPSERT|TRUNCATE|DROP|ALTER)\b|\bCREATE\s+TABLE\b", re.I)
NEED_COLS = ["id", "need", "volume", "source", "how", "cleanup", "status"]


def nocomments(text):
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def header_value(text, key):
    m = re.search(r"(?im)^[\s>*_-]*%s[\s*_]*:[\s*_]*(.*?)\s*$" % key, text)
    return None if m is None else m.group(1).strip().strip("*_").strip()


def check_datamap(text, name="data-map.md"):
    """Problems of the test data map (test-data-engineer): headers, the Needs table, read-only find, create through the app."""
    text = nocomments(text)
    secs = sections(text)
    out = []
    ap = header_value(text, "Approved")
    if ap is None:
        out.append("%s: no `Approved:` line (no, or <name>, <date>)" % name)
    elif ap.lower() != "no" and not re.match(r"^[^,]+,\s*\S+", ap):
        out.append("%s: `Approved:` is `%s`; write `no` or `<name>, <date>`" % (name, ap))
    for k in ("Hosts", "Query"):
        if header_value(text, k) is None:
            out.append("%s: no `%s:` line" % (name, k))
    body = find(secs, "needs")
    rows = table_rows(body) if body is not None else []
    if body is None:
        out.append("%s: no `## Needs` section" % name)
    elif not rows:
        out.append("%s: `## Needs` has no table" % name)
    else:
        cols = [c.lower() for c in rows[0]]
        if cols != NEED_COLS:
            out.append("%s: Needs table columns are `%s`; use | ID | Need | Volume | Source | How | Cleanup | Status |" % (
                name, " | ".join(rows[0])))
            rows = []
    ask = find(secs, "ask list") or ""
    asked = set(m.upper() for m in re.findall(r"(?im)^\s*[-*]\s*(D\d+)\s*:", ask))
    seen = set()
    for r in rows[1:]:
        if len(r) != 7:
            out.append("%s: row `%s` has %d cells, expected 7" % (name, r[0] if r else "", len(r)))
            continue
        rid, need, vol, src, how, clean, stat = r
        if not re.match(r"^D\d+$", rid):
            out.append("%s: row ID `%s` is not D1, D2, ..." % (name, rid))
        if rid in seen:
            out.append("%s: row %s appears twice" % (name, rid))
        seen.add(rid)
        if src.lower() not in ("find", "create", "ask"):
            out.append("%s: %s Source `%s` must be find, create or ask" % (name, rid, src))
        if stat.lower() not in ("planned", "ready", "missing", "asked", "blocked"):
            out.append("%s: %s Status `%s` must be planned, ready, missing, asked or blocked" % (name, rid, stat))
        w = SQL_WRITE.search(how)
        if src.lower() == "find" and w:
            out.append("%s: %s is a find row but How holds %s; find is read-only" % (name, rid, w.group(0).upper()))
        if src.lower() == "create":
            if w:
                out.append("%s: %s is a create row but How holds %s; create only through the app" % (name, rid, w.group(0).upper()))
            elif not ("/" in how or re.search(r"(?i)\b(import|seed)", how)):
                out.append("%s: %s create row: How must name an API path, an import or a seed script" % (name, rid))
            if clean.strip() in ("", "-"):
                out.append("%s: %s create row: Cleanup is empty" % (name, rid))
        if src.lower() == "ask" and rid.upper() not in asked:
            out.append("%s: %s is an ask row with no `- %s: ...` entry under ## Ask list" % (name, rid, rid))
    return out


def check_datamd(text, tid, name="data.md"):
    """Problems of a ticket's data.md (test-data-engineer): state line, record table, ask list, QA-<ID>- ids."""
    secs = sections(text)
    out = []
    m = re.search(r"(?im)^[\s>*_-]*Data[\s*_]*:[\s*_]*(\w+)", text)
    state = m.group(1).upper() if m else ""
    if state not in ("READY", "PARTIAL", "BLOCKED"):
        out.append("%s: no `Data: READY|PARTIAL|BLOCKED` line" % name)
    rows = table_rows(text)
    hdr = next((i for i, r in enumerate(rows) if [c.lower() for c in r] == ["row", "need", "record ids", "source", "status"]), None)
    if hdr is None:
        out.append("%s: no table | Row | Need | Record ids | Source | Status |" % name)
        return out
    ask = find(secs, "ask list") or ""
    blocked = False
    for r in rows[hdr + 1:]:
        if len(r) != 5:
            break
        row, need, rec, src, stat = r
        if stat.lower() not in ("ready", "asked", "blocked"):
            out.append("%s: row %s Status `%s` must be ready, asked or blocked" % (name, row, stat))
        if stat.lower() == "blocked":
            blocked = True
        if stat.lower() in ("asked", "blocked") and not re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(row), ask):
            out.append("%s: row %s is %s but not listed under ## Ask list" % (name, row, stat.lower()))
        if src.lower().startswith("create") and ("QA-%s-" % tid) not in rec:
            out.append("%s: row %s is created data; its record ids must contain QA-%s-" % (name, row, tid))
    if state == "READY" and blocked:
        out.append("%s: Data is READY but a row is blocked" % name)
    return out


def check_smoke(text, name="smoke.md"):
    """Problems of the smoke list: areas with paths and items, journeys with Role, Steps and Expected."""
    text = nocomments(text)
    out = []
    parts = re.split(r"(?m)^##[ \t]+(?=\S)", "\n" + text)[1:]
    if not parts:
        return ["%s: no `## <area>` sections" % name]
    for part in parts:
        head, _, body = part.partition("\n")
        area = head.strip()
        top, *subs = re.split(r"(?m)^###[ \t]+", body)
        pm = re.search(r"(?im)^[\s>*_-]*paths[\s*_]*:[\s*_]*(.*?)\s*$", top)
        if not pm or not re.search(r"[\w*/.]", pm.group(1)):
            out.append("%s: ## %s has no `paths:` line with a glob" % (name, area))
        if not re.search(r"(?m)^\s*- \S", top):
            out.append("%s: ## %s has no `- ` item" % (name, area))
        for sub in subs:
            sh, _, sb = sub.partition("\n")
            jm = re.match(r"(?i)^Journey:\s*(.*?)\s*(\[P1\])?\s*$", sh.strip())
            if not jm:
                continue
            jn = "## %s / Journey %s" % (area, jm.group(1) or "?")
            if not jm.group(1):
                out.append("%s: %s has no name" % (name, jn))
            for key in ("Role", "Expected"):
                km = re.search(r"(?im)^[\s>*_-]*%s[\s*_]*:[\s*_]*(.*?)\s*$" % key, sb)
                if not km or not km.group(1):
                    out.append("%s: %s has no `%s:` line" % (name, jn, key))
            if not re.search(r"(?im)^[\s>*_-]*Steps[\s*_]*:[\s*_]*(?:\d+[.)]|.*\n\s*\d+[.)])", sb):
                out.append("%s: %s has no `Steps:` with numbered steps" % (name, jn))
    return out


def standalone(flag):
    """--data-map [PATH] and --smoke [PATH]: no ticket id; the default file from the config or the repo."""
    i = sys.argv.index(flag)
    given = sys.argv[i + 1] if len(sys.argv) > i + 1 and not sys.argv[i + 1].startswith("--") else None
    if flag == "--data-map":
        dflt = (((CFG.get("qa") or {}).get("data") or {}).get("map")) or ".claude/qa/data-map.md"
        fn = check_datamap
    else:
        dflt = ".claude/smoke.md"
        fn = check_smoke
    p = given or dflt
    full = p if os.path.isabs(p) else os.path.join(ROOT, p)
    text = read(full)
    if text is None:
        if given is None:  # the default file is checked only when it exists
            print("%s: not found, skipped." % p)
            sys.exit(0)
        print("PROBLEM %s: not found" % p)
        sys.exit(1)
    problems = fn(text, os.path.basename(p))
    for x in problems:
        print("PROBLEM " + x)
    if not problems:
        print("%s check passed." % os.path.basename(p))
    sys.exit(1 if problems else 0)


def check(folder, files=None):
    """(problems, hints) for the given files of a task folder. Unknown documents get hints only."""
    if not os.path.isdir(folder):
        return ["task folder %s not found" % os.path.basename(folder)], []
    files = files or [os.path.relpath(f, folder).replace("\\", "/") for f in
                      [os.path.join(folder, n) for n in ALL_DOCS]
                      + sorted(glob.glob(os.path.join(folder, "decisions", "D*.md"))) if os.path.isfile(f)]
    files = list(files) + [n for n in TASK_DOCS if os.path.isfile(os.path.join(folder, n))
                           and n not in [os.path.basename(f.replace("\\", "/")) for f in files]]
    if os.path.isfile(os.path.join(folder, "fix-list.md")) and "fix-list.md" not in [os.path.basename(f.replace("\\", "/")) for f in files]:
        files = list(files) + ["fix-list.md"]
    if os.path.isfile(os.path.join(folder, "fix-proof.md")) and "fix-proof.md" not in [os.path.basename(f.replace("\\", "/")) for f in files]:
        files = list(files) + ["fix-proof.md"]
    for extra in ("data.md", "test.md", "test-plan.md"):
        if os.path.isfile(os.path.join(folder, extra)) and extra not in [os.path.basename(f.replace("\\", "/")) for f in files]:
            files = list(files) + [extra]
    reviews = review_docs()
    problems, hints = [], []
    for f in files:
        name = f.replace("\\", "/")
        text = read(os.path.join(folder, name))
        base = os.path.basename(name)
        if text is None:
            if base in REQUIRED or re.match(r"(decisions/)?D[1-8]-", name, re.I):
                problems.append("%s: not found in the task folder" % name)
            continue
        known = True
        if base == "fix-proof.md":
            r = fixproof_report(text, name, escape=False)[0], [name + ": " + h for b, s in fix_blocks(text)
                                                                for h in escape_problems(b, s)]
        elif base in BRIEF_DOCS:
            r = check_brief(text, base)
        elif base == "fix-list.md":
            r = check_fixlist(text, name), []
        elif base == "data.md":
            r = check_datamd(text, os.path.basename(folder.rstrip("/\\")), name), []
        elif base == "test.md":
            known = find(sections(text), "acceptance tests") is not None
            r = check_acceptance(text, read(os.path.join(folder, "spec.md")), name), []
        elif base == "test-plan.md":
            r = check_test_types(text, name)
        elif base in SPEC_DOCS:
            dor = base not in PRODUCT_DOCS and find(sections(text), "definition of ready") is not None
            if dor and not re.search(r"(?im)^[\s>*_-]*kind of work[\s*_]*:", text):
                r = check_dor(text, base), []  # a requirements-only spec: the technical part comes after READY
                if status(folder).get("skill") == "review-spec" and os.path.isfile(os.path.join(folder, "context.md")):
                    r = r[0] + check_today(text, base), r[1]
            else:
                r = check_spec(text, read(os.path.join(folder, SPEC_DOCS[base])), folder, base)
                if dor:
                    r = r[0] + check_dor(text, base), r[1]
            if dor and vague_due(text):
                r = r[0] + check_vague(text, base), r[1]
        elif base in DESIGN_DOCS:
            stories = read(os.path.join(folder, STORIES)) if base in PRODUCT_DOCS else None
            r = check_design(text, read(os.path.join(folder, DESIGN_DOCS[base])), base, stories, base in PRODUCT_DOCS)
            r = r[0] + check_task_design(folder, base), r[1]
        elif base == "triage.md":
            r = check_triage(text, folder)
        elif base == "context.md":
            r = check_context(text, folder)
        elif base == "safety.md":
            r = check_safety(text, folder)
        elif base in PERF_DOCS:
            # Spec writes the first three parts, Design the next three; "After" is filled at Verify
            need = PERF_PARTS[:6] if os.path.isfile(os.path.join(folder, PERF_DOCS[base])) else PERF_PARTS[:3]
            r = missing_parts(base, sections(text), need), []
        elif base in UI_DOCS:
            design, parts = UI_DOCS[base]
            secs = sections(text)
            journeys_only = find(secs, "journeys") is not None and not any(find(secs, x.lower()) is not None for x in parts)
            if journeys_only and not os.path.isfile(os.path.join(folder, design)):
                r = [], plain_hints(base, text, secs)  # journeys first; the screen parts follow at design
            else:
                r = missing_parts(base, secs, parts), plain_hints(base, text, secs)
        elif base in EXPERT_PARTS:
            r = missing_parts(base, sections(text), EXPERT_PARTS[base]), []
        elif base in reviews:
            r = missing_parts(base, sections(text), REVIEW_PARTS), []
        elif re.match(r"D[1-8]-", base, re.I):
            r = check_card(name, text)
        elif base in DATA_MODEL_DOCS:
            ep, human = explained(base, text, sections(text))
            r, known = ([], ep + plain_hints(base, human, sections(human))), False
        elif base.lower().endswith(".md"):
            r, known = ([], plain_hints(base, text, sections(text))), False
        else:
            continue
        problems += r[0]
        hints += r[1]
        if EMAIL.search(text):
            msg = "%s: has an e-mail address (%s...); use a made-up name or a role, never real people's data" \
                  % (name, EMAIL.search(text).group(0)[:3])
            (problems if known else hints).append(msg)
    return problems, hints


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    for flag in ("--data-map", "--smoke"):
        if flag in sys.argv[1:]:
            standalone(flag)
    folder = os.path.join(WORK, sys.argv[1])
    if not os.path.isdir(folder) and os.path.isdir(sys.argv[1]):
        folder = os.path.abspath(sys.argv[1])  # a folder path: requirements only (requirements/<id>, no project.json)
    if "--fix" in sys.argv[2:]:
        i = sys.argv.index("--fix")
        text = read(os.path.join(folder, "fix-proof.md"))
        if text is None:
            print("PROBLEM fix-proof.md: not found in the task folder")
            sys.exit(1)
        problems, lines = fixproof_report(text, "fix-proof.md", sys.argv[i + 1:] or None)
        print("\n".join(lines))
        sys.exit(1 if problems else 0)
    problems, hints = check(folder, sys.argv[2:] or None)
    for x in problems:
        print("PROBLEM " + x)
    for x in hints:
        print("hint    " + x)
    if not problems:
        print("Hand-off check passed" + (" (%d hint(s))" % len(hints) if hints else "") + ".")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
