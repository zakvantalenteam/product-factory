"""Install or update the agent core in a repo (the Claude Code plugin is built by build_plugin.py).

  python <core>/scripts/install.py <repo> [--dry-run] [--adopt] [--write-settings] [--project-name NAME]
  python <core>/scripts/install.py <repo> --check        (also works from the repo's own .claude/core/scripts/)

Run it from the core source (the product-factory repo: <product-factory>/core/scripts/install.py). It copies
  core agents/*.md       -> <repo>/.claude/agents/
  core skills/<name>/    -> <repo>/.claude/skills/<name>/
  core hooks, scripts, reference, templates, VERSION -> <repo>/.claude/core/
and records every file with its hash in <repo>/.claude/core/core.lock. On an update it never overwrites a core file
that was edited by hand in the repo (it lists it: move that fix into the core) and removes core files the new
version dropped (when unchanged). A repo file with a core name that the core does not own yet (e.g. the repo's own
code-reviewer.md) is left alone unless --adopt is given; adopted and replaced files are first copied to
<repo>/.claude/core-backup/<date>/.

It also: writes a starter .claude/project.json, .claude/smoke.md and .claude/review/lessons.md when there are none; adds or refreshes the core block in AGENTS.md
(between <!-- core:start --> and <!-- core:end -->) and creates CLAUDE.md (@AGENTS.md) when missing; adds the work
folder to .gitignore; shows the core hook entries for .claude/settings.json and the live-status entry for
.claude/launch.json, and writes them with --write-settings (old copies of the core hooks are replaced, and the
product-factory plugin is switched off in the repo, which carries the core itself, so no hook runs twice); then runs
cursor_sync.py in the repo. Installing into the core's home repo (the folder above core/ with
.claude-plugin/marketplace.json) also rebuilds the plugin there (build_plugin.py).

--check lists core files edited by hand or missing, an older installed version than this core, missing hook entries
and stale Cursor copies; exit 1 when anything is wrong.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
CORE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
INSTALLED = os.path.basename(CORE) == "core" and os.path.basename(os.path.dirname(CORE)) == ".claude"
SKIP_NAMES = {"__pycache__", "core-plan.md", ".claude-plugin", "hooks.json", "session_start.py", "build_plugin.py"}
PLUGIN_ID = "product-factory@talenteam"  # plugin@marketplace, as in the home repo's .claude-plugin/marketplace.json
OLD_PLUGIN_IDS = ("agent-core@talenteam",)  # the plugin's name before 1.4.0: its settings entry is removed
BLOCK_START, BLOCK_END = "<!-- core:start -->", "<!-- core:end -->"
# hook scripts the core replaces: entries running these are old copies and are swapped for the core ones
OLD_HOOKS = re.compile(r"(guard|flow_check|rules_check|flow_guard|intake_guard|factory_tracker)\.py|live_status\.py\" hook"
                       r"|live_status\.py hook")


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read().replace(b"\r\n", b"\n")).hexdigest()[:16]


def version(core_dir):
    try:
        with open(os.path.join(core_dir, "VERSION"), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return "0"


def core_files():
    """{repo-relative destination: absolute source} for every file the core installs."""
    out = {}
    for top, dest in (("agents", ".claude/agents"), ("skills", ".claude/skills"), ("hooks", ".claude/core/hooks"),
                      ("scripts", ".claude/core/scripts"), ("reference", ".claude/core/reference"),
                      ("templates", ".claude/core/templates")):
        base = os.path.join(CORE, top)
        for d, dirs, files in os.walk(base):
            dirs[:] = [x for x in dirs if x not in SKIP_NAMES]
            for name in files:
                if name in SKIP_NAMES or name.endswith(".pyc"):
                    continue
                src = os.path.join(d, name)
                out[dest + "/" + os.path.relpath(src, base).replace("\\", "/")] = src
    out[".claude/core/VERSION"] = os.path.join(CORE, "VERSION")
    return out


def load_lock(repo):
    try:
        with open(os.path.join(repo, ".claude", "core", "core.lock"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"version": "", "files": {}}


def read(p):
    try:
        with open(p, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def write(p, text, newline="\n"):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline=newline) as f:
        f.write(text)


def repo_newline(repo):
    try:
        with open(os.path.join(repo, ".claude", "project.json"), encoding="utf-8") as f:
            return "\r\n" if str(json.load(f).get("newline", "lf")).lower() == "crlf" else "\n"
    except (OSError, ValueError):
        return "\n"


def copy_text(src, dst, newline):
    """Copy keeping text files in the repo's line endings (binary files byte for byte)."""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(src, "rb") as f:
        data = f.read()
    try:
        text = data.decode("utf-8").replace("\r\n", "\n")
    except UnicodeDecodeError:
        with open(dst, "wb") as f:
            f.write(data)
        return
    with open(dst, "w", encoding="utf-8", newline=newline) as f:
        f.write(text)


