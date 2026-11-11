"""Keeps work on the core flow (sdlc triage; task mode or product mode, with the stage agents and the live page).

  prompt         Claude UserPromptSubmit. A message that looks like a requirement document or a build-a-product
                 request gets the product-lane hold-on reminder (never build straight from a PRD). Otherwise a
                 session's first prompt gets a one-line reminder of the triage (or of the session's active task).
                 Also records the git verbs the message asks for (`guard.git_on_request`, default pull) for the guard.
  stop           Claude Stop: when this turn changed repo files and the session has no task, or its task still has
                 stages left and is not waiting at a gate, blocks the stop once with what to do next. A recorded
                 quick fix (live_status.py quick) within its limits passes; edits only to the AI setup (.claude/,
                 .cursor/, AGENTS.md, CLAUDE.md, `setup_paths` in project.json) pass when the Cursor copies are in
                 step; flow documents in the work folder never count. From Build on, a changed file the task's plan
                 does not name (scope_check.py) blocks the stop once, even at a gate.
  stop --cursor  Cursor stop: the same check, sent back as {"followup_message": ...} (first loop only).

Edits are recorded per session by `live_status.py hook` (PostToolUse) and cleared at every stop. Any internal error
exits 0 with no output (fail open). Cursor gap: no hook adds context to a prompt, so `prompt` is Claude-only; Cursor
gets the same rules from AGENTS.md, which it always loads, and the `stop --cursor` check.
"""
import json
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
try:
    import project  # noqa: E402
    if __name__ == "__main__":
        project.hook_start()
    import live_status as ls  # noqa: E402
except SystemExit:
    raise
except Exception as _e:  # the turn goes on, with a warning
    sys.stderr.write("agent core flow check could not start (%s: %s)\n" % (type(_e).__name__, _e))
    sys.exit(0 if "--cursor" in sys.argv else 1)

CFG = project.config()
CORE_AGENTS = ("spec-analyst, bug-investigator, performance-engineer, product-critic, story-sizer, ux-designer, "
               "solution-architect, data-architect, security-architect, code-reviewer, qa-lead, qa-engineer, "
               "ui-qa-expert, e2e-qa-expert, test-data-engineer, verifier, "
               "audit-expert, release-manager")

# Turns that are not the user's own words: side-session and system events injected as prompts, slash-command expansions.
_WRAP = r"side-sessions?-event|system-reminder|task-notification|cross-session-message|ci-monitor-event|command-name|command-message|command-args|local-command-\w+"
WRAPPED = re.compile(r"<(%s)\b[^>]*>.*?(</\1>|\Z)" % _WRAP, re.I | re.S)
CODE = re.compile(r"```.*?(```|\Z)|`[^`\n]*`", re.S)
# file names and paths are not requirement documents; .docx/.pdf stay (an attachment), .md only with an attach cue
FILEREF = re.compile(r"(?<![\w])(?:[\w.~-]*[\\/])+[\w.-]+|\b[\w-]+\.(?:txt|py|js|ts|tsx|java|json|ya?ml|xml|html|css|sql|csv|log|toml|ini|cfg|sh|gradle|properties|lock)\b"
                     r"|\b(?:spec|specs|requirements|prd|readme)\.md\b", re.I)
REQ_DOC = re.compile(
    r"\b(prd|brd|product requirements?( doc\w*)?|business requirements?|requirements? (doc|document|spec|specification)"
    r"|functional (spec|specification|requirements?)|(user|use) stor(y|ies)|acceptance criteria"
    r"|(review|check|refine|complete|assess|here (is|are)|attached|attaching|see)( (this|these|the|my|our|a|an|following))?"
    r"( \w+){0,2} (requirements?|spec|specification)\b(?! (check|test|file|regex))"
    r"|requirements?\b.{0,20}\bfor [A-Z][A-Z0-9]+-\d+)", re.I)
