#!/usr/bin/env python3
"""Review and design pack (agent core): what a reviewer or a designer needs for one task, in one file, in seconds.

    review_pack.py ID                          <work>/ID/review-pack.md and review-state.json
    review_pack.py ID --full                   pack every task file again, even after a review
    review_pack.py ID --base REV [--head REV]  diff against REV (default HEAD); --head packs a commit range
    review_pack.py ID --files GLOB...          the task's files (default: the scope baseline, else Planned files)
    review_pack.py ID --design                 <work>/ID/design-pack.md, plus a design.md skeleton when there is none
    --root DIR                                 the code repo (a product root) when it is not this repo

Review pack, in this order: pre-filled MUST rows (scope, safety, callers nobody checked), the acceptance criteria,
the approved cards and fixed answers (one line each), the callers from the impact map, the files, the checklist
sections whose path trigger matches a changed file (core and project; a project item replaces the core item of the
same id), the hard rules of AGENTS.md, the `.claude/rules/*.md` files and the lessons.md lines for those paths, the
live checks for the matched items, then the diff with new-side line numbers (new files in full; both capped; values
in secret files masked). A checklist section's trigger is the backticked globs after " - " in its heading, or a
`Paths:` line right under it; a backticked `@Marker` matches the changed text.

Re-review: review-state.json keeps a hash and a copy of every packed file. When review.md exists, the next run packs
only the files changed since then (as the change since the last review), names the files whose PASS stays, and lists
the previous MUST rows to re-check. --full packs everything again.

Design pack: the criteria, fixed answers, the impact-map rows, the decision cards the paths may need (project.json
`decisions`), the hard rules, the path rules, the repo facts (`.claude/experts/*.md` lines naming a path) and the
lessons for the paths that context.md names. The skeleton has one Changes row per criterion and one Impact map row
per impact-map line; every `<fill>` left fails handoff_check.

Read-only git only (diff, ls-files, rev-parse, status). Standard library only.
Exit codes: 0 done, 1 no task folder or bad id, 2 usage error.
"""
import argparse
import difflib
import hashlib
import json
import os
import re
import sys
import time

sys.dont_write_bytecode = True
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:  # `python -I` leaves the script's folder off sys.path
    sys.path.insert(0, _HERE)
import project  # noqa: E402
import scope_check  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

PACK, STATE, DPACK = "review-pack.md", "review-state.json", "design-pack.md"
CAP_FILE, CAP_NEW, CAP_TOTAL, CAP_WIDTH = 400, 300, 4000, 300  # rendered lines per diff / new file / pack; chars
CAP_ROWS = 40
KEEP_TEXT = 256 * 1024  # files up to this size keep a copy in review-state.json for the next delta
BIG_NEW = 2 * 1024 * 1024
SECRET = ["application*.properties", "manifest.yml", "manifest.yaml", "xs-security*.json", "*Constants*", ".env",
          ".env.*"]
META = ("which focus", "how to use", "severity", "live checks", "definition of done")
STOP = {"and", "the", "for", "with", "every", "change", "changes", "code", "files", "file", "all", "new", "other"}
TICK = re.compile(r"`([^`]+)`")
ITEM = re.compile(r"^\s*[-*]\s+\*\*([A-Z]{2,3}\d+)\b")
CITE = re.compile(r"\b([A-Z]{2,3})(\d+)(?:\s*-\s*(?:\1)?(\d+))?\b")
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
PATHISH = re.compile(r"[\w.\-/]*[\w\-]\.(?:java|kt|js|jsx|ts|tsx|vue|html|xml|css|scss|properties|json|py|sql|yml|"
                     r"yaml|md|groovy|go|cs)\b")


# ---------------------------------------------------------------- small helpers

def read(path):
    try:
        with open(path, "rb") as f:
            return f.read().decode("utf-8", "replace").replace("\r\n", "\n")
    except OSError:
        return None


def sections(text, mark="## "):
    """[(heading, [body lines])] for each heading of that level; code fences respected."""
    out, fence = [], False
    for ln in (text or "").split("\n"):
        if ln.lstrip().startswith("```"):
            fence = not fence
        if not fence and ln.startswith(mark) and not ln.startswith(mark + "#"):
            out.append((ln[len(mark):].strip(), []))
        elif out:
            out[-1][1].append(ln)
    return out


def section(text, *names):
    """Body lines of the first `## ` section whose heading starts with one of the names (case-insensitive)."""
    for head, body in sections(text):
        if head.lower().startswith(tuple(n.lower() for n in names)):
            return body
    return None


def tidy(lines, cap=CAP_ROWS):
    """Lines without leading, trailing and doubled blank lines, capped with a "+N more" note."""
    out = []
    for ln in lines or []:
        if ln.strip() or (out and out[-1].strip()):
            out.append(clip(ln.rstrip()))
    while out and not out[-1].strip():
        out.pop()
    if len(out) > cap:
        out = out[:cap] + ["(+%d more lines in the source file)" % (len(out) - cap)]
    return out


def clip(s, width=CAP_WIDTH):
    return s if len(s) <= width else s[:width] + " ...(+%d chars)" % (len(s) - width)


def words(s):
    return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if len(w) > 2 and w not in STOP}


def git(root, args, timeout=60):
    p = scope_check._git(root, args, timeout=timeout)
    if p is None or p.returncode != 0:
        return None
    return p.stdout.decode("utf-8", "replace")


