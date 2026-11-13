"""Find every copy of the product-factory agent core on this machine and say what is wrong. Read only.

  python <core>/scripts/doctor.py [--home DIR] [--targets FILE] [--all]
                                  [--claude-home DIR] [--claude-data DIR]

Copies it finds:
  - the marketplace install: ~/.claude/plugins/cache/<marketplace>/product-factory/<version>; the one
    ~/.claude/plugins/installed_plugins.json names is installed, ~/.claude/settings.json `enabledPlugins` says
    whether it is on; older cached versions are counted, not used (--all lists them);
  - the marketplace clone: ~/.claude/plugins/marketplaces/<marketplace>/<plugin folder> (what an update installs);
  - claude.ai-synced copies: <claude-data>/*/rpm/**/plugin_* whose .claude-plugin/plugin.json is product-factory
    (claude-data: %LOCALAPPDATA%/Claude-Data); one its folder's manifest.json lists is synced, so on;
  - repo copies: .claude/core/ in each repo of the release targets (<home>/release.local.json) and in the
    current project.
Per copy: version, whether it is on, complete (a plugin copy has every file its hooks/hooks.json names and every
file of the home repo's plugin/ of the same version, or of the installed commit; a repo copy has every file of
its core.lock) and stale (older than the core source, else than the newest copy found).
Problems, each with one fix line: the plugin on twice; the plugin older than the repo cores; repo cores that
differ; repo cores older than the core source; a copy missing files. Exit 0 when clean, 1 otherwise.
The home (the core source) is --home, else PRODUCT_FACTORY_HOME, else the repo this script sits in when it has
.claude-plugin/marketplace.json, else a marketplace whose source is a local folder.
It never writes: not to a copy, not to the claude.ai folder, not to settings.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True
NAME = "product-factory"
HERE = os.path.dirname(os.path.abspath(__file__))
SKIP = {"__pycache__"}


def parse(v):
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", (v or "").strip())
    return tuple(int(x) for x in m.groups()) if m else None


def vkey(v):
    return parse(v) or (0, 0, 0)


def read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError):
        return None


def load(path, default=None):
    try:
        return json.loads(read(path) or "")
    except ValueError:
        return default


def same(a, b):
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def files_of(folder):
    out = set()
    for top, dirs, names in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for n in names:
            if not n.endswith(".pyc"):
                out.add(os.path.relpath(os.path.join(top, n), folder).replace("\\", "/"))
    return out


def plugin_version(folder):
    pj = load(os.path.join(folder, ".claude-plugin", "plugin.json"), {}) or {}
    return str(pj.get("version") or (read(os.path.join(folder, "VERSION")) or "").strip() or "?")


def hook_paths(folder):
    """Files a plugin copy's hooks/hooks.json names as ${CLAUDE_PLUGIN_ROOT}/<file>; None when hooks.json is gone."""
    text = read(os.path.join(folder, "hooks", "hooks.json"))
    if text is None:
        return None
    return sorted(set(re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s\"']+)", text)))


# ---- where things are -------------------------------------------------------------------------------------------

def find_home(arg, claude_home):
    for cand in (arg, os.environ.get("PRODUCT_FACTORY_HOME")):
        if cand and os.path.isfile(os.path.join(cand, "core", "VERSION")):
            return os.path.abspath(cand)
    for up in (os.path.join(HERE, "..", ".."), os.path.join(HERE, "..", "..", "..")):
        up = os.path.abspath(up)
        if os.path.isfile(os.path.join(up, ".claude-plugin", "marketplace.json")) and os.path.isdir(
                os.path.join(up, "core")):
            return up
    for m in (load(os.path.join(claude_home, "plugins", "known_marketplaces.json"), {}) or {}).values():
        src = (m or {}).get("source") or {}
        p = src.get("path") or (src.get("url") if src.get("source") in ("directory", "local") else None)
        if p and os.path.isfile(os.path.join(p, "core", "VERSION")):
            return os.path.abspath(p)
    return None


