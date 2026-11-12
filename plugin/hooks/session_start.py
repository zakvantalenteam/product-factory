"""Plugin only (SessionStart): tell the main session how the agent core runs in this repo.

Nothing at all in a repo without `.claude/project.json`: the plugin is switched on at user level, and a repo that
has not opted in to the core must not pay for it (no tokens, no rules). With project.json:
  - the repo also carries the core (`.claude/core/core.lock`, for teammates without the plugin): a short note to use
    the plugin's agents and skills (the repo copy's hooks step aside while the plugin is on);
  - the core comes from this plugin and AGENTS.md has the core block: one line naming the plugin folder, so the
    core paths in AGENTS.md, the skills and the reference files resolve;
  - no core block in AGENTS.md: that line and the core block with this plugin's paths.
Two checks add a one-line warning (shown to the developer and added to the session):
  - this copy of the plugin is missing a file its own hooks/hooks.json or .claude-plugin/plugin.json names (an
    incomplete sync): which copy, which file and the fix (the guard entry blocks every checked call while its file
    is missing);
  - two copies of the plugin are on (for example the marketplace copy and the claude.ai copy): each copy records its
    folder against the session id in the temp folder; a different folder recorded within 5 seconds of this one is
    the other copy starting the same session, and the first copy to claim the session's warning prints it.
An internal error prints a one-line warning on stderr and adds nothing.
"""
import hashlib
import json
import os
import re
import sys
import tempfile
import time

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")
SAME_START = 5  # seconds: two copies starting one session record their folders this close together


def copy_name(root):
    """(name, fix): which copy of the plugin a folder is, as the plugin manager lists it, and how to fix it."""
    w = root.replace("\\", "/")
    try:
        with open(os.path.join(root, "VERSION"), encoding="utf-8") as f:
            v = f.read().strip()
    except OSError:
        v = "?"
    k = (w.split("/plugins/cache/")[1:] or [""])[0].split("/")
    if len(k) > 2:
        return ("marketplace copy (%s@%s %s)" % (k[1], k[0], v),
                "turn it off or update it in the plugin manager (/plugin)")
    if "/rpm/" in w:
        return ("claude.ai copy (product-factory@inline %s, synced from claude.ai)" % v,
                "turn it off on claude.ai or in the plugin manager, or update it on claude.ai")
    return "copy in %s (%s)" % (root, v), "turn it off in the plugin manager, or reinstall or update it"


def root_paths(value):
    """Every `${CLAUDE_PLUGIN_ROOT}/<path>` in a JSON value's strings, as <path>."""
    if isinstance(value, dict):
        return [p for v in value.values() for p in root_paths(v)]
    if isinstance(value, list):
        return [p for v in value for p in root_paths(v)]
    return re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s\"']+)", value) if isinstance(value, str) else []


def missing_files():
    """Paths this copy's hooks/hooks.json or .claude-plugin/plugin.json name that are not in this copy."""
    out = set()
    for src in ("hooks/hooks.json", ".claude-plugin/plugin.json"):
        try:
            with open(os.path.join(ROOT, src), encoding="utf-8") as f:
                cfg = json.load(f)
        except OSError:
            continue
        out.update(rel for rel in root_paths(cfg) if not os.path.exists(os.path.join(ROOT, rel)))
    return sorted(out)


