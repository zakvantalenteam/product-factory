"""Install or update the agent core in a repo (the Claude Code plugin is built by build_plugin.py).

  python <core>/scripts/install.py <repo> [--dry-run] [--adopt] [--write-settings] [--project-name NAME]
  python <core>/scripts/install.py <repo> --check        (also works from the repo's own .claude/core/scripts/)
  python <core>/scripts/install.py <repo> --switch-to-plugin [--dry-run] [--force] [--marketplace-url URL]

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

--check lists core files edited by hand or missing, an older installed version than this core, missing hook entries,
missing Read deny rules, skill and agent headers that are not valid YAML and stale Cursor copies; exit 1 when
anything is wrong. In a repo switched to the plugin it checks that layout instead (plugin on, marketplace entry, no
core hooks or core copies left, the Cursor copy in step).

Read deny rules: --write-settings adds a native `permissions.deny` rule `Read(//**/<glob>)` (the Windows-safe form)
for each `guard.secret_files` and `guard.no_read` glob of .claude/project.json, so Claude Code refuses those reads
before any hook runs; the guard no longer runs on Read (Cursor's beforeReadFile hook still does).

--switch-to-plugin moves a repo that carries the core onto the Claude Code plugin in one change (so no hook runs twice
and no skill shows twice): it removes every file of .claude/core/core.lock and the .claude/core/ folder, drops the
core hook entries from .claude/settings.json, writes `extraKnownMarketplaces` (with autoUpdate) and
`enabledPlugins: true` from templates/plugin-source.json (--marketplace-url overrides the git URL), points the core
paths in AGENTS.md, CLAUDE.md, .claude/ text files, the forwarder shims, the allow rules and launch.json at the
generated core copy in .cursor/runtime/, and regenerates .cursor/ (cursor_sync.py of this core: agents, skills and
the whole core for Cursor). It stops when a core file was edited by hand (--force drops those edits). Old files go to
.claude/core-backup/<date>/. --dry-run lists what it would do.
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
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import project  # noqa: E402

CORE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
# an installed copy (.claude/core) or the generated Cursor copy (.cursor/runtime): --check only
INSTALLED = (os.path.basename(CORE), os.path.basename(os.path.dirname(CORE))) in (("core", ".claude"),
                                                                                 ("runtime", ".cursor"))
RUNTIME = ".cursor/runtime/"  # the generated core copy in a repo switched to the plugin (cursor_sync.py)
REVERSE = (b"${CLAUDE_PLUGIN_ROOT}/", b".claude/core/")  # installing from the plugin: its paths back to the repo's
SKIP_NAMES = {"__pycache__", "core-plan.md", "exam-scores.json", ".claude-plugin", "hooks.json", "session_start.py", "build_plugin.py"}
PLUGIN_ID = "product-factory@talenteam"  # plugin@marketplace, as in the home repo's .claude-plugin/marketplace.json
OLD_PLUGIN_IDS = ("agent-core@talenteam",)  # the plugin's name before 1.4.0: its settings entry is removed
BLOCK_START, BLOCK_END = "<!-- core:start -->", "<!-- core:end -->"
# hook scripts the core replaces: entries running these are old copies and are swapped for the core ones
OLD_HOOKS = re.compile(r"(guard|flow_check|rules_check|flow_guard|intake_guard|factory_tracker)\.py|live_status\.py\" hook"
                       r"|live_status\.py hook")


def sha(path):
    with open(path, "rb") as f:
        return sha_bytes(f.read())


def sha_bytes(data):
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()[:16]


def src_data(src):
    """The bytes a core file lands with in a repo: markdown from the plugin gets its `.claude/core/` paths back."""
    with open(src, "rb") as f:
        data = f.read()
    return data.replace(*REVERSE) if src.endswith(".md") else data


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
    data = src_data(src)
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


def deny_rule(glob):
    g = glob.strip().replace("\\", "/")
    return "Read(//**/%s)" % (g[3:] if g.startswith("**/") else g.lstrip("/"))


def read_denies(repo):
    """Native Read deny rules for the project's secret files and no-read paths: Claude Code refuses those reads before
    any hook runs (no Python process per Read). A glob anywhere in the tree, in the `//**/` form Windows needs."""
    try:
        g = json.loads(read(os.path.join(repo, ".claude", "project.json")) or "{}").get("guard") or {}
    except ValueError:
        return []
    globs = list(g.get("secret_files") or []) + [p for nr in g.get("no_read") or [] for p in nr.get("paths") or []]
    return list(dict.fromkeys(deny_rule(x) for x in globs if x.strip()))


def project_cfg(repo):
    try:
        return json.loads(read(os.path.join(repo, ".claude", "project.json")) or "{}") if repo else {}
    except ValueError:
        return {}


def want_permissions(repo, switched=False):
    """The permissions every project gets, from templates/settings-permissions.json plus the project's secret and
    no-read paths: (allow, deny, replace). Switched: core paths point at the generated copy in .cursor/runtime/."""
    t = json.loads(read(os.path.join(CORE, "templates", "settings-permissions.json")) or "{}")
    cfg = project_cfg(repo)
    work = (cfg.get("work_dir") or ".claude/work").replace("\\", "/").strip("/")
    fix = lambda r: r.replace(".claude/core/", RUNTIME) if switched else r
    allow = [fix(r.replace("{work_dir}", work)) for r in t.get("allow") or []
             if "{work_dir}" not in r or not (os.path.isabs(work) or ":" in work)]
    secret = [x for x in (cfg.get("guard") or {}).get("secret_files") or [] if x.strip()]
    deny = [fix(r) for r in t.get("deny") or []] + (read_denies(repo) if repo else [])
    deny += [d for d in dict.fromkeys(deny_rule(x).replace("Read(", "Edit(", 1) for x in secret) if d not in deny]
    return allow, deny, t.get("replace") or {}


def apply_permissions(s, repo, switched=False):
    """Adds the template's rules (keeping the project's own) and drops the broad forms it replaces."""
    allow, deny, replace = want_permissions(repo, switched)
    perms = s.setdefault("permissions", {})
    for key, want in (("allow", allow), ("deny", deny)):
        have = [r for r in perms.get(key) or [] if r not in replace]
        perms[key] = have + [r for r in want if r not in have]


def permission_problems(repo, how, switched=False):
    s = json.loads(read(os.path.join(repo, ".claude", "settings.json")) or "{}")
    perms = s.get("permissions") or {}
    allow, deny, replace = want_permissions(repo, switched)
    out = []
    for key, want in (("allow", allow), ("deny", deny)):
        have = perms.get(key) or []
        out += ["settings  %s rule %s is broader than read-only: use %s (%s)" % (key, r, " and ".join(replace[r]), how)
                for r in have if r in replace]
        out += ["settings  missing %s rule %s (%s)" % (key, r, how) for r in want if r not in have]
    return out


def plugin_scripts_rules(src):
    """After the switch Claude runs the core scripts from the plugin cache, a versioned folder under the user's
    config: a user-level allow rule for that folder replaces the dead `.claude/core/scripts/*` rule."""
    base = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    name = (src.get("plugin") or PLUGIN_ID).split("@")[0]
    root = os.path.join(base, "plugins", "cache", src["marketplace"], name).replace("\\", "/")
    return ["Bash(python %s/*)" % root, "Bash(python -I %s/*)" % root]


def user_settings_path(a):
    if a is not None and getattr(a, "user_settings", ""):
        return os.path.abspath(a.user_settings)
    base = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    return os.path.join(base, "settings.json")


def front_files(repo):
    out = []
    for d in ("agents", "skills"):
        folder = os.path.join(repo, ".claude", d)
        for name in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
            rel = ".claude/%s/%s%s" % (d, name, "/SKILL.md" if d == "skills" else "")
            if rel.endswith(".md") and os.path.isfile(os.path.join(repo, rel)):
                out.append(rel)
    return out


def header_problems(repo):
    return ["header    %s: %s" % (rel, e) for rel in front_files(repo)
            for e in project.front_errors(read(os.path.join(repo, rel)) or "")]


def merged_settings(current, repo=None):
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
    apply_permissions(s, repo)
    s.setdefault("env", {}).update({k: v for k, v in want.get("env", {}).items() if k not in s["env"]})
    plugins = s.setdefault("enabledPlugins", {})
    for old in OLD_PLUGIN_IDS:
        plugins.pop(old, None)
    plugins[PLUGIN_ID] = False  # the repo carries the core: the plugin would repeat it
    return s


def settings_missing(repo):
    s = json.loads(read(os.path.join(repo, ".claude", "settings.json")) or "{}")
    # an async hook must stay async (no wait per call), the guard must fail closed
    key = lambda ev, h, m: (ev, h.get("command"), bool(h.get("async")), h.get("onFailure"), m.get("matcher"))
    have = {key(ev, h, e) for ev, es in (s.get("hooks") or {}).items() for e in es for h in e.get("hooks") or []}
    need = [key(ev, h, e) for ev, es in core_hooks()["hooks"].items() for e in es for h in e["hooks"]]
    return sorted({"%s %s%s%s" % (ev, c[-60:], " (async)" if asy else "", " (onFailure %s)" % fail if fail else "")
                   for ev, c, asy, fail, m in need if (ev, c, asy, fail, m) not in have})


def is_switched(repo):
    """A repo that gets the core from the plugin: no in-repo core, the plugin switched on in its settings."""
    s = json.loads(read(os.path.join(repo, ".claude", "settings.json")) or "{}")
    return not load_lock(repo)["files"] and (s.get("enabledPlugins") or {}).get(PLUGIN_ID) is True


def plugin_left_on(repo):
    s = json.loads(read(os.path.join(repo, ".claude", "settings.json")) or "{}")
    return (s.get("enabledPlugins") or {}).get(PLUGIN_ID) is not False


def launch_entry(port, base=".claude/core/"):
    return {"name": "live-status", "runtimeExecutable": "python",
            "runtimeArgs": [base + "scripts/live_status.py", "serve"], "port": port,
            "url": "http://localhost:%d" % port}


def merged_launch(current, port, base=".claude/core/"):
    s = json.loads(json.dumps(current or {"version": "0.0.1", "configurations": []}))
    confs = [c for c in s.setdefault("configurations", []) if c.get("name") != "live-status"]
    s["configurations"] = confs + [launch_entry(port, base)]
    return s


# ---- AGENTS.md ------------------------------------------------------------------------------------------------

def core_block(switched=False):
    text = (read(os.path.join(CORE, "templates", "AGENTS-core.md")) or "").replace(*(x.decode() for x in REVERSE))
    if switched:  # the core comes from the plugin; Cursor and the scripts use the generated copy in .cursor/runtime/
        text = text.replace("the core agents and skills listed in `.claude/core/core.lock`",
                            "the core agents and skills of the plugin").replace(".claude/core/", RUNTIME)
        text = ("This repo gets the agent core from the Claude Code plugin product-factory; `" + RUNTIME + "`, "
                "`.cursor/agents/` and `.cursor/skills/` hold the generated copy for Cursor and the scripts "
                "(`cursor_sync.py`).\n\n" + text.strip())
    return BLOCK_START + "\n" + text.strip() + "\n" + BLOCK_END


def agents_md(current, name, switched=False):
    block = core_block(switched)
    if current is None:
        return "# %s\n\n<Stack, build and run, repo map and hard rules of this repo.>\n\n%s\n" % (name or "Project", block)
    cur = current.replace("\r\n", "\n")
    if BLOCK_START in cur and BLOCK_END in cur:
        a, b = cur.index(BLOCK_START), cur.index(BLOCK_END) + len(BLOCK_END)
        return cur[:a] + block + cur[b:]
    return cur.rstrip("\n") + "\n\n" + block + "\n"


# ---- .gitignore -----------------------------------------------------------------------------------------------

def cursor_gitignore(repo, dry_run):
    """A repo that ignores `/.cursor/*` except named folders must also share the generated Cursor runtime and skills,
    or teammates' Cursor runs hooks whose scripts are missing (no guard)."""
    gi = os.path.join(repo, ".gitignore")
    cur = read(gi)
    if not cur:
        return
    lines = cur.replace("\r\n", "\n").split("\n")
    if not any(l.strip() in ("/.cursor/*", ".cursor/*") for l in lines):
        return
    added = []
    for n in ("!/.cursor/runtime/", "!/.cursor/skills/"):
        if n not in lines and n.replace("!/", "!") not in lines:
            at = max(i for i, l in enumerate(lines) if l.strip() in ("/.cursor/*", ".cursor/*")
                     or l.strip().startswith(("!/.cursor/", "!.cursor/")))
            lines.insert(at + 1, n)
            added.append(n)
    if added:
        print(".gitignore: + " + ", ".join(added) + " (the generated Cursor runtime and skills are shared)")
        if not dry_run:
            write(gi, "\n".join(lines), repo_newline(repo))