ATTACH_DOC = re.compile(r"\b[\w -]*(requirement|prd|brd|spec|user[ _-]?stor|acceptance)[\w -]*\.(docx?|pdf)\b"
                        r"|\battach\w*\b.{0,60}\b[\w-]*(requirement|prd|brd|spec)[\w-]*\.md\b", re.I)
NEW_PRODUCT = re.compile(
    r"\b(build|create|make|develop|start|need|want)\s+(me\s+|us\s+)?(a\s+|an\s+|the\s+)?new\s+(\w+\s+){0,3}(app|application|product|system|platform)\b"
    r"|\bnew product\b(?!\s+(page|screen|tab|form|field|filter|catalog|list|card|dialog|view))"
    r"|\b(app|application|product|system|platform)\b.{0,30}\bfrom scratch\b|\bfrom scratch\b.{0,30}\b(app|application|product|system|platform)\b"
    r"|\b(prd|brd|requirements?|spec)\b.{0,25}\bfor (a|an) new\b"
    r"|\bbuild (this|the following|an? (new )?(app|application|product|system))\b", re.I)
ENGINEERING = re.compile(r"\b(regex|regexp|hooks?|flow_check|pip install|npm|pytest|unit tests?|spec tests?|stack ?trace|lint|compile)\b"
                         r"|\b(why|how does|what is|what's|where is)\b[^.]{0,80}\?\s*$", re.I)


def prompt_lane(prompt):
    """None, "factory" or "review-spec": which skill a requirement-like message belongs to. Fail-safe: None."""
    try:
        text = WRAPPED.sub(" ", prompt or "")
        text = CODE.sub(" ", text)
        if not ATTACH_DOC.search(text):
            text = FILEREF.sub(" ", text)
        text = text.strip()
        if len(text) < 8:
            return None
        if len(text) < 300 and ENGINEERING.search(text):
            return None
        product_repo = (CFG.get("default_mode") or "task") == "product"
        if NEW_PRODUCT.search(text):
            return "factory"
        if REQ_DOC.search(text) or ATTACH_DOC.search(text):
            return "factory" if product_repo else "review-spec"
        return None
    except Exception:
        return None


HOLD_ON = (
    "PRODUCT LANE CHECK: this message may be a request to build a new product (or, in the product factory repo, a "
    "requirement document). If it is, "
    "do not design or write code from it: follow the `factory` skill, stage intake (S0): say \"Hold on - I won't "
    "start building from this directly\" and why in one line; 3-5 lines of what you understood; the plan (stages, "
    "teams, what the user decides at each gate); at most 5 first questions with recommended answers; then "
    "`live_status.py init <slug> --mode product`, save the document as 00-prd.md, run spec-analyst (prd-review) and "
    "wait for G0. If it is a change to an existing product, a question or setup work, triage it with the sdlc skill.")

REVIEW_SPEC = (
    "REQUIREMENT LANE CHECK: this looks like a requirement, PRD or spec for an existing product. If it is, route it to "
    "the `review-spec` skill (`/review-spec`: plain-words requirements with the Definition of Ready, one gate with the "
    "requester) and do not design or write code from it. If it is a change that is already ready to build, use /develop; "
    "a bug, /fix; a question, just answer it.")


def agents_line():
    extra = [a for a in CFG.get("experts") or [] if a not in CORE_AGENTS]
    return CORE_AGENTS + (", " + ", ".join(extra) if extra else "")


def first_prompt(sid):
    f = ls.path(".sessions", sid + ".seen")
    if os.path.exists(f):
        return False
    os.makedirs(ls.path(".sessions"), exist_ok=True)
    ls.write(f, "1")
    return True


