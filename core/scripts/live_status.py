"""Live status of the task or product an agent is working on, for Claude Code and Cursor (agent core).

Keeps <work>/<id>/status.json (+ status.md, status.js, events.jsonl) and <work>/live.js, which <work>/live.html
shows live in a browser tab. <work> is `work_dir` in .claude/project.json (default .claude/work). The sdlc and
factory skills call the commands; hooks call `hook` on every tool call, so reads, edits, commands and agents
appear by themselves.

Two modes, fixed at the first init:
  task     a change to an existing product. Stages: spec design build review test verify release wrap.
  product  a new product (factory flow). Stages: intake base requirements product prototype stories design build
           review audit release. Gates G0 intake, G1 product, GP prototype, G2 stories, G3 design, G4 release.

  L = python .claude/core/scripts/live_status.py
  init ID [--title T] [--size S|M|L] [--mode task|product] [--root PATH] [--screen] [--tool claude|cursor]
                                     start or resume (binds this session to it); product mode starts with the
                                     factory's default team; --root is the product root (product mode default:
                                     products_root/ID); --screen keeps the prototype stage of a size S product
  stage ID STAGE start|done|fail [--out TEXT] [--actor NAME]
  gate ID STAGE "QUESTION" [--file F]... [--open prototype.html] [--decision D2] [--skip-check REASON] [--by AGENT]
                                     wait for the developer; repeat --file to review a stage's documents in one
                                     gate (decisions/D2-*.md cards are recognised); spec/design documents must pass
                                     handoff_check.py first; prints the gate's full text for the chat
  chat ID                            the open gate's full text again (every document, then the question)
  quick "TEXT"                       a quick fix done without a task (sdlc triage): logged in quick-fixes.md
  ok ID STAGE [--note TEXT] [--decision D2 | --file F]   the developer approved all of the gate, or one card
                                     (product mode: the stage's gate G0..G4 is approved with the note as the words)
  changes ID STAGE "SUMMARY" [--decision D3]...   the developer asked for changes (to these cards)
  ask ID "QUESTION" --answer "TEXT" [--decision D2 | --file F]   a question at the open gate and its answer
                                     (added to that document's Q&A)
  log ID "TEXT" [--kind note|block|flag|must] [--stage STAGE] [--actor NAME]   (must: one review MUST, kept in view)
  plan ID [--file F] [--why REASON]  the team: one row per expert from "## Who will work on this"
                                     (Stage | Expert | Why); default file spec.md or triage.md (task), 02-spec.md
                                     or 00-intake.md (product); stages with nobody on them are skipped (except
                                     build and wrap, or intake and build); after the team gate a change needs --why
  risk ID low|medium|high --why "EVIDENCE"   change the task's risk (plan reads "Risk: ..." and "## Risk evidence" from
                                     triage.md, default medium); the risk sets the stage time budgets (timing.py)
  expert ID STAGE "EXPERT" start|done|skip [--out TEXT]   one expert's status (agents are tracked by the hook)
  code ID open|closed                product mode: open or close code writes in the product root by hand (a live
                                     base stage and an approved G3 open them; base start and G3 clear the hand value)
  hook [--cursor]                    stdin: hook JSON; records activity for the session's task
  open [ID]                          serve <work> on 127.0.0.1:<live_port> if needed and open the page
  serve [--port N]                   the page server (what `open` starts): <work> plus /_file?p=<path>, read-only,
                                     so the page can open the files the agents changed (repo and product roots)

Time budgets: each stage has minutes per risk (timing.py BUDGETS, overridable with "budgets" in project.json);
the page shows a running stage's working time against it and flags an overrun (gate waits are not working time).
`python .claude/core/scripts/timing.py [ID ...]` prints the timing report.

Demo tasks (`demo-<scenario>`, written by simulate.py with `init --demo`) never bind a session, never write
live.js and are left out of timing reports; `simulate.py --clean` removes them.

For hooks and flow checks (import this module): session_of, session_task, load, tasks, code_writes_open,
record, session_edits, path, write, DECISIONS, ROOT, WORK.
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime

sys.dont_write_bytecode = True
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:  # `python -I` leaves the script's folder off sys.path
    sys.path.insert(0, _HERE)
import project  # noqa: E402
import timing  # noqa: E402

ROOT = project.repo_root()
WORK = project.work_dir(ROOT)
CFG = project.config(ROOT)
TEMPLATE = os.path.join(_HERE, "live_status.html")
PORT = int(CFG.get("live_port") or project.DEFAULTS["live_port"])
KEEP_EVENTS = 200
SCRIPT = "python .claude/core/scripts/live_status.py"

# ---- modes, stages, gates ---------------------------------------------------------------------

TASK_STAGES = [("spec", "Spec"), ("design", "Design"), ("build", "Build"), ("review", "Review"),
               ("test", "Test"), ("verify", "Verify"), ("release", "Release"), ("wrap", "Wrap-up")]
PRODUCT_STAGES = [("intake", "Intake"), ("base", "Base"), ("requirements", "Requirements"), ("product", "Product review"),
                  ("prototype", "Prototype"), ("stories", "Stories"), ("design", "Design"), ("build", "Build"),
                  ("review", "Review"), ("audit", "Audit"), ("release", "Release")]
MODES = {"task": TASK_STAGES, "product": PRODUCT_STAGES}
STAGES = TASK_STAGES
NAMES = dict(TASK_STAGES + PRODUCT_STAGES)
STAGE_IDS = {"intake": "S0", "base": "S1", "requirements": "S2", "product": "S3", "prototype": "SP", "stories": "S4",
             "design": "S5", "build": "S6", "review": "S7", "audit": "S8", "release": "S9"}
GATE_IDS = {"intake": "G0", "product": "G1", "prototype": "GP", "stories": "G2", "design": "G3", "release": "G4"}
GATE_NAMES = {"G0": "Plan agreed", "G1": "Product owner answers", "GP": "Prototype approved", "G2": "Scope and MVP",
              "G3": "Design approved", "G4": "Go-live"}
ACTOR = {"task": {"spec": "spec-analyst", "design": "solution-architect", "build": "main session",
                  "review": "code-reviewer", "test": "qa-engineer", "verify": "verifier",
                  "release": "release-manager", "wrap": "commit-msg"},
         "product": {"intake": "main session", "base": "base-builder", "requirements": "spec-analyst",
                     "product": "product-critic", "prototype": "ux-designer", "stories": "story-sizer",
                     "design": "solution-architect", "build": "backend-developer", "review": "code-reviewer",
                     "audit": "audit-expert", "release": "release-manager"}}
SKIP = {"task": {"S": {"spec", "design", "release"}, "M": {"release"}, "L": set()},
        "product": {"S": {"base", "product", "prototype", "stories"}, "M": {"base"}, "L": set()}}
ALWAYS = {"task": ("build", "wrap"), "product": ("intake", "build")}  # run even with nobody planned on them
CONFIRM = {"task": "spec", "product": "intake"}  # the gate that confirms the team
CLOSING = {"task": ("spec", "design"), "product": tuple(GATE_IDS)}  # an approved gate finishes the stage
CHECKED = {"task": ("spec", "design"), "product": ("requirements", "product", "design")}  # handoff_check first
BRIEF = {"task": "brief.md", "product": "02-gaps.md"}
BRIEF_AT = {"task": ("spec",), "product": ("requirements", "product")}
EXPERT_DOCS = {"task": ("perf.md", "ui.md", "sf.md", "ai.md", "n8n.md") + tuple(CFG.get("expert_docs") or {}),
               "product": ("05-performance.md", "05-ui.md", "05-sf-fields.md", "05-ai.md", "05-n8n.md")}
PLAN_FILES = {"task": ("spec.md", "triage.md"), "product": ("02-spec.md", "00-intake.md")}

# ---- agents and teams -------------------------------------------------------------------------

TEAMS = [("lead", "Lead", ["main session"]),
         ("product", "Product", ["spec-analyst", "product-critic", "story-sizer"]),
         ("design", "Design", ["ux-designer"]),
         ("architecture", "Architecture", ["solution-architect", "data-architect", "security-architect"]),
         ("engineering", "Engineering", ["base-builder", "backend-developer", "frontend-developer", "integration-engineer"]),
         ("domain", "Domain experts", ["sf-expert", "ai-engineer", "n8n-expert"]),
         ("quality", "Quality", ["code-reviewer", "qa-engineer", "verifier", "performance-engineer", "bug-investigator"]),
         ("audit", "Audit", ["audit-expert"]),
         ("operations", "Operations", ["devops-engineer", "release-manager"]),
         ("helpers", "Helpers", ["explorer"])]
DOMAIN_CORE = ("sf-expert", "ai-engineer", "n8n-expert")
# the bench a task-mode page shows next to the team (product mode shows every core agent)
TASK_BENCH = {"main session", "spec-analyst", "bug-investigator", "ux-designer", "solution-architect", "data-architect",
              "security-architect", "code-reviewer", "qa-engineer", "verifier", "performance-engineer",
              "release-manager", "explorer"}
# earlier agent names -> core agents; "<repo>-verifier" and "<repo>-explorer" map by their ending
RENAMES = {"test-runner": "qa-engineer", "ui-engineer": "ux-designer", "prd-reviewer": "spec-analyst",
           "requirements-analyst": "spec-analyst", "prototype-designer": "ux-designer",
           "api-designer": "solution-architect", "system-reviewer": "verifier", "technical-writer": "release-manager",
           "sf-consultant": "sf-expert", "team-lead": "main session"}
# task mode without a team: the stage an agent's start opens
AGENT_STAGE = {"spec-analyst": "spec", "bug-investigator": "spec", "solution-architect": "design",
               "data-architect": "design", "security-architect": "design", "ux-designer": "design",
               "sf-expert": "design", "ai-engineer": "design", "n8n-expert": "design", "code-reviewer": "review", "qa-engineer": "test",
               "verifier": "verify", "release-manager": "release"}
# product mode: the factory's default team (AGENTS.md flow table, core names); domain rows only when configured
PRODUCT_TEAM = [
    ("intake", "main session", "triage card and plan (00-intake.md)"),
    ("intake", "spec-analyst", "readiness of the requirement (01-prd-review.md)"),
    ("intake", "devops-engineer", "where and how it will run (00-infra.md)"),
    ("base", "base-builder", "fresh base project, checker 100 %"),
    ("base", "devops-engineer", "deploy check of the base"),
    ("requirements", "spec-analyst", "spec, non-functional sheet, gaps (02-spec.md, 02-nfr.md, 02-gaps.md)"),
    ("requirements", "sf-expert", "SuccessFactors fit (02-sf-fit.md)"),
    ("product", "product-critic", "a good, clear product? (03-product-review.md)"),
    ("product", "ux-designer", "journeys and screens (03-journeys.md)"),
    ("prototype", "ux-designer", "options or variants to approve (P-*.html)"),
    ("stories", "story-sizer", "stories, points, MVP slice (04-stories.md)"),
    ("design", "solution-architect (design)", "architecture (05-architecture.md)"),
    ("design", "solution-architect (contract)", "API contract (05-openapi.yaml)"),
    ("design", "data-architect", "data model (05-data-model.md)"),
    ("design", "security-architect", "access and privacy (05-security.md)"),
    ("design", "sf-expert", "SuccessFactors fields (05-sf-fields.md)"),
    ("design", "ai-engineer", "AI behaviour and cost (05-ai.md)"),
    ("design", "n8n-expert", "n8n workflows (05-n8n.md)"),
    ("design", "integration-engineer", "outside systems (05-integrations.md)"),
    ("design", "devops-engineer", "environments and pipeline (05-ops.md)"),
    ("design", "ux-designer", "UI build spec (05-ui.md)"),
    ("design", "performance-engineer", "budgets for volume (05-performance.md)"),
    ("design", "verifier", "the design parts fit together"),
    ("build", "backend-developer", "backend per story"),
    ("build", "frontend-developer", "screens per story"),
    ("build", "integration-engineer", "connections to outside systems"),
    ("build", "devops-engineer", "environment changes"),
    ("build", "qa-engineer", "tests from the criteria"),
    ("review", "code-reviewer", "code review (07-code-review.md)"),
    ("review", "qa-engineer", "run the tests (07-test-report.md)"),
    ("review", "performance-engineer", "hot paths (07-performance.md)"),
    ("review", "verifier", "the built product matches the design"),
    ("review", "sf-expert", "SuccessFactors code"),
    ("review", "n8n-expert", "n8n node changes"),
    ("audit", "audit-expert", "Definition of Done (08-audit.md)"),
    ("release", "devops-engineer", "deploy plan (09-deploy-plan.md)"),
    ("release", "release-manager", "go-live package (09-release.md)")]

SECRETISH = re.compile(r"(password|passwd|secret|token|api[_-]?key)\s*[=:]"
                       r"|\bbearer\s+\S|--?(password|passwd|secret|token|api[_-]?key|client[_-]?secret)\b|authorization:"
                       r"|\bcookie:|\s-u\s+\S+:\S|://[^/\s:@]+:[^@\s/]+@", re.I)
# Files the page and the feed never show (credentials and keys); a repo adds its own in project.json
# (guard.no_show, guard.secret_files).
NO_SHOW = [".env*", "*.pem", "*.key", "*.p12", "*.jks", "*.pfx", "*.keystore", "id_rsa*", "id_ed25519*"]


def experts_list():
    return [canon(e) for e in CFG.get("experts") or [] if isinstance(e, str) and e.strip()]


def canon(name):
    """The core agent of a hook or table name: drops a plugin prefix and maps earlier names."""
    n = project.agent_name(str(name or ""))
    low = n.lower()
    if low == "main" or low.startswith("main session"):
        return "main session"
    own = [str(e).lower() for e in CFG.get("experts") or []]
    if low in RENAMES and low not in own:  # a project that keeps its own agent of an earlier name keeps that name
        return RENAMES[low]
    if low not in own:
        for end, core in (("-verifier", "verifier"), ("-explorer", "explorer")):
            if low.endswith(end):
                return core
    return n


def team_of(agent):
    a = canon(agent).lower()
    for tid, _, agents in TEAMS:
        if a in agents:
            return tid
    return "domain" if a in [e.lower() for e in experts_list()] else "helpers"


CALLS = {}


def call_budget(agent, mode):
    """The "about N tool calls" of an agent's Speed line (task or product mode), for the page's calls meter."""
    key = (agent.lower(), mode)
    if key not in CALLS:
        CALLS[key] = 0
        for d in (os.path.join(ROOT, ".claude", "agents"), os.path.join(_HERE, "..", "agents")):
            try:
                with open(os.path.join(d, agent + ".md"), encoding="utf-8") as f:
                    speed = next((x for x in f.read().splitlines() if x.startswith("Speed:")), "")
            except OSError:
                continue
            m = re.search(r"\b%s mode about (\d+)" % mode, speed) or re.search(r"\babout (\d+) tool calls", speed)
            CALLS[key] = int(m.group(1)) if m else 0
            break
    return CALLS[key]


def teams_table(mode):
    """Every team with its bench of agents, for the page's team map (no project agent is hard-coded there)."""
    experts = experts_list()
    out = []
    for tid, name, agents in TEAMS:
        ags = list(agents)
        if tid == "domain":
            ags = [a for a in ags if not experts or a in experts] + \
                  [e for e in experts if e not in ags and team_of(e) == "domain"]
        elif mode == "task":
            ags = [a for a in ags if a in TASK_BENCH]
        out.append(dict(id=tid, name=name, agents=ags))
    return out


