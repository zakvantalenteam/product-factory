"""Live factory tracker: work/<slug>/tracker.json -> work/<slug>/tracker.html + tracker-data.js (offline, live).

Usage (slug defaults to the one in work/.active):
  python scripts/tracker.py stage S2 ["what is happening"]
  python scripts/tracker.py gate G1 waiting|approved|open ["user's words"]
  python scripts/tracker.py code open|closed            (also sets code_writes in status.md)
  python scripts/tracker.py note "one line"
  python scripts/tracker.py wait "what the user must do" | python scripts/tracker.py wait --clear
  python scripts/tracker.py agent-start <agent> ["task"]
  python scripts/tracker.py agent-done <agent> ["result in one line"] [--failed]
  python scripts/tracker.py act <agent> "what it is doing now"
  python scripts/tracker.py ask <input.json>             (puts a choice or questions in the tracker for the user)
  python scripts/tracker.py answers                      (reads what the user answered in the tracker)
  python scripts/tracker.py answered <id> "summary"      (the user answered in chat: closes the input)
  python scripts/tracker.py wait-answer [<id>] [--timeout <s>]   (run in background: exits on the answer)
  python scripts/tracker.py render
Add --slug <slug> to target another product.

An input (work/<slug>/inputs/<id>.json): {"id": "GP", "kind": "choice" | "questions" | "confirm",
  "title": "...", "detail": "...", "gate": "GP",
  "options": [{"id": "A", "label": "...", "detail": "...", "recommended": true}],
  "items": [{"id": "Q84", "q": "...", "rec": "recommended answer"}],
  "links": [{"label": "Open the prototype", "href": "P-prototype.html"}]}
Send in the tracker saves the answer as a download (factory-answer-<slug>-<id>.json in Downloads, or
factory.json "downloads_dir"); answers / wait-answer move it to work/<slug>/answers/<id>.json. Agents never
write either file.
"""
import csv
import datetime
import time
import json
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORK = os.path.join(ROOT, "work")


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def teams():
    with open(os.path.join(ROOT, "scripts", "teams.json"), encoding="utf-8") as f:
        return json.load(f)


def active_slug():
    p = os.path.join(WORK, ".active")
    if os.path.isfile(p):
        with open(p, encoding="utf-8") as f:
            return f.read().strip()
    return ""


def paths(slug):
    d = os.path.join(WORK, slug)
    return d, os.path.join(d, "tracker.json"), os.path.join(d, "tracker.html"), os.path.join(d, "status.md")


def load(slug):
    _, js, _, _ = paths(slug)
    if os.path.isfile(js):
        with open(js, encoding="utf-8") as f:
            return json.load(f)
    t = teams()
    return {"slug": slug, "name": slug, "stage": "S0", "stageNote": "", "waiting": "",
            "gates": {g["id"]: {"state": "open", "words": "", "at": ""} for g in t["gates"]},
            "runs": [], "log": [], "created": now(), "updated": now()}