def other_copy(session_id):
    """The folder of another copy of this plugin that started the same session within SAME_START seconds, when this
    copy is the one to report it; else None."""
    sid = re.sub(r"[^A-Za-z0-9_-]", "", session_id or "")[:100]
    if not sid:
        return None
    folder = os.path.join(tempfile.gettempdir(), "product-factory-sessions")
    os.makedirs(folder, exist_ok=True)
    me = os.path.normcase(os.path.realpath(ROOT))
    now = time.time()
    mine = os.path.join(folder, "%s.%s.json" % (sid, hashlib.sha1(me.encode("utf-8")).hexdigest()[:12]))
    tmp = "%s.%d.tmp" % (mine, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"root": ROOT, "at": now}, f)
    os.replace(tmp, mine)
    others = []
    for name in os.listdir(folder):
        full = os.path.join(folder, name)
        if name.startswith(sid + ".") and name.endswith(".json") and full != mine:
            try:
                with open(full, encoding="utf-8") as f:
                    rec = json.load(f)
                if (abs(float(rec["at"]) - now) <= SAME_START
                        and os.path.normcase(os.path.realpath(rec["root"])) != me):
                    others.append(rec["root"])
            except (OSError, ValueError, KeyError, TypeError):
                pass
        elif not name.startswith(sid + "."):
            try:
                if now - os.path.getmtime(full) > 86400:
                    os.remove(full)
            except OSError:
                pass
    if not others:
        return None
    try:  # the first copy to create the marker reports; the other stays quiet
        os.close(os.open(os.path.join(folder, sid + ".warned"), os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except FileExistsError:
        return None
    return sorted(others)[0]


def warnings(data):
    out = []
    name, fix = copy_name(ROOT)
    gone = missing_files()
    if gone:
        out.append("Warning: the product-factory plugin's %s is missing %s%s%s. Fix: %s." % (
            name, ", ".join(gone), "" if name.startswith("copy in ") else " (folder %s)" % ROOT,
            ", so every Bash, PowerShell, Edit and Write is blocked while it is on" if "hooks/guard.py" in gone
            else "; those hooks do not run", fix))
    other = other_copy(data.get("session_id"))
    if other:
        out.append("Warning: the product-factory plugin is on twice, the %s and the %s, so every hook runs twice. Fix: turn "
                   "one off in the plugin manager or on claude.ai." % (name, copy_name(other)[0]))
    return out


def stdin_json():
    try:
        if sys.stdin is None or sys.stdin.isatty():
            return {}
        return json.loads(sys.stdin.buffer.read().decode("utf-8-sig", "replace") or "{}")
    except Exception:
        return {}


def emit(text, warn):
    out = {"hookSpecificOutput": {"hookEventName": "SessionStart",
                                  "additionalContext": ("\n".join(warn) + "\n\n" + text if warn else text)[:9500]}}
    if warn:
        out["systemMessage"] = " ".join(warn)
    print(json.dumps(out))


try:
    proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    if not os.path.isfile(os.path.join(proj, ".claude", "project.json")):
        sys.exit(0)
    data = stdin_json()
    try:
        warn = warnings(data)
    except Exception as e:
        warn = []
        sys.stderr.write("agent core session start: the plugin copy check failed (%s: %s)\n"
                         % (type(e).__name__, str(e)[:160]))
    with open(os.path.join(ROOT, "VERSION"), encoding="utf-8") as f:
        version = f.read().strip()
    if os.path.isfile(os.path.join(proj, ".claude", "core", "core.lock")):
        try:
            with open(os.path.join(proj, ".claude", "core", "VERSION"), encoding="utf-8") as f:
                mine = f.read().strip()
        except OSError:
            mine = "?"
        text = ("The product-factory plugin (core %s) is on, and this repo also carries the core in `.claude/core/` "
                "(core %s) for teammates without the plugin. Use the plugin's agents `product-factory:<name>` (for "
                "example product-factory:explorer) and skills `/product-factory:<name>`, never the bare-named copies "
                "of the same agents and skills in `.claude/agents/` and `.claude/skills/`; the repo's own agents and "
                "skills with other names stay in use. Type /product-factory:<name> (for example "
                "/product-factory:develop); the bare /develop and the other skills marked (repo copy) are for "
                "teammates without the plugin. The repo copy's hooks step aside while the plugin is on and the "
                "plugin's hooks enforce the flow. The `.claude/core/` paths in AGENTS.md still work." % (version, mine))
        if mine != version:
            text += (" The versions differ: update the plugin (/plugin) or reinstall the repo copy, so both run the "
                     "same rules.")
        emit(text, warn)
        sys.exit(0)
    note = ("The agent core %s runs here as the Claude Code plugin product-factory: agents product-factory:<name> "
            "(for example product-factory:explorer), skills /product-factory:<name>. The core folder is %s: read every "
            "`.claude/core/`, `.cursor/runtime/` or `${CLAUDE_PLUGIN_ROOT}` path in AGENTS.md, the skills and the "
            "reference files as that folder (python %s/scripts/live_status.py open <id>)." % (version, ROOT, ROOT))
    am = os.path.join(proj, "AGENTS.md")
    has_block = os.path.isfile(am) and "<!-- core:start -->" in open(am, encoding="utf-8", errors="replace").read()
    text = note
    if not has_block:
        with open(os.path.join(ROOT, "templates", "AGENTS-core.md"), encoding="utf-8") as f:
            block = f.read().replace("${CLAUDE_PLUGIN_ROOT}/", ROOT + "/").replace(".claude/core/", ROOT + "/")
        text = note + "\n\n" + block
    emit(text, warn)
except SystemExit:
    raise
except Exception as e:
    sys.stderr.write("agent core session start failed (%s: %s); the core rules were not added\n"
                     % (type(e).__name__, str(e)[:160]))
