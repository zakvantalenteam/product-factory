#!/usr/bin/env python3
"""Risk levels, stage time budgets and the timing report of the live page (agent core).

  python .claude/core/scripts/timing.py [ID ...] [--last N] [--baseline ID | --baseline-file F.json] [--wall] [--csv]
                                        [--root PRODUCT_ROOT | --work WORK_DIR]

Reads <work>/<id>/status.json (and events.jsonl) of each task and prints one row per task: risk, size, working
minutes per stage, total working minutes, minutes spent waiting for the developer at gates (kept apart from working
time) and the stages that ran over their budget. A trailing + is a stage still running; * on a risk means the
task has none recorded (older status files) and medium is assumed. With no ID, the last 10 tasks (--last N).

Baseline: --baseline ID adds a delta column against that task; --baseline-file takes a JSON file with
{"stage": minutes}, for example a run from before a faster flow:
  {"spec": 45, "design": 14, "build": 47, "review": 29}
The delta is over the stages both the task and the baseline have (negative = faster than the baseline). A baseline
taken from wall-clock times includes the waits at gates: add --wall to count them in the stage minutes too.

Budgets are minutes per stage per risk (BUDGETS below). A project overrides them with "budgets" in
.claude/project.json, same shape {"<risk>": {"<stage>": minutes}}, deep-merged over these; null or 0 drops a stage's
budget. Product mode has no default budget (a whole product runs for days, a fixed number would only nag); a
project can give product stages one under "budgets": {"product": {"<risk>": {"<stage>": minutes}}}.

For live_status.py (import this module): BUDGETS, RISKS, DEFAULT_RISK, norm_risk, parse_risk, budgets_for,
stage_times, overruns, overrun_notes, gap_s.
"""
import argparse
import copy
import csv
import io
import json
import os
import re
import sys
from datetime import datetime

sys.dont_write_bytecode = True

RISKS = ("low", "medium", "high")
DEFAULT_RISK = "medium"
# Minutes per stage of a task (task mode). Product mode has none by default (see the module doc).
BUDGETS = {
    "low": {"spec": 5, "design": 10, "build": 30, "review": 10, "test": 10, "verify": 10, "release": 10, "wrap": 5},
    "medium": {"spec": 15, "design": 20, "build": 45, "review": 20, "test": 15, "verify": 15, "release": 15, "wrap": 5},
    "high": {"spec": 30, "design": 40, "build": 90, "review": 30, "test": 30, "verify": 20, "release": 20, "wrap": 10},
}
STAGE_ORDER = tuple(BUDGETS["low"])


# ---- risk ---------------------------------------------------------------------------------------

def norm_risk(v):
    """'low', 'medium' or 'high' from a value like 'High', '**high**' or 'med'; None when it is none of them."""
    m = re.match(r"[\s*_`]*(low|medium|med|high)\b(?!\s*\|)", str(v or ""), re.I)
    if not m:
        return None
    return "medium" if m.group(1).lower() == "med" else m.group(1).lower()


def parse_risk(text):
    """(risk or None, evidence bullets) from a triage or spec text: the "Risk: low|medium|high" line (an unfilled
    "low|medium|high" template line is ignored) and the bullets under "## Risk evidence"."""
    text = (text or "").replace("\r\n", "\n")
    m = re.search(r"(?im)^[>\s*_`-]*risk(?:\s+level)?[*_`]*\s*:[*_`\s]*(\S.*)$", text)
    risk = norm_risk(m.group(1)) if m else None
    bullets, inside = [], False
    for line in text.split("\n"):
        if re.match(r"^#{1,6}\s", line):
            inside = bool(re.match(r"^#{1,6}\s+risk evidence\b", line, re.I))
            continue
        b = re.match(r"^\s*[-*+]\s+(.+?)\s*$", line) if inside else None
        if b and len(bullets) < 8:
            bullets.append(b.group(1)[:160])
    return risk, bullets


# ---- budgets ------------------------------------------------------------------------------------