def sha1(data):
    return hashlib.sha1(data).hexdigest()


def file_bytes(root, path):
    try:
        with open(os.path.join(root, *path.split("/")), "rb") as f:
            return f.read()
    except OSError:
        return None


def glob_list(entries):
    return [e + "**" if e.endswith("/") else e for e in entries]


def hits(path, pats):
    """Glob match; a pattern with a folder that does not start at the repo root also matches deeper down."""
    out = []
    for p in pats:
        p = p.strip()
        if not p:
            continue
        out.append(p)
        if "/" in p.strip("/") and not p.startswith(("**", "/")):
            out.append("**/" + p)
    return project.match(path, out)


def cites(text):
    """Checklist ids a line cites: "RE1-RE4, PG9" -> {RE1, RE2, RE3, RE4, PG9}."""
    out = set()
    for pre, a, b in CITE.findall(text or ""):
        a = int(a)
        for n in range(a, (int(b) if b and int(b) >= a and int(b) - a < 40 else a) + 1):
            out.add("%s%d" % (pre, n))
    return out


# ---------------------------------------------------------------- places

class Ctx:
    def __init__(self, tid, a):
        self.here = project.repo_root()
        self.root = os.path.abspath(a.root) if a.root else self.here
        self.cfg_root = self.root if os.path.isdir(os.path.join(self.root, ".claude")) else self.here
        self.cfg = project.config(self.cfg_root)
        self.tid = tid
        self.tdir = os.path.join(project.work_dir(self.here), tid)
        self.a = a

    def doc(self, name):
        return read(os.path.join(self.tdir, name))

    def cfg_file(self, *parts):
        return read(os.path.join(self.cfg_root, *parts))

    def secret(self, path):
        g = self.cfg.get("guard") or {}
        return hits(path, SECRET + list(g.get("secret_files") or []) + list(g.get("no_show") or []))


def risk(c):
    for name in ("triage.md", "spec.md", "status.md"):
        m = re.search(r"(?im)^\W*risk\W*:\W*(low|medium|high)\b", c.doc(name) or "")
        if m:
            return m.group(1).lower()
    return "unknown"


def product_mode(c):
    return os.path.isfile(os.path.join(c.tdir, "02-spec.md"))


# ---------------------------------------------------------------- which files

def task_files(c):
    """-> ({path: "M"|"A"|"D"}, base sha, notes). Paths are relative to the code root with forward slashes."""
    a, notes = c.a, []
    base = (git(c.root, ["rev-parse", "--verify", "-q", (a.base or "HEAD") + "^{commit}"]) or "").strip()
    if not base:
        return None, "", ["no git, or %s is not a commit: nothing to diff" % (a.base or "HEAD")]
    rng = [base] + ([a.head] if a.head else [])
    raw = git(c.root, ["-c", "core.quotepath=off", "diff", "--relative", "--name-status", "--no-renames", *rng]) or ""
    status = {}
    for ln in raw.split("\n"):
        parts = ln.split("\t")
        if len(parts) == 2 and parts[0]:
            status[parts[1].replace("\\", "/")] = parts[0][0]
    if not a.head:
        for p in (git(c.root, ["-c", "core.quotepath=off", "ls-files", "--others", "--exclude-standard"]) or "").split("\n"):
            if p.strip():
                status.setdefault(p.strip().replace("\\", "/"), "A")
    work = project.rel(project.work_dir(c.here), c.root)
    skip = scope_check._skip_globs(c.root)
    status = {p: s for p, s in status.items()
              if not (work and work not in (".", "") and p.lower().startswith(work.rstrip("/") + "/"))
              and not project.match(p, skip)}

    plan_fp = scope_check._plan_file(c.tdir) if os.path.isdir(c.tdir) else None
    plan = glob_list(scope_check._planned(scope_check._read(plan_fp)[0]) or []) if plan_fp else []
    if a.files:
        keep = {p: s for p, s in status.items() if hits(p, glob_list(a.files))}
        notes.append("files from --files")
    elif not a.head and c.root == c.here and os.path.isfile(os.path.join(c.tdir, scope_check.BASELINE)):
        state, changed, _bad, _fp = scope_check._scan(c.tid, c.root)
        keep = {p: status.get(p, "M") for p in changed} if state == "ok" else dict(status)
        notes.append("files changed since the scope baseline" if state == "ok" else "scope baseline unreadable")
    elif plan:
        keep = {p: s for p, s in status.items() if hits(p, plan)}
        notes.append("files that match the Planned files")
    else:
        keep = dict(status)
        notes.append("no --files, scope baseline or Planned files: every changed file is packed (other people's "
                     "changes may be among them)")
    return dict(sorted(keep.items(), key=lambda kv: kv[0].lower())), base, notes


# ---------------------------------------------------------------- diff rendering

KV = re.compile(r"^(\s*[\"']?[\w.\-\[\]]+[\"']?\s*[=:]\s*)(\S.*)$")
STR = re.compile(r"\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'")


def mask(body, path):
    low = path.lower()
    if low.endswith((".properties", ".yml", ".yaml")) or os.path.basename(low).startswith(".env"):
        m = KV.match(body)
        return m.group(1) + "***" if m else STR.sub('"***"', body)
    if low.endswith(".json") and ":" in body:
        return re.sub(r"(:\s*)(\"(?:[^\"\\]|\\.)*\"|[^,\s{}\[\]]+)", r'\1"***"', body)
    return STR.sub('"***"', body)