def runtime_ignored(repo):
    """True when git ignores the generated Cursor runtime (read-only `git check-ignore`)."""
    try:
        return subprocess.run(["git", "-C", repo, "check-ignore", "-q", RUNTIME + "hooks/guard.py"],
                              capture_output=True, timeout=10).returncode == 0
    except Exception:
        return False


# ---- main -----------------------------------------------------------------------------------------------------

def run_sync(repo, check, script=None):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=repo, PYTHONDONTWRITEBYTECODE="1")
    args = [sys.executable, script or os.path.join(repo, ".claude", "core", "scripts", "cursor_sync.py")] + (
        ["--check"] if check else [])
    if not os.path.isfile(args[1]):
        return 1, "cursor_sync.py is not installed"
    p = subprocess.run(args, cwd=repo, env=env, capture_output=True, text=True, encoding="utf-8")
    return p.returncode, (p.stdout + p.stderr).strip()


def check_switched(repo):
    problems = []
    s = json.loads(read(os.path.join(repo, ".claude", "settings.json")) or "{}")
    src = plugin_source()
    if src["marketplace"] not in (s.get("extraKnownMarketplaces") or {}):
        problems.append("settings  no extraKnownMarketplaces.%s: teammates do not get the plugin" % src["marketplace"])
    left = [e for es in (s.get("hooks") or {}).values() for e in es if is_core_entry(e)]
    if left:
        problems.append("settings  %d core hook entr%s left: they run beside the plugin's (--switch-to-plugin)"
                        % (len(left), "y" if len(left) == 1 else "ies"))
    problems += permission_problems(repo, "--switch-to-plugin", switched=True)
    if runtime_ignored(repo):
        problems.append(".gitignore ignores %s: teammates' Cursor would run no guard (add !/%s)" % (RUNTIME, RUNTIME))
    for rel in front_files(repo):  # a repo copy with a core name shadows the plugin's when called by the bare name
        kind, name = rel.split("/")[1], rel.split("/")[2]
        if os.path.exists(os.path.join(CORE, kind, name)):
            problems.append("shadow    %s has a core name: it hides product-factory:%s" % (rel, name.replace(".md", "")))
    if BLOCK_START not in (read(os.path.join(repo, "AGENTS.md")) or ""):
        problems.append("AGENTS.md has no core block")
    problems += header_problems(repo)
    rc, out = run_sync(repo, True, os.path.join(CORE, "scripts", "cursor_sync.py"))
    if rc:
        problems.append("cursor    " + out.replace("\n", "; "))
    for p in problems:
        print(p)
    print("ok (plugin, core %s for Cursor)" % version(CORE) if not problems else "%d problem(s)" % len(problems))
    return 1 if problems else 0


