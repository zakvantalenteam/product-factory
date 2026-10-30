"""Core sync bot: installs the agent core from this repo into every product repo in targets.json.

Run by .github/workflows/core-sync.yml on each push to main that changes core/ (and by hand from the Actions tab).
Per target it clones the branch, runs core/scripts/install.py, then cursor_sync.py and both checks in the clone:
  nothing changed                      -> up to date, nothing pushed
  checks clean, no hand-edited files   -> one commit pushed straight to the branch (a push race is rebased and retried)
  otherwise, or --review / "review"    -> the commit goes to branch core/<version> and a pull request is opened
Only setup files may change (.claude/, .cursor/, AGENTS.md, CLAUDE.md, .gitignore); anything else stops that target.

  python .github/core-sync/sync.py [--only NAME] [--review] [--dry-run] [--targets FILE] [--work DIR]
  python .github/core-sync/sync.py --check-version     (VERSION and both plugin.json files agree)

Auth: GitHub targets use SYNC_GITHUB_TOKEN; CodeCommit targets use the AWS credentials of the job (OIDC role) via
`aws codecommit credential-helper`. "local" targets take a plain git URL or path (for trials).
"""
import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CORE = os.path.join(ROOT, "core")
SETUP = (".claude/", ".cursor/", "AGENTS.md", "CLAUDE.md", ".gitignore")
NEEDS_REVIEW = ("kept (edited by hand)", "skipped (repo's own file)", "need the core entries")


def say(msg):
    print(msg, flush=True)


def core_version():
    with open(os.path.join(CORE, "VERSION"), encoding="utf-8") as f:
        return f.read().strip()


def check_version():
    v = core_version()
    with open(os.path.join(CORE, ".claude-plugin", "plugin.json"), encoding="utf-8") as f:
        pv = json.load(f).get("version")
    with open(os.path.join(ROOT, "plugin", ".claude-plugin", "plugin.json"), encoding="utf-8") as f:
        bv = json.load(f).get("version")
    bad = [n for n, x in (("core/.claude-plugin/plugin.json", pv), ("plugin/.claude-plugin/plugin.json", bv)) if x != v]
    say("core %s: %s" % (v, "plugin.json files agree" if not bad else "differs in " + ", ".join(bad)))
    return 1 if bad else 0


# ---- git -----------------------------------------------------------------------------------------------------

def git_env(t):
    """Credentials through GIT_CONFIG_* so no token lands in a URL, the clone's config or the log."""
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    env.pop("CLAUDE_PROJECT_DIR", None)
    cfg = []
    if t["host"] == "github" and os.environ.get("SYNC_GITHUB_TOKEN"):
        basic = base64.b64encode(("x-access-token:" + os.environ["SYNC_GITHUB_TOKEN"]).encode()).decode()
        cfg.append(("http.https://github.com/.extraheader", "AUTHORIZATION: basic " + basic))
    if t["host"] == "codecommit":
        cfg += [("credential.helper", "!aws codecommit credential-helper $@"), ("credential.UseHttpPath", "true")]
    env["GIT_CONFIG_COUNT"] = str(len(cfg))
    for i, (k, v) in enumerate(cfg):
        env["GIT_CONFIG_KEY_%d" % i], env["GIT_CONFIG_VALUE_%d" % i] = k, v
    return env


def url_of(t):
    if t["host"] == "github":
        return "https://github.com/%s.git" % t["repo"]
    if t["host"] == "codecommit":
        return "https://git-codecommit.%s.amazonaws.com/v1/repos/%s" % (t["region"], t["repo"])
    return t["url"]


def run(cmd, cwd=None, env=None, check=True):
    p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (p.stdout or "") + (p.stderr or "")
    if check and p.returncode:
        raise RuntimeError("%s failed (%d): %s" % (" ".join(cmd[:3]), p.returncode, out.strip()[-800:]))
    return p.returncode, out


# ---- one target ----------------------------------------------------------------------------------------------

