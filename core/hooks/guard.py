"""PreToolUse guard of the agent core (Claude Code, and Cursor with --cursor). Product-neutral: every repo
detail comes from .claude/project.json (`guard`, `decisions`, `app`).

Blocks the tool calls that have cost hours before:
  - git commands that change the repo (default: all in project.GIT_RULES; read-only git passes); a verb in
    `git_on_request` (default: pull) passes in the turn after the developer asked for it in their own message;
  - the project's blocked commands, and build commands while the app or another server is up
    (`block_while_app_up`, `block_while_port_up`);
  - reading or printing secret files; whole-file reads of big files; `sed -i` on CRLF files;
  - edits to generated or core-owned files, to committed files that must stay frozen, to read-only roots;
  - data-model, access and config edits (decision triggers in `decisions`) until the task's card is approved;
  - product code written by the main session (the Tech Lead routes it to its area agent, `routing` in
    project.json; Claude Code only: Cursor's tool hooks do not say which agent made the call);
  - product mode: code in a product root before the base stage or the G3 design approval.

Contract (Claude Code): hook JSON on stdin; exit 2 + a message on stderr blocks the call; exit 0 lets it through.
Contract (Cursor, `--cursor`): always prints {"permission": "allow"|"deny", ...}, because Cursor blocks on empty
output. A repo without .claude/project.json is never checked (exit 0 at once). An internal error blocks the call
(fail closed: exit 2, or deny in Cursor) with a one-line reason and is logged (project.hook_error), so a broken guard
is seen at once instead of letting secrets and git writes through unnoticed.
"""
import glob
import json
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import project  # noqa: E402

CURSOR = "--cursor" in sys.argv
if __name__ == "__main__":
    project.hook_start(cursor=CURSOR)
ROOT = project.repo_root()
CFG = project.config(ROOT)
G = CFG["guard"]
PATH_KEYS = ("file_path", "path", "target_file", "filePath", "notebook_path")
CMD = r"(^|[\s;&|(])"
SECRETISH_NAMES = [".env", ".env.*", "*.pem", "*.key", "*.p12", "*.jks"]


class Blocked(Exception):
    pass


def block(msg):
    raise Blocked(msg)


def rel(path):
    return project.rel(path, ROOT)


def shown(path):
    """The path as written, relative to the repo, for messages (rel() is lower-case, for matching only)."""
    if not rel(path):
        return path
    try:
        return os.path.relpath(os.path.abspath(path), ROOT).replace("\\", "/")
    except ValueError:
        return rel(path)


def app_is_up():
    """True when the app answers at `app.url`. `app.strict`: only a 2xx counts (a 404 or a redirect is another app
    on the same port, not ours)."""
    app = CFG.get("app") or {}
    url = app.get("url")
    if not url:
        return False
    import urllib.request  # only here: it costs ~85 ms per hook call when imported at the top
    strict = bool(app.get("strict"))

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None  # a redirect is an answer: following it to a login host that is down would read as "app down"

    try:
        with urllib.request.build_opener(NoRedirect).open(url, timeout=1.5) as r:
            return 200 <= r.status < 300 if strict else r.status not in (502, 503, 504)
    except Exception as e:  # an HTTPError still means the server answered; 502-504 mean it is still starting
        return not strict and hasattr(e, "code") and e.code not in (502, 503, 504)


def port_is_open(host, port):
    import socket
    try:
        with socket.create_connection((host or "localhost", int(port)), timeout=0.5):
            return True
    except (OSError, ValueError):
        return False


def is_crlf(path):
    try:
        with open(path, "rb") as f:
            return b"\r\n" in f.read(65536)
    except OSError:
        return False