def record_git_request(sid, prompt):
    """The git verbs of `guard.git_on_request` (default: pull) that this message asks for; the guard lets them
    through until the next message. "pull request" is not a request to pull."""
    asked = [v for v in CFG["guard"].get("git_on_request") or []
             if re.search(r"(?<![\w-])%s(?![\w-])(?!\s*-?\s*requests?\b)" % re.escape(v), prompt or "", re.I)]
    f = ls.path(".sessions", sid + ".git")
    if asked:
        os.makedirs(ls.path(".sessions"), exist_ok=True)
        with open(f, "w", encoding="utf-8") as fh:
            json.dump({"asked": asked}, fh)
    elif os.path.isfile(f):
        os.remove(f)


def prompt_context(sid, prompt):
    first = first_prompt(sid)
    tid = ls.session_task(sid)
    if not tid:
        lane = prompt_lane(prompt)
        if lane:
            return HOLD_ON if lane == "factory" else REVIEW_SPEC
    if not first:
        return None
    if tid:
        st = ls.load(tid)
        left = [s["k"] for s in st["stages"] if s["state"] in ("todo", "live", "fail", "wait")]
        return "Active %s in this session: %s (size %s), stages left: %s. Continue it with the %s skill." % (
            "product" if st.get("mode") == "product" else "task", tid, st.get("size", "?"),
            ", ".join(left) or "none", "factory" if st.get("mode") == "product" else (st.get("skill") or "sdlc"))
    qf = CFG["quick_fix"]
    return ("Triage each request first (sdlc skill, the router): answer questions directly; requirements go to "
            "review-spec, a feature or change to develop, a bug or fix-list items to fix (a production incident: fix "
            "--hotfix), testing to test, a release's go or no-go to release, a new product to factory; changes to the AI setup itself (.claude, .cursor, AGENTS.md) you do with no task. develop and "
            "fix have a small path for an obvious small change (up to ~%d lines in up to %d files, nothing to decide: "
            "a quick brief to its area agent, then live_status.py quick \"<what>\"); everything else is a task with "
            "just the agents it needs (%s). You are the Tech Lead: "
            "you decide and route, the agents write the product code." % (qf.get("max_lines", 30), qf.get("max_files", 3),
                                                                          agents_line()))


def recent(t, minutes=30):
    """True when an ISO time is less than `minutes` old (a row left "working" longer than that is stale)."""
    try:
        from datetime import datetime, timezone
        return (datetime.now(timezone.utc) - datetime.fromisoformat(t)).total_seconds() < minutes * 60
    except (TypeError, ValueError):
        return False


def quick_marked(sid):
    f = ls.path(".sessions", sid + ".quick")
    if not os.path.exists(f):
        return False
    try:
        os.remove(f)
    except OSError:
        pass
    return True


def is_setup(r):
    return project.is_setup(r, CFG)


def in_work(r):
    w = project.rel(project.work_dir())
    return bool(w) and (r == w or r.startswith(w.rstrip("/") + "/"))


def not_quick(r):
    pats = list(CFG["quick_fix"].get("never") or [])
    for spec in (CFG.get("decisions") or {}).values():
        if spec and spec.get("paths") and not spec.get("file_markers") and not spec.get("line_markers"):
            pats += spec["paths"]
    return project.match(r, pats)


def cursor_stale():
    """True when the Cursor copies no longer match .claude/ (cursor_sync.py --check)."""
    script = os.path.join(HERE, "..", "scripts", "cursor_sync.py")
    if not os.path.isfile(script):  # the Cursor runtime carries no cursor_sync.py
        return False
    try:
        p = subprocess.run([sys.executable, script, "--check"],
                           capture_output=True, timeout=20, cwd=project.repo_root())
        return p.returncode != 0
    except Exception:
        return False


def listed(edits):
    return ", ".join(edits[:5]) + (" and %d more" % (len(edits) - 5) if len(edits) > 5 else "")


