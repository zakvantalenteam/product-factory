"""Build the Claude Code plugin product-factory from the core source, for the marketplace in the core's home repo.

  python core/scripts/build_plugin.py [--check]

Writes <home>/plugin/ (home = the folder above core/, which holds .claude-plugin/marketplace.json): the core's
agents, skills, hooks, scripts, reference, templates, VERSION and .claude-plugin/plugin.json, with every
`.claude/core/` path in agent and skill text turned into `${CLAUDE_PLUGIN_ROOT}/` (Claude Code fills it in, so the
plugin works in a repo that does not carry the core). install.py runs it when it installs into the home repo.
Repos that carry the core switch the plugin off in their settings (install.py), so its hooks never run twice.
It also writes the "Certified agents" table of <home>/README.md (between its certified-agents markers) from each
agent's `role:` and `certifications:` frontmatter, with the exam scores in core/exam-scores.json.
--check exits 1 when plugin/ or that table is not what a build would write (the sync workflow runs it before
anything ships).
"""
import argparse
import filecmp
import json
import os
import re
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import project  # noqa: E402

CORE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
HOME = os.path.dirname(CORE)
OUT = os.path.join(HOME, "plugin")
README = os.path.join(HOME, "README.md")
MARKS = ("<!-- certified-agents:start (build_plugin.py writes this table from the agent files) -->",
         "<!-- certified-agents:end -->")
SCORES = os.path.join(CORE, "exam-scores.json")  # blind exam scores per agent and core version, for the table
SKIP = {"__pycache__", "migration", "core-plan.md", "core.lock", "exam-scores.json"}
REWRITE = ("agents", "skills")  # markdown Claude reads: paths into the core point at the plugin root


def certified_table():
    with open(SCORES, encoding="utf-8") as fh:
        ex = json.load(fh)
    vers, top, got = ex["versions"], ex["max"], ex["agents"]
    rows = ["| Agent | Role | Certifications (general) | SAP |" + "".join(" Exam %s |" % v for v in vers),
            "|---|---|---|---|" + "---|" * len(vers)]
    folder = os.path.join(CORE, "agents")
    for f in sorted(os.listdir(folder)):
        with open(os.path.join(folder, f), encoding="utf-8") as fh:
            text = fh.read()
        certs = project.certifications(text)
        role = re.search(r"^role:[ \t]*(.*)$", text, re.M)
        gen = [c for c in certs if not c.startswith(project.SAP_CERT)]
        sap = [c for c in certs if c.startswith(project.SAP_CERT)]
        s = got.get(f[:-3], {})
        rows.append("| `%s` | %s | %s | %s |" % (f[:-3], role.group(1).strip() if role else "", "<br>".join(gen) or "-",
                                                 "<br>".join(sap) or "-")
                    + "".join(" %s |" % ("%d/%d" % (s[v], top) if v in s else "-") for v in vers))
    done = [a for a in got if all(v in got[a] for v in vers)]
    rows.append("| **Total (%d examined)** | | | |" % len(done)
                + "".join(" **%d/%d** |" % (sum(got[a][v] for a in done), top * len(done)) for v in vers))
    return "\n".join(rows)


def cert_drift():
    """Agents whose `Certified as:` line does not start with the text their `certifications:` list stands for."""
    out = []
    folder = os.path.join(CORE, "agents")
    for f in sorted(os.listdir(folder)):
        with open(os.path.join(folder, f), encoding="utf-8") as fh:
            text = fh.read()
        want = project.certified_line(project.certifications(text))
        line = next((x for x in text.splitlines() if x.startswith("Certified as: ")), "")
        if line != want and not line.startswith(want + " "):
            out.append(f[:-3])
    return out


def readme(write):
    """The README with its certified-agents table rebuilt; True when the file already matched."""
    with open(README, encoding="utf-8", newline="") as fh:
        raw = fh.read()
    nl = "\r\n" if "\r\n" in raw else "\n"
    text = raw.replace("\r\n", "\n")
    a, b = text.find(MARKS[0]), text.find(MARKS[1])
    if a < 0 or b < a:
        sys.exit("README.md has no certified-agents markers")
    new = text[:a + len(MARKS[0])] + "\n" + certified_table() + "\n" + text[b:]
    if write and new != text:
        with open(README, "w", encoding="utf-8", newline="") as fh:
            fh.write(new.replace("\n", nl))
    return new == text


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
    drift = cert_drift()
    if drift:
        sys.exit("Certified as line differs from the certifications list in: " + ", ".join(drift))
    if a.check:
        tmp = tempfile.mkdtemp(prefix="plugin-")
        try:
            build(os.path.join(tmp, "plugin"))
            diff = differences(os.path.join(tmp, "plugin"), OUT) if os.path.isdir(OUT) else ["plugin/ is missing"]
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        for d in diff[:20]:
            print("stale  " + os.path.relpath(d, tmp) if d.startswith(tmp) else "stale  " + d)
        same = readme(write=False)
        if not same:
            print("stale  README.md: its Certified agents table differs from the agent files")
        print("plugin up to date" if not diff and same else "plugin/ is stale: run python core/scripts/build_plugin.py")
        sys.exit(1 if diff or not same else 0)
    build(OUT)
    readme(write=True)
    print("plugin built: %s" % OUT)


if __name__ == "__main__":
    main()