def check(repo):
    problems = []
    lock = load_lock(repo)
    if not lock["files"] and is_switched(repo):
        return check_switched(repo)
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
    problems += permission_problems(repo, "--write-settings")
    if runtime_ignored(repo):
        problems.append(".gitignore ignores %s: teammates' Cursor would run no guard (rerun install.py)" % RUNTIME)
    if BLOCK_START not in (read(os.path.join(repo, "AGENTS.md")) or ""):
        problems.append("AGENTS.md has no core block")
    problems += header_problems(repo)
    rc, out = run_sync(repo, True)
    if rc:
        problems.append("cursor    " + out.replace("\n", "; "))
    for p in problems:
        print(p)
    print("ok (core %s)" % lock.get("version") if not problems else "%d problem(s)" % len(problems))
    return 1 if problems else 0


def install(repo, a):
    if is_switched(repo):
        sys.exit("This repo gets the core from the plugin (switched). Refresh its Cursor copy with: python %s %s"
                 % (os.path.join(CORE, "scripts", "cursor_sync.py").replace("\\", "/"), "(from the repo root)"))
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
        h_src = sha_bytes(src_data(src))
        if exists and not owned and sha(dst) != h_src:
            if not a.adopt:
                done["skipped (repo's own file)"].append(rel)
                continue
            save_backup(rel)
            done["adopted"].append(rel)
        elif exists and sha(dst) == h_src:
            done["same"].append(rel)
        else:
            done["updated" if exists else "new"].append(rel)
        if not a.dry_run:
            copy_text(src, dst, nl)
        new_lock["files"][rel] = h_src
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
    cursor_gitignore(repo, a.dry_run)
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
    new_s = merged_settings(cur_s, repo)
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


