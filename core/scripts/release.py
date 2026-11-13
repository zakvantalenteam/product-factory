"""Release a new agent core version in one command, from the core's home repo (product-factory).

  python core/scripts/release.py <version> --summary "<one line>" [--repos a,b] [--include PATH ...] [--dry-run]
                                 [--targets FILE]

Steps, in order; it stops at the first failure with a plain message, and a rerun of the same command is safe:
  1. checks the version: X.Y.Z, higher than the last committed core/VERSION (git HEAD) and not lower than the
     working copy's; without git, higher than core/VERSION unless this version was already started (a rerun)
  2. bumps core/VERSION, core/.claude-plugin/plugin.json and plugin/.claude-plugin/plugin.json
  3. builds the plugin (build_plugin.py), then build_plugin.py --check, then `claude plugin validate plugin
     --strict` (finds the claude CLI on PATH or in the desktop app's folder; a warning when there is none)
  4. install.py <repo> --write-settings in every target repo (the home repo first)
  5. install.py --check and cursor_sync.py --check in every target repo
  6. the tests in <home>/tests/ (every test_*.py)
  7. compares the installed core files of every target repo with the core source (hash, line endings ignored)
  8. prints the commit commands per repo, writes the report, and runs doctor.py
It never runs git that changes a repo (only `git status` and `git show HEAD:<file>` to read). The commit commands
are for PowerShell 5.1 (`git -C <repo>`, one command per line). `git add` names the exact files of the release,
never a folder: the uncommitted files the core owns (files in core.lock, the core lock, the generated Cursor
copies, the core block of AGENTS.md, the core entries of .claude/settings.json and launch.json, the .gitignore
lines install.py adds, untouched starters; in the home repo also core/, plugin/, tests/ and the agents table of
README.md). A file with other changes is listed as "left out" with every other uncommitted file, so another
session's work is never swept in; name a file you edited by hand for the release with --include: a bare path
(README.md, .github/...) is in the home repo, <repo name>:<path> in that repo (blend:.claude/project.json); a path
ending in / names every uncommitted file under that folder (blend:.claude/bench/).
Commit subjects: the home repo "core <v>: <summary>"; product repos "AI dev setup: agent core <v> - <summary>",
with the repo's `commit_prefix` from .claude/project.json in front (e.g. a ticket the repo requires).
Targets: <home>/release.local.json (machine-local, gitignored; see release.local.example.json):
  {"repos": [{"name": "product-factory", "path": "D:/product-factory/repo"}, {"name": "blend", "path": "..."}],
   "report_dir": ".release"}
The home repo is always a target. --repos limits the product repos (names, comma or space separated).
The report and the run's state go to <home>/<report_dir>/core-<version>.md and .json (gitignored).
--dry-run checks the version and targets, runs install.py --dry-run in every repo and shows the plan and today's
commit lines; it writes nothing.
"""
import argparse
import datetime
import glob
import json
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import install  # noqa: E402
from doctor import find_cli  # noqa: E402

CORE = install.CORE
HOME = os.path.dirname(CORE)
VERSION_FILES = ("core/VERSION", "core/.claude-plugin/plugin.json", "plugin/.claude-plugin/plugin.json")
STARTERS = {".claude/smoke.md": "smoke.md", ".claude/review/lessons.md": "lessons.md",
            ".claude/review/accepted.md": "accepted.md"}
CLAUDE_MD = ("Project instructions live in AGENTS.md, shared with Cursor. Claude Code loads them through this import:"
             "\n\n@AGENTS.md\n")
README_MARKS = ("<!-- certified-agents:start", "<!-- certified-agents:end -->")
HOME_SOURCE = ("core/", "plugin/", "tests/")
CURSOR_MARK = "cursor_sync.py"
PS_SAFE = re.compile(r"[A-Za-z0-9._/\\:\-]+")
PER_LINE = 20  # paths per `git add` line


class Stop(Exception):
    """A failed step: the message says where and what to do."""