# ---- settings -------------------------------------------------------------------------------------------------

def core_hooks():
    with open(os.path.join(CORE, "templates", "settings-hooks.json"), encoding="utf-8") as f:
        return json.load(f)


def is_core_entry(entry):
    return any(OLD_HOOKS.search(h.get("command", "")) or ".claude/core/" in h.get("command", "")
               for h in entry.get("hooks") or [])


def merged_settings(current):
    s = json.loads(json.dumps(current or {}))
    want = core_hooks()
    hooks = s.setdefault("hooks", {})
    for event in list(hooks):
        hooks[event] = [e for e in hooks[event] if not is_core_entry(e)]
        if not hooks[event]:
            del hooks[event]
    for event, entries in want["hooks"].items():
        hooks.setdefault(event, [])
        hooks[event] = entries + hooks[event]
    perms = s.setdefault("permissions", {})
    allow = perms.setdefault("allow", [])
    for a in want.get("allow", []):
        if a not in allow:
            allow.append(a)
    s.setdefault("env", {}).update({k: v for k, v in want.get("env", {}).items() if k not in s["env"]})
    plugins = s.setdefault("enabledPlugins", {})
    for old in OLD_PLUGIN_IDS:
        plugins.pop(old, None)
    plugins[PLUGIN_ID] = False  # the repo carries the core: the plugin would repeat it
    return s


def settings_missing(repo):
    s = json.loads(read(os.path.join(repo, ".claude", "settings.json")) or "{}")
    have = {h.get("command") for es in (s.get("hooks") or {}).values() for e in es for h in e.get("hooks") or []}
    need = [h["command"] for es in core_hooks()["hooks"].values() for e in es for h in e["hooks"]]
    return sorted({c for c in need if c not in have})


def plugin_left_on(repo):
    s = json.loads(read(os.path.join(repo, ".claude", "settings.json")) or "{}")
    return (s.get("enabledPlugins") or {}).get(PLUGIN_ID) is not False


def launch_entry(port):
    return {"name": "live-status", "runtimeExecutable": "python",
            "runtimeArgs": [".claude/core/scripts/live_status.py", "serve"], "port": port,
            "url": "http://localhost:%d" % port}


def merged_launch(current, port):
    s = json.loads(json.dumps(current or {"version": "0.0.1", "configurations": []}))
    confs = [c for c in s.setdefault("configurations", []) if c.get("name") != "live-status"]
    s["configurations"] = confs + [launch_entry(port)]
    return s


# ---- AGENTS.md ------------------------------------------------------------------------------------------------

def core_block():
    text = read(os.path.join(CORE, "templates", "AGENTS-core.md")) or ""
    return BLOCK_START + "\n" + text.strip() + "\n" + BLOCK_END


def agents_md(current, name):
    block = core_block()
    if current is None:
        return "# %s\n\n<Stack, build and run, repo map and hard rules of this repo.>\n\n%s\n" % (name or "Project", block)
    cur = current.replace("\r\n", "\n")
    if BLOCK_START in cur and BLOCK_END in cur:
        a, b = cur.index(BLOCK_START), cur.index(BLOCK_END) + len(BLOCK_END)
        return cur[:a] + block + cur[b:]
    return cur.rstrip("\n") + "\n\n" + block + "\n"


# ---- main -----------------------------------------------------------------------------------------------------

def run_sync(repo, check):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=repo, PYTHONDONTWRITEBYTECODE="1")
    args = [sys.executable, os.path.join(repo, ".claude", "core", "scripts", "cursor_sync.py")] + (["--check"] if check else [])
    if not os.path.isfile(args[1]):
        return 1, "cursor_sync.py is not installed"
    p = subprocess.run(args, cwd=repo, env=env, capture_output=True, text=True, encoding="utf-8")
    return p.returncode, (p.stdout + p.stderr).strip()