def scope_reason(tid, st):
    """From Build on: changed files the plan does not name (scope_check.py; nothing without a baseline or git)."""
    if not any(s["k"] == "build" and s["state"] in ("live", "done", "fail") for s in st.get("stages") or []):
        return None
    try:
        import scope_check
        extra = scope_check.unplanned(tid)
    except Exception:
        return None
    if not extra:
        return None
    return ("Task %s changed files its plan does not name: %s. Each is a MUST: undo it, or accept it with "
            "scope_check.py add %s <path> --why \"<reason>\"." % (tid, listed(extra), tid))


def stop_reason(sid):
    edits = [e for e in ls.session_edits(sid, clear=True) if not in_work(e.lower())]
    quick = quick_marked(sid)
    if not edits:
        return None
    tid = ls.session_task(sid)
    if not tid and all(is_setup(e.lower()) for e in edits):
        if cursor_stale():
            return ("You changed the AI setup (" + listed(edits) + ") and it is not in step for Cursor: run "
                    "python " + project.core_path("scripts/cursor_sync.py") + " --check and fix what it lists (Cursor users need the "
                    "same change).")
        return None
    if not tid:
        edits = [e for e in edits if not is_setup(e.lower())]
        big = [e for e in edits if not_quick(e.lower())]
        max_files = int(CFG["quick_fix"].get("max_files", 3))
        if quick and len(edits) <= max_files and not big:
            return None
        if quick:
            return ("This was more than a quick fix (" + (", ".join(big) if big else "%d files" % len(edits)) +
                    "): take the full path of the develop or fix skill (a task, then only the agents it needs).")
        return ("You changed repo files (" + listed(edits) + ") without a task. If it is an obvious small fix (up to "
                "~%d lines in up to %d files, nothing to decide: no tables, permissions, contracts or config), check "
                "it against the hard rules, run its tests and record it: live_status.py quick \"<what>\" (the small "
                "path of develop or fix). Otherwise start a task with the develop or fix skill. A throwaway edit you will revert: say so in one line." % (
                    int(CFG["quick_fix"].get("max_lines", 30)), max_files))
    st = ls.load(tid)
    out = scope_reason(tid, st)
    if out:
        return out
    if st.get("gate"):
        return None
    working = [r.get("start") for r in (st.get("plan") or {}).get("rows", [])
               if r.get("state") == "live" and r.get("agent") != "main session"] + \
              [b.get("start") for b in st.get("bg") or []]
    if any(recent(t) for t in working):
        return None  # an agent is still working in the background; its result continues the flow
    failed = [s["name"] for s in st["stages"] if s["state"] == "fail"]
    left = [s["name"] for s in st["stages"] if s["state"] in ("todo", "live", "fail")]
    if not left:
        return None
    why = ("Failed: " + ", ".join(failed) + " - go back to Build, fix every MUST, then run that stage again. ") \
        if failed else ""
    return ("Task %s is not finished. %sStages left: %s. Continue the flow, or open a gate (live_status.py gate) "
            "if you need the developer." % (tid, why, ", ".join(left)))


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    cursor = "--cursor" in sys.argv
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8-sig", "replace") or "{}")
        sid = ls.session_of(data)
        if not sid:
            return
        if mode == "prompt":
            try:
                record_git_request(sid, data.get("prompt") or "")
            except Exception:
                pass
            text = prompt_context(sid, data.get("prompt") or "")
            if text:
                print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                                         "additionalContext": text}}))
        elif mode == "stop":
            if cursor:
                if data.get("status", "completed") != "completed" or int(data.get("loop_count") or 0) > 0:
                    ls.session_edits(sid, clear=True)
                    return
                reason = stop_reason(sid)
                if reason:
                    print(json.dumps({"followup_message": reason}))
            else:
                if data.get("stop_hook_active"):
                    ls.session_edits(sid, clear=True)
                    return
                reason = stop_reason(sid)
                if reason:
                    print(json.dumps({"decision": "block", "reason": reason}))
    except Exception as e:
        sys.stderr.write(project.hook_error("flow check", e) + "\n")
        sys.exit(0 if cursor else 1)


if __name__ == "__main__":
    main()
