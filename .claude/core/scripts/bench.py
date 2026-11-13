#!/usr/bin/env python3
"""Bug test bench (agent core): how many real escaped bugs each stage of the team catches, rerun on every release.

    bench.py cases [--project NAME|all]          the cases per project and the stages each one runs in
    bench.py check [--project NAME|all]          check every case folder: fields, files, rubrics, commits
    bench.py run --max-cost-usd N [--project NAME|all] [--stage S] [--case GLOB] [--runs 3] [-j 3]
                 [--model sonnet] [--judge-model sonnet] [--plugin DIR] [--all] [--keep] [--dry-run]
    bench.py report [--project NAME|all]         catch rate per stage and agent, against the run before

A case is a real bug that escaped, kept in the project's own repo (committed there): `.claude/bench/cases/<id>/`
with case.json (introducing and fix commit, the files around the defect, the defect, the stage that should have
caught it), ticket.md (what the developer had before the change, never the bug report) and rubric-<stage>.md for
each stage it runs in (PASS and FAIL lines for a judge). The format: reference/bench.md.

run builds one eval suite in a temp folder and runs `claude plugin eval` on it (Claude Code only): a copy of the
plugin under test without its hooks, and one eval case per case and stage. Each run starts in an empty workspace
that the case's scaffold fills with read-only git: the case files at the introducing commit, the project layer
(project.json, review checklist, lessons, accepted, rules, AGENTS.md) from just before the fix, and the stage's
input (the review pack, or the ticket and the diff). The stage's agent runs on it and a judge grades its reply
against the rubric, 2 of 3 votes. Default 3 runs per case and stage; a stage caught the bug when at least 2 of 3
runs pass. The run writes .claude/bench/history/<stamp>.json (commit it) and keeps the report, the raw result and
every reply in .claude/bench/runs/<stamp>/ (gitignored). It runs only on a claude.ai subscription's tokens, never
real money: it refuses when the claude CLI is not signed in with claude.ai or an API key or cloud provider is set.
--max-cost-usd (required) caps the run's usage at list price; --dry-run stages the suite, prints the command and the
projected usage, and runs nothing.

Projects: the current repo; from the home repo, every repo of release.local.json that has cases (--project all).
Not-catchable cases are left out of a run unless --all. The plugin under test: --plugin, else the home repo's
plugin/, else the plugin copy this script is in, else the marketplace copy that is installed.
Read-only git only (archive, ls-tree, show, cat-file, diff); never changes a repo's git. Standard library only.
Exit codes: 0 done, 1 a check failed or a run did not finish, 2 usage error.
"""
import argparse
import fnmatch
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import doctor  # noqa: E402

PLUGIN = "product-factory"
STAGES = {  # stage -> the agent that runs it and what it gets
    "review-spec": "spec-analyst",
    "code-reviewer": "code-reviewer",
    "qa-lead": "qa-lead",
}
CAUGHT_AT = tuple(STAGES) + ("not-catchable",)
REQUIRED = ("id", "title", "introduced", "fixed", "files", "defect", "caught_at")
LAYER = (".claude/project.json", ".claude/review", ".claude/rules", ".claude/experts", ".claude/qa",
         ".claude/smoke.md", "AGENTS.md", "CLAUDE.md")
TASK = "bench-1"  # neutral: a case id can hint at the bug
EST_RUN_USD = 0.75  # spike, Nov 2026: $0.65 for one code review of a 110-line diff (Opus reviewer, Sonnet judge)
CASES_DIR = os.path.join(".claude", "bench", "cases")
HISTORY_DIR = os.path.join(".claude", "bench", "history")
RUNS_DIR = os.path.join(".claude", "bench", "runs")