def check(repo):
    problems = []
    lock = load_lock(repo)
    if not lock["files"]:
        print("not installed: no .claude/core/core.lock")
        return 1
    for rel, h in sorted(lock["files"].items()):
        p = os.path.join(repo, rel)
        if not os.path.isfile(p):
            problems.append("missing   " + rel)
        elif sha(p) != h:
            problems.append("edited    " + rel + "  (core-owned: move the change into the core)")
    if not INSTALLED and version(CORE) != lock.get("version"):
        problems.append("version   installed %s, core %s: run install.py to update" % (lock.get("version"), version(CORE)))
    for c in settings_missing(repo):
        problems.append("settings  missing hook: " + c)
    if plugin_left_on(repo):
        problems.append('settings  the plugin is not switched off: "enabledPlugins": {"%s": false} (--write-settings)' % PLUGIN_ID)
    if BLOCK_START not in (read(os.path.join(repo, "AGENTS.md")) or ""):
        problems.append("AGENTS.md has no core block")
    rc, out = run_sync(repo, True)
    if rc:
        problems.append("cursor    " + out.replace("\n", "; "))
    for p in problems:
        print(p)
    print("ok (core %s)" % lock.get("version") if not problems else "%d problem(s)" % len(problems))
    return 1 if problems else 0