def merge_budgets(base, over):
    """Deep merge of {risk: {stage: minutes}} tables: `over` wins; null or 0 removes a stage's budget; values that
    are not numbers are ignored."""
    out = copy.deepcopy(base or {})
    for risk, stages in (over or {}).items():
        if not isinstance(stages, dict):
            continue
        row = out.setdefault(risk, {})
        for k, v in stages.items():
            if v is None or v == 0:
                row.pop(k, None)
            elif isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0:
                row[k] = v
    return out


def budgets_for(risk, mode="task", cfg=None):
    """{stage: minutes} for a risk: the core table (task mode), merged with "budgets" from project.json."""
    over = (cfg or {}).get("budgets")
    over = over if isinstance(over, dict) else {}
    if mode == "product":
        table = merge_budgets({}, over.get("product") if isinstance(over.get("product"), dict) else {})
    else:
        table = merge_budgets(BUDGETS, {k: v for k, v in over.items() if k in RISKS})
    return dict(table.get(norm_risk(risk) or DEFAULT_RISK) or {})


# ---- time ---------------------------------------------------------------------------------------

def ts(v):
    """A datetime from an ISO string (naive = local time); None when it is not one."""
    try:
        d = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return d if d.tzinfo else d.astimezone()


def gap_s(a, b):
    """Seconds from ISO time a to ISO time b (0 when either is missing or b is earlier)."""
    x, y = ts(a), ts(b)
    return max(0.0, (y - x).total_seconds()) if x and y else 0.0


def event_waits(events):
    """Older status files: seconds each stage waited for the developer, from the gate event to the last ok or
    changes event of that stage before the next gate. A gate nothing closed is the open one and is left out."""
    ev = [e for e in events or [] if isinstance(e, dict)]
    out = {}
    for i, e in enumerate(ev):
        if e.get("kind") != "gate":
            continue
        k, t0 = e.get("stage"), ts(e.get("t"))
        nxt = next((j for j in range(i + 1, len(ev)) if ev[j].get("kind") == "gate"), len(ev))
        close = [ts(x.get("t")) for x in ev[i + 1:nxt] if x.get("kind") in ("ok", "changes") and x.get("stage") == k]
        close = [c for c in close if c]
        if k and t0 and close:
            out[k] = out.get(k, 0.0) + max(0.0, (max(close) - t0).total_seconds())
    return out


def stage_times(st, now=None, events=None):
    """{stage: {work, wait, state, running, waiting}} (seconds) for every stage that has started. Working time is
    start to end (or now) without the gate waits and the idle gaps between rounds. Gate waits come from the
    stage's wait_s (live_status.py records it); status files without it fall back to the gate events."""
    now = now or datetime.now().astimezone()
    g = st.get("gate") or {}
    ev_waits = None
    out = {}
    for s in st.get("stages") or []:
        k, state, t0 = s.get("k"), s.get("state"), ts(s.get("start"))
        if not k or t0 is None or state in ("todo", "skip"):
            continue
        gate_at = ts(g.get("at")) if g.get("stage") == k else None
        waiting = state == "wait"
        if state == "done":
            t1 = ts(s.get("end")) or t0
        elif waiting and gate_at:
            t1 = gate_at  # the stage stopped working when the gate opened
        elif state == "fail" and ts(s.get("end")):
            t1 = ts(s.get("end"))
        else:
            t1 = now
        if "wait_s" in s:
            closed = float(s.get("wait_s") or 0)
        else:
            if ev_waits is None:
                ev_waits = event_waits(events if events is not None else st.get("events"))
            closed = ev_waits.get(k, 0.0)
        work = max(0.0, (t1 - t0).total_seconds() - closed - float(s.get("idle_s") or 0))
        open_wait = max(0.0, (now - gate_at).total_seconds()) if waiting and gate_at else 0.0
        out[k] = dict(work=work, wait=closed + open_wait, state=state, waiting=waiting,
                      running=state in ("live", "fail") and not (state == "fail" and ts(s.get("end"))))
    return out


def overruns(times, budgets):
    """[(stage, work_minutes, budget_minutes, over_minutes, running)] for each stage past its budget."""
    out = []
    for k, t in times.items():
        b = (budgets or {}).get(k)
        if b and t["work"] > b * 60:
            out.append((k, t["work"] / 60.0, float(b), t["work"] / 60.0 - b, t["running"]))
    return out