def is_tracked(path):
    import subprocess
    try:
        r = subprocess.run(["git", "ls-files", "--error-unmatch", "--", os.path.abspath(path)], cwd=ROOT,
                           capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False


def name_regex(globs):
    """A regex that finds any of these file-name globs inside a shell command."""
    parts = []
    for g in globs:
        name = g.replace("\\", "/").rsplit("/", 1)[-1]
        parts.append("".join("[^\\s/\\\\'\"]*" if c == "*" else re.escape(c) for c in name))
    return re.compile(r"(?<![\w.-])(" + "|".join(parts) + r")(?![\w.-])", re.I) if parts else None


# ---- commands -------------------------------------------------------------------------------------------------

def git_asked(data):
    """Git verbs the developer asked for in their latest message (`guard.git_on_request`; flow_check.py prompt
    records them per session). Cursor has no prompt hook, so there it is always empty."""
    try:
        import live_status
        with open(live_status.path(".sessions", live_status.session_of(data) + ".git"), encoding="utf-8") as f:
            return json.load(f).get("asked") or []
    except Exception:
        return []


def check_bash(cmd, data=None):
    c = (cmd or "").replace("\\\n", " ")
    for key in G.get("git_blocked") or []:
        rule = project.GIT_RULES.get(key)
        if rule and re.search(CMD + rule[0], c):
            if key in (G.get("git_on_request") or []) and key in git_asked(data):
                continue
            block("Blocked: " + rule[1] + " The developer does git.")
    for b in G.get("blocked_commands") or []:
        if re.search(b.get("pattern", "(?!)"), c):
            block("Blocked: " + b.get("why", "this command is blocked in this repo (.claude/project.json)."))
    up = G.get("block_while_app_up")
    if up and re.search(up, c) and app_is_up():
        safe = [x for x in ((CFG.get("commands") or {}).get(k) for k in ("test", "test_all"))
                if x and not re.search(up, x)]
        block("Blocked: the app is running and `" + c.strip()[:80] + "` would rebuild under it and stop it. "
              + ("Run the tests with `%s` instead (safe while it runs), " % "` or `".join(safe) if safe else
                 "Run the tests with the project's test command, ")
              + "or ask the developer to stop the app first.")
    for pw in G.get("block_while_port_up") or []:
        try:
            hit = re.search(pw.get("pattern", "(?!)"), c) and not (pw.get("unless") and re.search(pw["unless"], c))
        except re.error:
            continue
        if hit and port_is_open(pw.get("host"), pw.get("port", 0)):
            block("Blocked: port %s is in use and `%s` %s" % (pw.get("port"), c.strip()[:80],
                                                             pw.get("why", "would break the server on it.")))
    secrets = name_regex(G.get("secret_files") or [])
    if secrets and secrets.search(c) and not any(ok in c for ok in G.get("secret_ok_commands") or []):
        block("Blocked: " + secrets.search(c).group(1) + " holds credentials. Never print or copy its values; "
              "name the key only.")
    for m in re.finditer(CMD + r"sed\s+(-[a-zA-Z]*i[a-zA-Z]*|--in-place)\b([^;&|]*)", c):
        for tok in m.group(3).split():
            tok = tok.strip("'\"")
            if tok.startswith("-") or not os.path.isfile(os.path.join(ROOT, tok)):
                continue
            if rel(os.path.join(ROOT, tok)) is not None and is_crlf(os.path.join(ROOT, tok)):
                block("Blocked: `sed -i` rewrites CRLF files as LF (" + tok + "). Use the Edit tool or "
                      "`python " + project.core_path("scripts/crlf_edit.py") + "`.")
    if is_lead(data):  # an in-place edit by command is still an edit: routed like Edit and Write
        for m in re.finditer(CMD + r"(?:sed\s+(?:-[a-zA-Z]*i[a-zA-Z]*|--in-place)\b|\S*crlf_edit\.py[\"']?)([^;&|]*)", c):
            for tok in m.group(2).split():
                tok = tok.strip("'\"")
                p = tok if os.path.isabs(tok) else os.path.join(ROOT, tok)
                if not tok.startswith("-") and os.path.isfile(p):
                    check_route(p, data)


# ---- reads ----------------------------------------------------------------------------------------------------

def check_read(inp, size_check=True):
    path = inp.get("file_path") or ""
    r = rel(path) if path else None
    if path and project.match(path.replace("\\", "/").rsplit("/", 1)[-1], G.get("secret_files") or []):
        block("Blocked: " + os.path.basename(path) + " holds credentials. Never read or copy its values.")
    if not r:
        return
    for nr in G.get("no_read") or []:
        if project.match(r, nr.get("paths")):
            block("Blocked: " + nr.get("why", r + " must not be read whole."))
    limit = int(G.get("big_file_kb") or 0) * 1024
    if size_check and limit and not inp.get("limit") and os.path.isfile(path):
        size = os.path.getsize(path)
        if size > limit and not path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".pdf", ".webp", ".svg")):
            how = next((h.get("how") for h in G.get("big_file_hints") or [] if project.match(r, h.get("paths"))),
                       None) or ("Map it first with `python %s %s` (or Grep), then Read with offset/limit."
                                 % (project.core_path("scripts/codemap.py"), r))
            block("Blocked: %s is %d KB. %s" % (r, size // 1024, how))


# ---- writes ---------------------------------------------------------------------------------------------------

def check_write(path):
    if not path:
        return
    target = project.norm_dir(path)
    for ro in G.get("read_only_roots") or []:
        if target.startswith(project.norm_dir(ro)):
            block("Blocked: %s is a read-only reference. Read it with Read or `git show` only." % ro)
    check_product_root(path)
    r = rel(path)
    if not r:
        return
    if project.match(r, [".claude/core/**"]):
        block("Blocked: " + r + " belongs to the agent core. Change the core source, then run its install.py "
              "(product-factory: core/, then `python core/scripts/install.py <repo>`).")
    if project.match(r, [".cursor/agents/**", ".cursor/rules/**", ".cursor/skills/**", ".cursor/hooks.json",
                         ".cursor/runtime/**"]):
        block("Blocked: " + r + " is generated from .claude/ and the agent core. Change the source and run "
              "`python " + project.core_path("scripts/cursor_sync.py") + "`.")
    if project.match(r, G.get("generated") or []):
        block("Blocked: " + r + " is generated. Change its source instead.")
    for nw in G.get("no_write") or []:
        if project.match(r, nw.get("paths")):
            block("Blocked: " + nw.get("why", r + " must not be edited directly."))
    if project.match(r, G.get("frozen_if_tracked") or []) and os.path.isfile(path) and is_tracked(path):
        block("Blocked: " + r + " is committed and must not change (environments that already ran it would "
              "silently differ). Add a new file instead.")


def is_lead(data):
    """The main session (the Tech Lead). Claude Code sends agent_type and agent_id only from inside a subagent (or
    a session started with --agent). Cursor's tool hooks name no agent, so Cursor is never treated as the lead."""
    return bool(data) and not CURSOR and not data.get("agent_type") and not data.get("agent_id")


def task_roots():
    """Product roots outside this repo that tasks and products work in (`init --root`)."""
    try:
        import live_status
        return [st["root"] for st in map(live_status.load, live_status.tasks()) if st.get("root")]
    except Exception:
        return []


def check_route(path, data):
    """Product code is written by its area agent: the Tech Lead triages, decides, briefs, routes, integrates and
    verifies. Its own edits stay in the AI setup, the work folder and the scratchpad."""
    if not path or not is_lead(data) or not (CFG.get("routing") or {}).get("enforce", True):
        return
    area = project.product_area(path, ROOT)
    if not area and not project.rel(path, ROOT):
        root = next((r for r in task_roots() if project.norm_dir(path).startswith(project.norm_dir(r))), None)
        area = project.product_area(path, os.path.abspath(root)) if root else None
    if area:
        block("Blocked: %s is product code, and the Tech Lead routes product code instead of writing it. Brief %s "
              "(the exact files and lines, the fix, the test to run; a quick fix in about 8 calls, no context pack) "
              "and launch it with the Agent tool; independent parts with no shared files go in one message. The "
              "Tech Lead keeps triage, gates and cards, live checks in the browser, the final checks and setup work "
              "(.claude/, .cursor/, AGENTS.md, setup_paths)." % (shown(path), area))


def legacy_roots():
    """Old product-factory status.md files (`product_root:` + `code_writes:`): still honoured after the switch."""
    out = []
    for st in glob.glob(os.path.join(project.work_dir(ROOT), "*", "status.md")):
        try:
            with open(st, encoding="utf-8") as f:
                text = f.read()
        except OSError:
            continue
        m = re.search(r"^product_root:\s*(.+)$", text, re.M)
        if m:
            open_ = bool(re.search(r"^code_writes:\s*open\b", text, re.M))
            out.append((os.path.basename(os.path.dirname(st)), m.group(1).strip(), open_))
    return out


def check_product_root(path):
    target = project.norm_dir(path)
    if os.path.normcase(target).startswith(os.path.normcase(project.norm_dir(project.work_dir(ROOT)))):
        return  # flow documents are never code
    roots = []
    try:
        import live_status
        for tid in live_status.tasks():
            st = live_status.load(tid)
            if st.get("mode") == "product" and st.get("root"):
                roots.append((tid, st["root"], live_status.code_writes_open(st)))
    except Exception:
        pass
    seen = {project.norm_dir(r) for _, r, _ in roots}
    roots += [x for x in legacy_roots() if project.norm_dir(x[1]) not in seen]
    for tid, root, open_ in roots:
        if target.startswith(project.norm_dir(root)) and not open_:
            block("Blocked: code writes are closed for %s (%s). Product code is written only in the base stage or "
                  "after the developer approved the design (G3). Open it with `live_status.py code %s open` once "
                  "they said yes." % (tid, root, tid))


# ---- decisions ------------------------------------------------------------------------------------------------

def whole_lines(old, new, current):
    """Widen a replacement to the full lines it sits in, so an edit to only the argument of a marked line
    (`@CheckPermission("A")` -> `("B")`) is seen with its marker."""
    i = current.find(old) if old else -1
    if i < 0:
        return old, new
    start = current.rfind("\n", 0, i) + 1
    end = current.find("\n", i + len(old))
    end = len(current) if end < 0 else end
    before, after = current[start:i], current[i + len(old):end]
    return before + old + after, before + new + after


def old_new(inp, current):
    """(text the edit removes, text it writes): Edit/StrReplace strings, MultiEdit edits, a whole-file write against
    the current file. A partial Cursor `code_edit` snippet has no removed side."""
    olds, news = [], []
    pairs = [(inp.get(ok), inp.get(nk)) for ok, nk in (("old_string", "new_string"), ("old_str", "new_str"))
             if isinstance(inp.get(ok), str) or isinstance(inp.get(nk), str)]
    pairs += [(e.get("old_string"), e.get("new_string")) for e in inp.get("edits") or [] if isinstance(e, dict)]
    for o, n in pairs:
        o, n = whole_lines(str(o or ""), str(n or ""), current)
        olds.append(o)
        news.append(n)
    for k in ("content", "contents", "file_text"):
        if isinstance(inp.get(k), str):
            olds.append(current)
            news.append(inp[k])
    if isinstance(inp.get("code_edit"), str):
        news.append(inp["code_edit"])
        return None, "\n".join(news)
    return "\n".join(olds), "\n".join(news)


def marker_re(markers):
    if not markers:
        return None
    parts = [re.escape(m) + (r"\b" if re.match(r".*\w$", m) else "") for m in markers]
    return re.compile("|".join(parts))


def marked(pattern, text):
    return sorted(l.strip() for l in (text or "").splitlines() if pattern.search(l))


_DECL = re.compile(r"\b(?:class|interface|enum|record)\s+(\w+)|(\w+)\s*\(")


def anchored(pattern, text):
    """Each marked annotation line with the name of the declaration it sits on (the first code line after it that is
    not blank, an annotation or a comment), so moving a check to another method counts as a change. A marker inside a
    method body (a guard call) keeps only its own line: the statement after it is not what it guards."""
    lines = (text or "").splitlines()
    out = []
    for i, line in enumerate(lines):
        if pattern.search(line):
            anchor = ""
            if line.strip().startswith("@"):
                nxt = next((x.strip() for x in lines[i + 1:] if x.strip() and not x.strip().startswith(
                    ("@", "//", "/*", "*"))), "")
                m = _DECL.search(nxt)
                anchor = (m.group(1) or m.group(2)) if m else nxt
            out.append((line.strip(), anchor))
    return sorted(out)


def changes(pattern, old, new, current):
    """True when the edit adds, removes or changes a line carrying the pattern, or moves one to another declaration
    (unchanged context lines don't count)."""
    if old is None:
        return bool(set(marked(pattern, new)) - set(marked(pattern, current)))
    if marked(pattern, old) != marked(pattern, new):
        return True
    after = current.replace(old, new, 1) if old and old in current else None
    return after is not None and anchored(pattern, current) != anchored(pattern, after)


def decision_needed(path, r, inp):
    """The first decision (D2..D8, from project.json `decisions`) this edit triggers, or None.
    Each decision: `paths` (globs; alone = any edit to them), `file_markers` (any edit to a file that holds one, or
    that adds or removes one), `line_markers` (only edits that change a line holding one), `any_paths` (globs: any
    edit to them, whatever the markers)."""
    if project.match(r, G.get("secret_files") or []):
        return None
    current = None
    for d in sorted(CFG.get("decisions") or {}):
        spec = CFG["decisions"][d] or {}
        if project.match(r, spec.get("any_paths") or []):
            return d
        if spec.get("paths") and not project.match(r, spec["paths"]):
            continue
        fm, lm = marker_re(spec.get("file_markers")), marker_re(spec.get("line_markers"))
        if not fm and not lm:
            if spec.get("paths"):
                return d
            continue
        if current is None:
            current = ""
            try:
                if os.path.getsize(path) < 400 * 1024:
                    with open(path, encoding="utf-8", errors="replace") as f:
                        current = f.read()
            except OSError:
                pass
            old, new = old_new(inp, current)
        if fm and (fm.search(current) or changes(fm, old, new, current)):
            return d
        if lm and changes(lm, old, new, current):
            return d
    return None


def binding_hook_installed():
    """Decision holds need `live_status.py hook` (it binds a session to its task). Without it a card could never be
    approved, so the decision check stands down instead of blocking for good."""
    if os.environ.get("CLAUDE_PLUGIN_ROOT") and not CURSOR:
        return True
    cfg = os.path.join(ROOT, ".cursor", "hooks.json") if CURSOR else os.path.join(ROOT, ".claude", "settings.json")
    try:
        with open(cfg, encoding="utf-8") as f:
            return "live_status.py" in f.read()
    except OSError:
        return False


def check_decision(inp, data, path):
    if isinstance(inp, str):
        inp = json.loads(inp)
    r = rel(path) if path else None
    d = decision_needed(path, r, inp) if r else None
    if not d or not binding_hook_installed():
        return
    try:
        import live_status
        sid = live_status.session_of(data)
        tid = live_status.session_task(sid) if sid else None
        state = live_status.load(tid).get("decisions", {}).get(d, {}).get("state") if tid else None
        title = live_status.DECISIONS.get(d, d)
    except Exception:
        return  # unreadable task state: fail open
    if state == "approved":
        return
    what = (CFG["decisions"].get(d) or {}).get("what") or title.lower()
    if not tid:
        block("Blocked: %s changes %s, which needs the developer's approval first (decision %s %s). Start a task "
              "(`live_status.py init`), write the %s card and gate it with `--decision %s`." % (
                  shown(path), what, d, title, d, d))
    block("Blocked: %s changes %s. Task %s has no approved %s %s decision%s. Write the card in "
          "`<work>/%s/decisions/` (layout `" + project.core_path("reference/review/decision-card.md") + "`), run "
          "`live_status.py gate %s design \"<question>\" --file design.md --file decisions/%s-<name>.md` (the stage's "
          "documents in one gate; with no Design stage, gate the card on build) and wait for the developer's approval; "
          "never approve it yourself." % (shown(path), what, tid, d, title, " (now: %s)" % state if state else "",
                                          tid, tid, d))


# ---- entry ----------------------------------------------------------------------------------------------------

def run_claude(data):
    tool = data.get("tool_name", "")
    inp = data.get("tool_input") or {}
    if tool in ("Bash", "PowerShell"):
        check_bash(inp.get("command") or "", data)
    elif tool == "Read":
        check_read(inp)
    elif tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        path = inp.get("file_path") or inp.get("notebook_path") or ""
        check_write(path)
        check_route(path, data)
        check_decision(inp, data, path)


def run_cursor(data):
    event = data.get("hook_event_name", "")
    if event == "beforeShellExecution":
        check_bash(data.get("command") or "", data)
    elif event == "beforeReadFile":
        check_read({"file_path": data.get("file_path") or ""}, size_check=False)  # Cursor pages big files itself
    elif event == "preToolUse":
        inp = data.get("tool_input") or {}
        if isinstance(inp, str):
            inp = json.loads(inp)
        path = next((inp[k] for k in PATH_KEYS if inp.get(k)), "")
        check_write(path)
        check_decision(inp, data, path)


def live(text, data):
    """Show the block on this session's live task page, if it has a task (best effort, never raises)."""
    try:
        import live_status
        live_status.record("block", text, "guard", data)
    except Exception:
        pass


def main():
    data = json.loads(sys.stdin.buffer.read().decode("utf-8-sig", "replace") or "{}")
    try:
        (run_cursor if CURSOR else run_claude)(data)
    except Blocked as b:
        live(str(b).splitlines()[0][:200], data)
        if CURSOR:
            print(json.dumps({"permission": "deny", "user_message": str(b), "agent_message": str(b)}))
            return
        sys.stderr.write(str(b) + "\n")
        sys.exit(2)
    if CURSOR:
        print(json.dumps({"permission": "allow"}))


def fail_closed(exc):
    """An internal error holds the call: a guard that lets everything through unnoticed is worse than a stop."""
    msg = ("Blocked: " + project.hook_error("guard", exc) + ". The call is held until the guard works again; tell "
           "the developer. To work without the core in this repo meanwhile, the developer renames "
           ".claude/project.json.")
    if CURSOR:
        print(json.dumps({"permission": "deny", "user_message": msg, "agent_message": msg}))
        sys.exit(0)
    sys.stderr.write(msg + "\n")
    sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except BaseException as e:  # noqa: B036 - KeyboardInterrupt too: never fail open
        fail_closed(e)
