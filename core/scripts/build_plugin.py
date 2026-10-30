"""Build the Claude Code plugin product-factory from the core source, for the marketplace in the core's home repo.

  python core/scripts/build_plugin.py [--check]

Writes <home>/plugin/ (home = the folder above core/, which holds .claude-plugin/marketplace.json): the core's
agents, skills, hooks, scripts, reference, templates, VERSION and .claude-plugin/plugin.json, with every
`.claude/core/` path in agent and skill text turned into `${CLAUDE_PLUGIN_ROOT}/` (Claude Code fills it in, so the
plugin works in a repo that does not carry the core). install.py runs it when it installs into the home repo.
Repos that carry the core switch the plugin off in their settings (install.py), so its hooks never run twice.
--check exits 1 when plugin/ is not what a build would write (the sync workflow runs it before anything ships).
"""
import argparse
import filecmp
import os
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
CORE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
HOME = os.path.dirname(CORE)
OUT = os.path.join(HOME, "plugin")
SKIP = {"__pycache__", "migration", "core-plan.md", "core.lock"}
REWRITE = ("agents", "skills")  # markdown Claude reads: paths into the core point at the plugin root


def build(dest):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    for top, dirs, files in os.walk(CORE):
        dirs[:] = sorted(d for d in dirs if d not in SKIP)
        rel = os.path.relpath(top, CORE)
        for f in sorted(files):
            if f in SKIP or f.endswith(".pyc"):
                continue
            src, dst = os.path.join(top, f), os.path.join(dest, rel, f)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if rel.split(os.sep)[0] in REWRITE and f.endswith(".md"):
                with open(src, encoding="utf-8", newline="") as fh:
                    text = fh.read()
                with open(dst, "w", encoding="utf-8", newline="") as fh:
                    fh.write(text.replace(".claude/core/", "${CLAUDE_PLUGIN_ROOT}/"))
            else:
                shutil.copyfile(src, dst)


def differences(a, b):
    out = []
    c = filecmp.dircmp(a, b)
    out += [os.path.join(a, x) for x in c.left_only + c.right_only + c.diff_files + c.funny_files]
    for d in c.common_dirs:
        out += differences(os.path.join(a, d), os.path.join(b, d))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not os.path.isfile(os.path.join(HOME, ".claude-plugin", "marketplace.json")):
        sys.exit("no .claude-plugin/marketplace.json in %s: the plugin is built only in the core's home repo" % HOME)
    if a.check:
        tmp = tempfile.mkdtemp(prefix="plugin-")
        try:
            build(os.path.join(tmp, "plugin"))
            diff = differences(os.path.join(tmp, "plugin"), OUT) if os.path.isdir(OUT) else ["plugin/ is missing"]
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        for d in diff[:20]:
            print("stale  " + os.path.relpath(d, tmp) if d.startswith(tmp) else "stale  " + d)
        print("plugin up to date" if not diff else "plugin/ is stale: run python core/scripts/build_plugin.py")
        sys.exit(1 if diff else 0)
    build(OUT)
    print("plugin built: %s" % OUT)


if __name__ == "__main__":
    main()
