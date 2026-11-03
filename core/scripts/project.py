"""Shared helpers for the agent core: where the repo is, its project config, path matching.

Every core script and hook imports this instead of hard-coding a repo. The repo comes from
CLAUDE_PROJECT_DIR / CURSOR_PROJECT_DIR, else the nearest folder above the working directory with a
`.claude/` folder, else the working directory, never from where the core files sit. That way the same
files run from a repo's `.claude/core/` and from a plugin folder.

The project layer is `.claude/project.json`; anything it leaves out falls back to DEFAULTS.
"""
import copy
import json
import os
import re

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
    "setup_paths": [],
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
ALWAYS_GENERATED = [".cursor/agents/**", ".cursor/rules/**", ".cursor/hooks.json", ".claude/core/**"]

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


def ticket_prefixes(cfg=None):
    """`ticket_prefix` as a list: one string ("BLEN-") or several (["OBIQ-", "JPG1-"])."""
    t = (cfg or config()).get("ticket_prefix") or []
    return [t] if isinstance(t, str) else [x for x in t if isinstance(x, str) and x]


def agent_name(name):
    """Plugin agents are named "<plugin>:<agent>"; the flow only cares about the agent part."""
    return (name or "").split(":")[-1].strip()


def norm_dir(p):
    return os.path.normcase(os.path.abspath(p.replace("/", os.sep))).rstrip(os.sep) + os.sep