def over_text(over_min):
    return "over by %d min" % max(1, int(round(over_min)))


def overrun_notes(st, now=None, events=None):
    """Plain lines for status.md: one per stage past its budget (the stage's budgets come from st["budgets"])."""
    names = {s.get("k"): s.get("name") or s.get("k") for s in st.get("stages") or []}
    times = stage_times(st, now, events)
    out = []
    for k, w, b, over, running in overruns(times, st.get("budgets") or {}):
        done = times[k]["state"] == "done"
        out.append("%s: %s%s (%d of %g min)" % (names.get(k, k), "ran " if done else "", over_text(over), int(w), b))
    return out


# ---- the report ---------------------------------------------------------------------------------

def read_task(work, tid):
    """status.json of a task with the full event list (events.jsonl keeps every event; status.json the last 200)."""
    d = os.path.join(work, tid)
    with open(os.path.join(d, "status.json"), encoding="utf-8") as f:
        st = json.load(f)
    try:
        with open(os.path.join(d, "events.jsonl"), encoding="utf-8") as f:
            ev = [json.loads(x) for x in f if x.strip()]
        if ev:
            st["events"] = ev
    except (OSError, ValueError):
        pass
    return st


def task_row(st, cfg=None, now=None, wall=False):
    """One report row: id, risk (risk_known False when the file has none), size, minutes per stage, totals, overruns.
    Stage minutes are working time; wall=True adds the gate waits (overruns stay on working time)."""
    risk = norm_risk(st.get("risk"))
    mode = st.get("mode") if st.get("mode") in ("task", "product") else "task"
    budgets = budgets_for(risk, mode, cfg)
    times = stage_times(st, now)
    stages = {k: (t["work"] + (t["wait"] if wall else 0)) / 60.0 for k, t in times.items()}
    return dict(id=st.get("id") or "", risk=risk or DEFAULT_RISK, risk_known=bool(risk), size=st.get("size") or "",
                started=st.get("started") or "", stages=stages,
                running=sorted(k for k, t in times.items() if t["running"]),
                total=sum(stages.values()), wait=sum(t["wait"] for t in times.values()) / 60.0,
                over=[(k, round(o)) for k, _, _, o, _ in overruns(times, budgets)])


def baseline_of(row=None, data=None):
    """{stage: minutes} from a report row or a loaded {stage: minutes} JSON; anything else is ignored."""
    src = row["stages"] if row else data
    if not isinstance(src, dict):
        raise ValueError("a baseline is {\"stage\": minutes}")
    return {str(k): float(v) for k, v in src.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}


def delta(row, base):
    """(total delta, {stage: delta}) of a row against a baseline, over the stages both have."""
    per = {k: row["stages"][k] - m for k, m in base.items() if k in row["stages"]}
    return sum(per.values()), per


def _sign(x):
    return "%+d" % round(x)