# ---- switch to the plugin -------------------------------------------------------------------------------------

def plugin_source(a=None):
    """Where teammates get the plugin (templates/plugin-source.json; --marketplace-url overrides the git URL)."""
    cfg = json.loads(read(os.path.join(CORE, "templates", "plugin-source.json")) or "{}")
    if a is not None and getattr(a, "marketplace_url", ""):
        cfg["source"] = {"source": "git", "url": a.marketplace_url}
    return cfg


def switched_settings(current, repo, src):
    s = json.loads(json.dumps(current or {}))
    hooks = s.get("hooks") or {}
    for event in list(hooks):
        hooks[event] = [e for e in hooks[event] if not is_core_entry(e)]
        if not hooks[event]:
            del hooks[event]
    if "hooks" in s and not s["hooks"]:
        del s["hooks"]
    perms = s.setdefault("permissions", {})
    perms["allow"] = list(dict.fromkeys(x.replace(".claude/core/", RUNTIME) for x in perms.get("allow") or []))
    apply_permissions(s, repo, switched=True)
    s.setdefault("extraKnownMarketplaces", {})[src["marketplace"]] = {"source": src["source"],
                                                                      "autoUpdate": bool(src.get("autoUpdate", True))}
    plugins = s.setdefault("enabledPlugins", {})
    for old in OLD_PLUGIN_IDS:
        plugins.pop(old, None)
    plugins[src.get("plugin") or PLUGIN_ID] = True
    return s