# ---- small helpers ----------------------------------------------------------------------------------------------

def parse(v):
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", (v or "").strip())
    return tuple(int(x) for x in m.groups()) if m else None


def read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError):
        return None


def norm(text):
    return None if text is None else text.replace("\r\n", "\n")


def run(args, cwd=None, env=None, timeout=1200):
    try:
        p = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout)
    except Exception as e:  # noqa: BLE001 - reported as a failed step
        return 1, "could not run %s: %s" % (" ".join(args[:3]), e)
    return p.returncode, (p.stdout + p.stderr).strip()


def tail(text, n=15):
    lines = (text or "").splitlines()
    return "\n".join(("  " + l) for l in lines[-n:]) or "  (no output)"


def win(path):
    return os.path.normpath(path)


def git(repo, *args):
    """Read-only git; stdout bytes, or None without git or outside a repo."""
    try:
        p = subprocess.run(["git", "--no-optional-locks", "-C", repo] + list(args), capture_output=True, timeout=60)
    except Exception:  # noqa: BLE001
        return None
    return p.stdout if p.returncode == 0 else None


_ROOTS = {}


def is_git_root(repo):
    """True when the folder is the top of a git repo (a folder inside another repo is not: its paths and HEAD
    would be that repo's)."""
    key = os.path.normcase(os.path.abspath(repo))
    if key not in _ROOTS:
        top = git(repo, "rev-parse", "--show-toplevel")
        _ROOTS[key] = top is not None and os.path.normcase(
            os.path.abspath(top.decode("utf-8", "replace").strip())) == key
    return _ROOTS[key]


def head_text(repo, rel):
    out = git(repo, "show", "HEAD:" + rel) if is_git_root(repo) else None
    return None if out is None else out.decode("utf-8", "replace")


def git_status(repo):
    """[(XY, path)] of uncommitted files (porcelain v1, every untracked file), or None when git cannot tell."""
    if not is_git_root(repo):
        return None  # not a repo root: paths would not line up
    out = git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    if out is None:
        return None
    parts, res, i = out.decode("utf-8", "replace").split("\0"), [], 0
    while i < len(parts):
        e = parts[i]
        i += 1
        if len(e) < 4:
            continue
        res.append((e[:2], e[3:]))
        if e[0] in "RC" and i < len(parts):  # a rename: the old path follows
            res.append(("D ", parts[i]))
            i += 1
    return res


def load_json(text, default):
    try:
        return json.loads(text) if text else default
    except ValueError:
        return default


def project_cfg(repo):
    return load_json(read(os.path.join(repo, ".claude", "project.json")), {})


# ---- targets ----------------------------------------------------------------------------------------------------

def load_targets(path, names):
    """[(name, abspath)] with the home repo first. names: the product repos to keep (None: all)."""
    data = load_json(read(path), None)
    if data is None:
        raise Stop("no targets file %s (machine-local, gitignored). Copy release.local.example.json to "
                   "release.local.json and fill in each repo's folder on this machine." % path)
    repos, seen = [], set()
    for r in data.get("repos") or []:
        name, p = str(r.get("name") or "").strip(), str(r.get("path") or "").strip()
        if not name or not p:
            raise Stop("%s: every repo needs a name and a path (%r)" % (path, r))
        full = os.path.abspath(os.path.expanduser(p))
        repos.append((name, full))
    home = [(n, p) for n, p in repos if os.path.normcase(p) == os.path.normcase(HOME)]
    home = home[0] if home else ("product-factory", HOME)
    products = [(n, p) for n, p in repos if os.path.normcase(p) != os.path.normcase(HOME)]
    if names:
        known = {n for n, _ in products}
        unknown = [n for n in names if n not in known and n != home[0]]
        if unknown:
            raise Stop("unknown repo name(s) %s; %s names: %s" % (", ".join(unknown), os.path.basename(path),
                                                                   ", ".join(sorted(known)) or "none"))
        products = [(n, p) for n, p in products if n in names]
    out = []
    for n, p in [home] + products:
        if os.path.normcase(p) in seen:
            continue
        seen.add(os.path.normcase(p))
        if not os.path.isdir(p):
            raise Stop("repo %s: no folder %s (fix its path in %s)" % (n, p, path))
        out.append((n, p))
    return out, data


