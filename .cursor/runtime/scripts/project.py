"""Shared helpers for the agent core: where the repo is, its project config, path matching.

Every core script and hook imports this instead of hard-coding a repo. The repo comes from
CLAUDE_PROJECT_DIR / CURSOR_PROJECT_DIR, else the nearest folder above the working directory with a
`.claude/` folder, else the working directory, never from where the core files sit. That way the same
files run from a repo's `.claude/core/` and from a plugin folder.

The project layer is `.claude/project.json`; anything it leaves out falls back to DEFAULTS. A repo without it has
not opted in: every hook exits at once there (hook_start), so the plugin switched on at user level changes nothing in
other repos.
"""
import copy
import json
import os
import re
import sys

CORE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# `git` plus any global options before the verb (-C <dir>, -c k=v, --no-pager, --git-dir=<dir>)
_ARG = r"(?:\"[^\"]*\"|'[^']*'|\S+)"
GIT = (r"git(?:\.exe)?(?:\s+(?:-[Cc]\s*" + _ARG + r"|--(?:git-dir|work-tree|namespace|exec-path|config-env)(?:=|\s+)"
       + _ARG + r"|--?[\w.-]+(?:=" + _ARG + r")?))*\s+")

# Every git command that changes the repo, its index, branches, remotes or config. Read-only git (status, diff, log,
# show, blame, grep, ls-files, branch/tag lists, stash list) stays allowed. `guard.git_on_request` (default: pull)
# lifts a rule for the turn after the developer asks for it in their own message.
_END = r"(?![\w-])"
GIT_RULES = {
    "push": (GIT + r"push" + _END, "the agent never pushes. The developer pushes."),
    "commit": (GIT + r"commit" + _END, "the agent never commits. The developer commits (ask for a message with the "
                                       "commit-msg skill)."),
    "pull": (GIT + r"pull" + _END, "the agent pulls only when the developer asks for it in their own message."),
    "fetch": (GIT + r"fetch" + _END, "the agent does not fetch. The developer updates from the remote."),
    "merge": (GIT + r"merge" + _END, "`git merge` changes the branch. The developer merges."),
    "rebase": (GIT + r"rebase" + _END, "`git rebase` rewrites the branch. The developer rebases."),
    "cherry-pick": (GIT + r"cherry-pick" + _END, "`git cherry-pick` adds commits. The developer runs it."),
    "revert": (GIT + r"revert" + _END, "`git revert` adds a commit. The developer runs it."),
    "am": (GIT + r"am" + _END, "`git am` applies commits. The developer runs it."),
    "stash": (GIT + r"stash(?!\s+(list|show)\b)" + _END, "`git stash` moves uncommitted work out of the tree."),
    "reset": (GIT + r"reset" + _END, "`git reset` can throw away work or move the branch. The developer runs it."),
    "checkout": (GIT + r"checkout" + _END, "`git checkout` switches branches or discards changes. The developer runs it."),
    "switch": (GIT + r"switch" + _END, "`git switch` changes the branch under everyone's uncommitted work."),
    "restore": (GIT + r"restore" + _END, "`git restore` discards changes or unstages the developer's work."),
    "clean": (GIT + r"clean\b[^;&|]*\s(?:-[a-zA-Z]*f|--force)", "`git clean -f` deletes untracked files."),
    "add": (GIT + r"add" + _END, "the agent does not stage files. The developer stages and commits."),
    "rm": (GIT + r"rm" + _END, "`git rm` deletes and stages. Delete the file with the file tools if needed; the "
                               "developer stages."),
    "mv": (GIT + r"mv" + _END, "`git mv` moves and stages. Move the file with the file tools; the developer stages."),
    "apply": (GIT + r"apply(?![^;&|]*(--check|--stat|--numstat|--summary))" + _END,
              "`git apply` changes files outside the edit tools. Make the change with Edit."),
    "tag": (GIT + r"tag\s+(?!-l\b|--list\b|-n\d*\b|--contains\b|--points-at\b|--merged\b|--no-merged\b|--sort\b)\S",
            "`git tag` creates or deletes tags. The developer tags."),
    "branch": (GIT + r"branch(?:\s+(?!-)\S|[^;&|]*\s(?:-[dDmMcCuf]\b|--delete|--move|--copy|--force|"
                     r"--set-upstream|--unset-upstream|--edit-description))",
               "`git branch` creates, renames or deletes branches. The developer does that."),
    "config": (GIT + r"config(?![^;&|]*(--get|--list|\s-l\b|--show-origin))" + _END,
               "`git config` changes settings. The developer does that."),
    "init": (GIT + r"init" + _END, "`git init` creates a repository. The developer does that."),
    "worktree": (GIT + r"worktree\s+(?:add|remove|move|prune|lock|unlock|repair)", "`git worktree` changes worktrees."),
    "submodule": (GIT + r"submodule\s+(?:add|update|init|deinit|sync|set-url|set-branch|absorbgitdirs)",
                  "`git submodule` changes submodules. The developer does that."),
}

