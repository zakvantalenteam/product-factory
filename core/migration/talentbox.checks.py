#!/usr/bin/env python3
"""TalentBox repo checks that a regex rule cannot do. Called by the agent core's `checks` hook after an Edit or Write.

Install: copy this file to <repo>/.claude/scripts/checks.py (LearningAdmin) and add to .claude/project.json:
  "checks": [{"id": "UI5", "paths": ["src/main/resources/static/view/**/*.xml"],
              "command": "python .claude/scripts/checks.py xml",
              "message": "the XML no longer parses; UI5 silently drops every control after the error"}]

    checks.py xml <repo-relative path>

  xml  a UI5 view/fragment that no longer parses (a duplicate attribute silently truncates the view), unless
       HEAD's version was already broken. Ported from `xml_problem` in the repo's old hooks/rules_check.py.

Contract (core `checks` hook): cwd is the repo root, CLAUDE_PROJECT_DIR is set, stdin is the hook payload JSON
(not needed here: the file is read from disk). Exit 0 = fine; exit 1 = problem, each stdout line is one problem
(the core prints `<id>: <message> -> <line>`). Any internal error exits 0 (fail open).
"""
import os
import subprocess
import sys
import xml.dom.minidom

REPO_DIR = os.path.abspath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def xml_problem(path):
    """The parser error of a UI5 view/fragment that no longer parses, unless HEAD's version was already broken;
    None when it parses or the check cannot decide. Takes the path in its own case: `git show HEAD:<path>` is
    case-sensitive."""
    full = os.path.abspath(os.path.join(REPO_DIR, path))
    if not os.path.isfile(full):
        return None
    try:
        xml.dom.minidom.parse(full)
        return None
    except Exception as e:
        err = str(e)
    try:
        head = subprocess.run(["git", "show", "HEAD:" + os.path.relpath(full, REPO_DIR).replace("\\", "/")],
                              cwd=REPO_DIR, capture_output=True, timeout=5)
        if head.returncode == 0:  # a new file has no HEAD version: report it
            xml.dom.minidom.parseString(head.stdout)
    except Exception:
        return None  # HEAD's version is broken too (not this edit's fault), or git failed: fail open
    return " ".join(err.split())[:120]


def check_xml(path):
    if not path.replace("\\", "/").lower().endswith(".xml"):
        return []
    p = xml_problem(path)
    return [p] if p else []


CHECKS = {"xml": check_xml}


def main():
    try:
        cmd, path = sys.argv[1], sys.argv[2]
        problems = CHECKS[cmd](path)
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
