"""Flow simulator (agent core): one request replayed on the real live page, to see how the flow works.

  python .claude/core/scripts/simulate.py [SCENARIO] [--speed N] [--bug] [--unplanned] [--app-up] [--open|--no-open]
  python .claude/core/scripts/simulate.py --list
  python .claude/core/scripts/simulate.py --clean [SCENARIO]

Writes <work>/simulate.html (the simulator page: pick a request, step through triage, context, risk, team, stages,
gates and checks) and, for a request that opens a task, replays it as the demo task demo-<scenario> through
live_status.py's own commands, so <work>/live.html?task=demo-<scenario> shows it as a real task would: team,
stages, gates with a question and the approval, checks, a review MUST and Build again, files.

Demo tasks never bind a session (the stop hook never sees them), never become the page's default task (live.js)
and are left out of timing reports. Their documents stay in the demo folder; nothing in the repo changes.
--speed N: N times faster (0 = no pauses). --bug: a review MUST sends the task back to Build. --unplanned: an edit
to a file nobody planned, blocked by the scope check. --app-up: the checks used while the app is running.
--clean removes every demo task (or the named one) and replays nothing. Run in a terminal (or with --open) it opens
the live page in the browser, starting the live-status server when nothing serves it (as live_status.py open does);
--no-open only prints the link.
"""
import argparse
import contextlib
import io
import json
import os
import re
import shutil
import sys
import time
from datetime import date

sys.dont_write_bytecode = True
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import live_status as ls  # noqa: E402
import project  # noqa: E402
import timing  # noqa: E402

PAGE = os.path.join(_HERE, "simulate.html")
SCRIPT = "python .claude/core/scripts/simulate.py"
LIVE = "python .claude/core/scripts/live_status.py"


def data():
    """The scenarios: the JSON block in simulate.html, the one source the page and this script share."""
    with open(PAGE, encoding="utf-8") as f:
        m = re.search(r'<script type="application/json" id="sim-data">(.*?)</script>', f.read(), re.S)
    return json.loads(m.group(1))


def front(text):
    """The frontmatter of an agent file as {key: value} (one line per key)."""
    m = re.match(r"---\s*\n(.*?)\n---", text, re.S)
    return dict(re.findall(r"(?m)^(\w+):\s*(.*?)\s*$", m.group(1))) if m else {}


def core_models(root, d):
    """Each core agent's model and turn limit from its own frontmatter (the installed copy, else the core source)."""
    for n, a in d["agents"].items():
        for folder in (os.path.join(root, ".claude", "agents"), os.path.join(os.path.dirname(PAGE), "..", "agents")):
            f = os.path.join(folder, n + ".md")
            if os.path.isfile(f):
                with open(f, encoding="utf-8", errors="replace") as fh:
                    fm = front(fh.read())
                if fm.get("model"):
                    a["model"] = fm["model"].strip().capitalize()
                    d["models"][n] = a["model"]
                if fm.get("maxTurns", "").isdigit():
                    a["turns"] = int(fm["maxTurns"])
                break


def own_agents(root, d):
    """The repo's own agents (.claude/agents/*.md that are not core agents), described from their frontmatter."""
    out = {}
    folder = os.path.join(root, ".claude", "agents")
    names = sorted(f[:-3] for f in os.listdir(folder) if f.endswith(".md")) if os.path.isdir(folder) else []
    for n in names:
        if n in d["agents"]:
            continue
        with open(os.path.join(folder, n + ".md"), encoding="utf-8", errors="replace") as f:
            fm = front(f.read())
        desc = fm.get("description", "")
        use = re.search(r"\bUse (?:it )?(when|for|after)\b(.*?)(?:\.(?:\s|$)|$)", desc)
        does = (desc[:use.start()] if use else desc).strip()
        if len(does) > 360:
            does = does[:360].rsplit(" ", 1)[0] + " ..."
        writes = sorted(set(re.findall(r"\b[\w-]+\.(?:md|html|yaml)\b", desc)))
        low = desc.lower()
        if "test" in n or "stage 5" in low:
            stages = ["test"]
        else:
            stages = ["design"] + (["review"] if "review mode" in low or any(w.startswith("review-") for w in writes) else [])
        joins = (use.group(1).capitalize() + use.group(2)).rstrip(".") + "." if use else "When the main session picks it for its area."
        out[n] = dict(team="This repo", model=(fm.get("model") or "sonnet").strip().capitalize(), turns=int(fm.get("maxTurns") or 30),
                      calls=35 if "design" in stages or "review" in stages else 20,
                      stages=stages, does=does or n, joins=joins, skipped="The change does not touch its area.",
                      reads="context.md, the lessons for its area, this repo's rules for its area",
                      writes=", ".join(writes) or "its output file in the task folder",
                      hands="the main session: its file feeds Build; review findings go back to Build",
                      web="WebSearch" in fm.get("tools", ""), own=True)
    return out