def install(repo, a):
    nl = repo_newline(repo)
    lock = load_lock(repo)
    want = core_files()
    stamp = datetime.date.today().isoformat()
    backup = os.path.join(repo, ".claude", "core-backup", stamp)
    done = {"new": [], "updated": [], "kept (edited by hand)": [], "skipped (repo's own file)": [], "adopted": [],
            "removed": [], "same": []}
    new_lock = {"version": version(CORE), "files": {}}

    def save_backup(rel):
        if not a.dry_run:
            dst = os.path.join(backup, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(repo, rel), dst)

    for rel, src in sorted(want.items()):
        dst = os.path.join(repo, rel)
        exists = os.path.isfile(dst)
        owned = rel in lock["files"]
        if exists and owned and sha(dst) != lock["files"][rel] and not a.adopt:
            done["kept (edited by hand)"].append(rel)
            new_lock["files"][rel] = lock["files"][rel]
            continue
        if exists and not owned and sha(dst) != sha(src):
            if not a.adopt:
                done["skipped (repo's own file)"].append(rel)
                continue
            save_backup(rel)
            done["adopted"].append(rel)
        elif exists and sha(dst) == sha(src):
            done["same"].append(rel)
        else:
            done["updated" if exists else "new"].append(rel)
        if not a.dry_run:
            copy_text(src, dst, nl)
        new_lock["files"][rel] = sha(src)
    for rel, h in lock["files"].items():
        if rel not in want:
            p = os.path.join(repo, rel)
            if os.path.isfile(p) and sha(p) == h:
                done["removed"].append(rel)
                if not a.dry_run:
                    os.remove(p)
            elif os.path.isfile(p):
                done["kept (edited by hand)"].append(rel + " (dropped by the core)")
    if not a.dry_run:
        write(os.path.join(repo, ".claude", "core", "core.lock"), json.dumps(new_lock, indent=1, sort_keys=True) + "\n")

    # project layer starters (never overwritten)
    pj = os.path.join(repo, ".claude", "project.json")
    if not os.path.isfile(pj):
        cfg = json.loads(read(os.path.join(CORE, "templates", "project.json")))
        cfg["name"] = a.project_name or os.path.basename(os.path.abspath(repo))
        print("project.json: starter written (fill in commands, protected paths, decisions, rules)")
        if not a.dry_run:
            write(pj, json.dumps(cfg, indent=2) + "\n", nl)
    for rel, tpl in ((".claude/smoke.md", "smoke.md"), (".claude/review/lessons.md", "lessons.md")):
        dst = os.path.join(repo, *rel.split("/"))
        if not os.path.isfile(dst):
            print("%s: starter written (the project fills it)" % rel)
            if not a.dry_run:
                write(dst, read(os.path.join(CORE, "templates", tpl)), nl)
    name = a.project_name or json.loads(read(pj) or "{}").get("name", "")
    am = os.path.join(repo, "AGENTS.md")
    new_am = agents_md(read(am), name)
    if new_am != (read(am) or "").replace("\r\n", "\n"):
        print("AGENTS.md: core block " + ("added" if BLOCK_START not in (read(am) or "") else "refreshed"))
        if not a.dry_run:
            write(am, new_am, nl)
    cm = os.path.join(repo, "CLAUDE.md")
    if not os.path.isfile(cm):
        print("CLAUDE.md: created (@AGENTS.md)")
        if not a.dry_run:
            write(cm, "Project instructions live in AGENTS.md, shared with Cursor. Claude Code loads them through "
                      "this import:\n\n@AGENTS.md\n", nl)

    # .gitignore
    try:
        work = json.loads(read(pj) or "{}").get("work_dir", ".claude/work")
    except ValueError:
        work = ".claude/work"
    gi = os.path.join(repo, ".gitignore")
    cur = read(gi) or ""
    w = work.strip("/")
    # a work folder inside .claude/ is local scratch; one outside it (product-factory's work/) holds product records
    # worth keeping in git, so only its runtime files are ignored
    ignore = [w + "/"] if w.startswith(".claude/") else [w + "/.sessions/", w + "/live.js", w + "/live.html",
                                                          w + "/*/status.js", w + "/*/events.jsonl",
                                                          w + "/simulate.html", w + "/demo-*/"]
    add = [l for l in ignore + [".claude/core-backup/", "__pycache__/"] if l not in cur.splitlines()]
    if add:
        print(".gitignore: + " + ", ".join(add))
        if not a.dry_run:
            write(gi, cur.rstrip("\n") + ("\n" if cur else "") + "\n".join(add) + "\n", nl)

    # settings.json and launch.json
    sp = os.path.join(repo, ".claude", "settings.json")
    cur_s = json.loads(read(sp) or "{}")
    new_s = merged_settings(cur_s)
    lp = os.path.join(repo, ".claude", "launch.json")
    cur_l = json.loads(read(lp) or "null")
    try:
        port = int(json.loads(read(pj) or "{}").get("live_port", 8766))
    except (ValueError, TypeError):
        port = 8766
    new_l = merged_launch(cur_l, port)
    if new_s != cur_s or new_l != cur_l:
        if a.write_settings and not a.dry_run:
            if os.path.isfile(sp):
                save_backup(".claude/settings.json")
            write(sp, json.dumps(new_s, indent=2) + "\n", nl)
            write(lp, json.dumps(new_l, indent=2) + "\n", nl)
            print("settings.json, launch.json: core hooks and live-status entry written (backup in core-backup/)")
        else:
            print("settings.json / launch.json need the core entries; rerun with --write-settings, or add:")
            print(json.dumps({"hooks": core_hooks()["hooks"]}, indent=1)[:3000])

    for k, v in done.items():
        if v and k != "same":
            print("%-26s %d: %s" % (k, len(v), ", ".join(v[:8]) + (" ..." if len(v) > 8 else "")))
    print("core %s -> %s: %d files, %d unchanged" % (lock.get("version") or "-", new_lock["version"], len(want),
                                                    len(done["same"])))
    home = os.path.dirname(CORE)
    if os.path.abspath(repo) == home and os.path.isfile(os.path.join(home, ".claude-plugin", "marketplace.json")) \
            and not a.dry_run:
        p = subprocess.run([sys.executable, os.path.join(CORE, "scripts", "build_plugin.py")], capture_output=True,
                           text=True, encoding="utf-8")
        print((p.stdout + p.stderr).strip().splitlines()[-1] if (p.stdout + p.stderr).strip() else "plugin: built")
    if not a.dry_run:
        rc, out = run_sync(repo, False)
        print("cursor_sync: " + out.splitlines()[-1] if out else "cursor_sync: done")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("repo")
    p.add_argument("--check", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--adopt", action="store_true", help="replace the repo's own files that have core names")
    p.add_argument("--write-settings", action="store_true")
    p.add_argument("--project-name", default="")
    a = p.parse_args()
    repo = os.path.abspath(a.repo)
    if not os.path.isdir(repo):
        sys.exit("no such folder: " + repo)
    if a.check:
        sys.exit(check(repo))
    if INSTALLED:
        sys.exit("This is an installed copy of the core; install and update from the core source "
                 "(from the product-factory repo: python core/scripts/install.py <repo>). --check works here.")
    sys.exit(install(repo, a))


if __name__ == "__main__":
    main()
