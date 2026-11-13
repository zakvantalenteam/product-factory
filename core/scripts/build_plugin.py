"""Build the Claude Code plugin product-factory from the core source, for the marketplace in the core's home repo.

  python core/scripts/build_plugin.py [--check]

Writes <home>/plugin/ (home = the folder above core/, which holds .claude-plugin/marketplace.json): the core's
agents, skills, hooks, scripts, reference, templates, VERSION and .claude-plugin/plugin.json, with every
`.claude/core/` path in markdown (agents, skills and their files, reference, templates) turned into
`${CLAUDE_PLUGIN_ROOT}/`: Claude Code fills it in inside agent and SKILL.md bodies, and the plugin's session start
note names the folder for the rest. Scripts and hooks need no rewrite: they find the core from their own folder
(project.core_path). install.py turns the paths back when it installs from the plugin, and runs this build when it
installs into the home repo. Repos that carry the core switch the plugin off in their settings, so no hook runs
twice; the plugin's hooks do nothing in a repo without .claude/project.json.
The build fails on a skill or agent header that is not valid YAML (Claude Code would drop its fields) and on a
plugin.json version that differs from VERSION, then runs `claude plugin validate --strict` on the result when the
claude CLI is on PATH (a warning when it is not).
It also writes the "Certified agents" table of <home>/README.md (between its certified-agents markers) from each
agent's `role:`, `model:` and `certifications:` frontmatter, with the exam scores in core/exam-scores.json.
Hook entries: core/hooks/hooks.json names each hook as `python ${CLAUDE_PLUGIN_ROOT}/<file> <args>`; the plugin's
hooks.json runs it through LAUNCHER (`python -c <launcher> <mode> ${CLAUDE_PLUGIN_ROOT}/<file> <args>`), so the
entry depends on no file. With the file there the launcher runs it unchanged (same stdin, output and exit code).
With the file missing (a plugin copy that synced incompletely): mode `block` (the entry with onFailure block, the
guard) exits 2 with a message naming the copy, its folder, the missing file and the fix; mode `warn` (SessionStart)
prints a one-line warning; mode `quiet` (every other hook) stays silent, because session start already warns. In a
folder without .claude/project.json the guard does nothing, so the launcher lets the call through there too.
The build and --check fail when hooks/hooks.json or .claude-plugin/plugin.json names a ${CLAUDE_PLUGIN_ROOT} path
that is not in plugin/.
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
SKIP = {"__pycache__", "migration", "core-plan.md", "core.lock", "exam-scores.json", "release.py"}  # release.py: home only
ROOT_VAR = "${CLAUDE_PLUGIN_ROOT}/"
# The hook launcher, one `python -c` line: argv = <mode> <file> <args>. No double quote, $, %, ^, &, |, <, >, !,
# backquote or backslash in it, so it passes unchanged through Claude Code's argument list and through Git Bash or
# PowerShell 5.1 when run by hand.
LAUNCHER = ";".join([
    "import itertools,json,os,runpy,sys",
    "m=(sys.argv[1:2] or ['block'])[0]",
    "p=os.path.abspath(sys.argv[2]) if sys.argv[2:] else ''",
    # a launcher error blocks in block mode (fail closed) and passes otherwise
    "sys.excepthook=lambda t,v,b:(sys.stderr.write('product-factory: the hook launcher failed ('+repr(v)+'), so '"
    "+('this call is blocked' if m=='block' else 'this hook did not run')+chr(10)),sys.stderr.flush(),"
    "os._exit(2 if m=='block' else 0))",
    # M(): the file is missing; returns the exit code. c = the project folder as project.repo_root finds it,
    # o = it opted in to the core, r = the plugin copy's folder, n = which copy, x = the fix, q = the missing file
    "M=lambda:("
    "c:=os.environ.get('CLAUDE_PROJECT_DIR') or next((x for x in itertools.accumulate(range(64),"
    "lambda d,i:os.path.dirname(d),initial=os.getcwd()) if os.path.isdir(os.path.join(x,'.claude'))),os.getcwd()),"
    "o:=os.path.isfile(os.path.join(c,'.claude','project.json')),"
    "r:=os.path.dirname(os.path.dirname(p)),"
    "w:=r.replace(os.sep,'/'),"
    "k:=(w.split('/plugins/cache/')[1:] or [''])[0].split('/'),"
    "v:=open(os.path.join(r,'VERSION')).read().strip() if os.path.isfile(os.path.join(r,'VERSION')) else '?',"
    "n:=('the marketplace copy of the '+k[1]+' plugin ('+k[1]+'@'+k[0]+' '+v+')') if k[2:] else "
    "('the claude.ai copy of the product-factory plugin (product-factory@inline '+v+', synced from claude.ai)') "
    "if '/rpm/' in w else ('a copy of the product-factory plugin ('+v+')'),"
    "x:='turn it off or update it in the plugin manager (/plugin)' if k[2:] else "
    "'turn it off on claude.ai or in the plugin manager, or update it on claude.ai' if '/rpm/' in w else "
    "'turn it off in the plugin manager, or reinstall or update it',"
    "q:=os.path.relpath(p,r).replace(os.sep,'/'),"
    "t:=n+' is missing '+q+' (folder '+r+')',"
    "o and m=='block' and sys.stderr.write('Blocked: '+t+', so its safety guard cannot check this call. Fix: '+x+'.'"
    "+chr(10)),"
    "o and m=='warn' and print(json.dumps({'systemMessage':'Warning: '+t+'; this copy is incomplete. Fix: '+x+'.',"
    "'hookSpecificOutput':{'hookEventName':'SessionStart','additionalContext':'Warning: '+t+'; this copy is "
    "incomplete. Tell the developer to '+x+'.'}})),"
    "2 if o and m=='block' else 0)[-1]",
    "os.path.isfile(p) or sys.exit(M())",
    # the file is there: run it as `python <file> <args>` would (its folder first on sys.path, not the working folder)
    "sys.argv=[p]+sys.argv[3:]",
    "sys.path[0]=os.path.dirname(p)",
    "sys.excepthook=sys.__excepthook__",
    "runpy.run_path(p,run_name='__main__')",
])


def certified_table():
    with open(SCORES, encoding="utf-8") as fh:
        ex = json.load(fh)
    vers, top, got = ex["versions"], ex["max"], ex["agents"]
    rows = ["| Agent | Role | Model | Certifications (general) | SAP |" + "".join(" Exam %s |" % v for v in vers),
            "|---|---|---|---|---|" + "---|" * len(vers)]
    folder = os.path.join(CORE, "agents")
    for f in sorted(os.listdir(folder)):
        with open(os.path.join(folder, f), encoding="utf-8") as fh:
            text = fh.read()
        certs = project.certifications(text)
        role = re.search(r"^role:[ \t]*(.*)$", text, re.M)
        model = re.search(r"^model:[ \t]*(\S+)", text, re.M)
        model = {"opus": "Opus", "sonnet": "Sonnet 5.5"}.get(model.group(1).lower(), model.group(1)) if model else "-"
        gen = [c for c in certs if not c.startswith(project.SAP_CERT)]
        sap = [c for c in certs if c.startswith(project.SAP_CERT)]
        s = got.get(f[:-3], {})
        rows.append("| `%s` | %s | %s | %s | %s |" % (f[:-3], role.group(1).strip() if role else "", model,
                                                      "<br>".join(gen) or "-", "<br>".join(sap) or "-")
                    + "".join(" %s |" % ("%d/%d" % (s[v], top) if v in s else "-") for v in vers))
    done = [a for a in got if all(v in got[a] for v in vers)]
    rows.append("| **Total (%d examined)** | | | | |" % len(done)
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


def header_errors():
    """Skill and agent files whose YAML frontmatter Claude Code cannot parse, and a plugin.json version that is not
    the core's VERSION."""
    out = []
    for d in ("agents", "skills"):
        folder = os.path.join(CORE, d)
        for name in sorted(os.listdir(folder)):
            rel = d + "/" + name + ("/SKILL.md" if d == "skills" else "")
            if rel.endswith(".md") and os.path.isfile(os.path.join(CORE, rel)):
                with open(os.path.join(CORE, rel), encoding="utf-8") as fh:
                    out += ["%s: %s" % (rel, e) for e in project.front_errors(fh.read())]
    with open(os.path.join(CORE, "VERSION"), encoding="utf-8") as fh:
        ver = fh.read().strip()
    with open(os.path.join(CORE, ".claude-plugin", "plugin.json"), encoding="utf-8") as fh:
        pj = json.load(fh)
    if pj.get("version") != ver:
        out.append(".claude-plugin/plugin.json: version %s, VERSION %s" % (pj.get("version"), ver))
    if "defaultEnabled" in pj:
        out.append(".claude-plugin/plugin.json: no defaultEnabled (the plugin manager alone switches the plugin on or off)")
    return out