def repo_texts(repo):
    """The repo's own setup text files that may name core paths: AGENTS.md, CLAUDE.md and .claude/ text files
    (not the work folder, worktrees, backups, the core itself or settings files)."""
    try:
        work = json.loads(read(os.path.join(repo, ".claude", "project.json")) or "{}").get("work_dir", ".claude/work")
    except ValueError:
        work = ".claude/work"
    skip = {os.path.normcase(os.path.join(repo, *p.split("/"))) for p in
            (work.strip("/"), ".claude/work", ".claude/worktrees", ".claude/core-backup", ".claude/core")}
    out = [f for f in ("AGENTS.md", "CLAUDE.md") if os.path.isfile(os.path.join(repo, f))]
    for d, dirs, files in os.walk(os.path.join(repo, ".claude")):
        dirs[:] = [x for x in dirs if os.path.normcase(os.path.join(d, x)) not in skip and x != "__pycache__"]
        for f in files:
            if f.endswith((".md", ".py", ".json", ".mdc")) and f not in ("settings.json", "settings.local.json",
                                                                         "launch.json"):
                out.append(os.path.relpath(os.path.join(d, f), repo).replace("\\", "/"))
    return out


def retarget(text):
    """Core paths into the generated copy: `.claude/core/` and the forwarder shims' ("..", "core", "scripts")."""
    return (text.replace(".claude/core/", RUNTIME)
            .replace('"..", "core", "scripts"', '"..", "..", ".cursor", "runtime", "scripts"'))


