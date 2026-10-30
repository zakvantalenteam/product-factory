"""Scope check for a task (agent core), for Claude Code and Cursor.

The files a task changed must be ones its plan named. The plan is the `## Planned files` section of
<work>/<id>/design.md (of triage.md when design.md has no such section): one bullet per repo path or glob,
optionally `- path - reason` (put the path in backticks when it contains " - ").

  python .claude/core/scripts/scope_check.py baseline ID            at Build start: snapshot what is already dirty
  python .claude/core/scripts/scope_check.py check ID               UNPLANNED <path> lines, exit 1 when any
  python .claude/core/scripts/scope_check.py add ID PATH --why "..."  accept an unplanned file into the plan

The baseline (<work>/ID/scope-baseline.json) is `git status --porcelain=v1 -uall` plus a content hash of each dirty
or untracked file, so work that was already uncommitted (other people's) never counts. A file counts as changed
when it is dirty now and was not dirty at the baseline, or its content hash differs. Skipped: the work folder,
`.claude/core/**`, `.cursor/**`, the project's `guard.generated` globs and files git ignores. A plan entry ending in
"/" means the whole folder. Without a baseline, or without git, the check prints a note and passes.

Importable for a stop hook: `unplanned(tid) -> list[str]` (empty without baseline or git; never raises; one
`git status`, hashes only the files dirty at the baseline). Read-only git only (status, check-ignore, rev-parse);
GIT_OPTIONAL_LOCKS=0 keeps `git status` from touching the index. Not covered: commits made after the baseline.
Exit codes: 0 ok / nothing to check, 1 unplanned files, 2 usage error.
"""
import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.dont_write_bytecode = True
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:  # `python -I` leaves the script's folder off sys.path
    sys.path.insert(0, _HERE)
import project  # noqa: E402

SECTION = "Planned files"
PLAN_FILES = ("design.md", "triage.md")
BASELINE = "scope-baseline.json"
ALWAYS_SKIP = [".claude/core/**", ".cursor/**"]
BIG_FILE = 32 * 1024 * 1024  # above this a file is "hashed" by size and mtime only
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_BULLET = re.compile(r"^\s*[-*+]\s+(.*\S)\s*$")


# ---------------------------------------------------------------- git (read-only)

def _git(root, args, data=None, timeout=20):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    kw = {"creationflags": 0x08000000} if sys.platform == "win32" else {}  # no console window from a hook
    try:
        return subprocess.run(["git", *args], cwd=root, input=data, capture_output=True, timeout=timeout,
                              env=env, **kw)
    except (OSError, subprocess.SubprocessError):
        return None


def _prefix(root):
    """Folder of the repo root inside its git work tree ("" when it is the top); None when there is no git repo."""
    if os.path.exists(os.path.join(root, ".git")):
        return ""
    p = _git(root, ["rev-parse", "--is-inside-work-tree", "--show-prefix"])
    if p is None or p.returncode != 0:
        return None
    lines = p.stdout.decode("utf-8", "replace").split("\n")
    if not lines or lines[0].strip() != "true":
        return None
    return (lines[1].strip() if len(lines) > 1 else "").replace("\\", "/")


def _parse_status(raw, prefix=""):
    """`git status --porcelain=v1 -z` output -> {path: "XY"}; paths relative to the repo root (prefix stripped)."""
    out, parts, i, pre = {}, raw.decode("utf-8", "replace").split("\0"), 0, prefix.lower()
    while i < len(parts):
        e, i = parts[i], i + 1
        if len(e) < 4 or e[2] != " ":
            continue
        xy, items = e[:2], [(e[3:], e[:2])]
        if "R" in xy or "C" in xy:  # the next record is the original path; a renamed-away file is a change too
            orig, i = (parts[i] if i < len(parts) else ""), i + 1
            if "R" in xy and orig:
                items.append((orig, " D"))
        for path, st in items:
            path = path.replace("\\", "/").rstrip("/")
            if pre:
                if not path.lower().startswith(pre):
                    continue
                path = path[len(pre):]
            if path:
                out[path] = st
    return out


def _dirty(root):
    """{path: "XY"} for every dirty or untracked file; None when there is no git repo or git cannot answer."""
    prefix = _prefix(root)
    if prefix is None:
        return None
    args = ["status", "--porcelain=v1", "-uall", "-z"] + (["--", "."] if prefix else [])
    p = _git(root, args)
    if p is None or p.returncode != 0:
        return None
    return _parse_status(p.stdout, prefix)


def _head(root):
    p = _git(root, ["rev-parse", "HEAD"])
    return p.stdout.decode("utf-8", "replace").strip() if p is not None and p.returncode == 0 else ""


def _ignored(root, paths):
    """The subset of paths git ignores (`git check-ignore`; tracked files are never reported)."""
    if not paths:
        return set()
    p = _git(root, ["check-ignore", "--stdin", "-z"], data=("\0".join(paths) + "\0").encode("utf-8"))
    if p is None or p.returncode not in (0, 1):
        return set()
    return {x.replace("\\", "/") for x in p.stdout.decode("utf-8", "replace").split("\0") if x}