# ---- version ----------------------------------------------------------------------------------------------------

def current_versions():
    """(working core/VERSION, committed core/VERSION or None)."""
    work = (read(os.path.join(CORE, "VERSION")) or "").strip()
    head = head_text(HOME, "core/VERSION")
    return work, (head.strip() if head else None)


def check_version(v, state):
    want = parse(v)
    if not want:
        raise Stop("version %r is not X.Y.Z (for example 1.17.0)" % v)
    work, head = current_versions()
    w = parse(work) or (0, 0, 0)
    if head is not None:
        h = parse(head) or (0, 0, 0)
        if want <= h:
            raise Stop("version %s is not higher than the last committed core version %s" % (v, head))
        if want < w:
            raise Stop("version %s is lower than core/VERSION %s in the working copy" % (v, work))
        return work, head
    if want < w or (want == w and not state):
        raise Stop("version %s is not higher than the current core version %s" % (v, work))
    return work, None


def bump(v, dry):
    """[(file, old, new)] for the three version spots; writes them unless dry."""
    out = []
    for rel in VERSION_FILES:
        p = os.path.join(HOME, *rel.split("/"))
        with open(p, encoding="utf-8", newline="") as fh:
            text = fh.read()
        if rel.endswith("VERSION"):
            old = text.strip()
            new_text = v + ("\r\n" if text.endswith("\r\n") else "\n")
        else:
            m = re.search(r'("version"\s*:\s*")([^"]*)(")', text)
            if not m:
                raise Stop("%s has no \"version\" field" % rel)
            old = m.group(2)
            new_text = text[:m.start(2)] + v + text[m.end(2):]
        out.append((rel, old, v))
        if not dry and new_text != text:
            with open(p, "w", encoding="utf-8", newline="") as fh:
                fh.write(new_text)
    return out


# ---- which uncommitted files belong to the release ---------------------------------------------------------------

def lock_files(text):
    return set((load_json(text, {}) or {}).get("files", {}))


def only_between(cur, old, marks):
    """True when cur and old differ only between the two markers (both have them)."""
    def cut(t):
        a, b = t.find(marks[0]), t.find(marks[1])
        return None if a < 0 or b < a else (t[:a], t[b:])
    c, o = cut(cur), cut(old)
    return c is not None and c == o


def owned_reason(repo, rel, xy, ctx):
    """Why the release owns this uncommitted path, or None (left out). ctx: per-repo facts."""
    full = os.path.join(repo, *rel.split("/"))
    cur = norm(read(full)) if os.path.isfile(full) else None
    untracked = xy == "??"

    def old():  # the committed text (None for a new file), read only when needed
        return norm(ctx["head"](rel))
    if rel in ctx["include"] or any(i.endswith("/") and rel.startswith(i) for i in ctx["include"]):
        return "named with --include"
    if ctx["home"] and rel.startswith(HOME_SOURCE):
        return {"core/": "core source", "plugin/": "plugin build", "tests/": "core tests"}[rel.split("/")[0] + "/"]
    if rel in ctx["core"]:
        return "core file"
    if rel.startswith(".cursor/runtime/") or rel == ".cursor/hooks.json":
        return "Cursor copy"
    if rel.startswith((".cursor/agents/", ".cursor/rules/", ".cursor/skills/")):
        text = cur if cur is not None else old()
        return "Cursor copy" if text and CURSOR_MARK in text else None
    if rel == "AGENTS.md" and cur is not None:
        want = install.agents_md(old(), ctx["name"], ctx["switched"])
        return "core block" if want == cur else None
    if rel == "CLAUDE.md" and untracked and cur == CLAUDE_MD:
        return "starter"
    if rel in STARTERS and untracked and cur == norm(read(os.path.join(CORE, "templates", STARTERS[rel]))):
        return "starter"
    if rel == ".gitignore" and cur is not None:
        was = set((old() or "").split("\n"))
        new = set(cur.split("\n"))
        extra = {l.strip() for l in new - was if l.strip()}
        allowed = set(install.ignore_lines(repo)) | set(install.CURSOR_UNIGNORES)
        return "core ignore lines" if was <= new and extra <= allowed else None
    if rel == ".claude/settings.json" and cur is not None:
        want = install.merged_settings(load_json(old(), {}), repo)
        return "core hook entries" if want == load_json(cur, None) else None
    if rel == ".claude/launch.json" and cur is not None:
        try:
            port = int(ctx["cfg"].get("live_port", 8766))
        except (TypeError, ValueError):
            port = 8766
        want = install.merged_launch(load_json(old(), None), port)
        return "live-status entry" if want == load_json(cur, None) else None
    if ctx["home"] and rel == "README.md" and cur is not None:
        was = old()
        return "agents table" if was is not None and only_between(cur, was, README_MARKS) else None
    return None