def switch_to_plugin(repo, a):
    if INSTALLED:
        sys.exit("Run the switch from the core source or the plugin folder, not from the copy it removes.")
    lock = load_lock(repo)
    if not lock["files"]:
        sys.exit("no in-repo core here (no .claude/core/core.lock): nothing to switch")
    if not os.path.isfile(os.path.join(repo, ".claude", "project.json")):
        sys.exit("no .claude/project.json: the plugin does nothing in a repo without it")
    edited = [rel for rel, h in sorted(lock["files"].items())
              if os.path.isfile(os.path.join(repo, rel)) and sha(os.path.join(repo, rel)) != h]
    if edited and not a.force:
        sys.exit("core files edited by hand (move the edits into the core first, or --force to drop them):\n  "
                 + "\n  ".join(edited))
    nl = repo_newline(repo)
    src = plugin_source(a)
    stamp = datetime.date.today().isoformat()
    backup = os.path.join(repo, ".claude", "core-backup", stamp)
    plan = []

    def keep(rel):
        if not a.dry_run and os.path.isfile(os.path.join(repo, rel)):
            dst = os.path.join(backup, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(repo, rel), dst)

    # 1. the in-repo core: every locked file (core agents and skills too), then .claude/core/ itself
    gone = [rel for rel in sorted(lock["files"]) if os.path.isfile(os.path.join(repo, rel))]
    plan.append("remove    %d core files (.claude/core/, %d core agents and skill files)"
                % (len(gone), len([r for r in gone if not r.startswith(".claude/core/")])))
    if not a.dry_run:
        for rel in gone:
            if not rel.startswith(".claude/core/"):
                keep(rel)
            os.remove(os.path.join(repo, rel))
        shutil.rmtree(os.path.join(repo, ".claude", "core"), ignore_errors=True)
        for d in (".claude/agents", ".claude/skills"):
            for top, dirs, files in os.walk(os.path.join(repo, d), topdown=False):
                if not os.listdir(top) and os.path.normcase(top) != os.path.normcase(os.path.join(repo, d)):
                    os.rmdir(top)
    # 2. settings: no core hooks, the plugin on with its marketplace, Read deny rules, allow rules retargeted
    sp = os.path.join(repo, ".claude", "settings.json")
    cur_s = json.loads(read(sp) or "{}")
    new_s = switched_settings(cur_s, repo, src)
    plan.append("settings  core hooks removed, extraKnownMarketplaces.%s (%s, autoUpdate), enabledPlugins %s: true"
                % (src["marketplace"], src["source"].get("url") or src["source"], src.get("plugin") or PLUGIN_ID))
    lp = os.path.join(repo, ".claude", "launch.json")
    cur_l = json.loads(read(lp) or "null")
    try:
        port = int(json.loads(read(os.path.join(repo, ".claude", "project.json")) or "{}").get("live_port", 8766))
    except (ValueError, TypeError):
        port = 8766
    new_l = merged_launch(cur_l, port, RUNTIME)
    plan.append("launch    live-status runs %sscripts/live_status.py" % RUNTIME)
    # 2b. user settings: allow the plugin's scripts (`.claude/core/scripts/*` points nowhere after the switch)
    up = user_settings_path(a)
    try:
        cur_u = json.loads(read(up) or "{}")
    except ValueError:
        cur_u = None
    rules = plugin_scripts_rules(src)
    add = [] if cur_u is None else [r for r in rules if r not in ((cur_u.get("permissions") or {}).get("allow") or [])]
    plan.append("user      %s: %s" % (up.replace("\\", "/"), "not valid JSON, add by hand: " + ", ".join(rules)
                                      if cur_u is None else ("allow " + ", ".join(add)) if add
                                      else "the plugin scripts are already allowed"))
    if not a.dry_run:
        keep(".claude/settings.json")
        keep(".claude/launch.json")
        write(sp, json.dumps(new_s, indent=2) + "\n", nl)
        write(lp, json.dumps(new_l, indent=2) + "\n", nl)
        if add:
            cur_u.setdefault("permissions", {}).setdefault("allow", []).extend(add)
            os.makedirs(os.path.dirname(up), exist_ok=True)
            write(up, json.dumps(cur_u, indent=2) + "\n", "\n")
    # 3. AGENTS.md core block for the plugin, and core paths in the repo's own setup files
    am = os.path.join(repo, "AGENTS.md")
    name = json.loads(read(os.path.join(repo, ".claude", "project.json")) or "{}").get("name", "")
    texts = []
    for rel in repo_texts(repo):
        if rel in lock["files"]:  # removed in step 1 (still there in a dry run)
            continue
        cur = (read(os.path.join(repo, rel)) or "").replace("\r\n", "\n")
        new = agents_md(retarget(cur), name, switched=True) if rel == "AGENTS.md" else retarget(cur)
        if new != cur:
            texts.append(rel)
            if not a.dry_run:
                keep(rel)
                write(os.path.join(repo, rel), new, nl)
    if not os.path.isfile(am):
        texts.append("AGENTS.md (new)")
        if not a.dry_run:
            write(am, agents_md(None, name, switched=True), nl)
    plan.append("text      core paths -> %s in %d file(s): %s" % (RUNTIME, len(texts), ", ".join(texts[:8])
                                                                    + (" ..." if len(texts) > 8 else "")))
    # 4. .cursor/ from this core: agents, skills and the whole core copy (shared through git)
    cursor_gitignore(repo, a.dry_run)
    plan.append("cursor    cursor_sync.py of core %s: .cursor/agents, .cursor/skills, %s" % (version(CORE), RUNTIME))
    for p in plan:
        print(p)
    if a.dry_run:
        print("dry run: nothing changed")
        return 0
    rc, out = run_sync(repo, False, os.path.join(CORE, "scripts", "cursor_sync.py"))
    print("cursor_sync: " + (out.splitlines()[-1] if out else "done"))
    print("switched to the plugin (backup in .claude/core-backup/%s/). Each teammate trusts the folder once; a private "
          "marketplace needs stored git credentials (gh auth login and gh auth setup-git)." % stamp)
    return 1 if rc else check_switched(repo)


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("repo")
    p.add_argument("--check", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--adopt", action="store_true", help="replace the repo's own files that have core names")
    p.add_argument("--write-settings", action="store_true")
    p.add_argument("--project-name", default="")
    p.add_argument("--switch-to-plugin", action="store_true", help="move the repo onto the Claude Code plugin")
    p.add_argument("--force", action="store_true", help="--switch-to-plugin: drop hand edits to core files")
    p.add_argument("--marketplace-url", default="", help="--switch-to-plugin: the marketplace git URL")
    p.add_argument("--user-settings", default="", help="--switch-to-plugin: the user settings file that gets the "
                   "plugin scripts allow rule (default: settings.json in CLAUDE_CONFIG_DIR or ~/.claude)")
    a = p.parse_args()
    repo = os.path.abspath(a.repo)
    if not os.path.isdir(repo):
        sys.exit("no such folder: " + repo)
    if a.check:
        sys.exit(check(repo))
    if a.switch_to_plugin:
        sys.exit(switch_to_plugin(repo, a))
    if INSTALLED:
        sys.exit("This is an installed copy of the core; install and update from the core source "
                 "(from the product-factory repo: python core/scripts/install.py <repo>). --check works here.")
    sys.exit(install(repo, a))


if __name__ == "__main__":
    main()