PROMPTS = {
    "code-reviewer": (
        "You are the Tech Lead. A change is ready for its code review. Start the {plugin}:code-reviewer agent on task "
        "{task}. Its review pack is `{work}/{task}/review-pack.md` in this workspace: the diff is in the pack, and the "
        "changed files and the files around them are in the workspace at their paths. Tell the reviewer it cannot run "
        "commands or write files here, so it must return its MUST and SHOULD findings in its reply (path:line, what "
        "is wrong, why, the fix). Do not review the change yourself. When the reviewer is done, reply with its "
        "findings exactly as it returned them, and nothing else."),
    "qa-lead": (
        "You are the Tech Lead. A change is built and needs its test plan. Start the {plugin}:qa-lead agent in mode "
        "plan on task {task}: the ticket is `{work}/{task}/ticket.md`, the change is the diff "
        "`{work}/{task}/change.diff`, and the changed files are in this workspace at their paths. Tell it it cannot run "
        "commands or write files here, so it must return the test matrix in its reply (criterion x test type x role "
        "x data volume, one row per line, each with its expected result). Do not plan the tests yourself. When it is "
        "done, reply with its matrix exactly as it returned it, and nothing else."),
    "review-spec": (
        "You are the Tech Lead. A requirement arrived before any work started. Start the {plugin}:spec-analyst agent "
        "in mode dor on task {task}: the ticket is `{work}/{task}/ticket.md`, and today's code is in this workspace. "
        "Tell it it cannot run commands or write files here, so it must return its Definition of Ready check in its "
        "reply, with every gap, open question and missing acceptance criterion. Do not check the ticket yourself. "
        "When it is done, reply with its result exactly as it returned it, and nothing else."),
}