def hidden(relpath):
    g = CFG.get("guard") or {}
    return project.match(relpath, NO_SHOW + list(g.get("no_show") or []) + list(g.get("secret_files") or []))


def secret_command(cmd):
    """A command whose text holds a credential or names a secret file is never recorded."""
    if SECRETISH.search(cmd):
        return True
    for tok in re.split(r"[\s\"'=<>|;&(),]+", cmd):
        t = tok.replace("\\", "/")
        while t.startswith("./"):
            t = t[2:]
        if t and hidden(t.lstrip("/")):
            return True
    return False


# ---- state ------------------------------------------------------------------------------------

def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def path(*parts):
    return os.path.join(WORK, *parts)


def write(p, text):
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    for _ in range(25):  # a browser reading the file can hold it for a moment on Windows
        try:
            os.replace(tmp, p)
            return
        except PermissionError:
            time.sleep(0.02)
    os.replace(tmp, p)


def with_lock(fn):
    os.makedirs(WORK, exist_ok=True)
    lock, fd = path(".lock"), None
    for _ in range(80):
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(lock) > 5:
                    os.remove(lock)
            except OSError:
                pass
            time.sleep(0.025)
    try:
        return fn()
    finally:
        if fd is not None:
            os.close(fd)
            try:
                os.remove(lock)
            except OSError:
                pass


def session_of(data):
    """Claude's session_id or Cursor's conversation_id from hook JSON, made safe for a file name."""
    sid = str((data or {}).get("session_id") or (data or {}).get("conversation_id") or "")
    return re.sub(r"[^A-Za-z0-9._-]", "", sid)[:80] or None


def session_task(sid):
    """The task a session works on: bound when that session runs a live_status.py command for it."""
    try:
        with open(path(".sessions", sid), encoding="utf-8") as f:
            tid = f.read().strip()
        return tid if tid and not is_demo(tid) and os.path.isfile(path(tid, "status.json")) else None
    except (OSError, TypeError):
        return None


def is_demo(tid):
    """A demo task replayed by simulate.py: never bound to a session, never the page's default task."""
    return str(tid or "").startswith("demo-")


def load(tid):
    with open(path(tid, "status.json"), encoding="utf-8") as f:
        return json.load(f)


def tasks():
    """Ids of every task and product in <work> (folders with a status.json)."""
    try:
        names = sorted(os.listdir(WORK))
    except OSError:
        return []
    return [n for n in names if not n.startswith(".") and os.path.isfile(path(n, "status.json"))]


def mode_of(st):
    m = (st or {}).get("mode") or "task"
    return m if m in MODES else "task"


def code_writes_open(st):
    """May code be written in the product root? Task mode: always (the decision cards guard it). Product mode:
    by hand (`code ID open|closed`, until base starts again or G3 is approved), else while the base stage runs
    and after the design gate (G3) is approved."""
    if mode_of(st) != "product":
        return True
    cw = st.get("code_writes")
    if cw in ("open", "closed"):
        return cw == "open"
    base = next((s for s in st.get("stages") or [] if s.get("k") == "base"), None)
    if base and base.get("state") in ("live", "fail"):
        return True
    return ((st.get("gates") or {}).get("G3") or {}).get("state") == "approved"


def stage_of(st, k):
    return next(s for s in st["stages"] if s["k"] == k)


def need_stage(st, k, cmd):
    keys = [s["k"] for s in st["stages"]]
    if k in keys:
        return None
    return "%s: %s has no stage %s (%s mode: %s)" % (cmd, st["id"], k, mode_of(st), " ".join(keys))


def sname(st, k):
    return next((s["name"] for s in st["stages"] if s["k"] == k), NAMES.get(k, k))


def current_stage(st):
    for state in ("wait", "live", "fail"):
        hit = [s for s in st["stages"] if s["state"] == state]
        if hit:
            return hit[-1]["k"]
    started = [s for s in st["stages"] if s.get("start")]
    if started:
        return started[-1]["k"]
    return next((s["k"] for s in st["stages"] if s["state"] != "skip"), st["stages"][0]["k"])