def _hash(root, path):
    """Content hash of one working-tree file ("missing" when gone, "dir" for a folder); a huge file is hashed by size
    and mtime only."""
    fp = os.path.join(root, *path.split("/"))
    try:
        with open(fp, "rb") as f:
            st = os.fstat(f.fileno())
            if st.st_size > BIG_FILE:
                return "big:%d:%d" % (st.st_size, st.st_mtime_ns)
            h = hashlib.sha1()
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return "dir" if os.path.isdir(fp) else "missing"


def _hash_all(root, paths):
    """{path: hash}; many files are hashed on a few threads (file opens dominate on Windows)."""
    paths = list(paths)
    if len(paths) < 64:
        return {p: _hash(root, p) for p in paths}
    with ThreadPoolExecutor(max_workers=8) as ex:
        return dict(zip(paths, ex.map(lambda p: _hash(root, p), paths)))


# ---------------------------------------------------------------- plan (Planned files section)

def _read(path):
    """(lines, newline, had_final_newline) of a text file; lines are LF-normalised."""
    with open(path, "rb") as f:
        text = f.read().decode("utf-8", "replace")
    nl = "\r\n" if "\r\n" in text else "\n"
    text = text.replace("\r\n", "\n")
    return text.split("\n"), nl


def _section(lines):
    """(heading index, end index) of the `## Planned files` section (up to the next heading of the same or a higher
    level, headings inside code fences ignored); None when there is none."""
    start, level, fence = None, 0, False
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("```"):
            fence = not fence
            continue
        m = None if fence else _HEADING.match(ln)
        if not m:
            continue
        if start is None:
            if m.group(2).strip().rstrip(":").strip().lower() == SECTION.lower():
                start, level = i, len(m.group(1))
        elif len(m.group(1)) <= level:
            return start, i
    return (start, len(lines)) if start is not None else None


def _entry(text):
    """Path or glob of one bullet: `path`, `path - reason`, `- [ ] path`, `**path**: reason` -> path."""
    text = re.sub(r"^\[[ xX]\]\s*", "", text.strip())
    m = re.match(r"`([^`]+)`", text)
    path = m.group(1) if m else re.split(r"\s+[-–—]\s+", text, maxsplit=1)[0]
    path = path.strip().strip("*`\"'").rstrip(":").strip().replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    return path


def _planned(lines):
    """Plan entries (as written, trailing "/" kept) of the section in lines; None when there is no section."""
    b = _section(lines)
    if b is None:
        return None
    out, fence = [], False
    for ln in lines[b[0] + 1:b[1]]:
        if ln.lstrip().startswith("```"):
            fence = not fence
            continue
        m = None if fence else _BULLET.match(ln)
        if m and _entry(m.group(1)):
            out.append(_entry(m.group(1)))
    return out


def _task_dir(root, tid):
    if not tid or re.search(r"[\\/]|^\.+$", tid):
        return None
    return os.path.join(project.work_dir(root), tid)


def _plan_file(tdir):
    """Path of the plan file that has the section (design.md before triage.md); None when neither has it."""
    for name in PLAN_FILES:
        fp = os.path.join(tdir, name)
        if os.path.isfile(fp) and _section(_read(fp)[0]) is not None:
            return fp
    return None


def _globs(entries):
    return [e + "**" if e.endswith("/") else e for e in entries]


# ---------------------------------------------------------------- scan

def _skip_globs(root):
    gen = (project.config(root).get("guard") or {}).get("generated") or []
    return ALWAYS_SKIP + [g for g in gen if isinstance(g, str)]


def _scan(tid, root=None):
    """-> (state, changed, unplanned, plan_file). state: "ok", "nogit", "nobaseline" or "badbaseline"."""
    root = root or project.repo_root()
    dirty = _dirty(root)
    if dirty is None:
        return "nogit", [], [], None
    tdir = _task_dir(root, tid)
    bp = os.path.join(tdir, BASELINE) if tdir else None
    if not bp or not os.path.isfile(bp):
        return "nobaseline", [], [], None
    try:
        with open(bp, encoding="utf-8") as f:
            files = json.load(f)["files"]
        base = {k.lower(): v for k, v in files.items()}
    except (OSError, ValueError, KeyError, AttributeError):
        return "badbaseline", [], [], None

    skip, work = _skip_globs(root), project.rel(project.work_dir(root), root)
    if work in (".", ""):
        work = None
    changed, was_dirty = [], []
    for path in dirty:
        low = path.lower()
        if work and (low == work or low.startswith(work + "/")) or project.match(low, skip):
            continue
        (was_dirty if low in base else changed).append(path)  # not dirty at the baseline = changed
    for path, h in _hash_all(root, was_dirty).items():
        if h != base[path.lower()]:
            changed.append(path)
    changed.sort(key=str.lower)

    plan_fp = _plan_file(tdir)
    globs = _globs(_planned(_read(plan_fp)[0]) or []) if plan_fp else []
    bad = [p for p in changed if not project.match(p, globs)]
    gone = _ignored(root, bad)
    if gone:
        changed = [p for p in changed if p not in gone]
        bad = [p for p in bad if p not in gone]
    return "ok", changed, bad, plan_fp