def includes(items, name, home):
    """The --include paths for one repo: `<name>:<path>` for that repo, a bare path for the home repo."""
    out = []
    for i in items:
        m = re.fullmatch(r"([A-Za-z0-9_.-]+):(?![\\/])(.+)", i)  # not a drive letter (one character)
        if m and len(m.group(1)) > 1:
            if m.group(1) == name:
                out.append(m.group(2))
        elif home:
            out.append(i)
    return out


def rel_path(p):
    p = p.replace("\\", "/")
    return p[2:] if p.startswith("./") else p


def cursor_source(rel):
    """The .claude/ file a generated Cursor agent or rule comes from (None for others)."""
    m = re.fullmatch(r"\.cursor/(agents|rules)/(.+)\.(md|mdc)", rel)
    return ".claude/%s/%s.md" % (m.group(1), m.group(2)) if m else None


def classify(repo, entries, home, include=(), head=None):
    """(add, left): add = [(path, reason)] the release owns, left = [path] every other uncommitted file."""
    head = head or (lambda rel: head_text(repo, rel))
    cfg = project_cfg(repo)
    ctx = {"home": home, "include": {rel_path(i) for i in include},
           "core": lock_files(read(os.path.join(repo, ".claude", "core", "core.lock"))) | lock_files(
               head(".claude/core/core.lock")) | {".claude/core/core.lock"},
           "name": cfg.get("name", ""), "switched": install.is_switched(repo), "cfg": cfg, "head": head}
    add, left = [], []
    for xy, rel in sorted(set(entries), key=lambda e: e[1]):
        why = owned_reason(repo, rel, xy, ctx)
        (add.append((rel, why)) if why else left.append(rel))
    left_set = set(left)
    keep = []
    for rel, why in add:  # a generated Cursor file follows its source: left out when the source is left out
        src = cursor_source(rel) if why == "Cursor copy" else None
        if src and src in left_set:
            left.append(rel)
        else:
            keep.append((rel, why))
    return keep, sorted(left)


# ---- commit commands --------------------------------------------------------------------------------------------

def ps(arg):
    """One PowerShell 5.1 argument: bare when safe, else single-quoted ('' for a quote)."""
    return arg if PS_SAFE.fullmatch(arg) else "'" + arg.replace("'", "''") + "'"


def subject(repo, home, v, summary):
    s = summary.replace('"', "'").strip()
    text = ("core %s: %s" if home else "AI dev setup: agent core %s - %s") % (v, s)
    prefix = str(project_cfg(repo).get("commit_prefix") or "").strip()
    return (prefix + " " + text) if prefix else text


def add_lines(repo, files):
    return ["git -C %s add %s" % (ps(win(repo)), " ".join(ps(f) for f in files[i:i + PER_LINE]))
            for i in range(0, len(files), PER_LINE)]