def current_repo():
    """The project this runs for: CLAUDE_PROJECT_DIR, else the repo around this script's .claude/core, else the
    nearest folder above the working folder with .claude/core."""
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env and os.path.isdir(os.path.join(env, ".claude", "core")):
        return os.path.abspath(env)
    up = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
    if os.path.basename(os.path.dirname(HERE)) == "core" and os.path.isdir(os.path.join(up, ".claude", "core")) \
            and same(os.path.join(up, ".claude", "core"), os.path.dirname(HERE)):
        return up
    d = os.getcwd()
    while True:
        if os.path.isdir(os.path.join(d, ".claude", "core")):
            return d
        nd = os.path.dirname(d)
        if nd == d:
            return None
        d = nd


def repo_targets(home, targets_file):
    out = []
    data = load(targets_file or (os.path.join(home, "release.local.json") if home else ""), {}) or {}
    for r in data.get("repos") or []:
        if r.get("path"):
            out.append((str(r.get("name") or os.path.basename(r["path"])), os.path.abspath(r["path"])))
    if home and not any(same(p, home) for _, p in out):
        out.insert(0, ("product-factory", home))
    cur = current_repo()
    if cur and not any(same(p, cur) for _, p in out):
        out.append((os.path.basename(cur), cur))
    return out


def git_files(home, sha, sub):
    """File names under <sub>/ at a commit (read-only git ls-tree), or None."""
    if not home or not sha or not os.path.exists(os.path.join(home, ".git")):
        return None  # only the home repo's own history
    try:
        p = subprocess.run(["git", "--no-optional-locks", "-C", home, "ls-tree", "-r", "--name-only", sha, "--", sub],
                           capture_output=True, timeout=30)
    except Exception:  # noqa: BLE001
        return None
    if p.returncode:
        return None
    pre = sub.rstrip("/") + "/"
    return {l[len(pre):] for l in p.stdout.decode("utf-8", "replace").splitlines() if l.startswith(pre)}


# ---- the copies -------------------------------------------------------------------------------------------------

class Copy:
    def __init__(self, kind, label, folder, version, on, sha=None, fix=""):
        self.kind, self.label, self.folder, self.version, self.on, self.sha, self.fix = (
            kind, label, folder, version, on, sha, fix)
        self.missing = []
        self.compared = ""


def marketplace_copies(claude_home):
    """(copies, older cached copies not in use)."""
    plugins = os.path.join(claude_home, "plugins")
    installed = (load(os.path.join(plugins, "installed_plugins.json"), {}) or {}).get("plugins") or {}
    enabled = (load(os.path.join(claude_home, "settings.json"), {}) or {}).get("enabledPlugins") or {}
    used, copies = set(), []
    for key, entries in installed.items():
        if key.split("@")[0] != NAME:
            continue
        for e in entries if isinstance(entries, list) else [entries]:
            path = (e or {}).get("installPath")
            if not path:
                continue
            used.add(os.path.normcase(os.path.abspath(path)))
            state = enabled.get(key)
            on = "on" if state is True else "off" if state is False else "installed"
            if e.get("scope") and e.get("scope") != "user":
                on += " (%s %s)" % (e.get("scope"), e.get("projectPath") or "")
            ver = plugin_version(path) if os.path.isdir(path) else str(e.get("version") or "?")
            copies.append(Copy("marketplace", "marketplace %s" % key, path, ver, on, e.get("gitCommitSha"),
                               "claude plugin update %s (or uninstall and install it again in /plugin)" % key))
    old = []
    for path in glob.glob(os.path.join(plugins, "cache", "*", NAME, "*")):
        if os.path.isdir(path) and os.path.normcase(os.path.abspath(path)) not in used:
            old.append(os.path.basename(path))
    return copies, sorted(old, key=vkey)


def clone_copies(claude_home):
    out = []
    for mk in glob.glob(os.path.join(claude_home, "plugins", "marketplaces", "*")):
        for p in (load(os.path.join(mk, ".claude-plugin", "marketplace.json"), {}) or {}).get("plugins") or []:
            src = p.get("source")
            if p.get("name") == NAME and isinstance(src, str) and os.path.isdir(os.path.join(mk, src)):
                folder = os.path.normpath(os.path.join(mk, src))
                name = os.path.basename(mk)
                out.append(Copy("clone", "marketplace clone %s" % name, folder, plugin_version(folder), "-",
                                fix="claude plugin marketplace update %s" % name))
    return out