def unplanned(tid):
    """Repo-relative paths changed since the baseline that the plan does not name. [] without baseline or git; never
    raises (for a stop hook)."""
    try:
        state, _changed, bad, _fp = _scan(tid)
        return bad if state == "ok" else []
    except Exception:  # noqa: BLE001 - a hook must never fail on this
        return []


# ---------------------------------------------------------------- commands

def cmd_baseline(tid):
    root = project.repo_root()
    tdir = _task_dir(root, tid)
    if not tdir or not os.path.isdir(tdir):
        print("scope_check: no task folder for %r in %s" % (tid, project.work_dir(root)), file=sys.stderr)
        return 2
    dirty = _dirty(root)
    if dirty is None:
        print("no git: scope check skipped")
        return 0
    data = {"version": 1, "task": tid, "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "head": _head(root),
            "files": dict(sorted(_hash_all(root, dirty).items(), key=lambda kv: kv[0].lower()))}
    bp = os.path.join(tdir, BASELINE)
    with open(bp + ".tmp", "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=1)
        f.write("\n")
    os.replace(bp + ".tmp", bp)
    print("Scope baseline saved: %d files were already uncommitted and are not counted" % len(data["files"]))
    return 0


def cmd_check(tid):
    root = project.repo_root()
    state, changed, bad, plan_fp = _scan(tid, root)
    if state == "nogit":
        print("no git: scope check skipped")
        return 0
    if state != "ok":
        print("No scope baseline for %s%s: run `scope_check.py baseline %s` at Build start. Scope check skipped."
              % (tid, " (unreadable)" if state == "badbaseline" else "", tid))
        return 0
    try:
        base_head = json.load(open(os.path.join(_task_dir(root, tid), BASELINE), encoding="utf-8")).get("head")
        if base_head and _head(root) not in ("", base_head):
            print("note: HEAD moved since the baseline; files committed since then are not covered")
    except (OSError, ValueError, AttributeError):
        pass
    if not bad:
        print("Scope check passed (%d changed files, all planned)" % len(changed))
        return 0
    for p in bad:
        print("UNPLANNED " + p)
    where = os.path.basename(plan_fp) if plan_fp else "design.md (or triage.md)"
    print("%d changed file%s not in the Planned files of %s. Name each with `scope_check.py add %s <path> --why "
          "\"<reason>\"`, or undo the change." % (len(bad), "" if len(bad) == 1 else "s", where, tid))
    return 1


def _norm_path(root, path):
    p = path.strip().strip("\"'")
    if os.path.isabs(p):
        r = os.path.relpath(p, root)
        p = p if r.startswith("..") or os.path.isabs(r) else r
    p = p.replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p


def cmd_add(tid, path, why):
    root = project.repo_root()
    tdir = _task_dir(root, tid)
    if not tdir or not os.path.isdir(tdir):
        print("scope_check: no task folder for %r in %s" % (tid, project.work_dir(root)), file=sys.stderr)
        return 2
    path = _norm_path(root, path)
    why = " ".join((why or "").split())
    if not path or not why:
        print("scope_check: add needs a path and a --why reason", file=sys.stderr)
        return 2
    fp = _plan_file(tdir)
    if fp is None:  # no section yet: design.md if there is one, else triage.md
        fp = next((os.path.join(tdir, n) for n in PLAN_FILES if os.path.isfile(os.path.join(tdir, n))), None)
        if fp is None:
            print("scope_check: %s has no design.md or triage.md to put the plan in" % tdir, file=sys.stderr)
            return 2
    lines, nl = _read(fp)
    have = _planned(lines)
    if have is not None and path.lower() in [e.lower() for e in have]:
        print("Already planned: %s (%s)" % (path, os.path.basename(fp)))
        return 0
    bullet = "- %s - %s" % ("`%s`" % path if re.search(r"\s", path) else path, why)
    b = _section(lines)
    if b is None:
        while lines and not lines[-1].strip():
            lines.pop()
        lines += ["", "## " + SECTION, "", bullet, ""]
    else:
        last = b[0]
        for j in range(b[0] + 1, b[1]):
            if lines[j].strip():
                last = j
        lines[last + 1:last + 1] = ([""] if last == b[0] else []) + [bullet]
    with open(fp, "wb") as f:
        f.write(nl.join(lines).encode("utf-8"))
    print("Added to Planned files in %s: %s" % (os.path.basename(fp), bullet[2:]))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="scope_check.py", description="Files a task changed must be ones its plan named.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("baseline", help="snapshot what is already uncommitted (run at Build start)").add_argument("id")
    sub.add_parser("check", help="list files changed since the baseline that the plan does not name").add_argument("id")
    a = sub.add_parser("add", help="add a path or glob to the Planned files section")
    a.add_argument("id")
    a.add_argument("path")
    a.add_argument("--why", required=True, help="why this file is in scope")
    args = ap.parse_args(argv)
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    if args.cmd == "baseline":
        return cmd_baseline(args.id)
    if args.cmd == "check":
        return cmd_check(args.id)
    return cmd_add(args.id, args.path, args.why)


if __name__ == "__main__":
    sys.exit(main())