def validate(folder):
    """`claude plugin validate --strict` on the built plugin; (ok, text). Without the CLI: ok with a warning."""
    import subprocess
    cli = shutil.which("claude")
    if not cli:
        return True, "warning: claude CLI not on PATH, so `claude plugin validate --strict` did not run"
    try:
        p = subprocess.run([cli, "plugin", "validate", "--strict", folder], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120)
    except Exception as e:
        return True, "warning: claude plugin validate could not run (%s)" % e
    text = (p.stdout + p.stderr).strip()
    return p.returncode == 0, "claude plugin validate --strict: " + ("ok" if p.returncode == 0 else text[-1500:])


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


def plugin_hooks(src):
    """The plugin's hooks.json text: each `python ${CLAUDE_PLUGIN_ROOT}/<file>` entry of the core's runs through
    LAUNCHER, mode block for the onFailure-block entry (the guard), warn for SessionStart, quiet for the rest."""
    with open(src, encoding="utf-8") as fh:
        cfg = json.load(fh)
    for event, entries in cfg.get("hooks", {}).items():
        for entry in entries:
            for h in entry.get("hooks", []):
                args = h.get("args") or []
                if h.get("command") != "python" or not args or not args[0].startswith(ROOT_VAR):
                    sys.exit("core/hooks/hooks.json: every hook must be `python` with args starting "
                             "${CLAUDE_PLUGIN_ROOT}/<file> (%s)" % event)
                mode = "block" if h.get("onFailure") == "block" else "warn" if event == "SessionStart" else "quiet"
                h["args"] = ["-c", LAUNCHER, mode] + args
    return json.dumps(cfg, indent=1, ensure_ascii=False) + "\n"