def render_diff(raw, path, secret):
    out, new_no, started = [], 0, False
    for line in raw.split("\n"):
        line = line.rstrip("\r")
        if not started:
            if line.startswith("Binary files"):
                return ["(binary file changed)"]
            m = HUNK.match(line)
            if not m:
                continue
            started = True
        m = HUNK.match(line)
        if m:
            new_no = int(m.group(1))
            out.append(clip(line))
            continue
        if not line or line.startswith("\\"):
            continue
        tag, body = line[0], line[1:]
        body = clip(mask(body, path) if secret else body)
        if tag == "+":
            out.append("%5d +%s" % (new_no, body))
            new_no += 1
        elif tag == "-":
            out.append("      -%s" % body)
        else:
            out.append("%5d  %s" % (new_no, body))
            new_no += 1
    return out


def render_new(data, path, secret):
    if data is None:
        return ["(file not readable)"]
    if b"\0" in data[:8192]:
        return ["(binary file, %d KB)" % (len(data) // 1024)]
    if len(data) > BIG_NEW:
        return ["(new file, %d KB: too big to show; open it with Read offset/limit)" % (len(data) // 1024)]
    lines = data.decode("utf-8", "replace").replace("\r\n", "\n").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return ["%5d +%s" % (i, clip(mask(ln, path) if secret else ln)) for i, ln in enumerate(lines, 1)]


def capped(lines, cap, path):
    if len(lines) <= cap:
        return lines
    last = next((ln for ln in reversed(lines[:cap]) if ln[:5].strip().isdigit()), "")
    at = (" (open `%s` from line %s)" % (path, last[:5].strip())) if last else ""
    return lines[:cap] + ["... cut: %d more lines%s" % (len(lines) - cap, at)]


def file_diff(c, path, st, base):
    """Rendered diff of one file against the base (or the commit range)."""
    secret = c.secret(path)
    if st == "A" and not c.a.head and git(c.root, ["ls-files", "--error-unmatch", "--", path]) is None:
        return capped(render_new(file_bytes(c.root, path), path, secret), CAP_NEW, path), secret
    rng = [base] + ([c.a.head] if c.a.head else [])
    raw = git(c.root, ["diff", "-U5", "--no-color", "--no-ext-diff", "--no-renames", *rng, "--", path]) or ""
    cap = CAP_NEW if st == "A" else CAP_FILE
    return capped(render_diff(raw, path, secret) or ["(no textual change)"], cap, path), secret


def since_diff(c, path, old_text):
    """The change since the last review, from the copy in review-state.json."""
    data = file_bytes(c.root, path)
    if data is None:
        return ["(deleted since the last review)"]
    new = data.decode("utf-8", "replace").replace("\r\n", "\n").split("\n")
    raw = "\n".join(difflib.unified_diff(old_text.split("\n"), new, "a", "b", n=5, lineterm=""))
    return capped(render_diff(raw, path, c.secret(path)) or ["(no textual change)"], CAP_FILE, path)


# ---------------------------------------------------------------- rules and checklists

def triggers(head, body):
    for ln in body[:4]:
        if ln.strip().lower().startswith("paths:"):
            return TICK.findall(ln)
    return TICK.findall(head.split(" - ", 1)[1]) if " - " in head else []


def section_hit(toks, files, texts):
    for t in toks:
        if t.startswith("@"):
            if any(t in x for x in texts):
                return True
        elif any(ch in t for ch in "/*.") and any(hits(f, [t]) for f in files):
            return True
    return False


def checklists(c, files, texts):
    """-> (rendered lines, matched section names, ids of the included items, live-check lines)."""
    core = read(os.path.join(project.CORE_DIR, "reference", "review", "checklist.md")) or ""
    proj = c.cfg_file(".claude", "review", "checklist.md") or ""
    proj_ids = {m.group(1) for ln in proj.split("\n") for m in [ITEM.match(ln)] if m}
    passes = set(re.findall(r"[\w-]+ \((ui|speed|sf|ai|n8n)\)", "\n".join(
        (c.doc(n) or "") for n in ("triage.md", "spec.md"))))
    out, names, ids, live = [], [], set(), {"core": [], "project": []}
    extra = []
    for src, text in (("core", core), ("project", proj)):
        for head, body in sections(text):
            low = head.lower()
            if low.startswith("live checks"):
                live[src] = [ln for ln in body if ln.lstrip().startswith("- ")]
                continue
            if low.startswith("which focus") and passes:
                extra += [ln for ln in body if re.match(r"^- `[\w-]+ \((%s)\)`" % "|".join(passes), ln.strip())]
            if low.startswith(META):
                continue
            if not (low.startswith("always") or section_hit(triggers(head, body), files, texts)):
                continue
            keep = []
            for ln in body:
                if ln.strip().lower().startswith("paths:"):
                    continue
                m = ITEM.match(ln)
                if m and src == "core" and m.group(1) in proj_ids:
                    continue  # the project's item of the same id wins
                if m:
                    ids.add(m.group(1))
                keep.append(ln)
            body = tidy(keep, 120)
            if any(ITEM.match(ln) for ln in body) or src == "project":
                out += ["### %s: %s" % (src, head)] + body + [""]
                names.append(head.split(" - ")[0])
    if extra:
        out += ["### Expert review passes on this team: the items each one reads"] + [clip(ln) for ln in extra] + [""]
    pool = live["project"] or live["core"]
    lv = [clip(ln) for ln in pool if not cites(ln) or cites(ln) & ids]
    return out, names, ids, lv


def rule_files(c, files):
    """[(name, globs, body lines)] of `.claude/rules/*.md` whose `paths:` or `globs:` match a file."""
    d = os.path.join(c.cfg_root, ".claude", "rules")
    out = []
    for name in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        text = read(os.path.join(d, name)) if name.endswith(".md") else None
        if not text:
            continue
        globs, body, lines = [], text.split("\n"), text.split("\n")
        if lines and lines[0].strip() == "---":
            end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), 0)
            key = ""
            for ln in lines[1:end]:
                m = re.match(r"^(\w+)\s*:\s*(.*)$", ln)
                if m:
                    key = m.group(1).lower()
                    if key in ("paths", "globs") and m.group(2).strip():
                        globs += [g.strip().strip("\"'") for g in m.group(2).strip("[]").split(",") if g.strip()]
                    continue
                m = re.match(r"^\s*-\s*[\"']?([^\"']+?)[\"']?\s*$", ln)
                if m and key in ("paths", "globs"):
                    globs.append(m.group(1))
            body = lines[end + 1:] if end else lines
        if globs and any(hits(f, globs) for f in files):
            out.append((".claude/rules/" + name, globs, tidy(body, 60)))
    return out


# a lesson tagged for another stage (`[review-spec R<n>]`, `[test <type>]`) is read by spec-analyst or qa-lead, not
# by the reviewer; untagged and `[develop review]` lines are the review's (sdlc skill, section 9)
OTHER_STAGE = re.compile(r"^\s*-\s[^\[\]]{0,160}?\[(?:review-spec(?:\s+(?:dor\s+)?R\d+)?|test\s+[\w-]+)\]\s*:", re.I)


def lesson_lines(c, files, areas):
    """lessons.md lines whose path tokens match a file, whose `###` area matches a matched section or rule file, or
    that name a changed class; lines tagged for another stage are left out."""
    text = c.cfg_file(".claude", "review", "lessons.md") or ""
    stems = {os.path.splitext(os.path.basename(f))[0] for f in files}
    stems = {s for s in stems if len(s) >= 6}
    area_words = set().union(*[words(a) for a in areas]) if areas else set()
    out, head = [], ""
    for ln in text.split("\n"):
        if ln.startswith("### "):
            head = ln[4:]
            continue
        if not ln.lstrip().startswith("- ") or OTHER_STAGE.match(ln):
            continue
        take = bool(words(head) & area_words) or "always" in head.lower() or any(s in ln for s in stems)
        if not take:
            m = re.search(r"\(([^()]*)\)[\s.]*(?:\(again[^)]*\)[\s.]*)*$", ln)
            for tok in re.split(r"[,;\s]+", m.group(1)) if m else []:
                tok = tok.strip("`'\".")
                if ("/" in tok or "*" in tok) and any(hits(f, [tok]) or tok.strip("*/").lower() in f.lower()
                                                     for f in files):
                    take = True
                    break
        if take:
            out.append(clip(ln.strip(), 400))
    return out[:CAP_ROWS] + (["(+%d more lessons)" % (len(out) - CAP_ROWS)] if len(out) > CAP_ROWS else [])


def hard_rules(c):
    body = section(c.cfg_file("AGENTS.md") or "", "hard rules")
    return tidy(body, 60) if body else []


# ---------------------------------------------------------------- task documents

def criteria(c):
    for name in (("02-spec.md",) if product_mode(c) else ()) + ("spec.md", "triage.md", "brief.md"):
        body = section(c.doc(name) or "", "acceptance criteria")
        if body and any(ln.strip() for ln in body):
            return name, tidy(body, 60)
    return "", []


def fixed_answers(c):
    out = []
    for name in ("brief.md", "spec.md", "triage.md"):
        body = section(c.doc(name) or "", "not doing", "out of scope")
        if body:
            out += ["Not doing (%s):" % name] + [ln for ln in tidy(body, 15) if ln.strip()]
            break
    seen = set()
    for name in ("questions.md", "spec.md", "brief.md"):
        for ln in (c.doc(name) or "").split("\n"):
            m = re.match(r"^\s*(?:[-*|]\s*)?\**((?:Q|A)\d+)\b", ln)
            if m and m.group(1) not in seen:
                seen.add(m.group(1))
                out.append(clip(ln.strip(), 260))
    return out[:CAP_ROWS]


def cards(c):
    out = [clip(ln.strip()) for ln in (c.doc("decisions.md") or "").split("\n") if ln.strip().startswith("- ")]
    d = os.path.join(c.tdir, "decisions")
    for name in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        text = read(os.path.join(d, name)) if name.endswith(".md") else None
        if not text:
            continue
        title = next((ln[2:].strip() for ln in text.split("\n") if ln.startswith("# ")), name)
        body = section(text, "1.", "decision needed") or []
        first = next((ln.strip() for ln in body if ln.strip()), "")
        out.append(clip("- `decisions/%s` %s: %s" % (name, title, first), 400))
    return out


def impact_rows(c):
    """[(label, where path or "", planned check)] from context.md `## Impact map`, else design.md's."""
    for name in ("context.md", "design.md"):
        body = section(c.doc(name) or "", "impact map")
        if not body:
            continue
        rows, cols = [], None
        for ln in body:
            if not ln.strip().startswith("|"):
                continue
            cells = [x.strip() for x in ln.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-+:?", x) for x in cells if x):
                continue
            low = [x.lower() for x in cells]
            if "kind" in low or "area" in low or "where" in low:
                cols = low
                continue
            if cols and "kind" in cols and len(cells) >= 3:
                rows.append(("%s %s" % (cells[0], cells[1]), cells[2], ""))
            elif len(cells) >= 3:
                rows.append((cells[0], "", cells[2]))
            elif cells:
                rows.append((cells[0], "", ""))
        if rows:
            return name, rows
    return "", []


def where_path(where):
    m = re.search(r"`?([\w.\-/]+\.\w+)(?::\d+)?`?", where or "")
    return m.group(1) if m else ""


# ---------------------------------------------------------------- review pack

def prefilled(c, rk, files):
    rows, notes = [], []
    if c.a.head:
        notes.append("scope: not run (commit range)")
    elif c.root != c.here:
        notes.append("scope: run `scope_check.py check %s` in this repo" % c.tid)
    else:
        state, _changed, bad, _fp = scope_check._scan(c.tid, c.root)
        if state == "ok":
            rows += [("`%s`" % p, "not in the plan (scope)", "drop it, or `scope_check.py add %s %s --why \"...\"`"
                      % (c.tid, p)) for p in bad]
            notes.append("scope: %d changed files, %d unplanned" % (len(_changed), len(bad)))
        else:
            notes.append("scope: no baseline (%s), scope check not run" % state)
    if rk in ("medium", "high"):
        safety = c.doc("safety.md")
        if safety is None:
            rows.append(("`safety.md`", "safety net not run: safety.md is missing (risk %s)" % rk,
                         "run the before and after steps of sdlc section 5"))
        else:
            for part in ("before build", "after build"):
                body = section(safety, part)
                if not body or not any(ln.strip() for ln in body):
                    rows.append(("`safety.md`", "safety net not run: `## %s` is missing or empty" % part.capitalize(),
                                 "run that step and record the counts"))
            notes.append("safety: safety.md present; judge its counts")
    else:
        notes.append("safety: risk %s, full unit suite before and after only" % rk)
    return rows, notes


def caller_table(c, rk, files, only=None):
    src, rows = impact_rows(c)
    if not rows:
        return [], src
    test = (c.doc("test.md") or "") + "\n" + (c.doc("safety.md") or "")
    out = ["| # | caller | where | checked by | result |", "|---|---|---|---|---|"]
    n = 0
    for label, where, planned in rows:
        path = where_path(where)
        if only is not None and path and path not in only:
            continue
        base = os.path.basename(path) if path else ""
        if planned:
            by = "planned: " + planned
        elif base and base in test:
            by = "test.md or safety.md names %s" % base
        else:
            by = "unchecked" if rk in ("medium", "high") else "-"
        n += 1
        if n > CAP_ROWS:
            out.append("| | (+%d more in %s) | | | |" % (len(rows) - CAP_ROWS, src))
            break
        out.append("| C%d | %s | %s | %s | |" % (n, clip(label, 160), clip(where, 120), clip(by, 160)))
    return out, src


def prev_musts(c):
    text = c.doc("review.md") or ""
    verdict = next((ln.strip() for ln in text.split("\n") if "verdict" in ln.lower()), "")
    rows = []
    for head, body in sections(text):
        if "must" in head.lower() and "dropped" not in head.lower():
            for ln in body:
                s = ln.strip()
                if s.startswith("|") and not re.fullmatch(r"[|\s:-]+", s) and not re.match(r"\|\s*#\s*\|", s):
                    rows.append(clip(s, 600))
            break
    return verdict, rows


def load_state(c):
    try:
        with open(os.path.join(c.tdir, STATE), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def cur_sha(c, path):
    raw = file_bytes(c.root, path)
    return sha1(raw) if raw is not None else "missing"


def save_state(c, base, files):
    data = {"version": 1, "task": c.tid, "created": time.strftime("%Y-%m-%dT%H:%M:%S"), "base": base,
            "head": c.a.head or "", "files": {}}
    for p in files:
        raw = file_bytes(c.root, p)
        if raw is None:
            data["files"][p] = {"sha1": "missing"}
            continue
        entry = {"sha1": sha1(raw)}
        if len(raw) <= KEEP_TEXT and b"\0" not in raw[:8192]:
            entry["text"] = raw.decode("utf-8", "replace").replace("\r\n", "\n")
        data["files"][p] = entry
    tmp = os.path.join(c.tdir, STATE + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=0)
    os.replace(tmp, os.path.join(c.tdir, STATE))


def cmd_review(c):
    files, base, notes = task_files(c)
    if files is None:
        print("review_pack: " + notes[0], file=sys.stderr)
        return 1
    rk = risk(c)
    prev = None if c.a.full or c.a.head else load_state(c)
    delta = bool(prev and os.path.isfile(os.path.join(c.tdir, "review.md")) and prev.get("base") == base)
    changed = list(files)
    kept, dropped = [], []
    if delta:
        old = prev.get("files") or {}
        changed = [p for p in files if (old.get(p) or {}).get("sha1") != cur_sha(c, p)]
        kept = [p for p in files if p not in changed]
        dropped = [p for p in old if p not in files]

    diffs, texts, total, adds, dels = {}, [], 0, 0, 0
    for p in changed:
        old = (prev.get("files") or {}).get(p, {}) if delta else {}
        if delta and "text" in old:
            lines, secret = since_diff(c, p, old["text"]), c.secret(p)
        else:
            lines, secret = file_diff(c, p, files[p], base)
        adds += sum(1 for ln in lines if ln[5:7] == " +")
        dels += sum(1 for ln in lines if ln.startswith("      -"))
        room = CAP_TOTAL - total
        if room <= 0:
            lines = ["(not shown: the pack is full; read the file or `git diff -- %s`)" % p]
        elif len(lines) > room:
            lines = capped(lines, room, p)
        total += len(lines)
        diffs[p] = (lines, secret)
        texts.append("\n".join(lines))

    chk, areas, ids, live = checklists(c, changed, texts)
    rules = rule_files(c, changed)
    lessons = lesson_lines(c, changed, areas + [os.path.splitext(os.path.basename(r[0]))[0] for r in rules])
    pre, pre_notes = prefilled(c, rk, changed)
    callers, csrc = caller_table(c, rk, changed, only=set(changed) if delta else None)
    if rk in ("medium", "high"):
        for ln in callers:
            if "| unchecked |" in ln:
                cells = [x.strip() for x in ln.strip("|").split("|")]
                pre.append(("%s `%s`" % (cells[0], cells[2] or cells[1]), "unchecked caller: %s" % cells[1],
                            "check it (still correct, same contract, same permission) or name the test or live check"))
    src, acs = criteria(c)

    rng = "commits %s..%s" % (base[:10], c.a.head) if c.a.head else "working tree vs %s (%s)" % (
        c.a.base or "HEAD", base[:10])
    L = ["# Review pack - %s" % c.tid, "",
         "Built %s by `review_pack.py`. Mode: **%s**. Risk: %s. Diff: %s. %d file%s%s (+%d -%d lines shown)." % (
             time.strftime("%Y-%m-%d %H:%M"), "delta (re-review)" if delta else "full", rk, rng, len(changed),
             "" if len(changed) == 1 else "s", " of %d" % len(files) if delta else "", adds, dels),
         "Read this file and nothing else up front. Open code only to prove or drop a finding (Read with offset "
         "and limit, or one Grep); never re-run `git diff` per file. Write `%s/review.md`." % project.rel(
             c.tdir, c.here) if project.rel(c.tdir, c.here) else "Write review.md in the task folder.",
         "Notes: " + "; ".join(notes + pre_notes) + ".", ""]
    if delta:
        verdict, rows = prev_musts(c)
        L += ["## Re-review (delta)", "",
              "Last pack %s. Review only the change below, re-check each previous MUST row, keep the rest of "
              "review.md as it is (its PASS parts stay) and update the verdict." % prev.get("created", "?"),
              "Previous verdict: %s" % (verdict or "?"), "",
              "Previous MUST rows to re-check:", ""] + (rows or ["(none)"]) + [""]
        if kept:
            L += ["Unchanged since the last review (PASS stays): " + ", ".join("`%s`" % p for p in kept), ""]
        if dropped:
            L += ["No longer in the change: " + ", ".join("`%s`" % p for p in dropped), ""]
        if not changed:
            L += ["Nothing changed since the last review: re-check the MUST rows only.", ""]
    L += ["## Pre-filled MUST rows", "",
          "Each row stays a MUST unless you clear it with evidence (`path:line`, a test in test.md, a live check).", ""]
    if pre:
        L += ["| # | where | problem | fix |", "|---|---|---|---|"]
        L += ["| P%d | %s | %s | %s |" % (i, w, p, f) for i, (w, p, f) in enumerate(pre, 1)]
    else:
        L.append("(none)")
    L += ["", "## Acceptance criteria" + (" (%s)" % src if src else ""), ""] + (acs or ["(none found)"]) + [""]
    fa, cd = fixed_answers(c), cards(c)
    L += ["## Approved cards and fixed answers", "",
          "A change past an approved card is a MUST \"not approved: raise a change card\"; one against a Q#/A# or "
          "\"Not doing\" is a MUST \"goes against Q#/A#\".", ""] + (cd or ["(no cards)"]) + [""] + (fa or []) + [""]
    if callers:
        L += ["## Callers to check (%s)" % csrc, "",
              "Fill `checked by` and `result` in review.md `## Callers`. At risk medium or high a row left "
              "\"unchecked\" is a MUST \"unchecked caller\"." if rk in ("medium", "high") else
              "Risk %s: check the callers the diff touches." % rk, ""] + callers + [""]
    L += ["## Files", "", "| file | status | lines shown |", "|---|---|---|"]
    L += ["| `%s` | %s%s | %d |" % (p, {"A": "new", "D": "deleted"}.get(files[p], "changed"),
                                     ", secret: values masked" if diffs[p][1] else "", len(diffs[p][0]))
          for p in changed]
    L += ["", "## Checklist for these paths", "",
          "Only the sections whose path trigger matches a changed file. Cite the item id in each finding.", ""]
    L += chk or ["(no section matched)"]
    hr = hard_rules(c)
    if hr:
        L += ["## Hard rules (AGENTS.md)", ""] + hr + [""]
    if rules:
        L += ["## Path rules", ""]
        for name, globs, body in rules:
            L += ["### `%s` (%s)" % (name, ", ".join(globs))] + body + [""]
    L += ["## Lessons for these paths", "", "Each line is a mistake this repo already made: a repeat is a MUST.", ""]
    L += (lessons or ["(none)"]) + [""]
    L += ["## Live checks for Verify", "", "Not findings: copy the lines the change touches into review.md.", ""]
    L += (live or ["(none)"]) + [""]
    L += ["## Diff", "", "New-side line numbers on the left (cite them as `path:line`); `-` lines were removed.", ""]
    for p in changed:
        lines, _secret = diffs[p]
        L += ["### `%s`%s" % (p, " (since the last review)" if delta and p in (prev.get("files") or {}) else ""),
              "", "```diff"] + lines + ["```", ""]
    out = os.path.join(c.tdir, PACK)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L).rstrip() + "\n")
    save_state(c, base, list(files))
    print("Review pack: %s (%s, %d file%s, %d lines, %d pre-filled MUST row%s)" % (
        project.rel(out, c.here) or out, "delta" if delta else "full", len(changed), "" if len(changed) == 1 else "s",
        len(L), len(pre), "" if len(pre) == 1 else "s"))
    return 0


# ---------------------------------------------------------------- design pack

def design_paths(c):
    """Repo files that context.md, triage.md and the impact map name (bare file names resolved when unique)."""
    listed = [p for p in (git(c.root, ["-c", "core.quotepath=off", "ls-files", "--cached", "--others",
                                       "--exclude-standard"]) or "").split("\n") if p]
    by_name = {}
    for p in listed:
        by_name.setdefault(os.path.basename(p).lower(), []).append(p)
    text = "\n".join((c.doc(n) or "") for n in ("context.md", "triage.md", "spec.md", "brief.md"))
    out = []
    for m in PATHISH.finditer(text):
        tok = m.group(0)
        while tok.startswith("./"):
            tok = tok[2:]
        if "/" in tok and os.path.isfile(os.path.join(c.root, *tok.split("/"))):
            out.append(tok)
        elif "/" not in tok and len(by_name.get(tok.lower(), [])) == 1:
            out.append(by_name[tok.lower()][0])
    plan_fp = scope_check._plan_file(c.tdir)
    for e in (scope_check._planned(scope_check._read(plan_fp)[0]) or []) if plan_fp else []:
        if "*" not in e and os.path.isfile(os.path.join(c.root, *e.split("/"))):
            out.append(e)
    seen, res = set(), []
    for p in out:
        if p.lower() not in seen and not project.match(p, scope_check._skip_globs(c.root)):
            seen.add(p.lower())
            res.append(p)
    return res[:200]


def decisions_needed(c, paths):
    out = []
    for d, spec in sorted((c.cfg.get("decisions") or {}).items()):
        if not isinstance(spec, dict) or not spec.get("paths"):
            continue
        hit = [p for p in paths if hits(p, spec["paths"])]
        marks = list(spec.get("file_markers") or []) + list(spec.get("line_markers") or [])
        if marks:
            hit = [p for p in hit if any(m in ((file_bytes(c.root, p) or b"").decode("utf-8", "replace"))
                                         for m in marks)]
        if hit:
            out.append("- %s (%s): %s" % (d, spec.get("what", ""), ", ".join("`%s`" % p for p in hit[:6])
                                          + (" +%d more" % (len(hit) - 6) if len(hit) > 6 else "")))
    return out


def expert_facts(c, paths):
    d = os.path.join(c.cfg_root, ".claude", "experts")
    stems = {os.path.splitext(os.path.basename(p))[0] for p in paths}
    stems = {s for s in stems if len(s) >= 5}
    out = []
    for name in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        text = read(os.path.join(d, name)) if name.endswith(".md") else None
        head = ""
        for ln in (text or "").split("\n"):
            if ln.startswith("## "):
                head = ln[3:].strip()
            elif ln.strip() and any(re.search(r"\b%s\b" % re.escape(s), ln) for s in stems):
                out.append(clip("- `%s` %s: %s" % (name, head, ln.strip()), 400))
    return out[:CAP_ROWS]


def cmd_design(c):
    paths = design_paths(c)
    src, acs = criteria(c)
    isrc, irows = impact_rows(c)
    rules = rule_files(c, paths)
    texts = [(file_bytes(c.root, p) or b"")[:200000].decode("utf-8", "replace") for p in paths[:60]]
    _chk, areas, _ids, _live = checklists(c, paths, texts)
    lessons = lesson_lines(c, paths, areas + [os.path.splitext(os.path.basename(r[0]))[0] for r in rules])
    L = ["# Design pack - %s" % c.tid, "",
         "Built %s by `review_pack.py --design` from context.md, the spec and the repo's rules for %d paths. Read "
         "this file and context.md, then fill design.md. Open code only for a named gap in context.md `## Gaps` "
         "(add what you find there) or the one nearest example." % (time.strftime("%Y-%m-%d %H:%M"), len(paths)), ""]
    L += ["## Acceptance criteria" + (" (%s)" % src if src else ""), ""] + (acs or ["(none found)"]) + [""]
    fa, cd = fixed_answers(c), cards(c)
    if fa or cd:
        L += ["## Fixed answers, scope and cards so far", ""] + cd + fa + [""]
    if irows:
        L += ["## Impact map rows (%s)" % isrc, "", "Each gets a design.md `## Impact map` row with a test or live "
              "check.", ""] + ["- %s %s" % (clip(lab, 200), "`%s`" % w if w else "") for lab, w, _t in irows[:80]]
        L += [""]
    dn = decisions_needed(c, paths)
    if dn:
        L += ["## Decision cards these paths may need (project.json `decisions`)", ""] + dn + [""]
    hr = hard_rules(c)
    if hr:
        L += ["## Hard rules (AGENTS.md)", ""] + hr + [""]
    if rules:
        L += ["## Path rules", ""]
        for name, globs, body in rules:
            L += ["### `%s` (%s)" % (name, ", ".join(globs))] + body + [""]
    ef = expert_facts(c, paths)
    if ef:
        L += ["## Repo facts for these paths (.claude/experts)", ""] + ef + [""]
    L += ["## Lessons for these paths", ""] + (lessons or ["(none)"]) + [""]
    if areas:
        L += ["## Review checklist sections the build will meet", "", ", ".join(areas), ""]
    L += ["## Paths", ""] + ["- `%s`" % p for p in paths] + [""]
    out = os.path.join(c.tdir, DPACK)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L).rstrip() + "\n")
    made = ""
    dfp = os.path.join(c.tdir, "design.md")
    if not os.path.isfile(dfp) or not (read(dfp) or "").strip():
        with open(dfp, "w", encoding="utf-8", newline="\n") as f:
            f.write(skeleton(c, acs, irows, rules, dn))
        made = " and design.md skeleton"
    print("Design pack: %s%s (%d paths, %d criteria, %d impact rows, %d rule files)" % (
        project.rel(out, c.here) or out, made, len(paths), len(set(re.findall(r"\bAC\d+\b", "\n".join(acs)))),
        len(irows), len(rules)))
    return 0