def add(st, stage, kind, text, actor=None, **extra):
    st["seq"] = st.get("seq", 0) + 1
    e = dict(n=st["seq"], t=now(), stage=stage, kind=kind, actor=actor or "", text=str(text)[:220], **extra)
    st["events"] = (st.get("events", []) + [e])[-KEEP_EVENTS:]
    counts = st.setdefault("counts", {})
    counts[kind] = counts.get(kind, 0) + 1
    with open(path(st["id"], "events.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(e) + "\n")
    return e


def work_rel():
    return os.path.relpath(WORK, ROOT).replace("\\", "/")


def markdown(st):
    mode = mode_of(st)
    out = ["# %s %s" % (st["id"], st.get("title", "")), "",
           "Size %s, %s, %s mode. Live view: %s/live.html" % (st.get("size", "?"), st.get("tool", "claude"), mode,
                                                              work_rel())]
    if st.get("root"):
        out.append("product_root: " + st["root"])
    if mode == "product":
        out.append("code_writes: " + ("open" if code_writes_open(st) else "closed"))
    out.append("Risk: %s%s" % (timing.norm_risk(st.get("risk")) or timing.DEFAULT_RISK,
                              " (" + "; ".join(st["riskWhy"]) + ")" if st.get("riskWhy") else ""))
    out += ["", "| stage | state | evidence |", "|---|---|---|"]
    for s in st["stages"]:
        out.append("| %s | %s | %s |" % (((s["sid"] + " ") if s.get("sid") else "") + s["name"], s["state"], s.get("out", "")))
    over = timing.overrun_notes(st)
    if over:
        out += ["", "Over budget (working time, gate waits left out):"] + ["- " + x for x in over]
    if mode == "product":
        out += [""] + ["- %s %s: %s%s" % (g, GATE_NAMES[g], (st.get("gates") or {}).get(g, {}).get("state", "open"),
                                          ' - "%s"' % st["gates"][g]["words"] if (st.get("gates") or {}).get(g, {}).get("words") else "")
                       for g in GATE_NAMES]
    if st.get("decisions"):
        out += ["", "Decisions: " + ", ".join("%s %s %s" % (k, v.get("title", ""), v.get("state", ""))
                                             for k, v in sorted(st["decisions"].items()))]
    if st.get("gate"):
        out += ["", "Waiting for the developer: " + st["gate"]["question"]]
    return "\n".join(out) + "\n\n" + notes(st["id"])


def notes(tid):
    """The hand-written part of status.md (from "## Notes" on) survives every regeneration."""
    try:
        with open(path(tid, "status.md"), encoding="utf-8") as f:
            text = f.read()
        i = text.find("## Notes")
        if i >= 0:
            return text[i:]
    except OSError:
        pass
    return "## Notes\n\nFor release:\n"


def page_source():
    """The page template with this project's name and ticket prefix filled in."""
    with open(TEMPLATE, "rb") as f:
        src = f.read()
    meta = json.dumps({"name": CFG.get("name") or "", "ticket": (project.ticket_prefixes(CFG) or [""])[0]}) \
        .replace("</", "<\\/")
    return src.replace(b'window.__PROJECT__={"name":"","ticket":""};', ("window.__PROJECT__=%s;" % meta).encode("utf-8"), 1)


def sync_page():
    try:
        src = page_source()
        dst = path("live.html")
        cur = None
        if os.path.isfile(dst):
            with open(dst, "rb") as f:
                cur = f.read()
        if cur != src:
            with open(dst, "wb") as f:
                f.write(src)
    except OSError:
        pass


TOOL_KINDS = ("read", "edit", "run", "search", "skill")


def now_rows(st):
    """Per agent of the current stage (its experts, background agents, the main session): tool calls since its
    row started, its latest action and the last file it wrote, for the page's "now working" card (the page
    gets only the last 80 events)."""
    k = current_stage(st)
    s = stage_of(st, k)
    who = [(r["expert"], r["agent"], r["start"], r.get("end")) for r in (st.get("plan") or {}).get("rows", [])
           if r["stage"] == k and r.get("start") and r["agent"] != "main session"]
    who += [(b["agent"], b["agent"], b["start"], None) for b in st.get("bg") or []]
    who.append(("main session", "main session", s.get("run") or s.get("start") or "", None))
    out = {}
    for ex, ag, t0, t1 in who:
        alone = sum(1 for w in who if w[1] == ag) == 1
        mine = [e for e in st.get("events", []) if e["t"] >= t0 and (not t1 or e["t"] <= t1)
                and (e.get("actor") == ex or (alone and e.get("actor") == ag))]
        acts = [e for e in mine if e["kind"] not in ("gate", "ok", "changes", "plan", "risk")]
        wrote = [e for e in mine if e["kind"] == "edit" and e.get("file")]
        out[ex] = {"k": k, "n": sum(1 for e in mine if e["kind"] in TOOL_KINDS), "last": acts[-1]["text"] if acts else "",
                   "wrote": wrote[-1]["file"] if wrote else ""}
    return out


def save(st):
    st["updated"] = now()
    st["project"] = CFG.get("name") or ""
    st["teams"] = teams_table(mode_of(st))
    st["risk"] = timing.norm_risk(st.get("risk")) or timing.DEFAULT_RISK
    keys = {s["k"] for s in st["stages"]}
    st["budgets"] = {k: v for k, v in timing.budgets_for(st["risk"], mode_of(st), CFG).items() if k in keys}
    for r in (st.get("plan") or {}).get("rows", []):
        r["team"] = team_of(r.get("agent") or r.get("expert") or "")
    ags = {r["agent"] for r in (st.get("plan") or {}).get("rows", []) + (st.get("runs") or [])} |         {b["agent"] for b in st.get("bg") or []}
    st["calls"] = {a: n for a in sorted(ags) if a != "main session" for n in [call_budget(a, mode_of(st))] if n}
    st["now"] = now_rows(st)
    d = path(st["id"])
    os.makedirs(d, exist_ok=True)
    write(os.path.join(d, "status.json"), json.dumps(st, indent=1))
    js = "window.__LIVE__=" + json.dumps(dict(st, events=st["events"][-80:], codeOpen=code_writes_open(st))) + ";\n"
    write(os.path.join(d, "status.js"), js)
    if not st.get("demo"):  # a demo replay never takes over the page's default view
        write(path("live.js"), js)
    write(os.path.join(d, "status.md"), markdown(st))
    sync_page()


def href(tid, f):
    """Link from <work>/live.html to a file in the task folder or the repo."""
    if os.path.isfile(path(tid, f)):
        return tid + "/" + f.replace("\\", "/")
    return os.path.relpath(ROOT, WORK).replace("\\", "/") + "/" + f.replace("\\", "/")


def secret_path(r):
    """Files the page never shows: credentials and keys, and anything under .git."""
    r = r.replace("\\", "/")
    return bool(hidden(r) or ".git" in r.lower().split("/"))


def read_lines(tid, f):
    """Lines of a gate file: from the task folder, or a repo file that holds no secrets."""
    for p in (path(tid, f), os.path.join(ROOT, f)):
        a = os.path.abspath(p)
        r = project.rel(a, ROOT)
        if r and os.path.isfile(a) and not secret_path(r):
            with open(a, encoding="utf-8", errors="replace") as fh:
                return [line.rstrip("\r\n")[:1200] for line in fh.readlines()[:500]]
    return []


DECISION_FILE = re.compile(r"(?:^|/)(D[1-8])-", re.I)
BRIEF_DOCS = ("brief.md", "02-gaps.md")
# Who wrote a gate document, so the page can say which agent waits for the developer's approval.
AUTHORS = [(r"(^|/)(review-sf\.md|07-sf-review\.md|sf\.md|02-sf-fit\.md|05-sf-fields\.md)$", "sf-expert"),
           (r"(^|/)(review-ai\.md|ai\.md|05-ai\.md)$", "ai-engineer"),
           (r"(^|/)(review-n8n\.md|n8n\.md|05-n8n\.md)$", "n8n-expert"),
           (r"(^|/)(brief|spec|02-gaps|02-spec|02-nfr|01-prd-review)\.md$", "spec-analyst"),
           (r"(^|/)00-infra\.md$", "devops-engineer"),
           (r"(^|/)(design|05-architecture)\.md$|(^|/)05-openapi\.ya?ml$|(^|/)adr/", "solution-architect"),
           (r"(^|/)D2-|(^|/)05-data-model\.md$", "data-architect"),
           (r"(^|/)D4-|(^|/)05-security\.md$", "security-architect"),
           (r"(^|/)D[367]-", "solution-architect"), (r"(^|/)D8-", "release-manager"),
           (r"(^|/)D5-|(^|/)prototype\.html$", "main session (prototype)"),
           (r"(^|/)P-[^/]*$|(^|/)(ui|05-ui|03-journeys)\.md$", "ux-designer"),
           (r"(^|/)(product-review|03-product-review)\.md$", "product-critic"),
           (r"(^|/)(stories|04-stories)\.md$|(^|/)04-backlog\.csv$", "story-sizer"),
           (r"(^|/)(integrations|05-integrations)\.md$", "integration-engineer"),
           (r"(^|/)(ops|05-ops|09-deploy-plan)\.md$", "devops-engineer"),
           (r"(^|/)(perf|05-performance|07-performance)\.md$", "performance-engineer"),
           (r"(^|/)(review(-[\w-]+)?|07-code-review)\.md$", "code-reviewer"),
           (r"(^|/)(test|07-test-report)\.md$", "qa-engineer"),
           (r"(^|/)07-system-review\.md$", "verifier"),
           (r"(^|/)08-audit\.md$", "audit-expert"),
           (r"(^|/)(release|09-release)\.md$", "release-manager"),
           (r"(^|/)10-base-check\.md$", "base-builder"),
           (r"(^|/)(triage|00-intake|06-build-log)\.md$", "main session")]


def author_of(f, default):
    f = f.replace("\\", "/")
    for e in experts_list():  # a project expert's own notes: <x>-expert -> <x>.md, review-<x>.md
        short = re.escape(e.split("-")[0])
        if e not in DOMAIN_CORE and re.search(r"(^|/)(review-)?%s\.md$" % short, f, re.I):
            return e
    for pat, who in AUTHORS:
        if re.search(pat, f, re.I):
            return who
    return default


def handoff_problems(tid, files):
    """Run handoff_check.py on the documents of a spec or design gate: (problems, hints). A check that
    cannot run is a problem too, so a gate never opens unchecked by accident."""
    try:
        import handoff_check
        return handoff_check.check(path(tid), files)
    except Exception as e:
        return ["the hand-off check could not run (%s: %s)" % (type(e).__name__, str(e)[:200])], []


# ---- commands -------------------------------------------------------------------------------

def new_stage(mode, k, n, skipped):
    s = dict(k=k, name=n, state="skip" if skipped else "todo", actor=ACTOR[mode][k])
    if mode == "product":
        s["sid"] = STAGE_IDS[k]
        if k in GATE_IDS:
            s["gate"] = GATE_IDS[k]
    return s


def product_root(a, mode):
    if a.root:
        r = os.path.abspath(os.path.join(ROOT, os.path.expanduser(a.root)))
    elif mode == "product" and CFG.get("products_root"):
        r = os.path.abspath(os.path.join(ROOT, os.path.expanduser(CFG["products_root"]), a.id))
    else:
        return ""
    if os.path.dirname(r) == r or os.path.normcase(r) == os.path.normcase(os.path.expanduser("~")):
        sys.exit("init: --root %s is a drive or home folder; give the product's own folder" % r)
    return r.replace("\\", "/")


def default_plan(st):
    """Product mode: the factory's default team, one row per expert, for every stage the size runs."""
    experts = experts_list()
    skipped = {s["k"] for s in st["stages"] if s["state"] == "skip"}
    rows = []
    for stage, expert, why in PRODUCT_TEAM:
        agent = base_agent(expert)
        if stage in skipped or (agent in DOMAIN_CORE and agent not in experts):
            continue
        rows.append(dict(stage=stage, expert=expert, agent=agent, why=why, state="todo", team=team_of(agent)))
    return dict(kinds=[], rows=rows, at=now(), file="", default=True, confirmed=False, changes=[])


def fit_stages(st, rows):
    """The team decides the stages: nobody on one, nothing to run (except the mode's ALWAYS stages)."""
    always = ALWAYS[mode_of(st)]
    for s in st["stages"]:
        mine = [r for r in rows if r["stage"] == s["k"]]
        if not mine and s["state"] == "todo" and s["k"] not in always:
            s["state"] = "skip"
        elif mine and s["state"] == "skip":
            s["state"] = "todo"
        if mine and s["state"] == "todo":  # the main session runs a stage it is on the team for
            s["actor"] = "main session" if any(r["agent"] == "main session" for r in mine) else mine[0]["agent"]
        for r in rows:
            if r["stage"] == s["k"] and r["state"] == "todo" and s["state"] in ("done", "skip"):
                r["state"] = "done" if s["state"] == "done" else "skip"


def cmd_init(a):
    msgs = []
    exists = os.path.isfile(path(a.id, "status.json"))
    mode = mode_of(load(a.id)) if exists else (a.mode or CFG.get("default_mode") or "task").lower()
    mode = mode if mode in MODES else "task"
    root = product_root(a, mode) if (a.root or not exists) else None  # checked before anything is written

    def run():
        os.makedirs(path(a.id), exist_ok=True)
        fresh = not os.path.isfile(path(a.id, "status.json"))
        if fresh:
            size = a.size.upper()
            skip = set(SKIP[mode].get(size, set()))
            if mode == "product" and a.screen:
                skip.discard("prototype")
            st = dict(id=a.id, title=a.title or a.id, size=size, tool=a.tool, mode=mode, root=root or "",
                      started=now(), seq=0, events=[], counts={}, gate=None,
                      stages=[new_stage(mode, k, n, k in skip) for k, n in MODES[mode]])
            if getattr(a, "demo", False) and is_demo(a.id):
                st["demo"] = True
            if mode == "product":
                st["gates"] = {g: dict(state="open") for g in GATE_NAMES}
                st["plan"] = default_plan(st)
                fit_stages(st, st["plan"]["rows"])
        else:
            st = load(a.id)
            if a.title:
                st["title"] = a.title
            st["tool"] = a.tool
            if a.root:
                st["root"] = root
            if a.mode and a.mode.lower() != mode_of(st):
                msgs.append("note: %s stays in %s mode (the mode is fixed at the first init)" % (a.id, mode_of(st)))
        what = "Product" if mode_of(st) == "product" else "Task"
        add(st, current_stage(st), "note", what + (" started: " if fresh else " resumed: ") + st["title"], "main session")
        if fresh and st.get("plan"):
            add(st, current_stage(st), "plan", "Team planned: %d experts over %d stages (the factory's default team)"
                % (len(st["plan"]["rows"]), len({r["stage"] for r in st["plan"]["rows"]})), "main session")
        msgs.append("Mode: %s%s" % (mode_of(st), ", product root: " + st["root"] if st.get("root") else ""))
        save(st)
    with_lock(run)
    for m in msgs:
        print(m)
    print("Live status: " + page_url(a.id) + "  (Claude: the live-status preview; Cursor/CLI: " + SCRIPT + " open " + a.id + ")")


def page_url(tid=None):
    return "http://localhost:%d/live.html%s" % (PORT, "?task=" + tid if tid else "")


def serving():
    import socket
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", PORT)) == 0


def cmd_open(a):
    """Start `serve` on 127.0.0.1:<live_port> (the same server as Claude's `live-status` preview) unless
    something already serves it, then open the task's page in the default browser."""
    import subprocess
    os.makedirs(WORK, exist_ok=True)
    sync_page()
    if not serving():
        flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        subprocess.Popen([sys.executable, os.path.abspath(__file__), "serve", "--port", str(PORT)],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=flags, start_new_session=os.name != "nt", cwd=ROOT)
        for _ in range(20):
            if serving():
                break
            time.sleep(0.1)
    url = page_url(a.id)
    import webbrowser  # only for `open`: the hook runs on every tool call
    webbrowser.open(url)
    print("Live status: " + url + "  (in Cursor you can also open it with Simple Browser: Show)")


MAX_VIEW = 1024 * 1024
# On some Windows machines a loopback response over 64 KB stalls about half the time, so the server gzips
# text and the page reads a file in pieces of this size.
CHUNK = 48 * 1024


def file_roots():
    """Folders the page may open files from: the repo and every task's product root (never a drive root or a
    folder that holds the repo)."""
    roots = [ROOT]
    for t in tasks():
        try:
            r = load(t).get("root")
        except Exception:
            r = None
        if not r or not os.path.isdir(r):
            continue
        a = os.path.abspath(r)
        if os.path.dirname(a) == a or os.path.normcase(ROOT).startswith(os.path.normcase(a.rstrip("\\/")) + os.sep):
            continue
        roots.append(a)
    return roots


def repo_file(p, roots=None):
    """A file the page may open: (absolute path, page path), or None outside the roots, for a secret or a folder.
    The page path is repo-relative for a repo file and absolute (forward slashes) for a product-root file."""
    if not p:
        return None
    real_root = os.path.realpath(ROOT)
    for base in (roots if roots is not None else file_roots()):
        try:
            b = os.path.realpath(base)
            a = os.path.realpath(os.path.join(b, p))
            if os.path.normcase(os.path.commonpath([a, b])) != os.path.normcase(b) or not os.path.isfile(a):
                continue
        except (ValueError, OSError):
            continue
        r = os.path.relpath(a, b).replace("\\", "/")
        if secret_path(r):
            return None
        return a, (r if os.path.normcase(b) == os.path.normcase(real_root) else a.replace("\\", "/"))
    return None


def cmd_serve(a):
    """The live page server: <work> as static files, plus GET /_file?p=<path>&o=<offset>, a piece of a repo or
    product-root file read-only (never one outside them or a secret), so the page can open the files the agents
    changed."""
    import gzip
    import http.server
    import urllib.parse
    os.makedirs(WORK, exist_ok=True)
    sync_page()

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kw):
            super().__init__(*args, directory=WORK, **kw)

        def log_message(self, *args):
            pass

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Live", "1")
            super().end_headers()

        def send_body(self, body, ctype, headers=()):
            headers = list(headers)
            if len(body) > 1024 and "gzip" in (self.headers.get("Accept-Encoding") or ""):
                body = gzip.compress(body, 6)
                headers.append(("Content-Encoding", "gzip"))
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            for k, v in headers + [("Content-Length", len(body))]:
                self.send_header(k, str(v))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if (self.headers.get("Host") or "").rsplit(":", 1)[0] not in ("localhost", "127.0.0.1"):
                return self.send_error(403)  # only this machine's names (no DNS rebinding)
            u = urllib.parse.urlsplit(self.path)
            if u.path == "/_file":
                return self.repo_piece(urllib.parse.parse_qs(u.query))
            f = self.translate_path(u.path)
            if os.path.isfile(f) and f.lower().endswith((".html", ".js", ".json", ".md", ".css", ".txt")):
                with open(f, "rb") as h:
                    return self.send_body(h.read(), self.guess_type(f))
            return super().do_GET()

        def repo_piece(self, q):
            hit = repo_file(q.get("p", [""])[0])
            o = q.get("o", ["0"])[0]
            if not hit or not o.isdigit():
                return self.send_error(404, "Not a file the page may show")
            o = int(o)
            with open(hit[0], "rb") as f:
                full = os.fstat(f.fileno()).st_size
                size = min(full, MAX_VIEW)
                if o == 0 and b"\0" in f.read(8192):
                    return self.send_error(415, "Binary file")
                f.seek(o)
                body = f.read(max(0, min(CHUNK, size - o)))
            self.send_body(body, "text/plain; charset=utf-8", [("X-Size", size)] + ([("X-Truncated", 1)] if full > size else []))

    class Server(http.server.ThreadingHTTPServer):
        allow_reuse_address = os.name != "nt"  # on Windows reuse lets two servers share the port

    # the Claude preview passes its port in PORT when the configured one is taken
    with Server(("127.0.0.1", a.port or int(os.environ.get("PORT") or PORT)), Handler) as s:
        s.serve_forever()


# ---- team ("Who will work on this"): one row per expert, each with its own status -------------

STAGE_ALIASES = {"task": {"wrapup": "wrap"},
                 "product": {"productreview": "product", "prd": "intake", "spec": "requirements",
                             "s0": "intake", "s1": "base", "s2": "requirements", "s3": "product", "sp": "prototype",
                             "s4": "stories", "s5": "design", "s6": "build", "s7": "review", "s8": "audit",
                             "s9": "release"}}


def stage_key(name, mode="task"):
    raw = str(name).strip().lower()
    m = re.match(r"^(s\d|sp)\b", raw)
    if m and mode == "product":
        return STAGE_ALIASES["product"][m.group(1)]
    n = re.sub(r"[^a-z]", "", raw)
    n = STAGE_ALIASES.get(mode, {}).get(n, n)
    return n if n in dict(MODES.get(mode, TASK_STAGES)) else None


def base_agent(expert):
    """The agent of an expert label: "code-reviewer (rules)" -> code-reviewer, "data-architect when D2" -> data-architect."""
    e = expert.split("(")[0].strip()
    if e.lower().startswith("main session"):
        return "main session"
    return canon((re.match(r"[A-Za-z][\w:-]*", e) or [e])[0])


def parse_team(text, mode="task"):
    """(kinds, rows) from a spec: the "Kind of work:" line and the "## Who will work on this" table.
    A cell naming several experts ("a, b" or "a + b") becomes one row per expert."""
    m = re.search(r"(?im)^[*_ ]*kind of work[*_ ]*:\s*(.+)$", text)
    kinds = [k.strip(" *_.").lower() for k in re.split(r",|/|\band\b", m.group(1))] if m else []
    rows, inside = [], False
    for line in text.replace("\r\n", "\n").split("\n"):
        if re.match(r"^#{1,6}\s", line):
            inside = bool(re.match(r"^#{2,6}\s+who will work on this", line, re.I))
            continue
        if not inside or not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        k = stage_key(cells[0], mode) if len(cells) > 1 else None
        if not k:
            continue
        prev = ""
        for who in re.split(r"\s*(?:,|;|\s\+\s)\s*(?![^()]*\))", cells[1].replace("`", "").replace("*", "").strip()):
            if who.startswith("(") and prev:  # "code-reviewer (rules), (bugs)": the bare focus keeps the agent
                who = prev + " " + who
            if who:
                prev = base_agent(who)
                rows.append(dict(stage=k, expert=who, agent=prev, why=cells[2] if len(cells) > 2 else "",
                                 state="todo", team=team_of(prev)))
    return [k for k in kinds if k], rows


def team_rows(st, stage, agent=None, states=None):
    return [r for r in (st.get("plan") or {}).get("rows", []) if r["stage"] == stage
            and (agent is None or r["agent"].lower() == agent.lower()) and (states is None or r["state"] in states)]


def mark_expert(st, stage, agent, state, hint="", out=""):
    """Moves one expert row of the stage: start = first planned one (the one whose "(focus)" is in the hint
    when several), done = first working one (else first planned)."""
    if state == "live":
        cands = team_rows(st, stage, agent, ("todo",))
    else:
        cands = team_rows(st, stage, agent, ("live",)) or team_rows(st, stage, agent, ("todo",))
    m = re.search(r"\bfocus\s*[:=]\s*([a-z]+)|\bpass:\s*([a-z]+)", hint.lower())
    focus = (m.group(1) or m.group(2)) if m else ""
    pick = next((r for r in cands if focus and "(" in r["expert"]
                 and focus in re.findall(r"[a-z]+", r["expert"].split("(", 1)[1].lower())), None) \
        or next((r for r in cands if not focus or "(" not in r["expert"]), None)
    if not pick:
        return None
    pick["state"] = state
    if state == "live":
        pick["start"] = now()
    else:
        pick["end"] = now()
        if out:
            pick["out"] = out[:200]
    return pick


def close_rows(st, stage):
    """A stage is finished: experts still working are done, planned ones that never ran are skipped."""
    for r in team_rows(st, stage, None, ("live", "todo")):
        ran = r["state"] == "live" or r["agent"] == "main session"
        r["state"], r["end"] = ("done" if ran else "skip"), now()
    finish_runs(st, stage)


STAGE_WORD = re.compile(r"^\W*(spec|design|build|review|test|verify|release)\b", re.I)


def agent_stage(st, name, cur, job=""):
    """The stage an agent works in: the current one when the team plans it there, else its first open row."""
    rows = (st.get("plan") or {}).get("rows", [])
    if not rows:
        if mode_of(st) == "product":
            owns = [k for k, e, _ in PRODUCT_TEAM if base_agent(e).lower() == name.lower()]
            if cur in owns:
                return cur
            return next((s["k"] for s in st["stages"] if s["k"] in owns and s["state"] not in ("done", "skip")), None)
        # a domain expert works in the stage its job names ("Build card 2: ..."), else its own, else the one that runs
        k = (STAGE_WORD.match(job or "") or [None, ""])[1].lower()
        if (name in DOMAIN_CORE or name in experts_list()) and \
                any(s["k"] == k and s["state"] not in ("done", "skip") for s in st["stages"]):
            return k
        if name in AGENT_STAGE:
            return AGENT_STAGE[name]
        if name not in experts_list():
            return None
        return cur if cur != "spec" and stage_of(st, cur)["state"] in ("live", "fail") else "design"
    if team_rows(st, cur, name, ("todo", "live")):
        return cur
    # not on the team (or all its rows finished): log it in the current stage, never reopen a finished one
    return next((r["stage"] for r in rows if r["agent"].lower() == name.lower() and r["state"] in ("todo", "live")), None)


def cmd_plan(a):
    st0 = load(a.id)
    mode = mode_of(st0)
    names = [a.file] if a.file else list(PLAN_FILES[mode])
    f = next((n for n in names if os.path.isfile(path(a.id, n))), None)
    if not f:
        sys.exit("plan: %s not found in %s/%s" % (" or ".join(names), work_rel(), a.id))
    with open(path(a.id, f), encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    kinds, rows = parse_team(text, mode)
    risk, why = timing.parse_risk(text)
    rfile = f
    for n in PLAN_FILES[mode]:  # the triage may be the other plan file than the one that holds the team
        if risk or n == f or not os.path.isfile(path(a.id, n)):
            continue
        with open(path(a.id, n), encoding="utf-8", errors="replace") as fh:
            risk, why = timing.parse_risk(fh.read())
        rfile = n
    if not rows:
        print("plan: %s has no \"## Who will work on this\" table (| Stage | Expert | Why |, one row per expert)" % f)
        sys.exit(2)

    def run():
        st = load(a.id)
        old = st.get("plan") or {}
        if old.get("confirmed") and not a.why:
            return "plan: the team was confirmed at the %s gate; pass --why \"<reason>\" to change it" % \
                NAMES[CONFIRM[mode]].lower()
        if risk and st.get("riskSet") != "command":  # a `risk` command is not undone by an older triage line
            set_risk(st, risk, why, "plan", rfile)
        prev = {(r["stage"], r["expert"].lower()): r for r in old.get("rows", [])}
        for r in rows:
            o = prev.get((r["stage"], r["expert"].lower()))
            if o:
                r.update({k: o[k] for k in ("state", "start", "end", "out", "added") if k in o})
        keys = {(r["stage"], r["expert"].lower()) for r in rows}
        added = [r for r in rows if (r["stage"], r["expert"].lower()) not in prev]
        removed = [o for k, o in prev.items() if k not in keys]
        plan = dict(kinds=kinds, rows=rows, at=now(), file=f, confirmed=bool(old.get("confirmed")),
                    changes=list(old.get("changes") or []))
        if old.get("confirmed"):
            plan["confirmedAt"] = old.get("confirmedAt")
            for r in added:
                r["added"] = True
        if old.get("confirmed") and (added or removed or a.why):
            plan["changes"].append(dict(at=now(), why=a.why, added=[NAMES[r["stage"]] + ": " + r["expert"] for r in added],
                                        removed=[NAMES[r["stage"]] + ": " + r["expert"] for r in removed]))
        st["plan"] = plan
        fit_stages(st, rows)
        text = ""
        if len(plan["changes"]) > len(old.get("changes") or []):
            last = plan["changes"][-1]
            moved = ["+ " + x for x in last["added"]] + ["- " + x for x in last["removed"]]
            text = "Team changed" + (": " + a.why if a.why else "") + (" (" + "; ".join(moved) + ")" if moved else "")
        elif not old or added or removed:
            text = ("Team updated: " if old else "Team planned: ") + "%d experts over %d stages" % (
                len(rows), len({r["stage"] for r in rows})) + (" (" + ", ".join(kinds) + ")" if kinds else "")
        if text:
            add(st, current_stage(st), "plan", text, "main session")
        save(st)
    err = with_lock(run)
    if err:
        print(err)
        sys.exit(2)


def set_risk(st, risk, why, src, label=""):
    """Sets the task's risk and its evidence; logs an event when the level changes. src: plan (read from a file)
    or command (`risk`, which a later plan does not override)."""
    old = timing.norm_risk(st.get("risk"))
    st["risk"], st["riskSet"] = risk, src
    st["riskWhy"] = [str(w)[:160] for w in (why if isinstance(why, list) else [why]) if str(w).strip()][:8]
    if src == "command":
        add(st, current_stage(st), "note", ("Risk changed from %s to %s" % (old, risk) if old and old != risk
                                            else "Risk confirmed: " + risk) + ": " + "; ".join(st["riskWhy"]), "main session")
    elif old != risk:
        add(st, current_stage(st), "note", "Risk %s (from %s)%s" % (risk, label, ": " + "; ".join(st["riskWhy"]) if st["riskWhy"] else ""),
            "main session")


def cmd_risk(a):
    def run():
        st = load(a.id)
        set_risk(st, a.level, a.why, "command")
        save(st)
    with_lock(run)
    print("%s: risk %s, budgets %s" % (a.id, a.level, ", ".join("%s %d" % kv for kv in load(a.id)["budgets"].items()) or "none"))


def close_wait(st, stage):
    """A gate closes (approved, or changes asked): the time it waited for the developer is kept on the stage as
    wait_s, apart from its working time (timing.py, the page)."""
    g = st.get("gate") or {}
    if g.get("stage") == stage:
        s = stage_of(st, stage)
        s["wait_s"] = round(s.get("wait_s", 0) + timing.gap_s(g.get("at"), now()))


def reopen(s):
    """A finished or failed stage runs again: the idle gap since it stopped is not working time (idle_s)."""
    if s.get("end") and s.get("state") in ("done", "fail"):
        s["idle_s"] = round(s.get("idle_s", 0) + timing.gap_s(s["end"], now()))


def cmd_expert(a):
    def run():
        st = load(a.id)
        err = need_stage(st, a.stage, "expert")
        if err:
            return err
        rows = team_rows(st, a.stage)
        agent = canon(a.expert)
        r = next((x for x in rows if x["expert"].lower() == a.expert.lower()), None) \
            or next((x for x in rows if x["agent"].lower() == agent.lower() and x["state"] != "done"), None)
        if not r:
            return "expert: %s is not on the team for %s (%s)" % (a.expert, sname(st, a.stage),
                                                                  ", ".join(x["expert"] for x in rows) or "no rows")
        r["state"] = {"start": "live", "done": "done", "skip": "skip"}[a.action]
        r["start" if a.action == "start" else "end"] = now()
        if a.out:
            r["out"] = a.out[:200]
        if a.action != "start":
            finish_runs(st, a.stage, r["expert"])
        add(st, a.stage, "agent", r["expert"] + {"start": " started", "done": " finished", "skip": " not needed"}[a.action]
            + (": " + a.out if a.out else ""), r["agent"])
        save(st)
    err = with_lock(run)
    if err:
        print(err)
        sys.exit(2)


def cmd_stage(a):
    def run():
        st = load(a.id)
        err = need_stage(st, a.stage, "stage")
        if err:
            return err
        s = stage_of(st, a.stage)
        name = sname(st, a.stage)
        actor = canon(a.actor) if a.actor else ""
        if a.action == "start":
            reopen(s)
            s["state"], s["run"] = "live", now()
            s.setdefault("start", s["run"])
            s["actor"] = actor or s.get("actor") or ACTOR[mode_of(st)][a.stage]
            mine = team_rows(st, a.stage)
            if mine and all(r["state"] in ("done", "skip") for r in mine):  # a new round of this stage
                for r in mine:
                    r["state"] = "todo"
                    for k in ("start", "end", "out"):
                        r.pop(k, None)
            if (actor or "main session") == "main session":  # agents move their own rows (hook)
                mark_expert(st, a.stage, "main session", "live")
            if mode_of(st) == "product" and a.stage == "base":
                st.pop("code_writes", None)  # the base is built now: code writes follow the stage again
            add(st, a.stage, "start", name + " started", s["actor"])
        elif a.action == "done":
            s["state"], s["end"] = "done", now()
            s.setdefault("start", s["end"])
            if a.out:
                s["out"] = a.out
            close_rows(st, a.stage)
            add(st, a.stage, "done", name + " done" + (": " + a.out if a.out else ""), actor or s.get("actor"))
        else:
            s["state"], s["end"] = "fail", now()
            if a.out:
                s["out"] = a.out
            add(st, a.stage, "fail", a.out or name + " found problems", actor or s.get("actor"))
        save(st)
    err = with_lock(run)
    if err:
        print(err)
        sys.exit(2)


def cmd_code(a):
    shown = []

    def run():
        st = load(a.id)
        if mode_of(st) != "product":
            return "code: %s is a task; code writes there are guarded by the decision cards, not by this switch" % a.id
        st["code_writes"] = a.state
        add(st, current_stage(st), "note", "Code writes " + ("opened" if a.state == "open" else "closed") + " by hand"
            + (" for " + st["root"] if st.get("root") else ""), "main session")
        save(st)
        shown.append(st)
    err = with_lock(run)
    if err:
        print(err)
        sys.exit(2)
    print("code writes: %s%s" % ("open" if code_writes_open(shown[0]) else "closed",
                                 " (" + shown[0]["root"] + ")" if shown[0].get("root") else ""))


def cmd_gate(a):
    files = [f for f in (a.file or []) if f]
    st0 = load(a.id)
    err = need_stage(st0, a.stage, "gate")
    if err:
        sys.exit(err)
    mode = mode_of(st0)
    if a.stage in CHECKED[mode] and files and not a.skip_check:
        # an expert's own document (perf.md, ui.md, sf.md, ai.md, or 05-*) is checked even when it is not shown here
        extra = [x for x in EXPERT_DOCS[mode] if os.path.isfile(path(a.id, x)) and not any(same_file(f, x) for f in files)]
        problems, hints = handoff_problems(a.id, files + extra)
        brief = BRIEF[mode]
        if a.stage in BRIEF_AT[mode] and os.path.isfile(path(a.id, brief)) and not any(same_file(f, brief) for f in files):
            problems.append("%s is what the developer confirms at the %s gate: add --file %s" % (brief, sname(st0, a.stage).lower(), brief))
        if problems:
            print("Gate NOT opened: the hand-off check found problems. Fix them and gate again "
                  "(or, only for a real reason, pass --skip-check \"<reason>\"; the page shows it):")
            for p in problems:
                print("- " + p)
            sys.exit(2)
        for h in hints:
            print("hint: " + h)

    def run():
        st = load(a.id)
        s = stage_of(st, a.stage)
        s["state"] = "wait"
        s.setdefault("start", now())
        g = dict(stage=a.stage, question=a.question, at=now(), key=str(st.get("seq", 0) + 1), files=[])
        gid = GATE_IDS.get(a.stage) if mode == "product" else None
        if gid:
            g["gid"] = gid
            st.setdefault("gates", {})[gid] = dict(state="waiting", at=now())
        actor = s.get("actor") or ACTOR[mode][a.stage]
        for f in files:
            m = DECISION_FILE.search(f.replace("\\", "/"))
            d = (a.decision if a.decision and len(files) == 1 else
                 m.group(1) if m else "D1" if os.path.basename(f) in BRIEF_DOCS else "").upper()
            e = dict(file=f, href=href(a.id, f), lines=read_lines(a.id, f),
                     by=canon(a.by) if a.by and len(files) == 1 else author_of(f, actor))
            if d:
                e.update(decision=d, title=DECISIONS.get(d, d))
                st.setdefault("decisions", {})[d] = dict(state="open", title=DECISIONS.get(d, d), file=f, at=now())
            g["files"].append(e)
        g["by"] = (canon(a.by) if a.by else "") or ", ".join(dict.fromkeys(e["by"] for e in g["files"])) or "main session"
        if len(g["files"]) == 1:  # one document: the original gate shape (file, href, lines, decision)
            g.update({k: v for k, v in g.pop("files")[0].items() if k != "by"})
        elif files:
            g["file"] = files[0]
        if a.decision and not g.get("decision") and not any(e.get("decision") for e in g.get("files") or []):
            d = a.decision.upper()
            g.update(decision=d, title=DECISIONS.get(d, d))
            st.setdefault("decisions", {})[d] = dict(state="open", title=DECISIONS.get(d, d), file="", at=now())
        if a.open:
            g.update(open=a.open, openHref=href(a.id, a.open))
        st["gate"] = g
        shown.append(g)
        cards = [e["decision"] + " " + e["title"] for e in g.get("files") or [] if e.get("decision")]
        if g.get("decision"):
            cards.append(g["decision"] + " " + g["title"])
        if a.skip_check:
            add(st, a.stage, "flag", "Gate opened without the hand-off check: " + a.skip_check, "main session")
        add(st, a.stage, "gate", (gid + ": " if gid else "") + (", ".join(cards) + ": " if cards else "") + a.question, "you")
        save(st)
    shown = []
    with_lock(run)
    if shown:
        print("Gate open. Put this text in your reply, in full, then wait for the developer:\n")
        print(chat_text(a.id, shown[0]))


# Decision gates (sdlc skill): a card per decision a change triggers; the guard checks D2, D4 and D6.
DECISIONS = {"D1": "Scope", "D2": "Data model", "D3": "API and contracts", "D4": "Access and privacy",
             "D5": "UI", "D6": "Dependencies and config", "D7": "Other owners", "D8": "Go-live"}


def same_file(x, y):
    return (x or "").replace("\\", "/").strip("./").lower() == (y or "").replace("\\", "/").strip("./").lower()


def approve_decision(st, tid, d, note):
    rec = st.setdefault("decisions", {}).setdefault(d, dict(title=DECISIONS.get(d, d), file=""))
    rec.update(state="approved", at=now())
    line = "- %s %s: approved %s%s%s" % (d, rec["title"], now()[:16].replace("T", " "),
                                         " (" + rec["file"] + ")" if rec.get("file") else "", ": " + note if note else "")
    with open(path(tid, "decisions.md"), "a", encoding="utf-8") as f:
        f.write(line + "\n")
    if rec.get("file") and os.path.isfile(path(tid, rec["file"])):
        with open(path(tid, rec["file"]), "a", encoding="utf-8") as f:
            f.write("\nApproved by the developer, %s.\n" % now()[:16].replace("T", " "))


def gate_docs(g):
    """The documents of a gate as entries: `files`, or the single-document gate itself as one entry."""
    if g.get("files"):
        return g["files"]
    return [g] if g.get("file") or g.get("decision") else []


def doc_names(docs):
    return ", ".join(e.get("file") or e.get("decision") for e in docs) or "no gate is open"


def chat_text(tid, g):
    """The open gate as chat text: every document in full, then the question, so the developer can read and
    approve in the chat (the live page shows the same documents with line comments)."""
    head = (g["gid"] + " " if g.get("gid") else "") + NAMES.get(g.get("stage"), g.get("stage", ""))
    out = ["## %s gate: %s" % (head, g.get("question", "")), ""]
    for e in gate_docs(g):
        name = e.get("file") or ""
        title = (e["decision"] + " " + e.get("title", "") + " - ") if e.get("decision") else ""
        out += ["---", "### " + title + (name or "card") + (" (by %s)" % e["by"] if e.get("by") else ""), ""]
        lines = read_lines(tid, name) if name else []
        out += lines if lines else ["(no text to show)"]
        if len(lines) >= 500:
            out.append("... (first 500 lines; the rest is on the live page)")
        out.append("")
    if g.get("open"):
        out += ["Open for review: " + g["open"], ""]
    out += ["---", "**%s**" % g.get("question", "Approve?"),
            "Reply \"approve\", or say what to change (line numbers and comments: the live page)."]
    return "\n".join(out)


def cmd_chat(a):
    g = load(a.id).get("gate")
    if not g:
        sys.exit("chat: no gate is open for " + a.id)
    print(chat_text(a.id, g))


def cmd_quick(a):
    """A quick fix done without a task (sdlc triage): one line in <work>/quick-fixes.md. The hook marks the
    session, so the stop check accepts the turn's edits while they stay within quick-fix limits."""
    os.makedirs(WORK, exist_ok=True)
    with open(path("quick-fixes.md"), "a", encoding="utf-8") as f:
        f.write("- %s %s\n" % (now()[:16].replace("T", " "), " ".join(a.text.split())))
    print("Quick fix recorded.")


def cmd_ok(a):
    """No --decision/--file: the whole gate is approved. With one: only that card or document; the gate
    stays open while other documents in it wait. A --decision outside the open gate (or with none open)
    is recorded all the same; a --file that names no gate document approves nothing and exits 2.
    Product mode: approving the whole gate of a gated stage records G0..G4 as approved (the note: the words)."""
    d = (a.decision or "").upper()
    if d and d not in DECISIONS:
        sys.exit("ok: unknown decision %s (use D1-D8)" % a.decision)

    def run():
        st = load(a.id)
        err = need_stage(st, a.stage, "ok")
        if err:
            return err
        mode = mode_of(st)
        s = stage_of(st, a.stage)
        g = st.get("gate") or {}
        docs = gate_docs(g)
        if a.file:
            hit = [e for e in docs if same_file(e.get("file"), a.file)]
            if not hit:
                return "ok: %s is not a document of the open gate (%s); nothing was approved" % (a.file, doc_names(docs))
        elif d:
            hit = [e for e in docs if (e.get("decision") or "").upper() == d]
        else:
            hit = docs
        new = [e for e in hit if not e.get("ok")]
        for e in new:
            e["ok"] = True
        approved = sorted({e["decision"].upper() for e in new if e.get("decision")})
        if d and not hit and (st.get("decisions") or {}).get(d, {}).get("state") != "approved":
            approved = [d]
        for dd in approved:
            approve_decision(st, a.id, dd, a.note)
        # with no gate open, `ok STAGE --decision/--file` records the card only; a plain `ok STAGE` approves the stage
        whole_gate = all(e.get("ok") for e in docs) and (bool(docs) or not (d or a.file))
        if whole_gate:
            close_wait(st, a.stage)
            st["gate"] = None
            if a.stage == CONFIRM[mode] and st.get("plan"):
                st["plan"].update(confirmed=True, confirmedAt=now())
            if a.stage in CLOSING[mode]:
                s["state"], s["end"] = "done", now()
                close_rows(st, a.stage)
            else:
                s["state"], s["run"] = "live", now()
        gid = GATE_IDS.get(a.stage) if mode == "product" else None
        if gid and whole_gate and ((g and g.get("stage") == a.stage) or (not g and not d and not a.file)):
            st.setdefault("gates", {})[gid] = dict(state="approved", at=now(), words=a.note or "")
            if gid == "G3":
                st.pop("code_writes", None)  # design approved: code writes are open from here on
        what = ", ".join(approved + [e["file"] for e in new if not e.get("decision") and e.get("file")])
        whole = not d and not a.file and len(docs) > 1
        add(st, a.stage, "ok", "You approved" + (" all" if whole else "") + (" " + what if what else "")
            + (" (" + gid + ")" if gid and (st.get("gates") or {}).get(gid, {}).get("state") == "approved" and whole_gate else "")
            + (": " + a.note if a.note else ""), "you")
        save(st)
    err = with_lock(run)
    if err:
        print(err)
        sys.exit(2)


def cmd_changes(a):
    """The developer asked for changes: the named cards (default: every card of the gate not yet approved)
    are marked "changes" and the gate closes; the agent changes them and gates again."""
    bad = [x for x in a.decision if x.upper() not in DECISIONS]
    if bad:
        sys.exit("changes: unknown decision %s (use D1-D8)" % ", ".join(bad))

    def run():
        st = load(a.id)
        err = need_stage(st, a.stage, "changes")
        if err:
            return err
        s = stage_of(st, a.stage)
        g = st.get("gate") or {}
        if a.decision:
            ds = [x.upper() for x in a.decision]
        else:
            ds = [e["decision"].upper() for e in gate_docs(g) if e.get("decision") and not e.get("ok")]
        for d in ds:
            st.setdefault("decisions", {}).setdefault(d, dict(title=DECISIONS.get(d, d), file=""))["state"] = "changes"
        gid = GATE_IDS.get(a.stage) if mode_of(st) == "product" else None
        if gid:
            st.setdefault("gates", {})[gid] = dict(state="changes", at=now(), words=a.summary)
        close_wait(st, a.stage)
        st["gate"] = None
        s["state"], s["run"] = "live", now()
        add(st, a.stage, "changes", "You asked for changes" + (" to " + ", ".join(ds) if ds else "") + ": " + a.summary, "you")
        save(st)
    err = with_lock(run)
    if err:
        print(err)
        sys.exit(2)


def gate_entry(g, file="", decision=""):
    """The gate document a question is about: by file or decision (None when neither matches), else the first."""
    docs = [e for e in gate_docs(g) if e.get("file")]
    if file or decision:
        for e in docs:
            if (file and same_file(e["file"], file)) or (decision and (e.get("decision") or "").upper() == decision.upper()):
                return e
        return None
    return docs[0] if docs else None


def cmd_ask(a):
    """A developer question at an open gate and its answer: logged, and added to the document's Q&A section."""
    def run():
        st = load(a.id)
        g = st.get("gate") or {}
        e = gate_entry(g, a.file, a.decision)
        if e is None and (a.file or a.decision):
            return "ask: %s is not a document of the open gate (%s); nothing was logged" % (a.file or a.decision, doc_names(gate_docs(g)))
        add(st, g.get("stage") or current_stage(st), "ask", "Q: " + a.question, "you", answer=a.answer[:600])
        if e and os.path.isfile(path(a.id, e["file"])):
            qa = "- Q: %s\n  A: %s\n" % (a.question.strip(), a.answer.strip().replace("\n", "\n  "))
            with open(path(a.id, e["file"]), encoding="utf-8") as f:
                text = f.read()
            m = re.search(r"^#+ .*questions and answers.*$", text, re.I | re.M)
            if m:
                nxt = re.search(r"^#+ ", text[m.end():], re.M)
                at = m.end() + nxt.start() if nxt else len(text)
                head = text[:at].rstrip("\n") + "\n"
                text = head + qa + ("\n" + text[at:] if nxt else "")
            else:
                text = text.rstrip("\n") + "\n\n## Questions and answers\n" + qa
            with open(path(a.id, e["file"]), "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            e["lines"] = read_lines(a.id, e["file"])
        save(st)
    err = with_lock(run)
    if err:
        print(err)
        sys.exit(2)


def cmd_log(a):
    def run():
        st = load(a.id)
        if a.stage:
            err = need_stage(st, a.stage, "log")
            if err:
                return err
        add(st, a.stage or current_stage(st), a.kind, a.text, canon(a.actor) if a.actor else "main session")
        save(st)
    err = with_lock(run)
    if err:
        print(err)
        sys.exit(2)


def record(kind, text, actor, data=None):
    """Best-effort entry from the guard hooks (blocked call, hard-rule flag) for the task of the
    session in `data` (the hook JSON). Never raises."""
    try:
        sid = session_of(data or {})
        tid = session_task(sid) if sid else None
        if not tid:
            return

        def run():
            st = load(tid)
            add(st, current_stage(st), kind, text, actor)
            save(st)
        with_lock(run)
    except Exception:
        pass


# ---- hook -----------------------------------------------------------------------------------

def rel(p, root=""):
    """A path as the feed shows it: repo-relative, else relative to the task's product root, else the file name."""
    try:
        a = os.path.abspath(os.path.join(ROOT, str(p)))
    except (TypeError, ValueError):
        return os.path.basename(str(p))
    for base in [ROOT] + ([root] if root else []):
        try:
            r = os.path.relpath(a, os.path.abspath(base))
        except ValueError:
            continue
        if not r.startswith(".."):
            return r.replace("\\", "/")
    return os.path.basename(a)


def tool_path(inp):
    return next((inp[k] for k in ("file_path", "path", "target_file", "filePath", "notebook_path")
                 if isinstance(inp.get(k), str) and inp.get(k)), "")


PROGS = ("python", "python3", "py", "node", "bash", "sh", "pwsh", "powershell", "npx", "uv", "uvx", "deno", "bun", "ruby")
TOOLS = ("git", "npm", "mvn", "mvnw", "gradle", "gradlew", "docker", "kubectl", "cf", "yarn", "pnpm", "dotnet", "cargo",
         "go", "make")


def short_cmd(cmd):
    """A command in a few plain words, for a step whose agent gave no description (Cursor sends none):
    "Run git status", "Run check_rules.py", "Read build.md", "Search for "token""."""
    for seg in re.split(r"\s*(?:&&|\|\||;|\|)\s*", cmd):
        toks = seg.split()
        while toks and (re.match(r"^[A-Za-z_]\w*=", toks[0]) or toks[0].lower() in ("sudo", "env", "time", "&", "call")):
            toks = toks[1:]
        if not toks or toks[0].lower() in ("cd", "set", "export", "pushd", "popd", "echo", "set-location", "printf"):
            continue
        prog = re.sub(r"\.(exe|cmd|bat)$", "", os.path.basename(toks[0].strip("\"'")).lower())
        rest = [t.strip("\"'") for t in toks[1:] if not t.startswith("-")]
        name = os.path.basename(rest[0].replace("\\", "/")) if rest else ""
        if prog in PROGS and name:
            return "Run " + name
        if prog in TOOLS and name:
            return "Run %s %s" % (prog, name)
        if prog in ("cat", "head", "tail", "less", "more", "type", "get-content", "sed", "awk") and rest:
            return "Read " + os.path.basename(rest[-1].replace("\\", "/"))[:60]
        if prog in ("grep", "rg", "findstr", "select-string") and rest:
            return 'Search for "%s"' % rest[0][:40]
        if prog in ("ls", "dir", "find", "tree", "get-childitem"):
            return "List files" + (" in " + name[:40] if name else "")
        if prog == "wc":
            return "Count lines"
        return "Run " + prog[:30]
    return "Run a command"


def describe(tool, inp, root=""):
    """(kind, step, extra) of one tool call: the step is an imperative in plain words ("Read context.md", the
    Bash call's own description); the page turns it into "Reading ..." and "Read ...". A command is kept in the
    event behind the step only when it passes secret_command."""
    p = tool_path(inp)
    name = os.path.basename(rel(p, root)) if p else ""
    if tool == "Read":
        return ("read", "Read " + name, {}) if p else None
    if tool in ("Edit", "Write", "MultiEdit", "StrReplace", "NotebookEdit"):
        x = {"file": name}
        hit = repo_file(p, [ROOT] + ([root] if root and os.path.isdir(root) else [])) if p else None
        if hit:
            x["path"] = hit[1]  # the page opens it with /_file
        return ("edit", ("Write " if tool == "Write" else "Edit ") + name, x) if p else None
    if tool == "Delete":
        return ("edit", "Delete " + name, {}) if p else None
    if tool in ("Bash", "PowerShell", "Shell"):
        cmd = " ".join(str(inp.get("command") or "").split())
        if not cmd or secret_command(cmd) or "live_status.py" in cmd:
            return None
        desc = " ".join(str(inp.get("description") or "").split())
        step = (desc[:1].upper() + desc[1:])[:140] if desc else short_cmd(cmd)
        return ("run", step, {"cmd": cmd[:300]})
    if tool in ("Grep", "Glob"):
        pat = str(inp.get("pattern") or inp.get("query") or "")[:50]
        if tool == "Glob":
            return ("search", "List files " + pat, {})
        return ("search", ("Search %s for" % name if name else "Search for") + ' "%s"' % pat, {})
    if tool == "Skill":
        return ("skill", "Use the " + str(inp.get("skill") or inp.get("name") or "") + " skill", {})
    if tool == "WebFetch":
        host = re.sub(r"^[a-z]+://", "", str(inp.get("url") or "")).split("/")[0]
        return ("search", "Look up " + host[:60], {})
    if tool == "WebSearch":
        return ("search", 'Look up "%s"' % str(inp.get("query") or "")[:60], {})
    return None


# ---- agent runs: one card per run on the page -----------------------------------------------------

KEEP_RUNS = 30
KEEP_STEPS = 60
BRIEF_STEP = re.compile(r"context|pack|triage|status|brief|task folder|decision|card|design file|spec\b|questions", re.I)
SUMMARY_HEAD = re.compile(r"(?im)(?:^[ \t]*#{1,6}[ \t]*|<!--[ \t]*)summary for people[ \t]*:?[ \t]*(?:-->)?[ \t]*$")
TURN_LIMIT = re.compile(r"max(?:imum)?[ _-]?turns|turn[ _-]?limit", re.I)
PLAN_HEAD = re.compile(r"(?im)^[ \t]*(?:#{1,6}[ \t]*)?plan[ \t]*:?[ \t]*$")
PLAN_ITEM = re.compile(r"^\s*[-*]\s*\[([ xX])\]\s+(\S.*?)\s*$")


def job_of(text):
    """The Agent call's description as one plain sentence; a trailing id in brackets ("(F-A8-008)") is dropped."""
    t = re.sub(r"\s*\([^()\s]*\d[^()\s]*\)\s*$", "", " ".join(str(text or "").split()))
    return (t[:1].upper() + t[1:])[:120]


def new_run(st, agent, expert, stage, job="", use="", aid=""):
    """One run of an agent: its job, the steps it takes, its calls against its Speed line, its job phase
    (0 read the brief, 1 look into it, 2 write its file, 3 check and finish) and, when it stops, its summary."""
    st["runN"] = st.get("runN", 0) + 1
    r = dict(id="r%d" % st["runN"], agent=agent, expert=expert, stage=stage, job=job, start=now(), state="live",
             n=0, ph=0, b=call_budget(agent, mode_of(st)) if agent != "main session" else 0, steps=[])
    if use:
        r["use"] = use
    if aid:
        r["aid"] = aid
    st["runs"] = (st.get("runs") or [])[-(KEEP_RUNS - 1):] + [r]
    return r


def find_run(st, aid="", use="", name="", oldest=False):
    """The live run of a hook call: by its run id, else by the Agent call that launched it, else the newest (or
    oldest) live run of that agent not yet bound to another run id."""
    runs = [r for r in st.get("runs") or [] if r["state"] == "live"]
    if not oldest:
        runs.reverse()
    for key, v in (("aid", aid), ("use", use)):
        hit = next((r for r in runs if v and r.get(key) == v), None)
        if hit:
            return hit
    low = name.lower()
    return next((r for r in runs if low and not (aid and r.get("aid")) and low in (r["agent"].lower(), r["expert"].lower())), None)


def plain(line):
    s = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s+", "", line.strip())
    s = re.sub(r"\*\*|__|`|<[^>]+>|\[([^\]]*)\]\([^)]*\)", lambda m: m.group(1) or "", s)
    return " ".join(s.split())[:200]


def summary_of(p, reply=""):
    """Up to 5 plain lines for people: the "## Summary for people" block of a run's output file (read once, when the
    run stops), else the file's first lines, else the first lines of the agent's reply."""
    text = ""
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            text = f.read(24000)
    except (OSError, TypeError):
        pass
    m = SUMMARY_HEAD.search(text)
    out = []
    if m:
        for ln in text[m.end():].splitlines():
            s = ln.strip()
            if PLAN_HEAD.match(s) or PLAN_ITEM.match(s):
                break
            if re.match(r"^(#|-->|<!--|---|\||```|</)", s):
                if out or not s.startswith("<!--"):
                    break
            if s and plain(s):
                out.append(plain(s))
            if len(out) == 5:
                break
        if out:
            return out
    if str(p).lower().endswith((".html", ".htm")):
        title = re.search(r"(?is)<title>(.*?)</title>", text)
        body = re.sub(r"(?is)<(script|style|head)\b.*?</\1>", " ", text)
        text = (title.group(1) + "\n" if title else "") + re.sub(r"<[^>]+>", "\n", body)
    for src in (text, reply):
        for ln in re.sub(r"(?s)^---\n.*?\n---\n", "", src or "").splitlines():
            s = ln.strip()
            if not s or re.match(r"^(#|\||```|---|<|>)", s) or PLAN_ITEM.match(s) or len(s.split()) < 3:
                continue
            out.append(plain(s))
            if len(out) == 3:
                return out
        if out:
            return out
    return out


def plan_of(p):
    """The "## Plan" checklist of a run's output file (an HTML file holds it in its top comment): its items in order,
    each with whether it is ticked; None when the file has none."""
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            text = f.read(40000)
    except (OSError, TypeError):
        return None
    for m in PLAN_HEAD.finditer(text):
        out = []
        for ln in text[m.end():].splitlines():
            hit = PLAN_ITEM.match(ln)
            if hit:
                out.append((plain(hit.group(2))[:120], hit.group(1) != " "))
                if len(out) == 12:
                    break
            elif ln.strip():
                break
        if out:
            return out
    return None


def tick_plan(r, items):
    """The run's live plan from its file: an item keeps the time it was first seen ticked; a step belongs to the
    first item not yet ticked when it ran."""
    old = {x["text"]: x.get("at") for x in r.get("plan") or [] if x.get("at")}
    r["plan"] = [dict(text=t, done=d, at=(old.get(t) or now()) if d else "") for t, d in items]


def stop_state(*objs):
    """done, stopped or failed, and why in plain words, from a stop hook's input or an Agent call's result."""
    for o in objs:
        if not isinstance(o, dict):
            continue
        s = str(o.get("status") or o.get("stop_reason") or o.get("subtype") or "").lower()
        why = " ".join(str(o.get(k) or "") for k in ("status", "stop_reason", "subtype", "reason", "error"))
        if TURN_LIMIT.search(why):
            return "stopped", "stopped at its turn limit"
        if s in ("aborted", "cancelled", "canceled", "interrupted", "killed", "stopped"):
            return "stopped", "stopped before it finished"
        if o.get("is_error") or o.get("error") or s in ("error", "failed", "failure"):
            msg = " ".join(str(o.get("error") or o.get("message") or "").split())[:100]
            return "failed", "failed" + (": " + msg if msg and msg not in ("True", "true") else "")
    return "done", ""


def reply_text(resp):
    """The text an agent handed back (an Agent call's result, or a stop hook's last message)."""
    if isinstance(resp, str):
        return resp
    if not isinstance(resp, dict):
        return ""
    c = resp.get("content") or resp.get("result") or resp.get("last_assistant_message") or ""
    if isinstance(c, list):
        c = "\n".join(str(x.get("text") or "") for x in c if isinstance(x, dict))
    return str(c)[:6000]


def finish_run(st, r, state="done", why="", reply="", again=False):
    """A run stops: its state, why when it did not finish, and its summary for people. A stop hook that comes
    after the run's row was marked done (again) only reads the summary once more."""
    if r["state"] != "live" and not again:
        return
    if r["state"] == "live":
        r["state"], r["end"] = state, now()
        if why:
            r["why"] = why
    out = os.path.join(WORK, r["out"]) if r.get("out") else ""
    lines = summary_of(out, reply)
    if lines:
        r["summary"] = lines
    items = plan_of(out)
    if items:
        tick_plan(r, items)
    for x in r.get("plan") or [] if r["state"] == "done" else []:  # a run that finished did its plan
        if not x["done"]:
            x["done"], x["at"] = True, r["end"]


def finish_runs(st, stage, expert=None):
    """The rows of a stage (or one expert's row) are marked done: their runs stop with them."""
    for r in st.get("runs") or []:
        if r["state"] == "live" and r["stage"] == stage and (expert is None or r["expert"].lower() == expert.lower()):
            finish_run(st, r)


def run_step(st, r, kind, text, extra, p):
    """One step of a run: counted against its Speed line, kept for the page's roll, and moving its job phase."""
    if kind in TOOL_KINDS:
        r["n"] += 1
    r["steps"] = (r["steps"] + [[now(), text] + ([extra["cmd"]] if extra.get("cmd") else [])])[-KEEP_STEPS:]
    own = False
    if kind == "edit" and p:
        a = os.path.abspath(p)
        if not r.get("out") and os.path.normcase(a).startswith(os.path.normcase(os.path.abspath(path(st["id"])) + os.sep)):
            r["out"], r["file"], r["fw"] = os.path.relpath(a, WORK).replace("\\", "/"), os.path.basename(a), 0
            if extra.get("path"):
                r["href"] = extra["path"]
        own = bool(r.get("out")) and os.path.normcase(a) == os.path.normcase(os.path.abspath(os.path.join(WORK, r["out"])))
    if r["ph"] == 0 and not BRIEF_STEP.search(text):
        r["ph"] = 1
    if own:
        r["fw"] = r.get("fw", 0) + 1
        if r["ph"] < 2 and (r["fw"] > 1 or (r["b"] and r["n"] >= 0.4 * r["b"])):  # the first write is its skeleton
            r["ph"] = 2
        items = plan_of(a)
        if items:
            tick_plan(r, items)
    elif r["ph"] == 2 and kind == "run":
        r["ph"] = 3
    pat = r.setdefault("pat", [])  # when each job phase ended: the page's plan when the file has none
    while len(pat) < r["ph"]:
        pat.append(now())


def bind(st, aid, name):
    """One run of an agent (Claude's agent_id, Cursor's subagent_id) -> its expert row: the first working row of
    that agent not taken by another run since the row started; off the team it is the agent itself."""
    aids = st.setdefault("aids", {})
    if aid in aids:
        return aids[aid]["expert"]
    taken = lambda r: any(v["expert"] == r["expert"] and v["t"] >= (r.get("start") or "") for v in aids.values())
    rows = [r for r in (st.get("plan") or {}).get("rows", []) if r["agent"].lower() == name.lower() and r["state"] == "live"]
    r = next((r for r in rows if r["stage"] == current_stage(st) and not taken(r)), None) or \
        next((r for r in rows if not taken(r)), None)
    aids[aid] = {"expert": r["expert"] if r else name, "t": now()}
    st["aids"] = dict(list(aids.items())[-30:])
    return aids[aid]["expert"]


def who(st, data, sid=""):
    """The agent behind a tool call. Claude sends agent_type (and agent_id) only from inside a subagent or a
    session started with --agent, so a call without them is the main session's. Cursor's tool hooks name no
    agent: a call from a subagent's own conversation is known from its subagentStart (bound by id)."""
    aid = str(data.get("agent_id") or "")
    if not aid and sid and sid in (st.get("aids") or {}):
        aid = sid
    if aid and aid in (st.get("aids") or {}):
        return st["aids"][aid]["expert"], aid
    if not data.get("agent_type"):
        return "main session", ""
    name = canon(data["agent_type"])
    return (bind(st, aid, name) if aid else name), aid


def on_tool(tid, data, sid=""):
    event = data.get("hook_event_name", "")
    tool = data.get("tool_name", "")
    inp = data.get("tool_input") or {}
    if isinstance(inp, str):
        try:
            inp = json.loads(inp)
        except ValueError:
            inp = {}
    pre = event in ("PreToolUse", "preToolUse")
    st = load(tid)
    cur = current_stage(st)
    if event in ("SubagentStart", "subagentStart"):
        # Cursor: a subagent starts in its own conversation; its tool calls are recorded under this task's run
        aid = re.sub(r"[^A-Za-z0-9._-]", "", str(data.get("subagent_id") or data.get("agent_id") or ""))[:80]
        name = canon(data.get("subagent_type") or data.get("agent_type") or "")
        if aid and name:
            ex = bind(st, aid, name)
            run = find_run(st, aid, "", name)
            if run:
                run["aid"] = aid
            else:
                job = job_of(data.get("description") or data.get("task") or "")
                new_run(st, name, ex, agent_stage(st, name, cur, job) or cur, job, aid=aid)
            os.makedirs(path(".sessions"), exist_ok=True)
            write(path(".sessions", aid), tid)
            save(st)
        return
    if event in ("SubagentStop", "subagentStop"):
        # a background agent finished: the row its run is bound to, else the first working row of that agent
        name = canon(data.get("agent_type") or data.get("subagent_type") or "")
        aid = str(data.get("agent_id") or data.get("subagent_id") or "")
        mine = ((st.get("aids") or {}).get(aid) or {}).get("expert")
        live = [x for x in (st.get("plan") or {}).get("rows", []) if x["state"] == "live"
                and (x["expert"] == mine if mine else name and x["agent"].lower() == name.lower())]
        r = live[0] if live else None
        bg = next((b for b in st.get("bg") or [] if aid and b.get("aid") == aid), None) or \
            next((b for b in st.get("bg") or [] if name and b["agent"].lower() == name.lower()), None)
        run = find_run(st, aid, "", name, oldest=not aid) or \
            next((x for x in reversed(st.get("runs") or []) if aid and x.get("aid") == aid), None)
        if run:
            finish_run(st, run, *stop_state(data), reply=reply_text(data), again=True)
        if r:
            r["state"], r["end"] = "done", now()
            add(st, r["stage"], "agent", r["expert"] + " finished", r["expert"])
        elif bg:
            st["bg"].remove(bg)
        if run or r or bg:
            save(st)
        return
    if tool in ("Agent", "Task"):
        name = canon(next((inp[k] for k in ("subagent_type", "subagent_name", "agent", "name", "type")
                           if isinstance(inp.get(k), str) and inp.get(k)), "agent"))
        stage = agent_stage(st, name, cur, str(inp.get("description") or ""))
        resp = data.get("tool_response")  # a background launch returns at once: {"isAsync": true, "status": "async_launched"}
        hint = " ".join(str(inp.get(k) or "") for k in ("description", "prompt"))[:4000]
        use = str(data.get("tool_use_id") or "")
        rid = isinstance(resp, dict) and str(resp.get("agentId") or resp.get("agent_id") or "")
        if pre and stage:
            s = stage_of(st, stage)
            r = mark_expert(st, stage, name, "live", hint)
            if r and use:  # the launch's result names the run (agentId): its tool calls then show on this row
                st["launch"] = dict(list((st.get("launch") or {}).items())[-9:] + [(use, r["expert"])])
            new_run(st, name, r["expert"] if r else name, stage, job_of(inp.get("description")) or (r or {}).get("why", ""), use)
            if s["state"] == "live":  # another expert of a stage that is already running
                add(st, stage, "agent", (r["expert"] if r else name) + " started", r["expert"] if r else name)
            else:
                reopen(s)
                s["state"], s["run"], s["actor"] = "live", now(), name
                s.setdefault("start", s["run"])
                add(st, stage, "start", s["name"] + " started", r["expert"] if r else name)
        elif pre:
            new_run(st, name, name, cur, job_of(inp.get("description")), use)
            add(st, cur, "agent", name + " agent started" + (": " + str(inp["description"])[:80] if inp.get("description") else ""), name)
        elif inp.get("run_in_background") or (isinstance(resp, dict) and (resp.get("isAsync") or resp.get("status") == "async_launched")) \
                or "async_launched" in str(resp)[:400]:
            # the call returns at launch: the agent keeps working until its result comes back
            ex = (st.get("launch") or {}).pop(use, None)
            run = find_run(st, "", use, "" if use else name)
            if rid:
                st.setdefault("aids", {})[rid] = {"expert": ex or name, "t": now()}
                if run:
                    run["aid"] = rid
            if not (stage and team_rows(st, stage, name, ("live",))):  # off the team: flow_check waits for it too
                st["bg"] = (st.get("bg") or [])[-9:] + [dict({"agent": name, "start": now()}, **({"aid": rid} if rid else {}))]
            add(st, stage or cur, "agent", (ex or name) + " is working in the background", name)
        else:
            run = find_run(st, "", use, name)  # a foreground agent is back: its run stops with its result
            if run:
                finish_run(st, run, *stop_state(resp), reply=reply_text(resp))
            if stage and team_rows(st, stage):
                # planned team: the stage ends with `stage done`, not when its first expert finishes
                r = mark_expert(st, stage, name, "done", hint)
                add(st, stage, "agent", (r["expert"] if r else name) + " finished", r["expert"] if r else name)
            elif stage and stage_of(st, stage)["state"] == "live":
                s = stage_of(st, stage)
                s["state"], s["end"] = "done", now()
                add(st, stage, "done", name + " finished", name)
            else:
                add(st, stage or cur, "agent", name + " finished", name)
        save(st)
        return
    if pre:
        return
    hit = describe(tool, inp, st.get("root") or "")
    if not hit:
        return
    kind, text, extra = hit
    actor, aid = who(st, data, sid)
    if aid:
        extra["aid"] = aid[-8:]  # two runs of one agent stay apart on the page
    if actor != "main session":
        run = find_run(st, aid, "", actor)
        if run is None and aid:  # launched before this hook saw it
            run = new_run(st, base_agent(actor), actor, cur, aid=aid)
        if run is not None:
            if aid:
                run["aid"] = aid
            tp = tool_path(inp)
            run_step(st, run, kind, text, extra, os.path.join(ROOT, tp) if tp else "")
            extra["run"] = run["id"]
    add(st, cur, kind, text, actor, **extra)
    save(st)


LIVE_ANY = re.compile(r"\b(?:init|stage|gate|ok|changes|ask|log|plan|risk|expert|code|chat)\s+[\"']?([A-Za-z0-9._-]+)")


def cmd_hook(a):
    """Each session records only into its own task, so parallel sessions never mix. A session is
    bound to a task when it runs a live_status.py command for that task (init, stage, gate, ...)."""
    data = {}
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace") or "{}")
        if not isinstance(data, dict):
            data = {}
        sid = session_of(data)
        if not sid:
            return
        inp = data.get("tool_input") or {}
        if isinstance(inp, str):
            inp = json.loads(inp)
        cmd = str(inp.get("command") or "")
        if "live_status" in cmd:
            # also `L="python .claude/core/scripts/live_status.py"; $L init <id>`: the last existing task named wins
            ids = [m.group(1) for m in LIVE_ANY.finditer(cmd)
                   if not is_demo(m.group(1)) and os.path.isfile(path(m.group(1), "status.json"))]
            if ids:
                os.makedirs(path(".sessions"), exist_ok=True)
                write(path(".sessions", sid), ids[-1])
            if re.search(r"live_status\.py[\"']?\s+quick\b", cmd) and data.get("hook_event_name") in ("PostToolUse", "postToolUse"):
                os.makedirs(path(".sessions"), exist_ok=True)
                write(path(".sessions", sid + ".quick"), "1")  # flow_check.py accepts this turn's quick fix
        tid = session_task(sid)
        if tid:
            with_lock(lambda: on_tool(tid, data, sid))
        if data.get("hook_event_name") in ("PostToolUse", "postToolUse"):
            note_edit(sid, data.get("tool_name", ""), inp)
    except Exception:
        pass
    finally:
        if a.cursor and data.get("hook_event_name") in ("preToolUse", "subagentStart", None):  # unreadable input: Cursor waits on a reply
            print(json.dumps({"permission": "allow"}))


EDIT_TOOLS = ("Edit", "Write", "MultiEdit", "StrReplace", "NotebookEdit", "Delete")


def note_edit(sid, tool, inp):
    """Remember the repo files this session changed since its last stop (flow_check.py reads and clears them)."""
    p = tool_path(inp)
    if tool not in EDIT_TOOLS or not p:
        return
    a = os.path.abspath(os.path.join(ROOT, p))
    if not os.path.normcase(a).startswith(os.path.normcase(ROOT) + os.sep) \
            or os.path.normcase(a).startswith(os.path.normcase(WORK) + os.sep):
        return
    seen = session_edits(sid)
    r = os.path.relpath(a, ROOT).replace("\\", "/")
    if r not in seen and len(seen) < 20:
        os.makedirs(path(".sessions"), exist_ok=True)
        with open(path(".sessions", sid + ".edits"), "a", encoding="utf-8") as fh:
            fh.write(r + "\n")


def session_edits(sid, clear=False):
    f = path(".sessions", sid + ".edits")
    try:
        with open(f, encoding="utf-8") as fh:
            out = [l.strip() for l in fh if l.strip()]
        if clear:
            os.remove(f)
        return out
    except OSError:
        return []


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    stage_names = list(NAMES)
    p = sub.add_parser("init")
    p.add_argument("id")
    p.add_argument("--title", default="")
    p.add_argument("--size", default="M", choices=["S", "M", "L", "s", "m", "l"])
    p.add_argument("--mode", default="", choices=["", "task", "product"], help="default: default_mode in project.json")
    p.add_argument("--root", default="", help="the product root (product mode default: products_root/ID)")
    p.add_argument("--screen", action="store_true", help="product mode, size S: the change has a screen (keeps the prototype)")
    p.add_argument("--tool", default="claude", choices=["claude", "cursor"])
    p.add_argument("--demo", action="store_true", help=argparse.SUPPRESS)  # simulate.py: a demo-<scenario> replay
    p.set_defaults(fn=cmd_init)
    p = sub.add_parser("stage")
    p.add_argument("id")
    p.add_argument("stage", choices=stage_names)
    p.add_argument("action", choices=["start", "done", "fail"])
    p.add_argument("--out", default="")
    p.add_argument("--actor", default="")
    p.set_defaults(fn=cmd_stage)
    p = sub.add_parser("gate")
    p.add_argument("id")
    p.add_argument("stage", choices=stage_names)
    p.add_argument("question")
    p.add_argument("--file", action="append", default=[], help="repeat to review several documents in one gate")
    p.add_argument("--open", default="")
    p.add_argument("--decision", default="", help="D1-D8 for a single card whose name does not start with Dn-")
    p.add_argument("--skip-check", default="", help="open a gate without handoff_check.py: the reason")
    p.add_argument("--by", default="", help="who waits for the developer (default: the author of each document)")
    p.set_defaults(fn=cmd_gate)
    p = sub.add_parser("ok")
    p.add_argument("id")
    p.add_argument("stage", choices=stage_names)
    p.add_argument("--note", default="")
    p.add_argument("--decision", default="", help="approve only this card (default: the whole gate)")
    p.add_argument("--file", default="", help="approve only this document of the gate")
    p.set_defaults(fn=cmd_ok)
    p = sub.add_parser("ask")
    p.add_argument("id")
    p.add_argument("question")
    p.add_argument("--answer", required=True)
    p.add_argument("--decision", default="", help="the card the question is about")
    p.add_argument("--file", default="", help="the document the question is about (default: the first)")
    p.set_defaults(fn=cmd_ask)
    p = sub.add_parser("changes")
    p.add_argument("id")
    p.add_argument("stage", choices=stage_names)
    p.add_argument("summary")
    p.add_argument("--decision", action="append", default=[], help="a card to change, repeatable (default: every card not yet approved)")
    p.set_defaults(fn=cmd_changes)
    p = sub.add_parser("log")
    p.add_argument("id")
    p.add_argument("text")
    p.add_argument("--kind", default="note", choices=["note", "block", "flag", "must", "read", "edit", "run", "search"])
    p.add_argument("--stage", choices=stage_names)
    p.add_argument("--actor", default="")
    p.set_defaults(fn=cmd_log)
    p = sub.add_parser("plan")
    p.add_argument("id")
    p.add_argument("--file", default="", help="the document with \"## Who will work on this\"")
    p.add_argument("--why", default="", help="why the team changes (needed after the team was confirmed)")
    p.set_defaults(fn=cmd_plan)
    p = sub.add_parser("risk")
    p.add_argument("id")
    p.add_argument("level", choices=list(timing.RISKS))
    p.add_argument("--why", required=True, help="the evidence for this level")
    p.set_defaults(fn=cmd_risk)
    p = sub.add_parser("expert")
    p.add_argument("id")
    p.add_argument("stage", choices=stage_names)
    p.add_argument("expert")
    p.add_argument("action", choices=["start", "done", "skip"])
    p.add_argument("--out", default="")
    p.set_defaults(fn=cmd_expert)
    p = sub.add_parser("code")
    p.add_argument("id")
    p.add_argument("state", choices=["open", "closed"])
    p.set_defaults(fn=cmd_code)
    p = sub.add_parser("hook")
    p.add_argument("--cursor", action="store_true")
    p.set_defaults(fn=cmd_hook)
    p = sub.add_parser("open")
    p.add_argument("id", nargs="?")
    p.set_defaults(fn=cmd_open)
    p = sub.add_parser("serve")
    p.add_argument("--port", type=int)
    p.set_defaults(fn=cmd_serve)
    p = sub.add_parser("chat")
    p.add_argument("id")
    p.set_defaults(fn=cmd_chat)
    p = sub.add_parser("quick")
    p.add_argument("text")
    p.set_defaults(fn=cmd_quick)
    a = ap.parse_args()
    if a.cmd not in ("init", "hook", "open", "serve", "quick") and not os.path.isfile(path(a.id, "status.json")):
        sys.exit("%s: no task %s in %s (start it with: %s init %s)" % (a.cmd, a.id, work_rel(), SCRIPT, a.id))
    a.fn(a)


if __name__ == "__main__":
    main()