def commit_block(name, repo, home, v, summary, add, left, carries):
    out = ["## %s" % name]
    if add is None:
        out.append("git cannot list this repo's changes (not a git repo root): commit its core files by hand.")
        return out
    if not add:
        out.append("Nothing to commit (the release changed no file here, or it is committed already).")
    else:
        if carries:
            out.append("This commit also carries core %s (installed here but not committed yet)." % carries)
        out.append("```powershell")
        out += add_lines(repo, [f for f, _ in add])
        out.append("git -C %s commit -m %s" % (ps(win(repo)), ps(subject(repo, home, v, summary))))
        if home:
            out.append("git -C %s push" % ps(win(repo)))
        out.append("```")
    if left:
        out.append("Left out (%d, not part of the release): %s" % (len(left), ", ".join(left[:40])
                                                                    + (" ... and %d more" % (len(left) - 40)
                                                                       if len(left) > 40 else "")))
    return out


# ---- the steps --------------------------------------------------------------------------------------------------

def py(script, *args):
    return [sys.executable, script] + list(args)


def env_for(repo):
    return dict(os.environ, CLAUDE_PROJECT_DIR=repo, PYTHONDONTWRITEBYTECODE="1")


def repo_script(repo, name):
    """The repo's own installed copy of a core script, else the core source's (a repo switched to the plugin)."""
    own = os.path.join(repo, ".claude", "core", "scripts", name)
    return own if os.path.isfile(own) else os.path.join(CORE, "scripts", name)


def compare_hashes(targets):
    """(ok lines, problems): every target's installed core files against the core source."""
    want = {rel: install.sha_bytes(install.src_data(src)) for rel, src in install.core_files().items()}
    problems, counted = [], []
    for name, repo in targets:
        if install.is_switched(repo):
            counted.append("%s gets the core from the plugin (no repo copy)" % name)
            continue
        bad = []
        for rel, h in sorted(want.items()):
            p = os.path.join(repo, *rel.split("/"))
            if not os.path.isfile(p):
                bad.append("missing " + rel)
            elif install.sha(p) != h:
                bad.append("differs " + rel)
        lock = load_json(read(os.path.join(repo, ".claude", "core", "core.lock")), {}).get("files", {})
        own = [b for b in bad if b.split(" ", 1)[1] not in lock and not b.startswith("missing")]
        bad = [b for b in bad if b not in own]  # a repo's own file with a core name (install.py skips it) is no drift
        if own:
            counted.append("%s keeps its own %s" % (name, ", ".join(b.split(" ", 1)[1] for b in own)))
        if any(lock.get(rel) != h for rel, h in want.items() if rel in lock) or set(lock) - set(want):
            bad.append("core.lock does not match the core source")
        if bad:
            problems.append("%s: %s" % (name, "; ".join(bad[:8]) + (" ..." if len(bad) > 8 else "")))
    copies = [n for n, r in targets if not install.is_switched(r)]
    return ["%d core files identical in %d repos (%s)" % (len(want), len(copies), ", ".join(copies))] + counted, problems