def skeleton(c, acs, irows, rules, dn):
    F = "<fill>"
    ac_ids = sorted(set(re.findall(r"\bAC(\d+)\b", "\n".join(acs))), key=int) or [""]
    L = ["# Design - %s" % c.tid, "",
         "<!-- Skeleton from review_pack.py --design: replace every %s (handoff_check fails while one is left). "
         "Facts: design-pack.md and context.md. -->" % F, "",
         "## How it will work", "", "%s (3-6 plain sentences, then a walk-through with the brief's example person; "
         "no file paths)" % F, "",
         "## What you are approving", "", "- %s (one line per document of the gate)" % F, "",
         "## Approach", "", "%s (at most 5 lines; a comparison table only for two or more real approaches)" % F, "",
         "## Decisions", "", "| D<n> | needed | who writes it | why |", "|---|---|---|---|"]
    L += ["| %s | %s | %s | %s |" % (ln[2:4], F, F, clip(ln[5:], 160)) for ln in dn] or ["| %s | | | |" % F]
    L += ["", "## Changes", "", "| # | file | change | criterion AC# | answer Q#/A# | decision relied on |",
          "|---|---|---|---|---|---|"]
    L += ["| %d | %s | %s | %s | | |" % (i, F, F, "AC" + n if n else F) for i, n in enumerate(ac_ids, 1)]
    L += ["", "## Data, permissions, labels, config keys", "", "%s (names only, never values; or \"none\")" % F, "",
          "## Contracts before and after", "", "%s (or \"none\")" % F, "",
          "## Who builds what", "", "%s (one line per developer; D7 hand-offs)" % F, "",
          "## Tests", "", F, "",
          "## Impact map", "", "| Area | What changes | How it is tested |", "|---|---|---|"]
    L += ["| %s %s | %s | %s |" % (clip(lab, 160), "(`%s`)" % w if w else "", F, F) for lab, w, _t in irows[:60]] \
        or ["| %s | %s | %s |" % (F, F, F)]
    L += ["", "## Planned files", "", "- %s (one bullet per file or glob, `- path - why`)" % F, "",
          "## Design patterns", "", F, "",
          "## Complexity count", "", "| added | count | why it is needed (criterion or number) |", "|---|---|---|"]
    L += ["| %s | %s | %s |" % (k, F, F) for k in ("new files", "new classes or modules", "new endpoints",
                                                 "new tables or columns", "new config keys", "new dependencies")]
    L += ["", "Rejected: %s (the bigger option and why it is not needed yet)" % F, "",
          "## Rules that apply", ""]
    L += ["- `%s`: %s (the traps that shape this design, or delete the line)" % (r[0], F) for r in rules] \
        or ["- %s" % F]
    L += ["", "## Risks and restart", "", F, ""]
    return "\n".join(L)


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(prog="review_pack.py", description="Review or design pack for one task.")
    ap.add_argument("id")
    ap.add_argument("--design", action="store_true", help="design pack and design.md skeleton instead")
    ap.add_argument("--full", action="store_true", help="pack every task file, even after a review")
    ap.add_argument("--base", help="diff against this commit (default HEAD)")
    ap.add_argument("--head", help="end of a commit range (default: the working tree)")
    ap.add_argument("--files", nargs="+", help="the task's files as paths or globs")
    ap.add_argument("--root", help="the code repo when it is not this repo (a product root)")
    a = ap.parse_args(argv)
    if a.head and not a.base:
        ap.error("--head needs --base")
    if not re.fullmatch(r"[\w.-]+", a.id) or re.fullmatch(r"\.+", a.id):
        print("review_pack: bad task id %r" % a.id, file=sys.stderr)
        return 1
    c = Ctx(a.id, a)
    if not os.path.isdir(c.tdir):
        print("review_pack: no task folder %s" % c.tdir, file=sys.stderr)
        return 1
    return cmd_design(c) if a.design else cmd_review(c)


if __name__ == "__main__":
    sys.exit(main())