def sync(t, a, work):
    name, branch, env = t["name"], t.get("branch", "dev"), git_env(t)
    if os.environ.get("GITHUB_ACTIONS"):  # in the workflow: name the missing setup step instead of a git error
        if t["host"] == "github" and not os.environ.get("SYNC_GITHUB_TOKEN"):
            raise RuntimeError("no SYNC_GITHUB_TOKEN secret yet (README, sync bot setup, steps 1-2)")
        if t["host"] == "codecommit" and not os.environ.get("AWS_ACCESS_KEY_ID"):  # not a failure: AWS is optional
            return {"name": name, "result": "skipped: AWS not set up yet, update by hand (README, sync bot setup, steps 3-4)"}
    dest = os.path.join(work, re.sub(r"\W+", "-", name))
    rc, out = run(["git", "clone", "--quiet", "--filter=blob:none", "--single-branch", "--branch", branch, url_of(t), dest],
                  env=env, check=False)
    if rc and t["host"] == "github" and re.search(r"403|not granted", out):
        raise RuntimeError("the SYNC_GITHUB_TOKEN token cannot reach %s: it must be owned by %s and list that repo "
                           "(README, sync bot setup, step 1)" % (t["repo"], t["repo"].split("/")[0]))
    if rc:
        raise RuntimeError("git clone failed (%d): %s" % (rc, out.strip()[-800:]))
    run(["git", "config", "user.name", a.bot["name"]], cwd=dest)
    run(["git", "config", "user.email", a.bot["email"]], cwd=dest)
    vf = os.path.join(dest, ".claude", "core", "VERSION")
    before = open(vf, encoding="utf-8").read().strip() if os.path.isfile(vf) else "none"
    after = core_version()

    why = []
    if before == "none":
        why.append("the core is not installed yet (first install needs a person: settings and project.json)")
    rc, out = run([sys.executable, os.path.join(CORE, "scripts", "install.py"), dest]
                  + (["--write-settings"] if before != "none" else []), env=env, check=False)
    if rc:
        raise RuntimeError("install.py failed: " + out.strip()[-800:])
    why += ["install: " + ln.strip() for ln in out.splitlines() if any(k in ln for k in NEEDS_REVIEW)]
    checks = []
    for cmd in (["cursor_sync.py"], ["cursor_sync.py", "--check"], ["install.py", ".", "--check"]):
        rc, out = run([sys.executable, os.path.join(".claude", "core", "scripts", cmd[0])] + cmd[1:], cwd=dest, env=env,
                      check=False)
        checks.append("%s: %s" % (" ".join(cmd), out.strip().splitlines()[-1] if out.strip() else rc))
        if rc:
            why.append("check failed: %s -> %s" % (" ".join(cmd), out.strip()[-400:]))

    _, st = run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=dest)
    changed = [ln[3:].strip().strip('"') for ln in st.splitlines() if ln.strip()]
    if not changed:
        return {"name": name, "before": before, "after": after, "result": "up to date"}
    outside = [p for p in changed if not p.startswith(SETUP)]
    if outside:
        raise RuntimeError("install changed files outside the setup: " + ", ".join(outside[:10]))

    run(["git", "add", "-A"], cwd=dest)
    if run(["git", "diff", "--cached", "--quiet"], cwd=dest, check=False)[0] == 0:
        return {"name": name, "before": before, "after": after, "result": "up to date"}  # only line endings differed
    review = a.review or t.get("review") or bool(why)
    msg = "chore(ai-setup): agent core %s -> %s\n\nInstalled by the core sync bot from product-factory.\n%s\n" % (
        before, after, "\n".join("- " + c for c in checks))
    run(["git", "commit", "--quiet", "-m", msg], cwd=dest)
    if a.dry_run:
        return {"name": name, "before": before, "after": after, "files": len(changed),
                "result": "dry run: would " + ("open a pull request" if review else "push to " + branch), "why": why}
    if not review:
        for _ in range(3):
            rc, out = run(["git", "push", "--quiet", "origin", "HEAD:" + branch], cwd=dest, env=env, check=False)
            if not rc:
                return {"name": name, "before": before, "after": after, "files": len(changed),
                        "result": "pushed to " + branch}
            if re.search(r"protected|denied|not allowed|GH006|pre-receive", out, re.I):
                why.append("direct push refused (protected branch): " + out.strip()[-200:])
                break
            rc, out = run(["git", "pull", "--quiet", "--rebase", "origin", branch], cwd=dest, env=env, check=False)
            if rc:
                run(["git", "rebase", "--abort"], cwd=dest, check=False)
                why.append("rebase on the newer %s failed: %s" % (branch, out.strip()[-200:]))
                break
        else:
            why.append("push kept losing the race with %s" % branch)
    head = "core/" + after
    run(["git", "push", "--quiet", "--force", "origin", "HEAD:refs/heads/" + head], cwd=dest, env=env)
    pr = open_pr(t, head, branch, "Agent core %s -> %s" % (before, after),
                 "The core sync bot did not push straight to %s because:\n%s\n\nChecks:\n%s\n" % (
                     branch, "\n".join("- " + w for w in why) or "- review was asked for", "\n".join("- " + c for c in checks)))
    return {"name": name, "before": before, "after": after, "files": len(changed), "result": "pull request " + pr,
            "why": why}