DEFAULTS = {
    "name": "",
    "ticket_prefix": "",
    "work_dir": ".claude/work",
    "live_port": 8766,
    # Token cost estimate (live page, share snapshots): USD per million tokens per model family (matched by name in
    # the model id): in = new input, out = output, cw = cache write, cr = cache read. Override in project.json "costs".
    # Source: the claude-api skill model table cached 2026-11-03 (in/out, cache read) for claude-opus-5-5,
    # claude-sonnet-5-5 and claude-haiku-5-5; cache write is NOT in that table and is estimated as 1.25 x input.
    "costs": {
        "currency": "USD",
        "as_of": "2026-11-03",
        "opus": {"in": 4.0, "out": 20.0, "cw": 5.0, "cr": 0.2},
        "sonnet": {"in": 2.0, "out": 10.0, "cw": 2.5, "cr": 0.1},
        "haiku": {"in": 0.1, "out": 0.5, "cw": 0.125, "cr": 0.01},
    },
    "default_mode": "task",
    "products_root": "",
    "app": {"url": "", "status": "", "strict": False},
    "commands": {},
    "guard": {
        "git_blocked": list(GIT_RULES),
        "git_on_request": ["pull"],
        "blocked_commands": [],
        "block_while_app_up": "",
        "block_while_port_up": [],
        "secret_files": [],
        "secret_ok_commands": [],
        "no_show": [],
        "no_read": [],
        "no_write": [],
        "generated": [],
        "frozen_if_tracked": [],
        "big_file_kb": 120,
        "big_file_hints": [],
        "read_only_roots": [],
    },
    "deploy": {},
    "stack": {},
    # the project's QA facts file (roles, test users, variants, languages, known traps), read by the QA agents,
    # spec-analyst and explorer when set
    # qa.data: the test data map (test-data-engineer): approved hosts, the read-only query tool, the seed script, cleanup
    # policy (keep|remove); merged key by key, so an existing qa.facts still works
    "qa": {"facts": "", "data": {"map": ".claude/qa/data-map.md", "hosts": [], "query": "", "seed": "", "cleanup": "keep"}},
    "setup_paths": [],
    # Product code (outside the AI setup and the work folder) is written by its area agent, never by the main
    # session (the Tech Lead); the guard blocks the main session's edits there. First matching area wins.
    "routing": {
        "enforce": True,
        "areas": [
            {"agent": "qa-engineer", "paths": ["**/src/test/**", "**/test/**", "**/tests/**", "**/__tests__/**",
                                               "*.test.*", "*.spec.*"]},
            {"agent": "devops-engineer", "paths": ["manifest*.yml", "mta.yaml", "*.mtaext", "xs-security.json",
                                                   "Dockerfile", "Jenkinsfile", "pom.xml", "build.gradle*",
                                                   "package.json", "package-lock.json", ".github/**", "**/helm/**",
                                                   "**/k8s/**"]},
            {"agent": "n8n-expert", "paths": ["**/n8n*/**"]},
            {"agent": "frontend-developer", "paths": ["*.js", "*.ts", "*.tsx", "*.jsx", "*.vue", "*.html", "*.css",
                                                      "*.scss", "**/webapp/**", "**/i18n/**"]},
            {"agent": "release-manager", "paths": ["*.md", "docs/**"]},
            {"agent": "backend-developer", "paths": ["**"]},
        ],
    },
    "newline": "lf",
    "quick_fix": {"max_files": 3, "max_lines": 30, "never": []},
    "decisions": {},
    "rules": [],
    "checks": [],
    "experts": [],
    "expert_docs": {},
    "glossary": {"code_words": "", "words": []},
    "impact": {
        "code": ["**/*.java", "**/*.ts", "**/*.tsx", "**/*.js"],
        "clients": ["**/*.js", "**/*.ts", "**/*.tsx", "**/*.html"],
        "n8n": {"paths": ["**/n8n*/**/*.json"], "command": ""},
        "tools": {"marker": "@McpTool", "inventory": ""},
        "skip": ["**/target/**", "**/node_modules/**", "**/dist/**", "**/*.min.js", ".claude/worktrees/**",
                 "**/.git/**"],
        "mappings": ["RequestMapping", "GetMapping", "PostMapping", "PutMapping", "DeleteMapping", "PatchMapping"],
        "cap": 25,
        "max_kb": 1024,
    },
}