def render(rows, base=None, as_csv=False):
    stages = [k for k in STAGE_ORDER if any(k in r["stages"] for r in rows)]
    stages += [k for r in rows for k in r["stages"] if k not in stages and k not in STAGE_ORDER]
    stages = list(dict.fromkeys(stages))
    head = ["task", "risk", "size"] + stages + ["total", "wait", "over"] + (["delta"] if base else [])
    lines = []
    for r in rows:
        d_tot, d_per = delta(r, base) if base else (0, {})
        if as_csv:
            line = [r["id"], r["risk"] if r["risk_known"] else r["risk"] + "*", r["size"]]
            line += ["%.1f" % r["stages"][k] if k in r["stages"] else "" for k in stages]
            line += ["%.1f" % r["total"], "%.1f" % r["wait"], " ".join("%s+%d" % o for o in r["over"])]
            if base:
                line.append("%.1f" % d_tot)
        else:
            line = [r["id"], r["risk"] + ("" if r["risk_known"] else "*"), r["size"]]
            for k in stages:
                if k not in r["stages"]:
                    line.append("-")
                    continue
                cell = "%d%s" % (round(r["stages"][k]), "+" if k in r["running"] else "")
                line.append(cell + (" (%s)" % _sign(d_per[k]) if k in d_per else ""))
            line += ["%d" % round(r["total"]), "%d" % round(r["wait"]), " ".join("%s+%d" % o for o in r["over"]) or "-"]
            if base:
                line.append(_sign(d_tot))
        lines.append(line)
    if as_csv:
        out = io.StringIO()
        w = csv.writer(out, lineterminator="\n")
        w.writerow(head)
        w.writerows(lines)
        return out.getvalue().rstrip("\n")
    cols = list(zip(*([head] + lines)))
    widths = [max(len(c) for c in col) for col in cols]
    left = {0, 1, 2, head.index("over")}

    def fmt(row):
        return "  ".join(c.ljust(w) if i in left else c.rjust(w) for i, (c, w) in enumerate(zip(row, widths))).rstrip()
    out = [fmt(head), "  ".join("-" * w for w in widths)] + [fmt(x) for x in lines]
    notes = ["minutes of working time; total = sum of the stages; wait = time waiting for the developer at gates",
             "over = stages past their budget (stage+minutes over); + = still running"]
    if any(not r["risk_known"] for r in rows):
        notes.append("* no risk recorded in the status file: medium assumed")
    if base:
        notes.append("(+n) and delta = minutes against the baseline, over the stages both have")
    return "\n".join(out + [""] + notes)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*", help="task ids (default: the last 10 tasks)")
    ap.add_argument("--last", type=int, help="the N most recently started tasks (when no ID is given)")
    ap.add_argument("--baseline", metavar="ID", help="add a delta column against this task")
    ap.add_argument("--baseline-file", metavar="JSON", help="add a delta column against {\"stage\": minutes} in this file")
    ap.add_argument("--csv", action="store_true", help="comma-separated output")
    ap.add_argument("--wall", action="store_true", help="count the waits at gates in the stage minutes (for a wall-clock baseline)")
    ap.add_argument("--root", help="the product root whose .claude/project.json and work folder to read (default: this repo)")
    ap.add_argument("--work", help="the work folder to read (default: work_dir of the project)")
    a = ap.parse_args(argv)
    if a.baseline and a.baseline_file:
        ap.error("pass --baseline or --baseline-file, not both")
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import project
    root = os.path.abspath(a.root) if a.root else project.repo_root()
    cfg = project.config(root)
    work = os.path.abspath(a.work) if a.work else project.work_dir(root)
    try:
        every = sorted(n for n in os.listdir(work) if not n.startswith(".") and os.path.isfile(os.path.join(work, n, "status.json")))
    except OSError:
        sys.exit("timing: no work folder at %s" % work)
    sts = {}
    for n in set(every) | set(a.ids) | ({a.baseline} if a.baseline else set()):
        try:
            sts[n] = read_task(work, n)
        except (OSError, ValueError):
            if n in a.ids or n == a.baseline:
                sys.exit("timing: no readable status.json for %s in %s" % (n, work))
    if a.ids:
        ids = list(a.ids)
    else:
        # demo replays (simulate.py) only when named
        real = sorted((n for n in sts if not sts[n].get("demo")), key=lambda n: (sts[n].get("started") or "", n))
        ids = real[-(a.last or 10):] if (a.last or 10) > 0 else real
        if len(real) > len(ids) and not a.last:
            print("(last %d of %d tasks; --last N for more)" % (len(ids), len(real)), file=sys.stderr)
    now = datetime.now().astimezone()
    rows = [task_row(sts[n], cfg, now, a.wall) for n in ids]
    base = None
    try:
        if a.baseline:
            base = baseline_of(row=task_row(sts[a.baseline], cfg, now, a.wall))
        elif a.baseline_file:
            with open(a.baseline_file, encoding="utf-8") as f:
                base = baseline_of(data=json.load(f))
    except (OSError, ValueError) as e:
        sys.exit("timing: baseline: %s" % e)
    print(render(rows, base, a.csv))


if __name__ == "__main__":
    main()