def open_pr(t, head, base, title, body):
    if t["host"] == "github":
        req = urllib.request.Request("https://api.github.com/repos/%s/pulls" % t["repo"], method="POST",
                                     data=json.dumps({"title": title, "head": head, "base": base, "body": body}).encode(),
                                     headers={"Authorization": "Bearer " + os.environ.get("SYNC_GITHUB_TOKEN", ""),
                                              "Accept": "application/vnd.github+json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r).get("html_url", "opened")
        except urllib.error.HTTPError as e:
            if e.code == 422:  # one is already open for this branch: the force-push updated it
                return "already open (branch %s updated)" % head
            raise RuntimeError("GitHub pull request: %s %s" % (e.code, e.read()[:300]))
    if t["host"] == "codecommit":
        _, out = run(["aws", "codecommit", "create-pull-request", "--region", t["region"], "--title", title,
                      "--description", body[:10000], "--targets",
                      "repositoryName=%s,sourceReference=%s,destinationReference=%s" % (t["repo"], head, base),
                      "--query", "pullRequest.pullRequestId", "--output", "text"], check=False)
        return ("#" + out.strip()) if out.strip().isdigit() else "not opened (%s)" % out.strip()[-200:]
    return "(local target: branch %s pushed)" % head


# ---- main ----------------------------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--targets", default=os.path.join(HERE, "targets.json"))
    ap.add_argument("--only", default=os.environ.get("SYNC_ONLY", ""), help="one target by name")
    ap.add_argument("--review", action="store_true", default=os.environ.get("SYNC_REVIEW") == "true",
                    help="open pull requests instead of pushing to the branch")
    ap.add_argument("--dry-run", action="store_true", default=os.environ.get("SYNC_DRY_RUN") == "true",
                    help="clone, install and commit locally; push nothing")
    ap.add_argument("--work", default="", help="folder for the clones (default: a temporary one)")
    ap.add_argument("--check-version", action="store_true")
    a = ap.parse_args()
    if a.check_version:
        sys.exit(check_version())
    with open(a.targets, encoding="utf-8") as f:
        cfg = json.load(f)
    a.bot = cfg.get("bot") or {"name": "agent-core bot", "email": "agent-core-bot@users.noreply.github.com"}
    targets = [t for t in cfg["targets"] if not a.only or t["name"].lower() == a.only.lower()]
    if not targets:
        sys.exit("no target named %r" % a.only)
    work = a.work or tempfile.mkdtemp(prefix="core-sync-")
    results, failed = [], 0
    for t in targets:
        say("== %s (%s %s, branch %s)" % (t["name"], t["host"], t.get("repo") or t.get("url"), t.get("branch", "dev")))
        try:
            r = sync(t, a, work)
        except Exception as e:  # one broken target must not stop the others
            failed += 1
            r = {"name": t["name"], "result": "ERROR: %s" % e}
        results.append(r)
        say("   %s%s" % (r["result"], "".join("\n   - " + w for w in r.get("why") or [])))
    rows = ["| Repo | Before | After | Files | Result |", "|---|---|---|---|---|"] + [
        "| %s | %s | %s | %s | %s |" % (r["name"], r.get("before", ""), r.get("after", ""), r.get("files", ""),
                                       r["result"].replace("|", "/")) for r in results]
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("## Agent core %s\n\n%s\n" % (core_version(), "\n".join(rows)))
    if not a.work:
        shutil.rmtree(work, ignore_errors=True)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