def save(slug, state):
    d, js, _, _ = paths(slug)
    os.makedirs(d, exist_ok=True)
    state["updated"] = now()
    with open(js, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    render(slug, state)


def log(state, text):
    state["log"].insert(0, {"at": now(), "text": text})
    del state["log"][60:]


def team_of(agent):
    for t in teams()["teams"]:
        if agent in t["agents"]:
            return t["name"]
    return "Other"


def set_status_line(slug, key, value):
    _, _, _, st = paths(slug)
    if not os.path.isfile(st):
        return
    with open(st, encoding="utf-8", newline="") as f:
        text = f.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    pat = re.compile(r"^(" + re.escape(key) + r"):.*$", re.M)
    text = pat.sub(lambda m: m.group(1) + ": " + value, text, count=1) if pat.search(text) \
        else text + nl + key + ": " + value + nl
    with open(st, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def set_gate_line(slug, gid, value):
    _, _, _, st = paths(slug)
    if not os.path.isfile(st):
        return
    with open(st, encoding="utf-8", newline="") as f:
        text = f.read()
    text = re.sub(r"^(- " + gid + r" [^:\n]*):.*$", lambda m: m.group(1) + ": " + value, text, count=1, flags=re.M)
    with open(st, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def agent_start(state, agent, task):
    state["runs"].insert(0, {"agent": agent, "team": team_of(agent), "task": task, "status": "working",
                             "stage": state["stage"], "startedAt": now(), "doneAt": "", "result": ""})
    log(state, "%s started: %s" % (agent, task or "-"))


def agent_done(state, agent, result, failed=False):
    for r in state["runs"]:
        if r["agent"] == agent and r["status"] == "working":
            r.update(status="failed" if failed else "done", doneAt=now(), result=result)
            break
    else:
        state["runs"].insert(0, {"agent": agent, "team": team_of(agent), "task": "", "startedAt": now(),
                                 "status": "failed" if failed else "done", "doneAt": now(), "result": result})
    log(state, "%s %s%s" % (agent, "failed" if failed else "finished", (": " + result) if result else ""))


# ---------- page ----------
# tracker.html is a fixed page (scripts/tracker_page.html); it reloads tracker-data.js every 3 s, so the page
# never flickers and works offline from file://. The data file carries the state plus counts read from the docs.

STAGE_OF = [("00-", "S0"), ("01-", "S0"), ("10-", "S1"), ("02-", "S2"), ("03-", "S3"), ("P-", "SP"), ("04-", "S4"),
            ("05-", "S5"), ("adr/", "S5"), ("06-", "S6"), ("07-", "S7"), ("08-", "S8"), ("09-", "S9")]


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def outputs(slug):
    d = paths(slug)[0]
    docs, by_stage = 0, {}
    for root, _, files in os.walk(d):
        for name in files:
            rel = os.path.relpath(os.path.join(root, name), d).replace("\\", "/")
            if not (rel.endswith((".md", ".yaml", ".csv")) or rel == "P-prototype.html"):
                continue
            stage = next((s for p, s in STAGE_OF if rel.startswith(p)), None)
            if stage:
                docs += 1
                by_stage[stage] = by_stage.get(stage, 0) + 1
    stories, points = 0, 0
    for cells in list(csv.reader(read(os.path.join(d, "04-backlog.csv")).splitlines()))[1:]:
        if len(cells) > 3 and cells[0].strip():
            stories += 1
            points += int(cells[3]) if cells[3].strip().isdigit() else 0
    adr = os.path.join(d, "adr")
    out = {"docs": docs,
           "questions": len(re.findall(r"^- \[\w+\] Q\d+", read(os.path.join(d, "questions.md")), re.M)),
           "criteria": read(os.path.join(d, "02-spec.md")).count("Given "),
           "stories": stories, "points": points,
           "ops": read(os.path.join(d, "05-openapi.yaml")).count("operationId:"),
           "decisions": len(re.findall(r"^- D\d+", read(os.path.join(d, "decisions.md")), re.M)),
           "adrs": len([f for f in os.listdir(adr) if f.endswith(".md")]) if os.path.isdir(adr) else 0}
    return out, by_stage


def write_atomic(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def render(slug, state):
    d, _, page, _ = paths(slug)
    t = teams()
    out, by_stage = outputs(slug)
    data = dict(state, log=state["log"][:40], teams=t["teams"], stages=t["stages"], gateDefs=t["gates"],
                outputs=out, stageDocs=by_stage, activity=load_activity(slug))
    write_atomic(os.path.join(d, "tracker-data.js"),
                 "window.__TRACKER__(%s);\n" % json.dumps(data, ensure_ascii=False))
    tpl = read(os.path.join(ROOT, "scripts", "tracker_page.html"))
    if tpl and read(page) != tpl:
        write_atomic(page, tpl)


def activity_path(slug):
    return os.path.join(paths(slug)[0], "tracker-activity.json")


def load_activity(slug):
    try:
        return json.loads(read(activity_path(slug)) or "{}")
    except ValueError:
        return {}


def set_activity(slug, agent, text):
    """What an agent is doing right now ('Reading 05-openapi.yaml'). Kept apart from tracker.json so the
    frequent writes from tool hooks never race with stage, gate and run updates."""
    act = load_activity(slug)
    act[agent] = {"text": text[:140], "at": now()}
    write_atomic(activity_path(slug), json.dumps(act, ensure_ascii=False))


# ---------- input from the user, answered in the tracker ----------

def answers_dir(slug):
    return os.path.join(paths(slug)[0], "answers")


def ask(slug, state, spec_path):
    with open(spec_path, encoding="utf-8") as f:
        item = json.load(f)
    if not item.get("id") or item.get("kind") not in ("choice", "questions", "confirm"):
        sys.exit("an input needs an id and a kind of choice, questions or confirm")
    old = os.path.join(answers_dir(slug), item["id"] + ".json")
    if os.path.isfile(old):  # asking again: the earlier answer is kept under a new name
        os.replace(old, old[:-5] + ".%s.json" % now().replace(":", "")[:17])
    item.update(status="open", askedAt=now(), answer=None, answeredAt="")
    state.setdefault("inputs", [])
    state["inputs"] = [i for i in state["inputs"] if i["id"] != item["id"]] + [item]
    state["waiting"] = item.get("title", "")
    if item.get("gate"):
        state["gates"][item["gate"]] = {"state": "waiting", "words": "", "at": now()}
    log(state, "waiting on you: " + item.get("title", item["id"]))


def downloads_dir():
    with open(os.path.join(ROOT, ".claude", "factory.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    return os.path.expanduser(cfg.get("downloads_dir") or "~/Downloads")


def import_downloads(slug, state):
    """The page saves an answer as a download, factory-answer-<slug>-<id>.json (Chrome adds ' (1)' on repeats);
    the newest one for each open input moves into work/<slug>/answers/<id>.json."""
    src = downloads_dir()
    if not os.path.isdir(src):
        return
    for item in state.get("inputs", []):
        if item["status"] != "open":
            continue
        prefix = "factory-answer-%s-%s" % (slug, item["id"])
        found = [os.path.join(src, n) for n in os.listdir(src)
                 if n.startswith(prefix) and n.endswith(".json") and re.fullmatch(r"( \(\d+\))?", n[len(prefix):-5])]
        found = [p for p in found if os.path.getmtime(p) >= datetime.datetime.fromisoformat(item["askedAt"]).timestamp()]
        if not found:
            continue
        os.makedirs(answers_dir(slug), exist_ok=True)
        newest = max(found, key=os.path.getmtime)
        shutil.move(newest, os.path.join(answers_dir(slug), item["id"] + ".json"))  # Downloads may be on another drive
        for p in found:
            if p != newest and os.path.isfile(p):
                os.remove(p)


def collect_answers(slug, state):
    import_downloads(slug, state)
    got = []
    for item in state.get("inputs", []):
        p = os.path.join(answers_dir(slug), item["id"] + ".json")
        if item["status"] != "open" or not os.path.isfile(p):
            continue
        try:
            ans = json.loads(read(p))
        except ValueError:
            continue
        item.update(status="answered", answer=ans, answeredAt=ans.get("at") or now())
        said = ans.get("choice") or ans.get("text") or "%d answers" % len(ans.get("items") or {})
        log(state, "you answered %s: %s" % (item["id"], said))
        got.append({"id": item["id"], "gate": item.get("gate", ""), "answer": ans})
    if got and not any(i["status"] == "open" for i in state.get("inputs", [])):
        state["waiting"] = ""
    return got


def wait_answer(slug, args):
    timeout = 3600
    if "--timeout" in args:
        timeout = int(args[args.index("--timeout") + 1])
        args = [a for a in args if a not in ("--timeout", str(timeout))]
    want = args[0] if args else ""
    end = time.time() + timeout
    while time.time() < end:
        st = load(slug)
        import_downloads(slug, st)
        ready = [i for i in st.get("inputs", []) if i["status"] == "open" and (not want or i["id"] == want)
                 and os.path.isfile(os.path.join(answers_dir(slug), i["id"] + ".json"))]
        if ready:
            got = collect_answers(slug, st)
            save(slug, st)
            print(json.dumps(got, indent=2, ensure_ascii=False))
            return 0
        time.sleep(3)
    print("no answer after %d s" % timeout)
    return 2


def main(argv):
    slug = active_slug()
    if "--slug" in argv:
        i = argv.index("--slug")
        slug = argv[i + 1]
        del argv[i:i + 2]
    failed = "--failed" in argv
    argv = [a for a in argv if a != "--failed"]
    if not slug or len(argv) < 1:
        print(__doc__)
        return 1
    cmd, args = argv[0], argv[1:]
    st = load(slug)
    if cmd == "stage":
        st["stage"], st["stageNote"] = args[0], " ".join(args[1:])
        set_status_line(slug, "stage", args[0] + (" " + " ".join(args[1:]) if args[1:] else ""))
        log(st, "stage %s %s" % (args[0], " ".join(args[1:])))
    elif cmd == "gate":
        gid, value, words = args[0], args[1], " ".join(args[2:])
        st["gates"][gid] = {"state": value, "words": words, "at": now()}
        set_gate_line(slug, gid, value + (' - "%s"' % words if words else ""))
        log(st, "gate %s %s%s" % (gid, value, (' - "%s"' % words) if words else ""))
    elif cmd == "code":
        set_status_line(slug, "code_writes", args[0])
        log(st, "code writes " + args[0])
    elif cmd == "note":
        log(st, " ".join(args))
    elif cmd == "wait":
        st["waiting"] = "" if args[:1] == ["--clear"] else " ".join(args)
        if st["waiting"]:
            log(st, "waiting on user: " + st["waiting"])
    elif cmd == "agent-start":
        agent_start(st, args[0], " ".join(args[1:]))
    elif cmd == "agent-done":
        agent_done(st, args[0], " ".join(args[1:]), failed)
    elif cmd == "act":
        set_activity(slug, args[0], " ".join(args[1:]))
        render(slug, st)
        return 0
    elif cmd == "ask":
        ask(slug, st, args[0])
    elif cmd == "answers":
        got = collect_answers(slug, st)
        print(json.dumps(got, indent=2, ensure_ascii=False) if got else "no new answers")
        if not got:
            return 0
    elif cmd == "answered":  # the user answered in chat instead of the tracker
        for item in st.get("inputs", []):
            if item["id"] == args[0] and item["status"] == "open":
                item.update(status="answered", answer={"text": " ".join(args[1:]), "via": "chat"}, answeredAt=now())
                log(st, "you answered %s in chat: %s" % (args[0], " ".join(args[1:])))
        if not any(i["status"] == "open" for i in st.get("inputs", [])):
            st["waiting"] = ""
    elif cmd == "wait-answer":
        return wait_answer(slug, args)
    elif cmd != "render":
        print(__doc__)
        return 1
    save(slug, st)
    print("tracker: " + paths(slug)[2])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
