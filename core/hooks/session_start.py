"""Plugin only (SessionStart): give the main session the core's flow rules where the repo does not carry the core.

A repo with the core installed has them in AGENTS.md and switches the plugin off; anywhere else this hands Claude
the core block of AGENTS.md with the plugin's own paths, so triage, gates and the hard rules apply the same way.
Fails open: any error prints nothing.
"""
import json
import os
import sys

try:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")
    proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    am = os.path.join(proj, "AGENTS.md")
    if os.path.isfile(am) and "<!-- core:start -->" in open(am, encoding="utf-8", errors="replace").read():
        sys.exit(0)
    with open(os.path.join(ROOT, "templates", "AGENTS-core.md"), encoding="utf-8") as f:
        block = f.read().replace(".claude/core/", ROOT + "/")
    with open(os.path.join(ROOT, "VERSION"), encoding="utf-8") as f:
        version = f.read().strip()
    note = ("The agent core %s runs here as the Claude Code plugin agent-core. Its agents are agent-core:<name> (for "
            "example agent-core:explorer), its skills /agent-core:<name>, its scripts and reference under %s. Project "
            "files (.claude/project.json, the work folder) are made in this repo when the flow needs them. To give the "
            "whole team the core in this repo (Cursor too), run: python %s/scripts/install.py . --write-settings"
            % (version, ROOT, ROOT))
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                             "additionalContext": (note + "\n\n" + block)[:9500]}}))
except SystemExit:
    raise
except Exception:
    pass