def claude_ai_copies(claude_data):
    out = []
    for folder in glob.glob(os.path.join(claude_data, "*", "rpm", "**", "plugin_*"), recursive=True):
        pj = load(os.path.join(folder, ".claude-plugin", "plugin.json"), {}) or {}
        if pj.get("name") != NAME:
            continue
        man = load(os.path.join(os.path.dirname(folder), "manifest.json"), {}) or {}
        entry = next((p for p in man.get("plugins") or [] if p.get("id") == os.path.basename(folder)), None)
        pref = (entry or {}).get("installationPreference")
        on = ("synced" + (" (%s)" % pref if pref else "")) if entry else "left on disk"
        out.append(Copy("claude.ai", "claude.ai %s" % os.path.basename(folder), folder, plugin_version(folder), on,
                        fix="turn it off on claude.ai (or in the plugin manager), or update it there"))
    return out


def repo_copies(targets, home):
    out = []
    for name, repo in targets:
        core = os.path.join(repo, ".claude", "core")
        lock = load(os.path.join(core, "core.lock"), None)
        if not os.path.isdir(core) or lock is None:
            continue
        c = Copy("repo", "repo %s" % name, core, (read(os.path.join(core, "VERSION")) or "?").strip(), "repo",
                 fix="python %s %s --write-settings" % (
                     (os.path.join(home, "core", "scripts", "install.py") if home else "<home>/core/scripts/install.py"),
                     repo))
        c.lock = lock.get("files") or {}
        c.repo = repo
        out.append(c)
    return out


def check_plugin(c, home):
    named = hook_paths(c.folder)
    if named is None:
        c.missing.append("hooks/hooks.json")
        named = []
    have = files_of(c.folder) if os.path.isdir(c.folder) else set()
    c.missing += [f for f in named if f not in have]
    ref = None
    if home and plugin_version(os.path.join(home, "plugin")) == c.version and os.path.isdir(os.path.join(home, "plugin")):
        ref, c.compared = files_of(os.path.join(home, "plugin")), "home plugin/"
    elif c.sha:
        ref = git_files(home, c.sha, "plugin")
        c.compared = "plugin/ at %s" % c.sha[:8] if ref is not None else ""
    if ref is not None:
        c.missing += sorted(f for f in ref - have if f not in c.missing)
    if not c.compared:
        c.compared = "hooks.json only (no plugin/ of %s here)" % c.version


def check_repo(c):
    root = os.path.dirname(os.path.dirname(c.folder))
    c.missing = sorted(rel for rel in c.lock if not os.path.isfile(os.path.join(root, *rel.split("/"))))
    c.compared = "core.lock (%d files)" % len(c.lock)


# ---- the report -------------------------------------------------------------------------------------------------

