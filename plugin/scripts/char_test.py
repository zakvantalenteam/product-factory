"""Characterization tests of the agent core: lock today's outputs of the shared methods a change touches before Build,
then prove after Build that they did not move (risk medium and high; see the sdlc skill, safety net).

  char_test.py run <id> before --dir <folder>   run every test in the folder; all must pass on today's code
  char_test.py run <id> after                   run the same tests again (the folder is remembered)
  char_test.py diff <id>                        every test whose output changed, minus the intended changes

A test is one file in the folder (the session scratchpad, never the repo) that prints the outputs it locks.
`commands.char_run` in .claude/project.json runs one test, `{file}` replaced by its path (a project script can compile
a class against the built code and run it). Without it: `python {file}` for .py, `node {file}` for .js/.mjs/.cjs.
Outputs and exit codes go to <work>/<id>/char/<phase>/<test>.out. `diff` skips the tests named under
`## Intended changes` in <work>/<id>/safety.md (`- <test file name>: <why>`) and exits 1 when any other changed.
"""
import json
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import project  # noqa: E402

ROOT = project.repo_root()
WORK = project.work_dir(ROOT)
CFG = project.config(ROOT)
DEFAULT_RUN = {".py": "python \"{file}\"", ".js": "node \"{file}\"", ".mjs": "node \"{file}\"", ".cjs": "node \"{file}\""}


def char_dir(tid, *parts):
    return os.path.join(WORK, tid, "char", *parts)


def tests_in(folder):
    return sorted(f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)) and not f.startswith(".")
                  and not f.endswith((".out", ".class", ".txt", ".md", ".json")))


def command_for(path):
    run = (CFG.get("commands") or {}).get("char_run") or DEFAULT_RUN.get(os.path.splitext(path)[1].lower())
    return run.replace("{file}", path) if run else None


def norm(text):
    return "\n".join(l.rstrip() for l in text.replace("\r\n", "\n").split("\n")).strip() + "\n"


def run(tid, phase, folder):
    remembered = char_dir(tid, "dir.txt")
    if not folder and os.path.isfile(remembered):
        folder = open(remembered, encoding="utf-8").read().strip()
    if not folder or not os.path.isdir(folder):
        sys.exit("no test folder: pass --dir <folder> (the session scratchpad) on the first run")
    os.makedirs(char_dir(tid, phase), exist_ok=True)
    with open(remembered, "w", encoding="utf-8") as f:
        f.write(os.path.abspath(folder))
    failed, ran = [], 0
    for name in tests_in(folder):
        cmd = command_for(os.path.join(os.path.abspath(folder), name))
        if not cmd:
            print("SKIP %s: no `commands.char_run` for this file type" % name)
            continue
        try:
            p = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, timeout=180)
            out, code = p.stdout.decode("utf-8", "replace"), p.returncode
            err = p.stderr.decode("utf-8", "replace")
        except subprocess.TimeoutExpired:
            out, code, err = "", "timeout", "timed out after 180 s"
        ran += 1
        with open(char_dir(tid, phase, name + ".out"), "w", encoding="utf-8", newline="\n") as f:
            f.write("exit: %s\n%s" % (code, norm(out)))
        if code != 0:
            failed.append(name)
            print("FAIL %s (exit %s): %s" % (name, code, " ".join(err.split())[:200]))
        else:
            print("PASS %s" % name)
    print("%s: %d test(s), %d failed" % (phase, ran, len(failed)))
    if phase == "before" and failed:
        print("Every characterization test must pass on today's code before Build: fix the test, not the code.")
    sys.exit(1 if failed or not ran else 0)


def intended(tid):
    try:
        text = open(os.path.join(WORK, tid, "safety.md"), encoding="utf-8").read()
    except OSError:
        return set()
    m = re.search(r"^##\s+Intended changes\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    return {re.match(r"\s*[-*]\s*`?([^`:\s]+)", l).group(1) for l in (m.group(1) if m else "").splitlines()
            if re.match(r"\s*[-*]\s*`?[^`:\s]+", l)}


def diff(tid):
    before, after = char_dir(tid, "before"), char_dir(tid, "after")
    if not os.path.isdir(before) or not os.path.isdir(after):
        sys.exit("run `char_test.py run %s before` before Build and `run %s after` after it first" % (tid, tid))
    ok_changes = intended(tid)
    changed, same, allowed = [], 0, []
    for name in sorted(os.listdir(before)):
        b = open(os.path.join(before, name), encoding="utf-8").read()
        a_path = os.path.join(after, name)
        a = open(a_path, encoding="utf-8").read() if os.path.isfile(a_path) else "(not run after Build)\n"
        test = name[:-4] if name.endswith(".out") else name
        if a == b:
            same += 1
        elif test in ok_changes:
            allowed.append(test)
        else:
            changed.append(test)
            bl, al = b.splitlines(), a.splitlines()
            i = next((k for k in range(max(len(bl), len(al))) if (bl[k:k + 1] or [""]) != (al[k:k + 1] or [""])), 0)
            print("CHANGED %s line %d:\n  before: %s\n  after:  %s" % (test, i + 1, (bl[i:i + 1] or ["(none)"])[0][:160],
                                                                     (al[i:i + 1] or ["(none)"])[0][:160]))
    for t in allowed:
        print("intended %s (listed in safety.md)" % t)
    print("%d unchanged, %d intended, %d changed" % (same, len(allowed), len(changed)))
    sys.exit(1 if changed else 0)


def main():
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == "run" and a[2] in ("before", "after"):
        folder = a[a.index("--dir") + 1] if "--dir" in a and a.index("--dir") + 1 < len(a) else None
        run(a[1], a[2], folder)
    elif len(a) == 2 and a[0] == "diff":
        diff(a[1])
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()