def own_scenario(own):
    """A medium-risk task that uses every one of the repo's own agents at the stages they work in."""
    lead = next((a for a in own.values() if "design" in a["stages"] and a["joins"].startswith("When")), own[next(iter(own))])
    when = lead["joins"]
    when = when[0].lower() + when[1:]
    if len(when) > 140:
        when = when[:140].rsplit(",", 1)[0] + ", ..."
    design = [n for n, a in own.items() if "design" in a["stages"]]
    review = [n for n, a in own.items() if "review" in a["stages"]]
    test = [n for n, a in own.items() if "test" in a["stages"]]
    short = {n: re.split(r" - |; |\. ", a["does"], 1)[0][:90] for n, a in own.items()}
    team = [dict(stage="design", agent=n, why=short[n]) for n in design]
    team += [dict(stage="design", agent="qa-engineer", focus="characterize", why="risk medium: lock today's outputs"),
             dict(stage="design", agent="qa-lead", focus="plan", why="every task that changes code: the test plan"),
             dict(stage="build", agent="backend-developer", why="the service change, routed by the Tech Lead"),
             dict(stage="build", agent="frontend-developer", why="the screen change, in parallel"),
             dict(stage="review", agent="code-reviewer", why="one review pass")]
    team += [dict(stage="review", agent=n, focus="review", why="a review pass in its own area") for n in review]
    team += [dict(stage="test", agent=n, why=short[n]) for n in test] or [dict(stage="test", agent="main session", why="existing tests")]
    team += [dict(stage="test", agent="ui-qa-expert", why="a screen changes: tested in the running app"),
             dict(stage="test", agent="qa-lead", focus="sign-off", why="no task closes without the QA sign-off")]
    team += [dict(stage="verify", agent="main session", why="live-check and the smoke list"),
             dict(stage="wrap", agent="main session", why="commit message")]
    dfiles = [w for n in design for w in own[n]["writes"].split(", ") if w.endswith(".md") and not w.startswith("review-")] \
        or ["design.md"]
    rfiles = ["review.md"] + [w for n in review for w in own[n]["writes"].split(", ") if w.startswith("review-")]
    steps = [dict(t="triage", why="sdlc 1: a change to the product that is more than a quick fix is a task."),
             dict(t="context", min=3, why="sdlc 2.4: the pack also names this area's own rules and owners."),
             dict(t="risk", why="sdlc 2.5: a shared part with callers outside the change = medium."),
             dict(t="team", why="sdlc 3: a repo's own expert joins when the change touches its area, the same way a core expert does.")]
    if design:
        steps.append(dict(t="stage", stage="design", agents=design, say="; ".join("%s: %s" % (n, short[n]) for n in design) + ".",
                          files=dfiles, min=15,
                          why="Own agents follow the core's rules: read context.md first, write their file first, stay within their tool-call budget."))
    steps += [dict(t="stage", stage="design", title="Characterization tests", agents=["qa-engineer"], files=["safety.md"], min=5,
                   say="qa-engineer locks today's outputs of the shared part.", why="sdlc 5: risk medium."),
              dict(t="stage", stage="design", title="Test plan", agents=["qa-lead"], files=["test-plan.md"], min=4,
                   say="qa-lead writes the test plan: the risks, the matrix and who tests what.",
                   why="sdlc 3: every task that changes code gets a QA plan and a sign-off."),
              dict(t="gate", stage="design", q="Approve the plan?", files=["triage.md"] + dfiles, by=design[0] if design else "main session",
                   why="sdlc 7: medium risk, one gate at the end of the last planning stage."),
              dict(t="check", stage="build", name="Before Build", say="Files baseline, compile, full unit suite.",
                   cmds=["python .claude/core/scripts/scope_check.py baseline <id>", "<commands.compile>", "<commands.test_all>"],
                   result="412 pass, 0 fail", why="sdlc 5."),
              dict(t="build", stage="build", agents=["backend-developer", "frontend-developer"],
                   say="Routed to backend-developer and frontend-developer in parallel (no shared files): they build what the approved plan says.",
                   files=["src/main/java/com/acme/area/AreaService.java", "src/main/resources/static/js/area/area.js"], min=20,
                   why="Build follows the approved plan; another owner's part gets a handoff instead of an edit."),
              dict(t="check", stage="build", name="After Build", say="Compile, the full suite, the characterization diff and the scope check.",
                   cmds=["<commands.compile>", "<commands.test_all>", "python .claude/core/scripts/char_test.py diff <id>",
                         "python .claude/core/scripts/scope_check.py check <id>"], result="414 pass, 0 fail", why="sdlc 5."),
              dict(t="review", stage="review", agents=["code-reviewer"] + review, files=rfiles, min=10,
                   say="code-reviewer" + "".join(" and a %s pass" % n for n in review) + ". PASS.",
                   why="An expert review pass joins when most of the change is in its area."),
              dict(t="stage", stage="test", agents=(test or ["main session"]) + ["ui-qa-expert"], min=14,
                   say=(("%s runs and adds the tests." % ", ".join(test)) if test else "The existing tests for the area pass.")
                   + " ui-qa-expert tests the changed screen in the running app against the UI checklist.",
                   why="Tests run without stopping your app; every UI change is tested in the browser."),
              dict(t="stage", stage="test", title="QA sign-off", agents=["qa-lead"], files=["qa-signoff.md"], min=2,
                   say="qa-lead merges every QA result into one verdict: SIGNED OFF.", why="No task closes without the sign-off."),
              dict(t="stage", stage="verify", agents=["main session"], min=6, say="Live-check, then the smoke items for the area.",
                   why="sdlc 5: + smoke at medium."),
              dict(t="stage", stage="wrap", agents=["main session"], min=2, say="commit-msg.", why="You commit."),
              dict(t="end", say="Done: this repo's own agents worked inside the same flow, rules and gates as the core ones.")]
    return dict(id="own", label="This repo's own agents", group="Task", mode="task", size="M",
                ask="A change in this repo's own area: " + when, lane="Task",
                laneWhy="A change in an area this repo has its own expert for.", risk="medium",
                riskWhy=["the area has its own expert, rules and owners", "a shared part with callers outside the change (context.md)"],
                context=dict(impact=[["area", "%s's area" % n, "the paths its agent file names", "sample"] for n in own],
                             rules=["this repo's rules for the area (AGENTS.md, .claude/rules)"], signals=["an area with its own expert"]),
                team=team, notNeeded=[dict(agent="spec-analyst", why="the goal is clear")], steps=steps)