def run_tests():
    files = sorted(glob.glob(os.path.join(HOME, "tests", "**", "test_*.py"), recursive=True))
    lines = []
    for f in files:
        rc, out = run(py(f), cwd=HOME, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        ran = [l for l in out.splitlines() if l.startswith("Ran ")]
        rel = os.path.relpath(f, HOME).replace("\\", "/")
        if rc:
            raise Stop("tests failed in %s:\n%s" % (rel, tail(out, 25)))
        lines.append("%s: %s, OK" % (rel, ran[-1][4:] if ran else "passed"))
    return lines or ["no tests in tests/"]


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("version")
    ap.add_argument("--summary", required=True, help="one line for the commit subjects and the report")
    ap.add_argument("--repos", nargs="*", default=None, help="product repo names to release to (default: all)")
    ap.add_argument("--include", nargs="*", default=[], help="files edited by hand to commit with the release: a path "
                    "in the home repo, or <repo name>:<path>; a path ending in / takes the folder")
    ap.add_argument("--targets", default=os.path.join(HOME, "release.local.json"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    names = [n.strip() for x in (a.repos or []) for n in x.split(",") if n.strip()] or None
    try:
        return release(a, names)
    except Stop as e:
        print("\nrelease stopped: %s\nFix it, then rerun the same command (the steps before it repeat safely)." % e)
        return 1


def release(a, names):
    v, summary = a.version.strip(), " ".join(a.summary.split())
    if not summary:
        raise Stop("--summary is empty")
    if not os.path.isfile(os.path.join(HOME, ".claude-plugin", "marketplace.json")):
        raise Stop("no .claude-plugin/marketplace.json in %s: release.py runs only in the core's home repo" % HOME)
    targets, tdata = load_targets(a.targets, names)
    report_dir = os.path.join(HOME, str(tdata.get("report_dir") or ".release"))
    state_path = os.path.join(report_dir, "core-%s.json" % v)
    state = load_json(read(state_path), None)
    work, head = check_version(v, state)
    previous = (state or {}).get("previous") or work
    steps = []

    def step(n, label):
        print("[%d/8] %s" % (n, label))

    print("core %s -> %s%s, targets: %s" % (previous, v, " (dry run: nothing is written)" if a.dry_run else "",
                                            ", ".join(n for n, _ in targets)))
    step(1, "version %s: ok (committed %s, working copy %s)" % (v, head or "unknown (no git)", work))

    if a.dry_run:
        for rel, old, new in bump(v, dry=True):
            print("  would set %s: %s -> %s" % (rel, old, new))
        print("  would run: build_plugin.py, build_plugin.py --check, claude plugin validate plugin --strict (%s)"
              % (find_cli() or "no claude CLI found: skipped with a warning"))
        for name, repo in targets:
            rc, out = run(py(os.path.join(CORE, "scripts", "install.py"), repo, "--write-settings", "--dry-run"),
                          cwd=HOME)
            last = [l for l in out.splitlines() if l.startswith("core ")]
            print("  %s: install.py --dry-run (before the bump): %s" % (
                name, last[-1] if last and not rc else "exit %d\n%s" % (rc, tail(out, 6))))
        print("  would run: install.py --check and cursor_sync.py --check per repo, the tests in tests/, the hash "
              "compare, then doctor.py")
        print("\nCommit lines for today's uncommitted files (before the release):")
        for name, repo in targets:
            entries = git_status(repo)
            home = repo == targets[0][1]
            add, left = classify(repo, entries, home, includes(a.include, name, home)) \
                if entries is not None else (None, [])
            print("\n".join(commit_block(name, repo, home, v, summary, add, left, None)))
        print("\ndry run: nothing written")
        return 0

    os.makedirs(report_dir, exist_ok=True)
    if not state:
        state = {"version": v, "previous": previous, "summary": summary,
                 "started": datetime.datetime.now().isoformat(timespec="seconds")}
        with open(state_path, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=1)

    bumped = bump(v, dry=False)
    step(2, "bump: " + ", ".join("%s %s -> %s" % (r, o, n) if o != n else "%s %s" % (r, n) for r, o, n in bumped))
    steps.append("Version: " + ", ".join("%s %s" % (r, n) for r, _, n in bumped))

    build = os.path.join(CORE, "scripts", "build_plugin.py")
    rc, out = run(py(build), cwd=HOME)
    if rc:
        raise Stop("build_plugin.py failed:\n" + tail(out))
    rc, out = run(py(build, "--check"), cwd=HOME)
    if rc:
        raise Stop("build_plugin.py --check failed:\n" + tail(out))
    cli = find_cli()
    if cli:
        rc, vout = run([cli, "plugin", "validate", os.path.join(HOME, "plugin"), "--strict"], cwd=HOME, timeout=300)
        if rc:
            raise Stop("claude plugin validate plugin --strict failed (%s):\n%s" % (cli, tail(vout)))
        val = "claude plugin validate --strict: " + (vout.splitlines()[-1] if vout else "ok")
    else:
        val = "warning: no claude CLI found (PATH or the desktop app's folder), so validate did not run"
    step(3, "plugin built, --check ok; " + val)
    steps.append("Plugin: built, `build_plugin.py --check` ok; " + val + (" (%s)" % cli if cli else ""))

    inst = []
    for name, repo in targets:
        rc, out = run(py(os.path.join(CORE, "scripts", "install.py"), repo, "--write-settings"), cwd=HOME)
        if rc:
            raise Stop("install.py %s --write-settings failed (%s):\n%s" % (repo, name, tail(out)))
        kept = [l for l in out.splitlines() if l.startswith(("kept (edited by hand)", "skipped (repo's own file)"))]
        last = [l for l in out.splitlines() if l.startswith("core ")]
        inst.append("%s: %s%s" % (name, last[-1] if last else "done", "; " + "; ".join(kept) if kept else ""))
    step(4, "installed: " + "; ".join(inst))
    steps += ["Install " + l for l in inst]

    for name, repo in targets:
        rc, out = run(py(repo_script(repo, "install.py"), repo, "--check"), cwd=repo, env=env_for(repo))
        if rc:
            raise Stop("install.py --check failed in %s:\n%s" % (name, tail(out)))
        rc2, out2 = run(py(repo_script(repo, "cursor_sync.py"), "--check"), cwd=repo, env=env_for(repo))
        if rc2:
            raise Stop("cursor_sync.py --check failed in %s:\n%s" % (name, tail(out2)))
        steps.append("Checks %s: install.py --check %s; cursor_sync.py --check %s" % (
            name, out.splitlines()[-1] if out else "ok", out2.splitlines()[-1] if out2 else "ok"))
    step(5, "install.py --check and cursor_sync.py --check clean in %d repos" % len(targets))

    tests = run_tests()
    step(6, "tests: " + "; ".join(tests))
    steps += ["Tests " + t for t in tests]

    ok, bad = compare_hashes(targets)
    if bad:
        raise Stop("installed core files differ from the core source:\n  " + "\n  ".join(bad))
    step(7, "; ".join(ok))
    steps += ["Hashes: " + l for l in ok]

    blocks = []
    for name, repo in targets:
        home = repo == targets[0][1]
        entries = git_status(repo)
        add, left = classify(repo, entries, home, includes(a.include, name, home)) if entries is not None else (None, [])
        was = head_text(repo, ".claude/core/VERSION")
        was = was.strip() if was else None
        carries = previous if (was and previous != v and parse(was) and parse(previous)
                               and parse(was) < parse(previous)) else None
        blocks.append(commit_block(name, repo, home, v, summary, add, left, carries))
    commands = ["# Commit commands (PowerShell 5.1)", ""]
    for b in blocks:
        commands += b + [""]
    commands += ["After the push to main: `claude plugin marketplace update talenteam`, then "
                 "`claude plugin update product-factory@talenteam`, and restart Claude Code. Push the product repos "
                 "as usual."]
    step(8, "commit commands, report and doctor")
    print("\n" + "\n".join(commands))

    rc, dout = run(py(os.path.join(CORE, "scripts", "doctor.py"), "--home", HOME, "--targets", a.targets), cwd=HOME)
    print("\n# doctor.py (exit %d)\n%s" % (rc, dout))
    report = os.path.join(report_dir, "core-%s.md" % v)
    with open(report, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# Core %s release\n\n%s\n\nFrom %s, %s. Nothing committed: the commands below are for the developer."
                 "\n\n## Steps\n%s\n\n%s\n\n## doctor.py (exit %d)\n```\n%s\n```\n" % (
                     v, summary, previous, datetime.date.today().isoformat(), "\n".join("- " + s for s in steps),
                     "\n".join(commands), rc, dout))
    state["done"] = datetime.datetime.now().isoformat(timespec="seconds")
    with open(state_path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=1)
    print("\nrelease %s ready: report %s" % (v, report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