# Always generated or core-owned, in every repo.
ALWAYS_GENERATED = [".cursor/agents/**", ".cursor/rules/**", ".cursor/skills/**", ".cursor/hooks.json",
                    ".cursor/runtime/**", ".claude/core/**"]

_cache = {}


def repo_root():
    env = os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("CURSOR_PROJECT_DIR")
    if env:
        return os.path.abspath(env)
    here = os.path.abspath(os.getcwd())
    d = here
    while True:
        if os.path.isdir(os.path.join(d, ".claude")):
            return d
        up = os.path.dirname(d)
        if up == d:
            return here
        d = up


def has_project(root=None):
    """True when the repo has opted in to the core: `.claude/project.json` exists."""
    return os.path.isfile(os.path.join(root or repo_root(), ".claude", "project.json"))


PLUGIN_ID = "product-factory@talenteam"


def claude_config_dir():
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")


def _json_file(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def in_repo_copy():
    """True when this file runs from a repo's own copy of the core (`.claude/core/`), not from the plugin."""
    here = os.path.normcase(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return here.endswith(os.path.normcase(os.path.join(".claude", "core")))


def plugin_active(root=None):
    """True when the product-factory plugin is on for this Claude session: the highest settings scope that names it
    (local, project, user) says true, and installed_plugins.json has it installed for the user or for this repo.
    Then the repo's own copy of the core steps aside and the plugin's hooks do the work. Anything unreadable: False,
    so the repo copy keeps guarding."""
    root = os.path.abspath(root or repo_root())
    cfg = claude_config_dir()
    on = None
    for f in (os.path.join(root, ".claude", "settings.local.json"), os.path.join(root, ".claude", "settings.json"),
              os.path.join(cfg, "settings.json")):
        e = _json_file(f).get("enabledPlugins")
        if isinstance(e, dict) and PLUGIN_ID in e:
            on = e[PLUGIN_ID]
            break
    if on is not True:
        return False
    recs = (_json_file(os.path.join(cfg, "plugins", "installed_plugins.json")).get("plugins") or {}).get(PLUGIN_ID)
    here = os.path.normcase(root)
    return any(isinstance(r, dict) and (r.get("scope") == "user" or (r.get("projectPath") and os.path.normcase(
        os.path.abspath(r["projectPath"])) == here)) for r in recs or [])


def utf8_io():
    """UTF-8 stdout and stderr: piped streams are cp1252 on Windows, and a message with another character would
    raise inside a hook."""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def hook_start(cursor=False):
    """First call in every hook: UTF-8 output, then exit 0 at once in a repo without `.claude/project.json` (a Cursor
    guard still answers allow, because Cursor blocks on empty output), and in Claude when this is the repo's own copy
    of the core while the product-factory plugin is on (the plugin's hooks run instead; Cursor is unaffected)."""
    utf8_io()
    if not has_project():
        if cursor:
            print(json.dumps({"permission": "allow"}))
        sys.exit(0)
    if not cursor and in_repo_copy() and plugin_active():
        sys.exit(0)


def error_log():
    d = os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.join(__import__("tempfile").gettempdir(), "agent-core")
    return os.path.join(d, "hook-errors.log")


def hook_error(hook, exc):
    """Log a hook's internal error and return its one-line warning (the hooks print it; the guard also blocks)."""
    import traceback
    import time
    tb = traceback.extract_tb(exc.__traceback__) if exc.__traceback__ else []
    where = "%s:%d" % (os.path.basename(tb[-1].filename), tb[-1].lineno) if tb else "?"
    what = "%s: %s at %s" % (type(exc).__name__, str(exc).replace("\n", " ")[:160], where)
    log = error_log()
    try:
        os.makedirs(os.path.dirname(log), exist_ok=True)
        with open(log, "a", encoding="utf-8") as f:
            f.write("%s %s %s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), hook, repo_root(), what))
    except OSError:
        pass
    return "agent core %s failed (%s; log %s)" % (hook, what, log.replace("\\", "/"))


def core_path(sub=""):
    """A core file as the developer or an agent types it: relative inside the repo (`.claude/core/...`,
    `.cursor/runtime/...`), else the absolute core folder (the plugin root), with forward slashes."""
    root = repo_root()
    inside = os.path.normcase(CORE_DIR).startswith(os.path.normcase(root).rstrip("\\/") + os.sep)
    base = (os.path.relpath(CORE_DIR, root) if inside else CORE_DIR).replace("\\", "/")
    return base + ("/" + sub if sub else "")


def front_errors(text):
    """Problems in a skill or agent file's YAML frontmatter (Claude Code drops every field of a header it cannot
    parse, so the description falls back to the first body line). PyYAML when installed, plus a check of the plain
    values YAML rejects (": " or " #" inside an unquoted value), so the result is the same without it."""
    m = re.match(r"---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
    if not m:
        return ["no frontmatter (--- lines)"]
    front, out = m.group(1).replace("\r\n", "\n"), []
    try:
        import yaml
        data = yaml.safe_load(front)
        if not isinstance(data, dict):
            out.append("frontmatter is not a mapping")
    except ImportError:
        pass
    except Exception as e:
        out.append("YAML: " + str(e).replace("\n", " ")[:200])
    block = False
    for n, line in enumerate(front.split("\n"), 2):
        mt = re.match(r"^(\s*-\s+|[\w-]+:[ \t]*)(.*)$", line)
        if not mt or line[:1] in " \t" and not line.lstrip().startswith("-"):
            continue
        if re.match(r"^[\w-]+:", line):
            block = mt.group(2).strip()[:1] in ("|", ">")
        if block:
            continue
        v = mt.group(2).strip()
        if not v:
            continue
        if v[0] in "\"'":
            if len(v) < 2 or v[-1] != v[0]:
                out.append("line %d: quoted value is not closed" % n)
        elif v[0] in "[{":
            continue
        elif v[0] in "&*!%@`|>":
            out.append("line %d: a plain value cannot start with %r; quote it" % (n, v[0]))
        elif ": " in v or " #" in v or v.endswith(":"):
            out.append("line %d: unquoted value holds \": \" or \" #\"; quote it" % n)
    return list(dict.fromkeys(out))


def _merge(base, over):
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def config(root=None):
    root = root or repo_root()
    if root not in _cache:
        data = {}
        try:
            with open(os.path.join(root, ".claude", "project.json"), encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            pass
        _cache[root] = _merge(DEFAULTS, data)
    return _cache[root]


def work_dir(root=None):
    root = root or repo_root()
    return os.path.abspath(os.path.join(root, config(root)["work_dir"]))


def rel(path, root=None):
    """Repo-relative path with forward slashes, lower-cased (Windows paths are case-insensitive); None outside."""
    root = root or repo_root()
    a = os.path.abspath(path)
    if not os.path.normcase(a).startswith(os.path.normcase(root).rstrip("\\/") + os.sep) and \
            os.path.normcase(a) != os.path.normcase(root):
        return None
    return os.path.relpath(a, root).replace("\\", "/").lower()


def _glob_re(pattern):
    p = pattern.strip().replace("\\", "/").lower()
    out, i = "", 0
    while i < len(p):
        if p.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif p.startswith("**", i):
            out, i = out + ".*", i + 2
        elif p[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif p[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(p[i]), i + 1
    return re.compile(out + "$")


def match(relpath, patterns):
    """True when a repo-relative path matches one of the globs. A glob without "/" matches the file name in any
    folder (like .gitignore); one with "/" matches from the repo root; "**" spans folders."""
    if not relpath:
        return False
    r = relpath.replace("\\", "/").lower()
    name = r.rsplit("/", 1)[-1]
    for p in patterns or []:
        if "/" in p.strip("/"):
            if _glob_re(p.lstrip("/")).match(r):
                return True
        elif _glob_re(p).match(name):
            return True
    return False


SETUP = [".claude/**", ".cursor/**", "agents.md", "claude.md"]


def is_setup(relpath, cfg=None):
    """The AI setup: .claude/, .cursor/, AGENTS.md, CLAUDE.md and the repo's `setup_paths`."""
    return match(relpath, SETUP + ((cfg or config()).get("setup_paths") or []))


def product_area(path, root=None):
    """The area agent that owns a file of product code (routing.areas), or None when the path is the AI setup, the
    work folder or outside the repo."""
    root = root or repo_root()
    r = rel(path, root)
    cfg = config(root)
    if not r or is_setup(r, cfg) or os.path.normcase(os.path.abspath(path)).startswith(
            os.path.normcase(work_dir(root)) + os.sep):
        return None
    return next((a.get("agent") for a in (cfg.get("routing") or {}).get("areas") or [] if match(r, a.get("paths"))),
                "backend-developer")


def ticket_prefixes(cfg=None):
    """`ticket_prefix` as a list: one string ("BLEN-") or several (["OBIQ-", "JPG1-"])."""
    t = (cfg or config()).get("ticket_prefix") or []
    return [t] if isinstance(t, str) else [x for x in t if isinstance(x, str) and x]


def agent_name(name):
    """Plugin agents are named "<plugin>:<agent>"; the flow only cares about the agent part."""
    return (name or "").split(":")[-1].strip()


def norm_dir(p):
    return os.path.normcase(os.path.abspath(p.replace("/", os.sep))).rstrip(os.sep) + os.sep


SAP_CERT = "SAP Certified"


def certifications(text):
    """The `certifications:` list in an agent file's frontmatter (general credentials first, then SAP ones)."""
    m = re.match(r"---\r?\n(.*?)\r?\n---", text, re.S)
    if not m:
        return []
    out, inside = [], False
    for line in m.group(1).splitlines():
        if line.startswith("certifications:"):
            inside = True
        elif inside and line.startswith("  - "):
            out.append(line[4:].strip().strip('"'))
        elif inside:
            break
    return out


def certified_line(certs):
    """The `Certified as:` text an agent's frontmatter list stands for: general credentials, then `SAP:` ones."""
    gen = [c for c in certs if not c.startswith(SAP_CERT)]
    sap = [c for c in certs if c.startswith(SAP_CERT)]
    parts = ["; ".join(gen)] if gen else []
    if sap:
        parts.append("SAP: " + "; ".join(sap))
    return "Certified as: " + "; ".join(parts) + "."
