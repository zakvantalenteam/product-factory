"""PostToolUse check of the agent core: the project's hard rules that a guard can't block up front.

Rules come from .claude/project.json `rules`, one object each:
  {"id": "rule 5", "paths": ["**/*.css"], "pattern": "#[0-9a-fA-F]{3,8}\\b", "message": "fixed hex colour; use the theme",
   "unless": "var\\(", "part": "line" | "value", "comments": false}
  paths     globs (project.match); the rule runs only on matching files
  pattern   regex; a line it finds is a problem
  unless    optional regex; a line it finds is fine
  part      "value" checks only the text after the first "=" (properties files); default the whole line
  comments  true also checks comment lines (//, /*, *, #, !, <!--); default false
  not_paths optional globs the rule skips (vendor, theme or test files)
  redact    true leaves the matched line out of the message (secrets)
Looks only at the lines an Edit/Write/MultiEdit added (not context lines that were already there), so legacy code
never triggers it.

Checks a regex can't do come from `checks`, one object each:
  {"id": "EP2", "paths": ["src/**/*.java"], "command": "python .claude/scripts/checks.py ep2", "message": "..."}
  The command runs as `<command> "<repo-relative path>"` in the repo root with the hook JSON on stdin. Exit 1 = a
  problem, one per stdout line (at most 5); exit 0, any other exit or over 10 s = fine.

Contract (Claude Code): exit 2 + a message on stderr reports the problems (the edit already happened, so the agent
fixes it); exit 0 when clean. Cursor (`--cursor`, postToolUse): prints {"additional_context": "..."}; nothing when
clean. Any internal error exits 0 (fail open).
"""
import json
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import project  # noqa: E402

CURSOR = "--cursor" in sys.argv
COMMENT = ("//", "/*", "*", "#", "!", "<!--")
# where "#" starts code (a CSS id selector, a JS private field), only the language's own comment marks count
C_STYLE = ("//", "/*", "*")
COMMENT_BY_EXT = dict([(e, C_STYLE) for e in ("css", "scss", "less", "js", "jsx", "mjs", "cjs", "ts", "tsx")]
                      + [(e, C_STYLE + ("<!--",)) for e in ("html", "htm", "vue", "svelte")])


def comment_marks(r):
    return COMMENT_BY_EXT.get(r.rsplit(".", 1)[-1] if "." in r else "", COMMENT)


def added_lines(tool, inp):
    """Lines the call introduced: new text minus lines that were already in the replaced text."""
    if tool == "Write":
        return (inp.get("content") or "").splitlines()
    out = []
    for e in inp.get("edits") or [inp]:
        old = set((e.get("old_string") or "").splitlines())
        out += [l for l in (e.get("new_string") or "").splitlines() if l not in old]
    return out


def cursor_edit(inp):
    """Cursor's file tools name their fields differently; map them onto (path, added lines)."""
    path = next((inp[k] for k in ("file_path", "path", "target_file", "filePath") if inp.get(k)), "")
    if "old_string" in inp or inp.get("edits"):
        return path, added_lines("Edit", inp)
    text = next((inp[k] for k in ("content", "contents", "code_edit", "file_text") if isinstance(inp.get(k), str)), "")
    return path, text.splitlines()


def check(r, lines, rules):
    problems = []
    marks = comment_marks(r)
    for rule in rules:
        if not project.match(r, rule.get("paths")) or project.match(r, rule.get("not_paths") or []):
            continue
        try:
            pat = re.compile(rule["pattern"])
            unless = re.compile(rule["unless"]) if rule.get("unless") else None
        except (KeyError, re.error):
            continue
        for l in lines:
            s = l.strip()
            if not s or (not rule.get("comments") and s.startswith(marks)):
                continue
            text = s.split("=", 1)[1] if rule.get("part") == "value" and "=" in s else s
            if pat.search(text) and not (unless and unless.search(text)):
                problems.append("%s: %s -> %s" % (rule.get("id", "rule"), rule.get("message", "breaks a hard rule"),
                                                   "(line not shown)" if rule.get("redact") else s[:120]))
    return problems


def run_checks(path, r, checks, data):
    """The project's own check scripts for this file (`checks`); they get the path in its real case."""
    import subprocess
    problems = []
    root = project.repo_root()
    real = os.path.relpath(os.path.abspath(path), root).replace("\\", "/")
    payload = json.dumps(data).encode("utf-8")
    for c in checks:
        if not c.get("command") or not project.match(r, c.get("paths")) or project.match(r, c.get("not_paths") or []):
            continue
        try:
            p = subprocess.run('%s "%s"' % (c["command"], real), shell=True, cwd=root, input=payload,
                               capture_output=True, timeout=10)
        except Exception:
            continue
        if p.returncode != 1:
            continue
        for line in p.stdout.decode("utf-8", "replace").splitlines()[:5]:
            if line.strip():
                problems.append("%s: %s -> %s" % (c.get("id", "check"), c.get("message", "project check"),
                                                   line.strip()[:160]))
    return problems


def live(text, data):
    try:
        import live_status
        live_status.record("flag", text, "rules check", data)
    except Exception:
        pass


def main():
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace") or "{}")
    except Exception:
        return
    cfg = project.config()
    rules, checks = cfg.get("rules") or [], cfg.get("checks") or []
    if not rules and not checks:
        return
    tool = data.get("tool_name", "")
    inp = data.get("tool_input") or {}
    if isinstance(inp, str):
        inp = json.loads(inp)
    if CURSOR:
        path, lines = cursor_edit(inp)
    elif tool in ("Edit", "Write", "MultiEdit"):
        path, lines = inp.get("file_path") or "", added_lines(tool, inp)
    else:
        return
    r = project.rel(path) if path else None
    if not r:
        return
    problems = check(r, lines, rules) + run_checks(path, r, checks, data)
    if problems:
        msg = "Hard-rule check on " + r + ":\n- " + "\n- ".join(problems[:10]) + "\n"
        live("Hard-rule check on " + r.rsplit("/", 1)[-1] + ": " + problems[0][:160], data)
        if CURSOR:
            print(json.dumps({"additional_context": msg}))
            return
        sys.stderr.write(msg)
        sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