ROOT_FILES = ("hooks/hooks.json", ".claude-plugin/plugin.json")  # the plugin files that name ${CLAUDE_PLUGIN_ROOT} paths


def root_paths(value):
    """Every `${CLAUDE_PLUGIN_ROOT}/<path>` in a JSON value's strings, as <path>."""
    if isinstance(value, dict):
        return [p for v in value.values() for p in root_paths(v)]
    if isinstance(value, list):
        return [p for v in value for p in root_paths(v)]
    return re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s\"']+)", value) if isinstance(value, str) else []


def plugin_files_missing(folder):
    """[(path, named in)]: paths that hooks/hooks.json or .claude-plugin/plugin.json name as ${CLAUDE_PLUGIN_ROOT}/<path>
    but <folder> does not have (a missing hooks.json counts too)."""
    out = set()
    for src in ROOT_FILES:
        path = os.path.join(folder, src)
        if not os.path.isfile(path):
            if src == "hooks/hooks.json":
                out.add((src, "the build"))
            continue
        with open(path, encoding="utf-8") as fh:
            for rel in root_paths(json.load(fh)):
                if not os.path.exists(os.path.join(folder, rel)):
                    out.add((rel, src))
    return sorted(out)


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
            if rel == "hooks" and f == "hooks.json":
                with open(dst, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(plugin_hooks(src))
            elif f.endswith(".md"):
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
    bad = header_errors()
    if bad:
        sys.exit("Not built, fix these first:\n  " + "\n  ".join(bad))
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
        gone = plugin_files_missing(OUT) if os.path.isdir(OUT) else []
        for rel, src in gone:
            print("missing  plugin/%s: %s names it" % (rel, src))
        print("plugin up to date" if not diff and same and not gone
              else "plugin/ is stale: run python core/scripts/build_plugin.py")
        sys.exit(1 if diff or not same or gone else 0)
    build(OUT)
    readme(write=True)
    gone = plugin_files_missing(OUT)
    if gone:
        sys.exit("plugin built but incomplete, not in %s: %s" % (OUT, ", ".join("%s (named in %s)" % g for g in gone)))
    ok, text = validate(OUT)
    print(text)
    if not ok:
        sys.exit("plugin built but not valid: %s" % OUT)
    print("plugin built: %s" % OUT)


if __name__ == "__main__":
    main()