def build(root=None):
    """The simulator data for a repo: the core scenarios and roster, plus its own agents and its stage budgets."""
    d = data()
    root = os.path.abspath(root or ls.ROOT)
    core_models(root, d)
    own = own_agents(root, d)
    for n, a in own.items():
        d["agents"][n] = a
        d["models"].setdefault(n, a["model"])
    if own:
        d["scenarios"].insert(len(d["scenarios"]) - 1, own_scenario(own))  # before the new product
    cfg = project.config(root)
    d["budgets"] = {r: timing.budgets_for(r, "task", cfg) for r in ("low", "medium", "high")}
    return d


def expand(sc, d, bug=False, unplanned=False):
    """The steps with the toggles applied (the page's expand() does the same)."""
    out, fail = [], sc.get("mustFail") or (d["bug"] if bug and sc.get("mode") == "task" else None)
    for s in sc["steps"]:
        if s["t"] == "review" and fail:
            out.append(dict(t="reviewFail", stage="review", agents=s.get("agents"), finding=fail["finding"]))
            out.append(dict(t="rebuild", stage="build", agents=["main session"], say=fail["fix"]))
            out.append(dict(s, again=True, say="Review again, only for what failed: PASS."))
            out.append(dict(t="lessons", stage="review", line=fail["lesson"].replace("<date>", date.today().isoformat())
                            .replace("<task>", "demo-" + sc["id"])))
            continue
        out.append(s)
        if s["t"] == "build" and unplanned and sc.get("mode") == "task":
            out.append(dict(t="scope", stage="build", file=d["unplanned"]["file"], say=d["unplanned"]["say"]))
    return out


