"""Plugin only (SessionStart): tell the main session how the agent core runs in this repo.

Nothing at all in a repo without `.claude/project.json`: the plugin is switched on at user level, and a repo that
has not opted in to the core must not pay for it (no tokens, no rules). With project.json:
  - the repo carries the core itself (`.claude/core/core.lock`): nothing, AGENTS.md has it all;
  - the core comes from this plugin and AGENTS.md has the core block: one line naming the plugin folder, so the
    core paths in AGENTS.md, the skills and the reference files resolve;
  - no core block in AGENTS.md: that line and the core block with this plugin's paths.
An internal error prints a one-line warning on stderr and adds nothing.
"""
import json
import os
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")
    proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    if not os.path.isfile(os.path.join(proj, ".claude", "project.json")):
        sys.exit(0)
    if os.path.isfile(os.path.join(proj, ".claude", "core", "core.lock")):
        sys.exit(0)
    with open(os.path.join(ROOT, "VERSION"), encoding="utf-8") as f:
        version = f.read().strip()
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
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text[:9500]}}))
except SystemExit:
    raise
except Exception as e:
    sys.stderr.write("agent core session start failed (%s: %s); the core rules were not added\n"
                     % (type(e).__name__, str(e)[:160]))
