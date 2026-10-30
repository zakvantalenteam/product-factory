#!/usr/bin/env python3
"""SkillsOS repo checks that a regex rule cannot do. Called by the agent core's `checks` hook after an Edit or Write.

Install: copy this file to <repo>/.claude/scripts/checks.py (next to locales.py) and add the `checks` array from
skillsos.project.json to .claude/project.json.

    checks.py ep2 <repo-relative path>   Backend/src/main/java/**/*.java
    checks.py db2 <repo-relative path>   Backend/src/main/resources/db/*.sql
    checks.py db9 <repo-relative path>   Backend/src/main/resources/db/*.sql
    checks.py lo1 <repo-relative path>   Frontend/src/locales/*.json

  ep2  MUST EP2: an added line has @RequestBody binding a class that is an @Entity (mass assignment); use a DTO.
  db2  MUST DB2: a NEW db script (not tracked by git) must be named NN_snake_case.sql with the next free number.
  db9  SHOULD DB9: a NEW db script written whole (Write tool) needs a header comment with the rollback SQL.
  lo1  MUST LO1: key parity across the five locale files, from `.claude/scripts/locales.py` (parity()).

Ported from .claude/hooks/rules_check.py (check_java, check_sql, check_locales); like the original, ep2 looks only
at the lines the Edit/Write added, so legacy code never triggers it.

Contract (core `checks` hook): cwd is the repo root, CLAUDE_PROJECT_DIR is set, stdin is the hook payload JSON
(tool_name, tool_input with file_path, old_string/new_string or content). Exit 0 = fine; exit 1 = problem, each
stdout line is one problem (the core prints `<id>: <message> -> <line>`). Any internal error exits 0 (fail open).
"""
import json
import os
import re
import subprocess
import sys

REPO_DIR = os.path.abspath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
REPO = os.path.normcase(REPO_DIR)
JAVA = "backend/src/main/java/"
DB = "backend/src/main/resources/db/"
FE = "frontend/src/"

REQUEST_BODY = re.compile(r"@RequestBody\s+(?:@Valid(?:ated)?\s+)?(?:final\s+)?([A-Z]\w*)\b")


def rel(path):
    """Repo-relative path with forward slashes, lower-cased (Windows paths are case-insensitive)."""
    a = os.path.abspath(os.path.join(REPO_DIR, path))
    if not os.path.normcase(a).startswith(REPO + os.sep):
        return None
    return os.path.relpath(a, REPO_DIR).replace("\\", "/").lower()


def added_lines(tool, inp):
    """Lines the call introduced: new text minus lines that were already in the replaced text."""
    if tool == "Write":
        return (inp.get("content") or "").splitlines()
    pairs = inp.get("edits") or [inp]
    out = []
    for e in pairs:
        old = set((e.get("old_string") or "").splitlines())
        out += [l for l in (e.get("new_string") or "").splitlines() if l not in old]
    return out


def read_edit():
    """(added lines, whole file written) from the hook payload on stdin; ([], False) when there is none."""
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace"))
        tool = data.get("tool_name", "")
        inp = data.get("tool_input") or {}
        if isinstance(inp, str):
            inp = json.loads(inp)
        if tool in ("Edit", "Write", "MultiEdit"):
            return added_lines(tool, inp), tool == "Write"
        if "old_string" in inp or inp.get("edits"):  # Cursor's file tools
            return added_lines("Edit", inp), False
        key = next((k for k in ("content", "contents", "code_edit", "file_text") if isinstance(inp.get(k), str)), "")
        return (inp.get(key) or "").splitlines(), key in ("content", "contents", "file_text")
    except Exception:
        return [], False


def is_comment(s):
    return s.startswith(("//", "/*", "*", "#", "!"))


def one_line(s, n=120):
    return " ".join(str(s).split())[:n]


def entity_names():
    names = set()
    base = os.path.join(REPO_DIR, "Backend", "src", "main", "java")
    for d, _, files in os.walk(base):
        for f in files:
            if f.endswith(".java"):
                try:
                    with open(os.path.join(d, f), encoding="utf-8", errors="replace") as fh:
                        if "@Entity" in fh.read():
                            names.add(f[:-5])
                except OSError:
                    pass
    return names


def tracked(path):
    try:
        return subprocess.run(["git", "ls-files", "--error-unmatch", "--", path], cwd=REPO_DIR,
                              capture_output=True, timeout=4).returncode == 0
    except Exception:
        return True


def check_ep2(path, r):
    if not (r.startswith(JAVA) and r.endswith(".java")):
        return []
    lines, _ = read_edit()
    problems = []
    entities = None
    for l in lines:
        s = l.strip()
        if not s or is_comment(s):
            continue
        m = REQUEST_BODY.search(s)
        if m:
            if entities is None:
                entities = entity_names()
            if m.group(1) in entities:
                problems.append("entity %s: %s" % (m.group(1), one_line(s)))
    return problems


def check_db2(path, r):
    if not (r.startswith(DB) and r.endswith(".sql")) or tracked(path):
        return []
    name = r.rsplit("/", 1)[-1]
    m = re.match(r"(\d+)_[a-z0-9_]+\.sql$", name)
    if not m:
        return [name]
    others = [f for f in os.listdir(os.path.dirname(os.path.join(REPO_DIR, path))) if f.lower() != name and re.match(r"\d+_", f)]
    nums = [int(f.split("_", 1)[0]) for f in others]
    n = int(m.group(1))
    if n in nums or (nums and n <= max(nums)):
        return ["%s: number %02d is taken or not above the highest script (%02d); use %02d" % (name, n, max(nums), max(nums) + 1)]
    return []


def check_db9(path, r):
    if not (r.startswith(DB) and r.endswith(".sql")) or tracked(path):
        return []
    lines, whole = read_edit()
    if whole and not re.search(r"(?i)rollback", "\n".join(lines)):
        return [r.rsplit("/", 1)[-1]]
    return []


def check_lo1(path, r):
    if not (r.startswith(FE + "locales/") and r.endswith(".json")):
        return []
    try:
        sys.dont_write_bytecode = True
        here = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, os.path.join(REPO_DIR, ".claude", "scripts"))
        sys.path.insert(0, here)
        import locales
        return [one_line(p) for p in locales.parity()[:10]]
    except ValueError as e:
        return ["a locale file is not valid JSON: %s" % one_line(e)]
    except Exception:
        return []


CHECKS = {"ep2": check_ep2, "db2": check_db2, "db9": check_db9, "lo1": check_lo1}


def main():
    try:
        cmd, path = sys.argv[1], sys.argv[2]
        r = rel(path)
        problems = CHECKS[cmd](path, r) if r else []
    except Exception:
        return 0  # usage error or internal error: fail open
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    for p in problems[:5]:
        print(p)
    return 1 if problems else 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception:
        code = 0
    sys.exit(code)