def page_copy(d):
    """<work>/simulate.html with this project's name, live port, own agents and budgets filled in."""
    with open(PAGE, encoding="utf-8") as f:
        src = f.read()
    m = re.search(r'<script type="application/json" id="sim-data">(.*?)</script>', src, re.S)
    src = src[:m.start(1)] + "\n" + json.dumps(d, ensure_ascii=False).replace("</", "<\\/") + "\n" + src[m.end(1):]
    meta = json.dumps({"port": ls.PORT, "name": ls.CFG.get("name") or ""}).replace("</", "<\\/")
    src = src.replace('window.__SIM__={"port":8766,"name":""};', "window.__SIM__=%s;" % meta, 1)
    os.makedirs(ls.WORK, exist_ok=True)
    ls.write(ls.path("simulate.html"), src)


def clean(which=None):
    gone = []
    for t in ls.tasks():
        if ls.is_demo(t) and (not which or t == "demo-" + which):
            shutil.rmtree(ls.path(t), ignore_errors=True)
            gone.append(t)
    return gone


class Replay:
    def __init__(self, sc, d, speed, app_up):
        self.sc, self.d, self.app_up = sc, d, app_up
        self.tid = "demo-" + sc["id"]
        self.mode = sc["mode"]
        self.pause_s = 0 if speed <= 0 else 1.2 / speed
        self.open = None  # the stage the replay is in
        self.told_app_up = False

    # -- live_status, as the skills call it --------------------------------------------------------
    def ls(self, *argv):
        old = sys.argv
        sys.argv = ["live_status.py"] + [str(x) for x in argv]
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                ls.main()
        except SystemExit as e:
            if e.code not in (None, 0):
                raise RuntimeError("live_status %s: %s %s" % (argv[0], e.code if isinstance(e.code, str) else "",
                                                             buf.getvalue().strip()))
        finally:
            sys.argv = old

    def hook(self, event, tool, inp, agent_type=None):
        """What the live hook does for one tool call of the session working on this task."""
        x = dict(hook_event_name=event, tool_name=tool, tool_input=inp)
        if agent_type:
            x["agent_type"] = agent_type
        ls.with_lock(lambda: ls.on_tool(self.tid, x))

    def wait(self, k=1.0):
        if self.pause_s:
            time.sleep(self.pause_s * k)

    def stages(self):
        return {s["k"]: s for s in ls.load(self.tid)["stages"]}

    def note(self, text, kind="note", actor="main session", stage=None):
        self.ls("log", self.tid, text, "--kind", kind, "--actor", actor, *(["--stage", stage] if stage else []))

    def doc(self, f, body):
        p = ls.path(self.tid, *f.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
        return p

    def wrote(self, f, actor="main session", in_task=True):
        p = ls.path(self.tid, *f.split("/")) if in_task else os.path.join(ls.ROOT, *f.split("/"))
        self.hook("PostToolUse", "Write", {"file_path": p}, actor)

    def ran(self, cmd, actor="main session"):
        self.hook("PostToolUse", "Bash", {"command": cmd}, actor)

    # -- stages -------------------------------------------------------------------------------------
    def close(self, keep=None):
        if self.open and self.open != keep and self.stages()[self.open]["state"] in ("live", "fail"):
            if self.stages()[self.open]["state"] == "live":
                self.ls("stage", self.tid, self.open, "done")
        if self.open != keep:
            self.open = None

    def enter(self, k, agents):
        """The stage runs: started by its first agent (the hook), or by the main session."""
        st = self.stages()
        if k not in st:
            return False
        self.close(keep=k)
        others = [a for a in agents or [] if a != "main session"]
        if st[k]["state"] != "live":
            self.ls("stage", self.tid, k, "start", "--actor", others[0] if others else "main session")
        self.open = k
        return True

    def own(self, agents, k):
        """The agents a stage's own team rows name (Review and Test run together, but each in its own stage)."""
        mine = {r["agent"] for r in (ls.load(self.tid).get("plan") or {}).get("rows", []) if r["stage"] == k}
        return [a for a in agents or [] if a in mine] or (agents or ["main session"])[:1]

    def agents_start(self, agents, why=""):
        for a in agents or []:
            if a != "main session":
                self.hook("PreToolUse", "Agent", {"subagent_type": a, "description": why[:80]})
                self.wait(0.3)

    def parallel(self, s, others):
        """Several experts at once, as background agents run: each reads the context pack, writes its own files
        in turn with the others, and finishes on its own; the main session waits. A file is the step's `owners`
        entry's, else the expert whose `writes` names it (or its decision card), else the first expert's."""
        def owner(f):
            name = os.path.basename(f)
            card = re.match(r"(D\d)-", name)
            return (s.get("owners") or {}).get(f) or next(
                (a for a in others if re.search(r"\b%s\b" % re.escape(card.group(1) if card else name),
                                                (self.d["agents"].get(a) or {}).get("writes", ""))), others[0])
        mine = {a: [f for f in s.get("files") or [] if owner(f) == a] for a in others}
        order = sorted(others, key=lambda a: len(mine[a]))  # the one with the least to write finishes first
        for a in others:
            self.hook("PostToolUse", "Read", {"file_path": ls.path(self.tid, "context.md")}, a)
            self.wait(0.3)
        while any(mine.values()):
            for a in others:
                if mine[a]:
                    self.files(dict(s, files=[mine[a].pop(0)]), a)
        for c in s.get("cmds") or []:
            self.ran(c.replace("<id>", self.tid), s.get("cmdsBy") or others[0])
        for a in order:
            self.hook("PostToolUse", "Agent", {"subagent_type": a})
            self.wait(0.8)
        if s.get("say"):
            self.note(("%s: " % s["title"] if s.get("title") else "") + s["say"])

    def agents_done(self, agents):
        for a in agents or []:
            if a != "main session":
                self.hook("PostToolUse", "Agent", {"subagent_type": a})
                self.wait(0.2)

    def checks(self, s):
        cmds = s.get("cmdsUp") if self.app_up and s.get("cmdsUp") else s.get("cmds") or []
        for c in cmds:
            if c.startswith("compile:"):
                self.note("Compile: " + c.split(":", 1)[1].strip())
            else:
                self.ran(c.replace("<id>", self.tid))
            self.wait(0.3)
        if self.app_up and s.get("cmdsUp") and not self.told_app_up:
            self.note(self.d["appUp"])
            self.told_app_up = True
        if s.get("result"):
            self.note(s["name"] + ": " + s["result"] if s.get("name") else s["result"])

    # -- the documents a task writes (samples; the page and the gates read them) ------------------------
    def triage_md(self):
        sc = self.sc
        rows = "\n".join("| %s | %s%s | %s |" % (ls.NAMES.get(r["stage"], r["stage"]), r["agent"],
                                                 " (%s)" % r["focus"] if r.get("focus") else "", r["why"])
                         for r in sc["team"])
        skip = "\n".join("- %s: %s" % (n["agent"], n["why"]) for n in sc.get("notNeeded") or [])
        files = sorted({f for s in sc["steps"] if s["t"] == "build" for f in s.get("files") or []})
        return ("# Triage: %s\n\nRequest: %s\nLane: %s - %s\nSize: %s\nRisk: %s\n\n## Risk evidence\n%s\n\n"
                "## Who will work on this\n| Stage | Expert | Why |\n|---|---|---|\n%s\n\n## Not needed\n%s\n\n"
                "## Planned files\n%s\n\n_Demo replay (simulate.py): a sample, not a real task._\n") % (
            sc["label"], sc["ask"], sc["lane"], sc["laneWhy"], sc.get("size", "M"), sc.get("risk", ""),
            "\n".join("- " + w for w in sc.get("riskWhy") or []), rows, skip or "- none",
            "\n".join("- " + f for f in files) or "- none")

    def context_md(self):
        c = self.sc["context"]
        return ("# Context pack: %s\n\n## Impact map\n| Kind | What | Where | Note |\n|---|---|---|---|\n%s\n\n"
                "## Rules that apply\n%s\n\n## Risk signals\n%s\n\n## Gaps\nnone\n\n"
                "_Demo replay: the paths are samples._\n") % (
            self.sc["ask"], "\n".join("| %s |" % " | ".join(r) for r in c["impact"]),
            "\n".join("- " + r for r in c["rules"]), "\n".join("- " + r for r in c["signals"]))

    def sample(self, f, s):
        """A short sample document for a gate or a stage."""
        title = os.path.basename(f).rsplit(".", 1)[0]
        body = ["# %s (demo)" % title, "", s.get("say") or s.get("q") or self.sc["ask"], ""]
        m = re.match(r"D(\d)-", title)
        if m:
            body += ["## Decision", "Recommended: as described in design.md.", "", "## What happens to existing data",
                     "Nothing changes for existing rows (demo).", ""]
        if title.endswith("qa-signoff"):
            body += ["## Verdict", "SIGNED OFF: every matrix row PASS (demo).", ""]
        if s.get("table"):
            for t in (s["table"], s.get("table2")):
                if t:
                    body += ["| " + " | ".join(t["head"]) + " |", "|" + "---|" * len(t["head"])]
                    body += ["| " + " | ".join(r) + " |" for r in t["rows"]] + [""]
        body.append("_Demo replay (simulate.py): a sample document._")
        return "\n".join(body) + "\n"

    def files(self, s, actor):
        for f in s.get("files") or []:
            if f.startswith((".claude/", "src/", "n8n_workflows/")):
                continue
            if not os.path.isfile(ls.path(self.tid, *f.split("/"))):
                self.doc(f, self.sample(f, s))
            self.wrote(f, actor)
            self.wait(0.2)

    # -- one step ---------------------------------------------------------------------------------
    def step(self, s):
        t, sc = s["t"], self.sc
        if t == "triage":
            argv = ["init", self.tid, "--title", sc["ask"][:90], "--size", sc.get("size", "M"), "--demo"]
            if self.mode == "product":
                argv += ["--mode", "product", "--root", ls.path(self.tid)]
            else:
                argv += ["--mode", "task"]
            self.ls(*argv)
            self.note("Triage: lane %s - %s" % (sc["lane"], sc["laneWhy"]))
            if self.mode == "product":
                self.doc("00-intake.md", self.triage_md())
                self.ls("plan", self.tid, "--file", "00-intake.md")
        elif t == "context":
            self.hook("PreToolUse", "Agent", {"subagent_type": "explorer", "description": "context pack"})
            self.wait(0.6)
            for r in [r for r in sc["context"]["impact"] if ":" in r[2]][:3]:
                self.hook("PostToolUse", "Read", {"file_path": os.path.join(ls.ROOT, r[2].split(":")[0])}, "explorer")
                self.wait(0.2)
            self.doc("context.md", self.context_md())
            self.wrote("context.md", "explorer")
            self.hook("PostToolUse", "Agent", {"subagent_type": "explorer"})
        elif t == "risk":
            self.ls("risk", self.tid, sc["risk"], "--why", "; ".join(sc["riskWhy"]))
        elif t == "team":
            self.doc("triage.md", self.triage_md())
            self.wrote("triage.md")
            self.ls("plan", self.tid, "--file", "triage.md")
        elif t in ("stage", "note", "review", "build", "rebuild"):
            k = s.get("stage") or self.open
            agents = self.own(s.get("agents"), k) if t == "review" else s.get("agents") or ["main session"]
            if k == "review" and s.get("again"):
                self.close()
            inside = self.enter(k, agents) if k else False
            if not inside and self.open:
                k = self.open
            self.agents_start(agents, s.get("title") or s.get("say") or "")
            lead = next((a for a in agents if a != "main session"), "main session")
            others = [a for a in agents if a != "main session"]
            if t not in ("build", "rebuild", "review") and len(others) > 1:
                self.parallel(s, others)
                return self.wait(1.0)
            if t in ("build", "rebuild"):
                for f in (s.get("files") or []) or [self.last_build[0]]:
                    owner = project.product_area(os.path.join(ls.ROOT, *f.split("/")), ls.ROOT)
                    self.wrote(f, owner if owner in others else lead, in_task=False)
                    self.wait(0.25)
                if t == "build":
                    self.last_build = s.get("files") or []
            else:
                self.files(s, lead)
            for c in s.get("cmds") or []:
                self.ran(c.replace("<id>", self.tid), lead)
            if s.get("say"):
                self.note(("%s: " % s["title"] if s.get("title") else "") + s["say"], actor=lead)
            self.agents_done(agents)
            if t == "review":
                self.close()
        elif t == "check":
            if s.get("stage") in self.stages():
                self.enter(s["stage"], ["main session"])
            self.checks(s)
        elif t == "gate":
            k = s["stage"]
            if self.open and self.open != k:
                self.close()
            files = s.get("files") or []
            for f in files:
                if not os.path.isfile(ls.path(self.tid, *f.split("/"))):
                    self.doc(f, self.sample(f, s))
            argv = ["gate", self.tid, k, s["q"], "--skip-check", "demo replay: sample documents"]
            for f in files:
                argv += ["--file", f]
            if s.get("by"):
                argv += ["--by", s["by"]]
            self.ls(*argv)
            self.wait(2.5)
            if s.get("qa"):
                self.ls("ask", self.tid, s["qa"]["q"], "--answer", s["qa"]["a"])
                self.wait(1.5)
            self.ls("ok", self.tid, k, "--note", "approved (demo)")
            st = self.stages()[k]
            self.open = k if st["state"] == "live" else None
        elif t == "reviewFail":
            self.close()
            agents = self.own(s.get("agents"), "review")
            self.enter("review", agents)
            self.agents_start(agents, "review")
            self.doc("review.md", "# Review (demo)\n\n## Findings\n| # | finding | MUST/SHOULD |\n|---|---|---|\n| 1 | %s | MUST |\n"
                     % s["finding"])
            self.wrote("review.md", "code-reviewer")
            self.note(s["finding"], kind="must", actor="code-reviewer", stage="review")
            self.agents_done(agents)
            self.ls("stage", self.tid, "review", "fail", "--out", "1 MUST: back to Build")
            self.open = None
        elif t == "lessons":
            p = self.doc("lessons.md", "# Lessons (demo copy; a real task adds this line to .claude/review/lessons.md)\n\n"
                         + s["line"] + "\n")
            self.wrote("lessons.md")
            self.note("Lesson recorded: " + s["line"].lstrip("- "))
            del p
        elif t == "scope":
            self.wrote(s["file"], in_task=False)
            self.wait(0.4)
            self.ran("python .claude/core/scripts/scope_check.py check " + self.tid)
            self.note("Scope check: %s is not planned (MUST). The agent drops that change." % s["file"], kind="block",
                      stage="build")
            self.note("Scope check clean: every changed file is planned.")
        elif t == "guard":
            self.note("Guard: edits to the data model were held until D2 was approved; approved now, they go through.")
        elif t == "end":
            self.close()
            self.note(s["say"])
        self.wait(1.0)

    def run(self, steps, opener=None):
        self.last_build = []
        for i, s in enumerate(steps, 1):
            self.step(s)
            if i == 1 and opener:  # the task exists now: show its live page while the rest replays
                opener()
                self.wait(2)
            try:
                print("  %2d/%d %s" % (i, len(steps), label(s, self.sc)), flush=True)
            except OSError:  # the output was closed (a pipe to head): the replay still finishes
                pass


def label(s, sc):
    t = s["t"]
    return {"triage": "Triage: " + sc["lane"], "context": "Context pack (explorer)", "risk": "Risk " + str(sc.get("risk")),
            "team": "Team planned", "gate": "Gate: " + s.get("q", ""), "reviewFail": "Review fails: back to Build",
            "rebuild": "Build again", "lessons": "Lesson recorded", "scope": "Scope check blocks an unplanned file",
            "guard": "Guard", "end": "Done", "check": s.get("name", "Checks"), "build": "Build",
            "review": "Review again" if s.get("again") else "Review"}.get(t) or s.get("title") or \
        ls.NAMES.get(s.get("stage") or "", s.get("stage") or t)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenario", nargs="?", help="the request to replay (--list shows them)")
    ap.add_argument("--speed", type=float, default=1.0, help="N times faster; 0 = no pauses")
    ap.add_argument("--bug", action="store_true", help="a review MUST sends the task back to Build")
    ap.add_argument("--unplanned", action="store_true", help="an edit to a file nobody planned (scope check)")
    ap.add_argument("--app-up", action="store_true", help="the checks used while the app is running")
    ap.add_argument("--clean", action="store_true", help="remove the demo tasks (all, or SCENARIO's) and stop")
    ap.add_argument("--list", action="store_true", help="list the requests")
    ap.add_argument("--open", dest="open", action="store_true", default=None,
                    help="open the live page in the browser (default when run in a terminal); starts the live-status "
                         "server if nothing serves it, as live_status.py open does")
    ap.add_argument("--no-open", dest="open", action="store_false", help="do not open the live page")
    a = ap.parse_args(argv)
    d = build()
    by = {s["id"]: s for s in d["scenarios"]}
    page_copy(d)
    page = "http://localhost:%d/simulate.html" % ls.PORT
    if a.list:
        for s in d["scenarios"]:
            print("  %-9s %-20s %s" % (s["id"], s["label"], s["ask"]))
        print("Simulator page: " + page)
        return 0
    if a.scenario and a.scenario not in by:
        ap.error("unknown scenario %s (one of: %s)" % (a.scenario, ", ".join(by)))
    if a.clean:
        gone = ls.with_lock(lambda: clean(a.scenario))
        print("Removed %s." % (", ".join(gone) if gone else "no demo tasks"))
        return 0
    if not a.scenario:
        print("Simulator page: %s\nReplay a request on the live page: %s <%s>" % (page, SCRIPT, "|".join(by)))
        return 0
    sc = by[a.scenario]
    print("Simulator page: %s#%s" % (page, sc["id"]))
    if sc["mode"] == "none":
        print("%s: lane %s. No task, so nothing appears on the live page; step through it on the simulator page."
              % (sc["label"], sc["lane"]))
        return 0
    tid = "demo-" + sc["id"]
    ls.with_lock(lambda: clean(sc["id"]))
    live = ls.page_url(tid)
    show = sys.stdout.isatty() if a.open is None else a.open
    print("Live page: " + live + ("" if show or ls.serving() else
                                  "\n  (nothing serves it yet: run %s open %s, or add --open)" % (LIVE, tid)))
    print("Replaying %s as %s:" % (sc["label"].lower(), tid))

    def opener():
        with contextlib.redirect_stdout(io.StringIO()):
            ls.cmd_open(argparse.Namespace(id=tid))  # the live-status server (the one server the flow may start) + browser
    Replay(sc, d, a.speed, a.app_up).run(expand(sc, d, a.bug, a.unplanned), opener if show else None)
    print("Done. Remove it with: %s --clean %s" % (SCRIPT, sc["id"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