class Usage(Exception):
    pass


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return None


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def git(repo, *args):
    """Read-only git: stdout as text, or None on failure."""
    try:
        p = subprocess.run(["git", "--no-optional-locks", "-C", repo] + list(args), capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return p.stdout.decode("utf-8", "replace") if p.returncode == 0 else None


def sq(s):
    """A bash single-quoted word."""
    return "'" + str(s).replace("'", "'\\''") + "'"


def slash(p):
    return os.path.abspath(p).replace("\\", "/")


# ---- projects and cases ----------------------------------------------------------------------------------------

def projects(name):
    """[(name, repo)] with a cases folder: the release targets from the home repo, else the current repo."""
    home = doctor.find_home("", os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude"))
    found = doctor.repo_targets(home, "") if home else []
    cur = doctor.current_repo()
    if cur and not any(doctor.same(p, cur) for _, p in found):
        found.append((os.path.basename(cur), cur))
    with_cases = [(n, p) for n, p in found if os.path.isdir(os.path.join(p, CASES_DIR))]
    if name in ("", None):
        if cur and os.path.isdir(os.path.join(cur, CASES_DIR)) and not (home and doctor.same(cur, home)):
            return [(n, p) for n, p in found if doctor.same(p, cur)][:1]
        return with_cases
    if name == "all":
        return with_cases
    pick = [(n, p) for n, p in found if n == name or os.path.basename(p) == name]
    if not pick:
        raise Usage("no project named %s (known: %s)" % (name, ", ".join(n for n, _ in found) or "none"))
    return pick


def load_case(folder):
    """(case dict, [problems]). The dict gains `stages`: {stage: rubric text} for each stage it runs in."""
    probs = []
    raw = read(os.path.join(folder, "case.json"))
    try:
        c = json.loads(raw) if raw else None
    except ValueError as e:
        c, raw = None, "invalid JSON: %s" % e
    if not isinstance(c, dict):
        return {"id": os.path.basename(folder), "stages": {}}, ["case.json missing or not a JSON object"]
    for k in REQUIRED:
        if not c.get(k):
            probs.append("case.json has no %s" % k)
    if c.get("caught_at") and c["caught_at"] not in CAUGHT_AT:
        probs.append("caught_at must be one of %s" % ", ".join(CAUGHT_AT))
    if c.get("id") and c["id"] != os.path.basename(folder):
        probs.append("id %s is not the folder name" % c["id"])
    if not isinstance(c.get("files"), list):
        probs.append("files must be a list of repo paths")
    d = c.get("defect")
    if d is not None and not (isinstance(d, dict) and d.get("file") and d.get("mechanism")):
        probs.append("defect needs file and mechanism")
    if not (read(os.path.join(folder, "ticket.md")) or "").strip():
        probs.append("ticket.md missing or empty")
    na = c.get("not_applicable") or {}
    c["stages"] = {}
    for stage in STAGES:
        rub = read(os.path.join(folder, "rubric-%s.md" % stage))
        if rub is None or stage in na:
            continue
        if not re.search(r"^\s*PASS if", rub, re.M) or not re.search(r"\bFAIL if", rub):
            probs.append("rubric-%s.md needs a 'PASS if' and a 'FAIL if' line" % stage)
        c["stages"][stage] = rub.strip()
    if not c["stages"] and c.get("caught_at") != "not-catchable":
        probs.append("no rubric-<stage>.md for any stage")
    c["folder"] = folder
    return c, probs


def cases_of(repo):
    root = os.path.join(repo, CASES_DIR)
    out = []
    for folder in sorted(glob.glob(os.path.join(root, "*", ""))):
        folder = folder.rstrip("\\/")
        if os.path.isfile(os.path.join(folder, "case.json")):
            out.append(load_case(folder))
    return out


def check_commits(repo, c):
    probs = []
    for k in ("introduced", "fixed"):
        if c.get(k) and git(repo, "cat-file", "-e", "%s^{commit}" % c[k]) is None:
            probs.append("%s commit %s not found" % (k, c[k]))
    if not probs:
        have = (git(repo, "ls-tree", "-r", "--name-only", c["introduced"], "--", *c.get("files", [])) or "").split()
        for f in c.get("files", []):
            if f not in have:
                probs.append("%s is not in the introducing commit" % f)
    return probs


# ---- the eval suite --------------------------------------------------------------------------------------------

def plugin_dir(arg):
    if arg:
        if not os.path.isfile(os.path.join(arg, ".claude-plugin", "plugin.json")):
            raise Usage("--plugin %s has no .claude-plugin/plugin.json" % arg)
        return os.path.abspath(arg)
    home = doctor.find_home("", os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude"))
    cands = [os.path.join(home, "plugin")] if home else []
    cands.append(os.path.dirname(HERE))
    copies, _old = doctor.marketplace_copies(os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude"))
    cands += [c.folder for c in copies if c.on.startswith("on")] + [c.folder for c in copies]
    for p in cands:
        if os.path.isfile(os.path.join(p, ".claude-plugin", "plugin.json")):
            return os.path.abspath(p)
    raise Usage("no %s plugin found: pass --plugin DIR" % PLUGIN)


def existing(repo, rev, paths):
    """The paths that exist at rev (top level of each)."""
    out = git(repo, "ls-tree", "--name-only", rev, "--", *paths) or ""
    have = set(out.split("\n"))
    return [p for p in paths if p in have]


def work_dir_at(repo, rev):
    try:
        cfg = json.loads(git(repo, "show", "%s:.claude/project.json" % rev) or "{}")
    except ValueError:
        cfg = {}
    return str(cfg.get("work_dir") or ".claude/work").strip("/")


def layer_rev(repo, c):
    """The project layer from just before the fix (newest knowledge without this bug's lessons), else the
    introducing commit; a case's `layer_rev` wins."""
    for rev in (c.get("layer_rev"), "%s~1" % c["fixed"], c["introduced"]):
        if rev and existing(repo, rev, [".claude/project.json", "AGENTS.md"]):
            return rev
    return c["introduced"]


def scaffold(repo, c, stage, case_dir, plugin, python):
    intro, base = c["introduced"], "%s~1" % c["introduced"]
    code_rev = base if stage == "review-spec" else intro
    files = existing(repo, code_rev, c["files"] + list(c.get("context_files") or []))
    lrev = layer_rev(repo, c)
    layer = existing(repo, lrev, list(LAYER))
    work = work_dir_at(repo, lrev)
    lines = ["#!/usr/bin/env bash",
             "# Bench snapshot: %s (%s). Read-only git only." % (c["id"], stage),
             "set -euo pipefail",
             "REPO=%s" % sq(slash(repo))]
    if files:
        lines.append('git -C "$REPO" archive %s -- %s | tar -x' % (sq(code_rev), " ".join(sq(f) for f in files)))
    if layer:
        lines.append('git -C "$REPO" archive %s -- %s | tar -x' % (sq(lrev), " ".join(sq(p) for p in layer)))
    task = "%s/%s" % (work, TASK)
    lines.append("mkdir -p %s" % sq(task))
    if stage == "code-reviewer":
        lines.append('CLAUDE_PROJECT_DIR="$PWD" PYTHONDONTWRITEBYTECODE=1 %s %s %s --root "$REPO" --base %s --head %s '
                     "--files %s > /dev/null" % (sq(python), sq(slash(os.path.join(plugin, "scripts", "review_pack.py"))),
                                                 TASK, sq(base), sq(intro), " ".join(sq(f) for f in c["files"])))
        lines.append("test -s %s" % sq(task + "/review-pack.md"))
    else:
        lines.append("cp %s %s" % (sq(slash(os.path.join(case_dir, "ticket.md"))), sq(task + "/ticket.md")))
        if stage == "qa-lead":
            lines.append('git -C "$REPO" diff %s %s -- %s > %s' % (sq(base), sq(intro),
                                                                   " ".join(sq(f) for f in c["files"]),
                                                                   sq(task + "/change.diff")))
    return "\n".join(lines) + "\n", work


def items_for(projs, stage=None, case_glob=None, all_cases=False):
    """[(project, repo, case, stage)] to run, and [(project, case id, problems)] skipped as invalid."""
    out, bad = [], []
    for name, repo in projs:
        for c, probs in cases_of(repo):
            if case_glob and not fnmatch.fnmatch(c["id"], case_glob):
                continue
            if probs:
                bad.append((name, c["id"], probs))
                continue
            if c["caught_at"] == "not-catchable" and not all_cases:
                continue
            for s in c["stages"]:
                if stage in (None, s):
                    out.append((name, repo, c, s))
    return out, bad


def eval_name(project, case_id, stage):
    return "%s--%s--%s" % (project, case_id, stage)


def stage_suite(root, plugin, items, python):
    """Copy the plugin without its hooks and write one eval case per item. Returns the suite folder."""
    suite = os.path.join(root, "suite")
    shutil.copytree(plugin, suite, ignore=shutil.ignore_patterns("hooks", "evals", "__pycache__", "*.pyc"))
    manifest = os.path.join(suite, ".claude-plugin", "plugin.json")
    m = json.loads(read(manifest) or "{}")
    if m.pop("hooks", None) is not None:
        write(manifest, json.dumps(m, indent=2) + "\n")
    for project, repo, c, stage in items:
        name = eval_name(project, c["id"], stage)
        d = os.path.join(suite, "evals", name)
        os.makedirs(os.path.join(d, "graders"))
        shutil.copy(os.path.join(c["folder"], "ticket.md"), os.path.join(d, "ticket.md"))
        script, work = scaffold(repo, c, stage, d, suite, python)
        write(os.path.join(d, "scaffold.sh"), script)
        write(os.path.join(d, "case.yaml"), 'schema_version: "1.1"\nname: %s\ntags: [%s, %s, %s]\n'
              "context:\n  scaffold_script: scaffold.sh\n" % (name, project, stage, c["caught_at"]))
        write(os.path.join(d, "prompt.md"), "---\nmax_turns: 30\ntimeout_seconds: 1800\n"
              "allowed_tools: [Read, Glob, Grep, Agent]\n---\n"
              + PROMPTS[stage].format(plugin=PLUGIN, task=TASK, work=work) + "\n")
        write(os.path.join(d, "graders", "caught.md"), "---\ntype: llm\n---\n" + c["stages"][stage] + "\n")
        write(os.path.join(d, "graders", "agent-ran.md"), "---\ntype: tool_used\ntool: Agent\n"
              "input_match: '%s:%s'\n---\n" % (PLUGIN, STAGES[stage]))
    return suite


# ---- results ---------------------------------------------------------------------------------------------------

def final_reply(trace_path):
    """The last assistant text of a run's trace, or ''."""
    last = ""
    for ln in (read(trace_path) or "").splitlines():
        try:
            m = json.loads(ln)
        except ValueError:
            continue
        msg = m.get("message") if isinstance(m, dict) else None
        if m.get("type") != "assistant" or not isinstance(msg, dict) or not isinstance(msg.get("content"), list):
            continue
        texts = [b.get("text", "") for b in msg["content"] if isinstance(b, dict) and b.get("type") == "text"]
        if any(t.strip() for t in texts):
            last = "\n".join(texts)
    return last


def grader(run, name):
    for g in run.get("graders") or []:
        if g.get("name") == name:
            return g
    return {}


def verdict(passed, runs):
    if runs == 0:
        return "not run"
    return "caught" if passed * 2 > runs else "missed"


def summarize(agg, items, replies_dir):
    """Per item: {project, case, stage, agent, caught_at, passed, runs, invalid, verdict, cost_usd}; replies are
    written to replies_dir."""
    by_name = {c.get("name"): c for c in agg.get("cases") or []}
    rows = []
    for project, _repo, c, stage in items:
        name = eval_name(project, c["id"], stage)
        runs = ((by_name.get(name) or {}).get("arms") or {}).get("with") or []
        passed = invalid = 0
        cost = 0.0
        for i, r in enumerate(runs, 1):
            cost += float(r.get("costUsd") or 0) + float(r.get("judgeCostUsd") or 0)
            ran = grader(r, "agent-ran").get("passed") is True
            if not ran or (r.get("error") and not r.get("graders")):
                invalid += 1
            elif grader(r, "caught").get("passed") is True:
                passed += 1
            reply = final_reply(r.get("tracePath") or "")
            write(os.path.join(replies_dir, "%s--%d.md" % (name, i)),
                  "# %s run %d: %s\n\n%s\n" % (name, i, "caught" if grader(r, "caught").get("passed") is True
                                                else "missed", reply or "(no reply: %s)" % (r.get("error") or "?")))
        valid = len(runs) - invalid
        rows.append({"project": project, "case": c["id"], "stage": stage, "agent": STAGES[stage],
                     "caught_at": c["caught_at"], "passed": passed, "runs": len(runs), "invalid": invalid,
                     "verdict": verdict(passed, valid), "cost_usd": round(cost, 4)})
    return rows


def plugin_version(plugin):
    return (read(os.path.join(plugin, "VERSION")) or "").strip() or doctor.plugin_version(plugin)


# ---- commands --------------------------------------------------------------------------------------------------

def cmd_cases(a):
    for name, repo in projects(a.project):
        print("## %s (%s)" % (name, repo))
        for c, probs in cases_of(repo):
            print("- %-38s %-14s %s%s" % (c["id"], c.get("caught_at", "?"), ", ".join(c["stages"]) or "-",
                                          "  (invalid: %s)" % "; ".join(probs) if probs else ""))
    return 0


def cmd_check(a):
    bad = 0
    for name, repo in projects(a.project):
        cases = cases_of(repo)
        for c, probs in cases:
            probs = probs + (check_commits(repo, c) if not probs else [])
            bad += bool(probs)
            print("%s %s/%s%s" % ("FAIL" if probs else "ok  ", name, c["id"],
                                  "".join("\n     - " + p for p in probs)))
        if not cases:
            print("no cases in %s" % os.path.join(repo, CASES_DIR))
    return 1 if bad else 0


def estimate(items, projs):
    """Cost per run: the mean of the latest history per stage, else EST_RUN_USD."""
    per = {}
    for _name, repo in projs:
        h = latest_history(repo)
        for r in (h[0] if h else {}).get("results", []):
            if r.get("runs"):
                per.setdefault(r["stage"], []).append(r["cost_usd"] / r["runs"])
    return {s: (sum(v) / len(v) if v else EST_RUN_USD) for s, v in per.items()}


PAID_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX",
            "CLAUDE_CODE_USE_FOUNDRY")


def paid_auth(cli, env):
    """Why a run could spend real money instead of the subscription's tokens, or '' when it signs in with a
    claude.ai subscription and nothing pay-per-call is set. The bench never runs on paid auth."""
    for k in PAID_ENV:
        if env.get(k):
            return "%s is set (pay per call)" % k
    try:
        p = subprocess.run([cli, "auth", "status"], capture_output=True, timeout=60, env=env)
        st = json.loads(p.stdout.decode("utf-8", "replace") or "{}")
    except (OSError, subprocess.SubprocessError, ValueError):
        return "could not read `claude auth status`"
    if not st.get("loggedIn"):
        return "the claude CLI is not signed in (run: claude auth login)"
    if st.get("authMethod") != "claude.ai":
        return "the claude CLI signs in with %s, not a claude.ai subscription" % (st.get("authMethod") or "?")
    return ""


def cmd_run(a):
    if a.max_cost_usd is None or a.max_cost_usd <= 0:
        raise Usage("--max-cost-usd is required (a ceiling on the run's usage, at list price)")
    projs = projects(a.project)
    if not projs:
        raise Usage("no project with %s here (add cases with /bench add)" % CASES_DIR.replace(os.sep, "/"))
    items, bad = items_for(projs, a.stage, a.case, a.all)
    for name, cid, probs in bad:
        print("skipped %s/%s: %s" % (name, cid, "; ".join(probs)))
    if not items:
        raise Usage("nothing to run (check --stage and --case; bench.py check lists invalid cases)")
    plugin = plugin_dir(a.plugin)
    per = estimate(items, projs)
    projected = sum(per.get(s, EST_RUN_USD) for _p, _r, _c, s in items) * a.runs
    print("bench: %d case-stages x %d runs = %d runs, plugin %s %s; projected usage about $%.2f at list price "
          "(subscription tokens, not a bill), ceiling $%.2f"
          % (len(items), a.runs, len(items) * a.runs, PLUGIN, plugin_version(plugin), projected, a.max_cost_usd))
    root = tempfile.mkdtemp(prefix="pf-bench-", dir=a.work or None)
    os.makedirs(os.path.join(root, "tmp"))
    suite = stage_suite(root, plugin, items, slash(sys.executable))
    out = os.path.join(root, "out")
    cli = doctor.find_cli()
    cmd = [cli or "claude", "plugin", "eval", suite, "--scaffold", "--trust-plugin", "--ablation", "none",
           "--no-publish", "--keep-temp", "--threshold", "0", "--runs", str(a.runs), "-j", str(a.jobs),
           "--model", a.model, "--judge-model", a.judge_model, "--max-cost-usd", str(a.max_cost_usd),
           "--output-dir", out]
    if a.dry_run:
        print("dry run: suite staged in %s (kept), nothing run\n%s" % (suite, subprocess.list2cmdline(cmd)))
        return 0
    if not cli:
        raise Usage("no claude CLI found (needs Claude Code 2.1.269 or later); Cursor has no plugin eval")
    env = dict(os.environ, TEMP=os.path.join(root, "tmp"), TMP=os.path.join(root, "tmp"),
               TMPDIR=os.path.join(root, "tmp"), PYTHONDONTWRITEBYTECODE="1")
    why = paid_auth(cli, env)
    if why:
        shutil.rmtree(root, ignore_errors=True)
        raise Usage("not run: %s. The bench runs on the subscription's tokens only, never real money." % why)
    stamp = time.strftime("%Y-%m-%d-%H%M")
    log = []
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    for raw in p.stdout:
        line = raw.decode("utf-8", "replace").rstrip()
        log.append(line)
        if " run " in line or line.startswith(("✓", "✗", "⚠", "CASE", "Error")) or "score" in line:
            print(line, flush=True)
    rc = p.wait()
    agg = json.loads(read(os.path.join(out, "aggregate-result.json")) or "{}")
    if not agg.get("cases"):
        print("\n".join(log[-20:]))
        print("bench run failed (exit %d): no results; staged suite kept in %s" % (rc, root))
        return 1
    status = 0
    for name, repo in projs:
        mine = [i for i in items if i[0] == name]
        if not mine:
            continue
        runs_dir = os.path.join(repo, RUNS_DIR, stamp)
        rows = summarize(agg, mine, os.path.join(runs_dir, "replies"))
        for f in ("aggregate-result.json", "report.html"):
            if os.path.isfile(os.path.join(out, f)):
                shutil.copy(os.path.join(out, f), os.path.join(runs_dir, f))
        write(os.path.join(runs_dir, "eval.log"), "\n".join(log) + "\n")
        hist = {"stamp": stamp, "plugin_version": plugin_version(plugin), "model": a.model,
                "judge_model": a.judge_model, "runs": a.runs, "partial": bool(agg.get("partial")),
                "partial_reason": agg.get("partialReason"), "claude_version": agg.get("claudeVersion"),
                "cost_usd": round(sum(r["cost_usd"] for r in rows), 2), "results": rows}
        write(os.path.join(repo, HISTORY_DIR, stamp + ".json"), json.dumps(hist, indent=2) + "\n")
        print("\n%s: history %s, replies and report in %s" % (
            name, os.path.join(HISTORY_DIR, stamp + ".json"), os.path.join(RUNS_DIR, stamp)))
        print(render_report(name, hist, None))
        status = 1 if hist["partial"] else status
    print("total usage $%.2f at list price (subscription tokens)%s" % (float(agg.get("costUsd") or 0),
                                                 " - PARTIAL: %s" % agg.get("partialReason") if agg.get("partial") else ""))
    if a.keep:
        print("staged suite kept in %s" % root)
    else:
        shutil.rmtree(root, ignore_errors=True)
    return status


def latest_history(repo):
    files = sorted(glob.glob(os.path.join(repo, HISTORY_DIR, "*.json")))
    out = []
    for f in reversed(files):
        try:
            out.append(json.loads(read(f) or "{}"))
        except ValueError:
            continue
    return out


def rates(rows, key):
    out = {}
    for r in rows:
        if r["verdict"] in ("caught", "missed"):
            t = out.setdefault(r[key], [0, 0])
            t[0] += r["verdict"] == "caught"
            t[1] += 1
    return out


def expected_total(rows):
    """[caught, total] over the rows run at the stage that should have caught the bug."""
    t = [0, 0]
    for r in rows:
        if r["stage"] == r["caught_at"] and r["verdict"] in ("caught", "missed"):
            t[0] += r["verdict"] == "caught"
            t[1] += 1
    return t


def pct(t):
    return "%d/%d (%d%%)" % (t[0], t[1], round(100.0 * t[0] / t[1])) if t and t[1] else "-"


def render_report(name, cur, prev):
    rows = cur.get("results", [])
    old = {(r["case"], r["stage"]): r for r in (prev or {}).get("results", [])}
    out = ["### %s: bench %s (plugin %s, %d runs each, $%.2f%s)" % (
        name, cur.get("stamp"), cur.get("plugin_version"), cur.get("runs", 0), cur.get("cost_usd", 0),
        ", PARTIAL" if cur.get("partial") else "")]
    if prev:
        out.append("Compared with %s (plugin %s)." % (prev.get("stamp"), prev.get("plugin_version")))
    out += ["", "| Stage (agent) | Caught | Before |", "|---|---|---|"]
    now_s, old_s = rates(rows, "stage"), rates(list(old.values()), "stage")
    for s in STAGES:
        if s in now_s or s in old_s:
            out.append("| %s (%s) | %s | %s |" % (s, STAGES[s], pct(now_s.get(s)), pct(old_s.get(s))))
    exp_now = expected_total(rows)
    if exp_now[1]:
        out.append("| at the stage where it should have been caught | %s | %s |" % (
            pct(exp_now), pct(expected_total(old.values())) if old else "-"))
    out += ["", "| Case | Stage | Runs passed | Verdict | Before |", "|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (r["stage"], r["case"])):
        o = old.get((r["case"], r["stage"]))
        out.append("| %s | %s%s | %d/%d%s | %s | %s |" % (
            r["case"], r["stage"], " (expected)" if r["stage"] == r["caught_at"] else "", r["passed"], r["runs"],
            ", %d invalid" % r["invalid"] if r["invalid"] else "", r["verdict"],
            ("%s%s" % (o["verdict"], " <- changed" if o["verdict"] != r["verdict"] else "")) if o else "-"))
    return "\n".join(out)


def cmd_report(a):
    shown = 0
    for name, repo in projects(a.project):
        h = latest_history(repo)
        if not h:
            print("%s: no bench run yet (bench.py run)" % name)
            continue
        print(render_report(name, h[0], h[1] if len(h) > 1 else None) + "\n")
        shown += 1
    return 0 if shown else 1


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for n in ("cases", "check", "report"):
        sp = sub.add_parser(n)
        sp.add_argument("--project", default="", help="a project name, or all (default: this repo)")
    r = sub.add_parser("run")
    r.add_argument("--project", default="")
    r.add_argument("--stage", choices=sorted(STAGES))
    r.add_argument("--case", help="case id glob")
    r.add_argument("--runs", type=int, default=3)
    r.add_argument("-j", "--jobs", type=int, default=3, help="runs at once (1-8)")
    r.add_argument("--model", default="sonnet", help="the main session that starts the agent (the agent keeps its own)")
    r.add_argument("--judge-model", default="sonnet")
    r.add_argument("--max-cost-usd", type=float, help="required: hard ceiling for the whole run")
    r.add_argument("--plugin", default="", help="the plugin under test (default: see the help)")
    r.add_argument("--all", action="store_true", help="also run not-catchable cases")
    r.add_argument("--work", default="", help="folder for the temp suite (default: the system temp folder)")
    r.add_argument("--keep", action="store_true", help="keep the temp suite and workspaces")
    r.add_argument("--dry-run", action="store_true", help="stage the suite and print the command; run nothing")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "run" and not 1 <= a.jobs <= 8:
            raise Usage("-j must be 1 to 8")
        if a.cmd == "run" and not 1 <= a.runs <= 50:
            raise Usage("--runs must be 1 to 50")
        return {"cases": cmd_cases, "check": cmd_check, "run": cmd_run, "report": cmd_report}[a.cmd](a)
    except Usage as e:
        print("bench: %s" % e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
