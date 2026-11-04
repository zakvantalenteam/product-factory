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

  python .claude/core/scripts/handoff_check.py ID [FILE ...]   (files relative to <work>/ID; default: all)
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
CARD_LAYOUT = ".claude/core/reference/review/decision-card.md"

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


def check(folder, files=None):
    """(problems, hints) for the given files of a task folder. Unknown documents get hints only."""
    if not os.path.isdir(folder):
        return ["task folder %s not found" % os.path.basename(folder)], []
    files = files or [os.path.relpath(f, folder).replace("\\", "/") for f in
                      [os.path.join(folder, n) for n in ALL_DOCS]
                      + sorted(glob.glob(os.path.join(folder, "decisions", "D*.md"))) if os.path.isfile(f)]
    files = list(files) + [n for n in TASK_DOCS if os.path.isfile(os.path.join(folder, n))
                           and n not in [os.path.basename(f.replace("\\", "/")) for f in files]]
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
        if base in BRIEF_DOCS:
            r = check_brief(text, base)
        elif base in SPEC_DOCS:
            r = check_spec(text, read(os.path.join(folder, SPEC_DOCS[base])), folder, base)
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
    folder = os.path.join(WORK, sys.argv[1])
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