def collect(home, claude_home, claude_data, targets_file):
    market, old = marketplace_copies(claude_home)
    plugins = market + clone_copies(claude_home) + claude_ai_copies(claude_data)
    targets = repo_targets(home, targets_file)
    repos = repo_copies(targets, home)
    for c in plugins:
        check_plugin(c, home)
    for c in repos:
        check_repo(c)
    source = (read(os.path.join(home, "core", "VERSION")) or "").strip() if home else ""
    newest = max([c.version for c in plugins + repos if parse(c.version)] or ["0.0.0"], key=vkey)
    ref = source or newest
    problems = []
    on = [c for c in plugins if c.kind == "marketplace" and c.on.startswith(("on", "installed"))] + \
         [c for c in plugins if c.kind == "claude.ai" and c.on.startswith("synced")]
    if len(on) > 1:
        problems.append(("the plugin is on twice (%s), so every hook runs twice" % ", ".join(
            "%s %s" % (c.label, c.version) for c in on),
            "keep one: turn the claude.ai copy off on claude.ai, or turn one off in the plugin manager (/plugin)"))
    repo_max = max([c.version for c in repos if parse(c.version)] or ["0.0.0"], key=vkey)
    clones = [c for c in plugins if c.kind == "clone"]
    for c in on:
        if repos and vkey(c.version) < vkey(repo_max):
            if c.kind == "claude.ai":
                fix = "update it on claude.ai, or turn it off there"
            elif any(vkey(k.version) >= vkey(repo_max) for k in clones):
                fix = "claude plugin update %s, then restart Claude Code" % c.label.split(" ", 1)[1]
            else:
                key = c.label.split(" ", 1)[1]
                fix = ("push the core to main in the home repo, then claude plugin marketplace update %s and "
                       "claude plugin update %s, then restart Claude Code" % (key.split("@")[-1], key))
            problems.append(("the plugin (%s %s) is older than the repo cores (%s)" % (c.label, c.version, repo_max),
                             fix))
    versions = sorted({c.version for c in repos}, key=vkey)
    if len(versions) > 1:
        problems.append(("the repo cores differ: %s" % ", ".join("%s %s" % (c.label[5:], c.version) for c in repos),
                         "release them together from the home repo: python core/scripts/release.py <version> "
                         "--summary \"...\" (or install.py <repo> --write-settings for the older ones)"))
    elif len(repos) > 1:
        base = repos[0].lock
        diff = [c.label[5:] for c in repos[1:] if c.lock != base]
        if diff:
            problems.append(("the repo cores have the same version but different files (%s vs %s)" % (
                ", ".join(diff), repos[0].label[5:]),
                "reinstall from the home repo: python core/scripts/install.py <repo> --write-settings in each"))
    if source:
        behind = [c for c in repos if vkey(c.version) < vkey(source)]
        if behind:
            problems.append(("the core source is %s but %s" % (source, ", ".join(
                "%s has %s" % (c.label[5:], c.version) for c in behind)),
                "python core/scripts/release.py %s --summary \"...\" in the home repo" % source))
    for c in plugins + repos:
        if c.missing and c.kind != "clone":
            problems.append(("%s %s is missing %d file%s: %s" % (c.label, c.version, len(c.missing),
                                                                 "" if len(c.missing) == 1 else "s",
                                                                 ", ".join(c.missing[:6]) + (" ..." if len(c.missing) > 6 else "")),
                             c.fix))
        elif c.missing:
            problems.append(("%s %s is missing %s" % (c.label, c.version, ", ".join(c.missing[:6])), c.fix))
    return {"copies": plugins + repos, "old": old, "ref": ref, "source": source, "problems": problems,
            "home": home, "targets": targets}


def table(rows):
    w = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    out = []
    for n, r in enumerate(rows):
        out.append("  ".join(c.ljust(w[i]) for i, c in enumerate(r)).rstrip())
        if n == 0:
            out.append("  ".join("-" * x for x in w))
    return "\n".join(out)


def render(res, all_old=False):
    ref = res["ref"]
    rows = [["Copy", "Version", "On", "Complete", "Stale", "Folder"]]
    for c in res["copies"]:
        comp = "yes" if not c.missing else "NO: %d missing (%s)" % (len(c.missing), c.missing[0])
        stale = "-" if not parse(c.version) else ("yes (%s)" % ref if vkey(c.version) < vkey(ref) else "no")
        rows.append([c.label, c.version, c.on, comp, stale, c.folder])
    lines = ["product-factory copies on this machine (core source: %s)" % (
        "%s in %s" % (res["source"], res["home"]) if res["source"] else "not found; compared with the newest copy")]
    lines.append(table(rows) if len(rows) > 1 else "no copies found")
    if res["old"]:
        lines.append("older marketplace cache, not in use: %s" % (", ".join(res["old"]) if all_old else "%d versions (%s to %s)" % (
            len(res["old"]), res["old"][0], res["old"][-1])))
    if res["problems"]:
        lines.append("")
        lines.append("%d problem%s:" % (len(res["problems"]), "" if len(res["problems"]) == 1 else "s"))
        for what, fix in res["problems"]:
            lines.append("- %s.\n  Fix: %s" % (what, fix))
    else:
        lines.append("\nno problems")
    return "\n".join(lines)


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--home", default="", help="the core's home repo (the core source)")
    ap.add_argument("--targets", default="", help="the release targets file (default <home>/release.local.json)")
    ap.add_argument("--claude-home", default=os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude"))
    ap.add_argument("--claude-data", default=os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"),
                                                          "Claude-Data"))
    ap.add_argument("--all", action="store_true", help="list every older cached version")
    a = ap.parse_args(argv)
    home = find_home(a.home, a.claude_home)
    res = collect(home, a.claude_home, a.claude_data, a.targets)
    print(render(res, a.all))
    return 1 if res["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
