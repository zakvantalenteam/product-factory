#!/usr/bin/env python3
"""Impact map: what a change touches. The grep part of the context pack, run by `explorer` before the team is picked.

    impact.py TASK_ID TARGET... [--depth 1|2] [--print] [--config FILE] [--root DIR]

TARGET is a repo file path, `Class#method`, or a bare symbol (class or method name). Writes (or replaces) the
`## Impact map` section of <work_dir>/<TASK_ID>/context.md and leaves every other section as it is; --print shows it
instead. One table per target, `| kind | what | where |`, `where` is path:line:

  caller    word-boundary uses of the class or method over the `code` globs (comments and strings ignored in Java;
            the definition itself skipped). --depth 2 adds the callers of those callers.
  endpoint  Spring mapping annotations on the target or on a caller: HTTP method + path (class-level
            @RequestMapping prefix joined).
  client    the endpoint path (cut before the first path variable) found in the `clients` globs (JS, TS, HTML ...).
  n8n       workflow-export nodes (n8n.paths) that mention those endpoints or MCP tools; plus n8n.command output.
  tool      methods with the tools.marker annotation (@McpTool) in the target file or in a caller, and the line
            that lists the tool in tools.inventory.

Each kind is capped (default 25 rows, then "+N more"); the last line is `Counts:` (the lead uses it for risk).
Name based, no type resolution: a caller row is a lead to check, not proof ("name only" marks a hit in a file
that never mentions the class). Lines of secret or *Constants* files are never printed.

Config: `impact` in .claude/project.json (all optional; defaults in project.py): code, clients, skip (globs),
n8n {paths, command with {term}}, tools {marker, inventory}, mappings (endpoint annotations), cap, max_kb.
--root scans another repo (a product root) while the section goes to this repo's work folder. Read-only on the
scanned repo; standard library only; the file tree is walked once (git ls-files when it is a git repo) and every
file is read once. Exit: 0 done (also when nothing is found), 1 bad task id, 2 usage.
"""
import argparse
import bisect
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import project  # noqa: E402

FALLBACK = {
    "code": ["**/*.java", "**/*.ts", "**/*.tsx", "**/*.js"],
    "clients": ["**/*.js", "**/*.ts", "**/*.tsx", "**/*.html"],
    "n8n": {"paths": ["**/n8n*/**/*.json"], "command": ""},
    "tools": {"marker": "@McpTool", "inventory": ""},
    "skip": ["**/target/**", "**/node_modules/**", "**/dist/**", "**/*.min.js", ".claude/worktrees/**", "**/.git/**"],
    "mappings": ["RequestMapping", "GetMapping", "PostMapping", "PutMapping", "DeleteMapping", "PatchMapping"],
    "cap": 25,
    "max_kb": 1024,
}
KINDS = ["caller", "endpoint", "client", "n8n", "tool"]
SECRET_NAME = re.compile(r"^(application[\w.-]*\.properties|manifest\.ya?ml|xs-security[\w.-]*\.json|\.env.*)$", re.I)
NOT_A_TYPE = {"return", "new", "throw", "else", "case", "do", "assert", "yield", "await", "instanceof", "in", "of"}
NOT_A_METHOD = {"if", "for", "while", "switch", "catch", "synchronized", "try", "return", "new", "super", "this", "else",
                "do", "assert", "throw", "case", "instanceof", "function"}
HTTP = {"GetMapping": "GET", "PostMapping": "POST", "PutMapping": "PUT", "DeleteMapping": "DELETE",
        "PatchMapping": "PATCH"}


# --------------------------------------------------------------------------- small helpers

def matcher(patterns):
    """Compile globs once (project.match recompiles them on every call: too slow for thousands of files).
    `**/*.ext` and `*.ext` become a plain suffix test."""
    pats, suffixes = [], []
    for p in patterns or []:
        p = (p or "").strip()
        if not p:
            continue
        m = re.match(r"^(?:\*\*/)?\*(\.[\w]+)$", p)
        if m:
            suffixes.append(m.group(1).lower())
            continue
        anchored = "/" in p.strip("/")
        pats.append((anchored, project._glob_re(p.lstrip("/") if anchored else p)))
    suffixes = tuple(suffixes)

    def m(relpath):
        r = relpath.lower()
        if suffixes and r.endswith(suffixes):
            return True
        if not pats:
            return False
        name = r.rsplit("/", 1)[-1]
        return any(rx.match(r if anchored else name) for anchored, rx in pats)
    return m


def is_test(rel):
    r = "/" + rel.lower()
    return ("/test/" in r or "/tests/" in r or "/__tests__/" in r or ".spec." in r or ".test." in r
            or "/src/test" in r or "/e2e/" in r)


def esc(s):
    return re.sub(r"\s+", " ", str(s)).replace("|", "\\|").strip()


def snippet(s, n=110):
    s = re.sub(r"\s+", " ", s).strip().replace("`", "'")
    return s if len(s) <= n else s[:n - 3] + "..."


def is_java(rel):
    return rel.lower().endswith(".java")


def norm_join(*parts):
    segs = [p.strip("/") for p in parts if p and p.strip("/")]
    return "/" + "/".join(segs)


# --------------------------------------------------------------------------- Java structure

_TOK = re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|"""[\s\S]*?"""|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'')
_NONNL = re.compile(r"[^\n]")
_CALL = re.compile(r"(?<![\w$.@])([A-Za-z_$][\w$]*)\s*\(")
_TYPE = re.compile(r"(?<![\w$.])(?:(@interface|class|interface|enum)\s+([A-Za-z_$][\w$]*)|record\s+([A-Za-z_$][\w$]*)\s*[(<])")


class Method:
    __slots__ = ("rel", "cls", "name", "off", "line", "start", "end", "anns", "prefix")


class JType:
    __slots__ = ("name", "off", "start", "end", "anns", "prefix", "top")


class JavaInfo:
    """Comment- and string-blanked copies of a Java file (same offsets), its types and its method declarations."""

    def __init__(self, rel, text):
        def blank_all(m):
            return _NONNL.sub(" ", m.group(0))

        def blank_comments(m):
            s = m.group(0)
            return _NONNL.sub(" ", s) if s.startswith("/") else s
        self.rel, self.text = rel, text
        self.mcom = _TOK.sub(blank_comments, text)
        self.mall = _TOK.sub(blank_all, text)
        self.nl = [m.start() for m in re.finditer("\n", text)]
        self.pairs = {}
        stack = []
        for m in re.finditer(r"[{}]", self.mall):
            if m.group(0) == "{":
                stack.append(m.start())
            elif stack:
                self.pairs[stack.pop()] = m.start()
        self.types, self.methods = [], []
        self._parse()

    def line(self, off):
        return bisect.bisect_right(self.nl, off) + 1

    def _chunk_start(self, off):
        """Start of the declaration (annotations, modifiers, type) that ends at `off`."""
        depth, i, mall = 0, off - 1, self.mall
        while i >= 0:
            c = mall[i]
            if c == ")":
                depth += 1
            elif c == "(":
                depth -= 1
            elif depth <= 0 and c in ";{}":
                break
            i -= 1
        return i + 1

    def _parse(self):
        mall = self.mall
        for m in _TYPE.finditer(mall):
            name = m.group(2) or m.group(3)
            t = JType()
            t.name, t.off = name, m.start()
            t.start = self._chunk_start(m.start())
            ob = mall.find("{", m.end())
            t.end = self.pairs.get(ob, len(mall)) if ob >= 0 else len(mall)
            t.anns = annotations(self.mcom[t.start:m.start()])
            t.prefix = ""
            for an, args in t.anns:
                if an.rsplit(".", 1)[-1] == "RequestMapping":
                    ps = paths_of(args)
                    t.prefix = ps[0] if ps else ""
            t.top = True
            self.types.append(t)
        for t in self.types:
            t.top = not any(o is not t and o.off < t.off < o.end for o in self.types)
        for m in _CALL.finditer(mall):
            name = m.group(1)
            if name in NOT_A_METHOD:
                continue
            j = m.start() - 1
            while j >= 0 and mall[j] in " \t\r\n":
                j -= 1
            if j < 0:
                continue
            c = mall[j]
            if c.isalnum() or c in "_$":
                k = j
                while k >= 0 and (mall[k].isalnum() or mall[k] in "_$"):
                    k -= 1
                if mall[k + 1:j + 1] in NOT_A_TYPE:
                    continue
            elif c == ">":
                if j > 0 and mall[j - 1] == "-":
                    continue
            elif c != "]":
                continue
            p, depth, n = m.end(), 1, len(mall)
            while p < n and depth:
                if mall[p] == "(":
                    depth += 1
                elif mall[p] == ")":
                    depth -= 1
                p += 1
            q = p
            while q < n and mall[q] in " \t\r\n":
                q += 1
            if mall.startswith("throws", q):
                while q < n and mall[q] not in "{;":
                    q += 1
            if q >= n or mall[q] not in "{;":
                continue
            md = Method()
            md.name, md.off, md.line = name, m.start(1), self.line(m.start(1))
            md.start = self._chunk_start(m.start(1))
            md.end = self.pairs.get(q, p) if mall[q] == "{" else p
            md.anns = annotations(self.mcom[md.start:m.start(1)])
            md.rel, md.cls, md.prefix = self.rel, "", ""
            owner = None
            for t in self.types:
                if t.off < md.off < t.end and (owner is None or t.off > owner.off):
                    owner = t
            if owner:
                md.cls, md.prefix = owner.name, owner.prefix
            self.methods.append(md)

    def encl(self, off):
        best = None
        for md in self.methods:
            if md.start <= off <= md.end and (best is None or md.start > best.start):
                best = md
        return best

    def encl_type(self, off):
        best = None
        for t in self.types:
            if t.off <= off <= t.end and (best is None or t.off > best.off):
                best = t
        return best


def annotations(chunk):
    """[(name, args or None)] for the top-level annotations in a declaration chunk (strings and parens aware)."""
    out, i, n = [], 0, len(chunk)
    name_re = re.compile(r"@([\w.]+)")
    while True:
        i = chunk.find("@", i)
        if i < 0:
            break
        m = name_re.match(chunk, i)
        if not m:
            i += 1
            continue
        j, k, args = m.end(), m.end(), None
        while k < n and chunk[k] in " \t\r\n":
            k += 1
        if k < n and chunk[k] == "(":
            depth, q, s = 0, None, k
            while k < n:
                c = chunk[k]
                if q:
                    if c == "\\":
                        k += 1
                    elif c == q:
                        q = None
                elif c in "\"'":
                    q = c
                elif c == "(":
                    depth += 1
                elif c == ")":
                    depth -= 1
                    if depth == 0:
                        break
                k += 1
            args, j = chunk[s + 1:k], k + 1
        out.append((m.group(1), args))
        i = max(j, i + 1)
    return out


def paths_of(args):
    """Path strings of a mapping annotation's arguments ([""] when it has none)."""
    if args is None or not args.strip():
        return [""]
    m = re.search(r'\b(?:value|path)\s*=\s*(\{[^}]*\}|"(?:\\.|[^"\\])*"(?:\s*\+\s*[\w."]+)*|[\w.]+(?:\s*\+\s*[\w."]+)*)', args)
    seg = m.group(1) if m else None
    if seg is None:
        m = re.match(r'\s*(\{[^}]*\}|"(?:\\.|[^"\\])*"(?:\s*\+\s*[\w."]+)*|[A-Za-z_][\w.]*(?:\s*\+\s*[\w."]+)*)\s*(?:,|$)', args)
        seg = m.group(1) if m else None
    if seg is None:
        return [""]
    if seg.startswith("{"):
        strs = re.findall(r'"((?:\\.|[^"\\])*)"', seg)
        return strs or [""]
    out = ""
    for tok in re.findall(r'"(?:\\.|[^"\\])*"|[A-Za-z_][\w.]*', seg):
        out += tok[1:-1] if tok.startswith('"') else "{" + tok + "}"
    return [out]


def endpoints_of(md):
    """[(verb, full path)] of a method with a mapping annotation, class-level prefix joined."""
    out = []
    for an, args in md.anns:
        short = an.rsplit(".", 1)[-1]
        if short not in MAPPINGS:
            continue
        if short in HTTP:
            verbs = [HTTP[short]]
        elif short == "RequestMapping":
            mm = re.search(r"\bmethod\s*=\s*(\{[^}]*\}|[\w.]+)", args or "")
            verbs = re.findall(r"\b(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\b", mm.group(1)) if mm else []
            verbs = verbs or ["ANY"]
        else:
            verbs = [short.replace("Mapping", "").upper() or "ANY"]
        for p in paths_of(args):
            out.append(("|".join(verbs), norm_join(md.prefix, p)))
    return out


def tool_name(md, marker):
    for an, args in md.anns:
        if an.rsplit(".", 1)[-1] == marker:
            m = re.search(r'\bname\s*=\s*"([^"]+)"', args or "")
            return m.group(1) if m else md.name
    return None


MAPPINGS = set(FALLBACK["mappings"])
MAX_SEARCHED = 60   # endpoint paths searched in the client and n8n files per target (time bound)


# --------------------------------------------------------------------------- the repo

class Hit:
    __slots__ = ("rel", "off", "line", "weak", "depth", "text")


class Repo:
    def __init__(self, root, cfg, guard_root=None):
        self.root, self.cfg = root, cfg
        self.is_skip = matcher(cfg["skip"])
        self.is_code = matcher(cfg["code"])
        self.is_client = matcher(cfg["clients"])
        self.is_n8n = matcher(cfg["n8n"]["paths"])
        guard = (project.config(guard_root or root).get("guard") or {}).get("secret_files") or []
        self.is_secret_cfg = matcher(guard)
        self.files = self._list()
        self.by_lower = {r.lower(): r for r in self.files}
        self.text, self._lines, self._nl, self._java = {}, {}, {}, {}
        self.too_big = 0
        self.code, self.clients, self.n8n = [], [], []
        limit = int(cfg["max_kb"]) * 1024
        want = []
        for rel in self.files:
            code, client, n8n = self.is_code(rel), self.is_client(rel), self.is_n8n(rel)
            if code or client or n8n:
                want.append((rel, code, client, n8n))
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=8) as pool:   # opening files is the slow part on Windows
            texts = list(pool.map(lambda w: self._read(w[0], max(limit, 32 << 20) if w[3] else limit), want))
        for (rel, code, client, n8n), t in zip(want, texts):
            if t is None:
                continue
            self.text[rel] = t
            if code:
                self.code.append(rel)
            if client:
                self.clients.append(rel)
            if n8n:
                self.n8n.append(rel)
        self._n8n_nodes = {}

    def _list(self):
        files = None
        try:
            r = subprocess.run(["git", "-C", self.root, "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                               capture_output=True, timeout=60)
            if r.returncode == 0 and r.stdout:
                files = [p for p in r.stdout.decode("utf-8", "replace").split("\0") if p]
        except (OSError, subprocess.SubprocessError):
            files = None
        if files is None:
            prune = {".git"}
            for p in self.cfg["skip"]:
                m = re.match(r"^(?:\*\*/)?([\w.-]+)/\*\*$", p.strip())
                if m:
                    prune.add(m.group(1))
            files = []
            for d, dirs, names in os.walk(self.root):
                dirs[:] = [x for x in dirs if x not in prune]
                for n in names:
                    files.append(os.path.relpath(os.path.join(d, n), self.root).replace("\\", "/"))
        seen, out = set(), []
        for f in files:
            f = f.replace("\\", "/")
            if f not in seen and not self.is_skip(f):
                seen.add(f)
                out.append(f)
        return out

    def _read(self, rel, limit):
        try:
            p = os.path.join(self.root, rel)
            if os.path.getsize(p) > limit:
                self.too_big += 1
                return None
            with open(p, "rb") as f:
                b = f.read()
        except OSError:
            return None
        if b"\0" in b[:4096]:
            return None
        return b.decode("utf-8", "replace")

    def read_extra(self, rel):
        if rel not in self.text:
            t = self._read(rel, 1 << 30)
            if t is not None:
                self.text[rel] = t
        return self.text.get(rel)

    def java(self, rel):
        if rel not in self._java:
            self._java[rel] = JavaInfo(rel, self.text[rel])
        return self._java[rel]

    def lines(self, rel):
        if rel not in self._lines:
            self._lines[rel] = self.text[rel].split("\n")
        return self._lines[rel]

    def lineno(self, rel, off):
        if is_java(rel):
            return self.java(rel).line(off)
        if rel not in self._nl:
            self._nl[rel] = [m.start() for m in re.finditer("\n", self.text[rel])]
        return bisect.bisect_right(self._nl[rel], off) + 1

    def secret(self, rel):
        name = rel.rsplit("/", 1)[-1]
        return bool(SECRET_NAME.match(name)) or "constants" in name.lower() or self.is_secret_cfg(rel)

    def snip(self, rel, line):
        if self.secret(rel):
            return "(line hidden: secret or constants file)"
        try:
            return snippet(self.lines(rel)[line - 1])
        except IndexError:
            return ""

    # ---- finding uses

    def uses(self, regex_for, prefilter, defs=(), skip_files=(), skip_offsets=None, cls=None, java_decl_names=None):
        """Hits of a symbol over the code files, one per line. regex_for(is_def_file) gives the regex. Java code is
        only searched for Java definitions and JS/TS only for JS/TS ones (a REST call is the `client` kind)."""
        hits = {}
        fams = {"java" if is_java(d) else "js" for d in defs}
        fam = fams.pop() if len(fams) == 1 else None
        cls_re = re.compile(r"\b%s\b" % re.escape(cls)) if cls else None
        for rel in self.code:
            text = self.text[rel]
            if prefilter not in text or rel in skip_files or (fam and ("java" if is_java(rel) else "js") != fam):
                continue
            hay = self.java(rel).mall if is_java(rel) else text
            rx = regex_for(rel in defs)
            weak = bool(cls_re) and rel not in defs and not cls_re.search(text)
            skip_here = (skip_offsets or {}).get(rel, ())
            for m in rx.finditer(hay):
                off = m.start() if not m.groups() else m.start(m.lastindex or 0)
                if off in skip_here:
                    continue
                line = self.lineno(rel, off)
                if (rel, line) in hits:
                    continue
                ltext = self.lines(rel)[line - 1] if line - 1 < len(self.lines(rel)) else ""
                ls = ltext.lstrip()
                if is_java(rel):
                    if ls.startswith(("import ", "package ")):
                        continue
                elif ls.startswith(("//", "*", "/*")):
                    continue
                elif java_decl_names and rel in defs and JS_DECL.match(ltext) and java_decl_names.search(ltext):
                    continue
                h = Hit()
                h.rel, h.off, h.line, h.weak, h.depth, h.text = rel, off, line, weak, 1, ltext
                hits[(rel, line)] = h
        return list(hits.values())

    def encl_label(self, h):
        """(label, Method or None) of the code around a hit."""
        if is_java(h.rel):
            info = self.java(h.rel)
            md = info.encl(h.off)
            if md:
                if md.name == md.cls:
                    return md.cls, md
                return (md.cls + "#" + md.name if md.cls else md.name), md
            t = info.encl_type(h.off)
            return (t.name if t else h.rel.rsplit("/", 1)[-1]), None
        name = None
        ls = self.lines(h.rel)
        for i in range(h.line - 1, max(-1, h.line - 160), -1):
            m = JS_FUNC.match(ls[i])
            if m:
                name = next(g for g in m.groups() if g)
                if name in NOT_A_METHOD:
                    continue
                break
        stem = h.rel.rsplit("/", 1)[-1].split(".")[0]
        return (stem + "#" + name if name else stem), None

    # ---- n8n

    def n8n_nodes(self, rel):
        if rel not in self._n8n_nodes:
            nodes = []
            try:
                data = json.loads(self.text[rel])

                def walk(o):
                    if isinstance(o, dict):
                        if "name" in o and "type" in o and ("parameters" in o or "position" in o):
                            nodes.append((str(o["name"]), str(o["type"]), "\n".join(leaves(o))))
                        else:
                            for v in o.values():
                                walk(v)
                    elif isinstance(o, list):
                        for v in o:
                            walk(v)
                walk(data)
            except (ValueError, RecursionError):
                nodes = None
            self._n8n_nodes[rel] = nodes
        return self._n8n_nodes[rel]

    def n8n_hits(self, rx):
        """[(rel, line, node, type)] of workflow nodes that match; raw line hits when the file is not valid JSON."""
        out = []
        for rel in self.n8n:
            text = self.text[rel]
            first = rx.search(text)
            if not first:
                continue
            nodes = self.n8n_nodes(rel)
            if not nodes:
                out.append((rel, self.lineno(rel, first.start()), "", ""))
                continue
            for name, typ, blob in nodes:
                if not rx.search(blob):
                    continue
                line = None
                for form in (json.dumps(name, ensure_ascii=False), json.dumps(name)):
                    m = re.search(r'"name"\s*:\s*' + re.escape(form), text)
                    if m:
                        line = self.lineno(rel, m.start())
                        break
                out.append((rel, line or self.lineno(rel, first.start()), name, typ))
        return out


def leaves(o, out=None):
    """Every key and string value inside a JSON object, decoded (so \n is a real newline)."""
    out = [] if out is None else out
    if isinstance(o, dict):
        for k, v in o.items():
            out.append(str(k))
            leaves(v, out)
    elif isinstance(o, list):
        for v in o:
            leaves(v, out)
    elif isinstance(o, str):
        out.append(o)
    return out


JS_DECL = re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?(?:function\*?|class|interface|type|enum|const|let|var|"
                     r"abstract\s+class|public|private|protected|static|readonly|override|get|set)\b|^\s*\w+\s*\(.*\)\s*[:{]")
JS_FUNC = re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)|"
                     r"^\s*(?:(?:export|const|let|var)\s+)+([A-Za-z_$][\w$]*)\s*(?::[^=]*)?=\s*(?:async\s*)?(?:function|\([^)]*\)\s*(?::[^=]*)?=>|[\w$]+\s*=>)|"
                     r"^\s*(?:[\w$.]+\.)?([A-Za-z_$][\w$]*)\s*[:=]\s*(?:async\s*)?(?:function\b|\([^)]*\)\s*=>)|"
                     r"^\s*(?:async\s+)?([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*(?::\s*[\w<>\[\]|., ]+)?\s*\{\s*$")


# --------------------------------------------------------------------------- targets

class Target:
    def __init__(self, raw):
        self.raw = raw
        self.kind = ""           # file | class | member | symbol | none
        self.label = raw
        self.defs = []           # defining files
        self.syms = []           # class names (file/class kinds)
        self.member = ""
        self.cls = ""
        self.note = ""


def resolve(repo, raw):
    t = Target(raw)
    cand = [raw, os.path.join(repo.root, raw)]
    for c in cand:
        if os.path.isfile(c):
            a = os.path.abspath(c)
            r = rel_to(repo.root, a)
            if r is None:
                t.kind, t.note = "none", "file is outside the repo"
                return t
            r = repo.by_lower.get(r.lower(), r)
            repo.read_extra(r)
            if r not in repo.text:
                t.kind, t.note = "none", "file not readable"
                return t
            t.kind, t.defs, t.label = "file", [r], r
            if is_java(r):
                t.syms = [x.name for x in repo.java(r).types if x.top][:5] or [os.path.basename(r)[:-5]]
            else:
                t.syms = js_exports(repo.text[r])
            return t
    if os.path.isdir(raw) or os.path.isdir(os.path.join(repo.root, raw)):
        t.kind, t.note = "none", "a folder: give files, classes or symbols"
        return t
    if "#" in raw:
        cls, member = raw.split("#", 1)
        cls, member = cls.strip().split(".")[-1], member.strip().rstrip("()")
        t.kind, t.cls, t.member = "member", cls, member
        t.defs, t.cls = type_files(repo, cls)
        if not t.defs:
            t.kind, t.note = "none", "class %s not found in the repo" % cls
        elif t.cls != cls:
            t.note = "class %s resolved to %s" % (cls, t.cls)
        return t
    sym = raw.strip().rstrip("()")
    files, actual = type_files(repo, sym)
    if files:
        t.kind, t.syms, t.defs, t.label = "class", [actual], files, raw
        if actual != sym:
            t.note = "class %s resolved to %s" % (sym, actual)
        return t
    t.kind, t.member = "symbol", sym
    for rel in repo.code:
        if sym in repo.text[rel]:
            if is_java(rel):
                if any(m.name == sym for m in repo.java(rel).methods):
                    t.defs.append(rel)
            elif any(re.search(r"\b%s\b" % re.escape(sym), ln) and JS_DECL.match(ln) for ln in repo.lines(rel)):
                t.defs.append(rel)
    return t


def rel_to(root, a):
    r = os.path.relpath(a, root)
    return None if r.startswith("..") or os.path.isabs(r) else r.replace("\\", "/")


def type_files(repo, name):
    """(files that define the class `name`, the name as spelled there). A file named after the class wins over a
    file that only declares it; a case-insensitive file name match is the fallback."""
    pat = re.compile(r"(?<![\w$.])(?:class|interface|enum|record|@interface|type|abstract\s+class)\s+%s\b" % re.escape(name))
    by_stem, declared, low, loose = [], [], name.lower(), []
    for rel in repo.code:
        stem = rel.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        if stem == name:
            by_stem.append(rel)
        elif stem.lower() == low:
            loose.append(rel)
        elif name in repo.text[rel] and pat.search(repo.text[rel]):
            declared.append(rel)
    if by_stem or declared:
        return sorted(by_stem) + sorted(declared), name
    if loose:
        return sorted(loose), loose[0].rsplit("/", 1)[-1].rsplit(".", 1)[0]
    return [], name


def js_exports(text):
    names = re.findall(r"export\s+(?:default\s+)?(?:abstract\s+)?(?:async\s+)?(?:class|function\*?|const|let|interface|type|enum)"
                       r"\s+([A-Za-z_$][\w$]*)", text)
    seen = []
    for n in names:
        if n not in seen:
            seen.append(n)
    return seen[:8]


# --------------------------------------------------------------------------- the analysis

class Row:
    __slots__ = ("kind", "what", "where", "test", "order", "aux")

    def __init__(self, kind, what, where, test=False, order=(0,), aux=False):
        self.kind, self.what, self.where, self.test, self.order, self.aux = kind, what, where, test, order, aux


class Analysis:
    def __init__(self, repo, cfg, depth):
        self.repo, self.cfg, self.depth = repo, cfg, depth
        self.marker = (cfg["tools"]["marker"] or "").lstrip("@").strip()
        self.inventory = None
        inv = cfg["tools"].get("inventory") or ""
        if inv:
            p = inv if os.path.isabs(inv) else os.path.join(repo.root, inv)
            try:
                with open(p, encoding="utf-8", errors="replace") as f:
                    t = f.read()
            except OSError:
                t = None
            if t is not None:
                self.inventory = (inv.replace("\\", "/"), t.split("\n"))
        self.n8n_cmd = cfg["n8n"].get("command") or ""

    # ---- pieces

    def caller_hits(self, t):
        repo = self.repo
        hits = []
        if t.kind in ("file", "class"):
            defs = set(t.defs)
            for sym in t.syms:
                esc_s = re.escape(sym)
                rx = re.compile(r"(?<![\w$])%s(?![\w$])" % esc_s)
                hits += repo.uses(lambda d, rx=rx: rx, sym, defs=defs, skip_files=defs)
            if t.kind == "file" and not is_java(t.defs[0]):
                stem = os.path.basename(t.defs[0]).split(".")[0]
                rx = re.compile(r"""(?:from\s+|require\(\s*|import\(\s*|import\s+)['"][^'"\n]*[/.]%s(?:\.[jt]sx?)?['"]""" % re.escape(stem))
                hits += repo.uses(lambda d, rx=rx: rx, stem, defs=set(t.defs), skip_files=set(t.defs))
        elif t.kind == "member":
            hits = self.member_hits(t.member, t.cls, set(t.defs))
        elif t.kind == "symbol":
            sym = t.member
            rx = re.compile(r"(?<![\w$])%s(?![\w$])" % re.escape(sym))
            skip = self.decl_offsets(sym, t.defs)
            hits = repo.uses(lambda d: rx, sym, defs=set(t.defs), skip_offsets=skip,
                             java_decl_names=re.compile(r"\b%s\b" % re.escape(sym)))
        uniq = {}
        for h in hits:
            uniq.setdefault((h.rel, h.line), h)
        return list(uniq.values())

    def decl_offsets(self, sym, defs):
        out = {}
        for rel in defs:
            if is_java(rel):
                out[rel] = {m.off for m in self.repo.java(rel).methods if m.name == sym}
        return out

    def member_hits(self, member, cls, defs):
        e = re.escape(member)
        rx_def = re.compile(r"(?<![\w$])%s(?![\w$])" % e)
        rx_other = re.compile(r"(?:\.\s*|::\s*)%s(?![\w$])" % e)
        skip = self.decl_offsets(member, defs)
        return self.repo.uses(lambda d: rx_def if d else rx_other, member, defs=defs, skip_offsets=skip, cls=cls,
                              java_decl_names=re.compile(r"\b%s\b" % e))

    def expand(self, hits, seen_keys):
        """Depth 2: callers of the methods (or classes) that hold the depth-1 hits."""
        repo, out, seeds = self.repo, [], {}
        for h in hits:
            label, md = repo.encl_label(h)
            if is_java(h.rel):
                info = repo.java(h.rel)
                t = info.encl_type(h.off)
                cls = t.name if t else ""
                if md and md.name != cls:
                    seeds.setdefault(("m", h.rel, cls, md.name), (md.name, cls))
                elif cls:
                    seeds.setdefault(("c", h.rel, cls), (None, cls))
            elif "#" in label:
                name = label.split("#", 1)[1]
                if len(name) >= 6:
                    seeds.setdefault(("j", h.rel, name), (name, ""))
        for n, (key, (name, cls)) in enumerate(seeds.items()):
            if n >= 80:
                break
            defs = {key[1]}
            if name and cls:
                found = self.member_hits(name, cls, defs)
            elif name:
                rx = re.compile(r"(?<![\w$])%s\s*\(|\.\s*%s(?![\w$])" % (re.escape(name), re.escape(name)))
                found = repo.uses(lambda d: rx, name, defs=defs, cls=None)
                for f in found:
                    f.weak = True
            else:
                rx = re.compile(r"(?<![\w$])%s(?![\w$])" % re.escape(cls))
                found = repo.uses(lambda d: rx, cls, defs=defs, skip_files=defs)
            for f in found:
                if (f.rel, f.line) not in seen_keys:
                    f.depth = 2
                    seen_keys.add((f.rel, f.line))
                    out.append(f)
        return out

    def own_methods(self, t):
        if not t.defs:
            return []
        out = []
        for rel in t.defs:
            if not is_java(rel):
                continue
            for m in self.repo.java(rel).methods:
                if t.kind in ("file", "class") or (m.name == t.member and (not t.cls or m.cls == t.cls)):
                    out.append(m)
        return out

    def where(self, rel, line):
        return "%s:%d" % (rel, line)

    def tool_rows(self, md):
        name = tool_name(md, self.marker) if self.marker else None
        if not name:
            return []
        rows = [Row("tool", "`%s` (%s#%s)" % (name, md.cls, md.name), self.where(md.rel, md.line), is_test(md.rel),
                    (md.rel, md.line))]
        if self.inventory:
            inv, lines = self.inventory
            rx = re.compile(r"(?<![\w])%s(?![\w])" % re.escape(name))
            own = re.compile(r"^\s*(?:\||[-*#]+)\s*(?:\d+\.?\s*)?[`'\"]?%s[`'\"]?\s*(?:\||$)" % re.escape(name))
            head = re.compile(r"^#+\s+.*(?<![\w])%s(?![\w])" % re.escape(name))
            hit = next((i for i, ln in enumerate(lines) if own.match(ln)), None)
            if hit is None:
                hit = next((i for i, ln in enumerate(lines) if head.match(ln)), None)
            if hit is None:
                hit = next((i for i, ln in enumerate(lines) if rx.search(ln) and ln.lstrip().startswith("|")), None)
            if hit is None:
                hit = next((i for i, ln in enumerate(lines) if rx.search(ln)), None)
            if hit is None:
                rows.append(Row("tool", "`%s` is not listed in the tools inventory" % name, inv, False, (md.rel, md.line, 1), True))
            else:
                rows.append(Row("tool", "inventory: `%s`" % snippet(lines[hit]), "%s:%d" % (inv, hit + 1), False,
                                (md.rel, md.line, 1), True))
        return rows

    def client_terms(self, path):
        """(regex, shown term) for an endpoint path: cut before the first path variable."""
        cut = re.split(r"[{*]", path, 1)
        term = cut[0]
        has_var = len(cut) > 1
        core = term.strip("/")
        if len(core) < 4 or core.lower() in ("api", "rest", "v1", "v2"):
            return None
        rx = re.escape(term) if has_var else re.escape(term.rstrip("/") or term) + r"(?![\w\-]|/[\w{$])"
        return re.compile(rx), term

    def run_command(self, term):
        cmd = self.n8n_cmd
        if not cmd:
            return []
        q = '"%s"' % term.replace('"', "") if os.name == "nt" else shlex.quote(term)
        try:
            r = subprocess.run(cmd.replace("{term}", q), shell=True, cwd=self.repo.root, capture_output=True, timeout=20)
            out = r.stdout.decode("utf-8", "replace")
        except (OSError, subprocess.SubprocessError):
            return []
        return [ln for ln in out.splitlines() if ln.strip()][:self.cfg["cap"]]

    # ---- one target

    def analyse(self, raw):
        repo, t = self.repo, resolve(self.repo, raw)
        rows, endpoints, tools, notes = [], {}, {}, []
        if t.kind == "none":
            return t, rows, [t.note]
        if t.note:
            notes.append(t.note)

        hits = self.caller_hits(t)
        seen = {(h.rel, h.line) for h in hits}
        if self.depth >= 2 and hits:
            hits += self.expand(list(hits), seen)

        def add_methods(mds):
            for md in mds:
                for verb, path in endpoints_of(md):
                    endpoints.setdefault((md.rel, md.line, verb, path), md)
                if self.marker and tool_name(md, self.marker):
                    tools.setdefault((md.rel, md.line), md)

        add_methods(self.own_methods(t))
        groups = {}
        for h in sorted(hits, key=lambda h: (h.depth, h.rel, h.line)):
            label, md = repo.encl_label(h)
            if md is not None and not h.weak:
                add_methods([md])
            groups.setdefault((h.rel, label), []).append(h)
        for (rel, label), hs in groups.items():
            h = hs[0]
            more = " (+%d more line%s here)" % (len(hs) - 1, "" if len(hs) == 2 else "s") if len(hs) > 1 else ""
            flags = ("(d2) " if h.depth == 2 else "") + ("(name only) " if h.weak else "")
            rows.append(Row("caller", flags + "`%s`: %s%s" % (label, repo.snip(h.rel, h.line), more),
                            self.where(h.rel, h.line), is_test(h.rel), (is_test(h.rel), h.weak, h.depth, h.rel, h.line)))

        terms, skipped, searched = {}, [], 0
        own_keys = {(m.rel, m.line) for m in self.own_methods(t)}
        for (rel, line, verb, path), md in sorted(endpoints.items(), key=lambda kv: ((kv[0][0], kv[0][1]) not in own_keys, kv[0])):
            rows.append(Row("endpoint", "`%s %s` (%s#%s)" % (verb, path, md.cls, md.name), self.where(rel, line),
                            is_test(rel), (rel, line, path)))
            ct = self.client_terms(path)
            if not ct:
                skipped.append(path)
            elif ct[1] in terms:
                continue
            elif len(terms) >= MAX_SEARCHED:
                searched += 1
            else:
                terms[ct[1]] = (ct[0], path)
        if skipped:
            notes.append("client and n8n search skipped for %d endpoint(s) whose path is too general (e.g. `%s`)" %
                         (len(skipped), skipped[0]))
        if searched:
            notes.append("client and n8n search ran for the first %d endpoint paths only, %d more were not searched "
                         "(narrow the target)" % (MAX_SEARCHED, searched))
        for (rel, line), md in sorted(tools.items()):
            rows += self.tool_rows(md)

        # clients: endpoint path in the client files; fall back to shorter paths (apps often add a base path in code)
        found = {}
        for term, (rx, path) in terms.items():
            hit_any = False
            for cand_term, cand_rx, partial in self.term_variants(term, rx):
                for rel in repo.clients:
                    text = repo.text[rel]
                    if cand_term not in text:
                        continue
                    for m in cand_rx.finditer(text):
                        line = repo.lineno(rel, m.start())
                        found.setdefault((rel, line), set()).add(cand_term + partial)
                        hit_any = True
                if hit_any:
                    break
        for (rel, line), ts in sorted(found.items()):
            ts = {x for x in ts if not any(y != x and y.startswith(x.split(" (")[0]) and len(y) > len(x) for y in ts)}
            rows.append(Row("client", "`%s`: %s" % (", ".join(sorted(ts)), repo.snip(rel, line)), self.where(rel, line),
                            is_test(rel), (is_test(rel), rel, line)))

        # n8n: endpoints and tool names
        n8n_terms = [(term, rx) for term, (rx, _p) in terms.items()]
        for (rel, line), md in sorted(tools.items()):
            nm = tool_name(md, self.marker)
            n8n_terms.append((nm, re.compile(r"(?<![\w])%s(?![\w])" % re.escape(nm))))
        nodes = {}
        for term, rx in n8n_terms:
            if repo.n8n:
                got = repo.n8n_hits(rx)
                last = term.rstrip("/").rsplit("/", 1)[-1]
                if not got and "/" in term and not term.endswith("/") and len(last) >= 8 and re.search(r"[-_]", last):
                    # workflows often get the base URL from the app and keep only the last segment
                    got, term = repo.n8n_hits(re.compile(re.escape("/" + last) + r"(?![\w])")), "/" + last + " (segment only)"
                for rel, line, name, typ in got:
                    nodes.setdefault((rel, line, name, typ), set()).add(term)
            for ln in self.run_command(term):
                rows.append(Row("n8n", "`%s` (command, term `%s`)" % (snippet(ln), term),
                                "n8n.command", False, ("~", ln)))
        for (rel, line, name, typ), ts in sorted(nodes.items()):
            what = "node `%s` (%s): %s" % (name, typ.rsplit(".", 1)[-1], ", ".join("`%s`" % x for x in sorted(ts))) if name \
                else "workflow file: %s" % ", ".join("`%s`" % x for x in sorted(ts))
            rows.append(Row("n8n", what, self.where(rel, line), False, (rel, line)))

        seen_rows, uniq = set(), []
        for r in rows:
            k = (r.kind, r.what, r.where)
            if k not in seen_rows:
                seen_rows.add(k)
                uniq.append(r)
        return t, uniq, notes

    def term_variants(self, term, rx):
        """The path itself, then shorter forms: parent paths (a page often carries only the base URL) and paths
        without their first segment (a base path added in code). Callers stop at the first form with hits."""
        yield term, rx, ""
        segs = [s for s in term.split("/") if s]
        trailing = term.endswith("/")
        for k in range(len(segs) - 1, 3, -1):
            rest = "/" + "/".join(segs[:k]) + "/"
            yield rest, re.compile(re.escape(rest)), " (parent path)"
        for i in range(1, len(segs) - 1):
            rest = "/" + "/".join(segs[i:]) + ("/" if trailing else "")
            if len(rest.strip("/")) >= 6:
                yield rest, re.compile(re.escape(rest)), " (partial path)"


# --------------------------------------------------------------------------- output

def render(analysis, targets, repo_info):
    cap = int(analysis.cfg["cap"])
    out = ["## Impact map", ""]
    out.append("Generated by `impact.py` (depth %d): %s. Name-based search, so a row is a lead to check, not proof." %
               (analysis.depth, repo_info))
    totals = {k: 0 for k in KINDS}
    total_tests = 0
    for raw, t, rows, notes in targets:
        out.append("")
        head = "### `%s`" % raw
        if t.kind == "file":
            head += " (file%s)" % ((": " + ", ".join(t.syms)) if t.syms else "")
        elif t.kind in ("class", "member") and t.defs:
            head += " (%s)" % t.defs[0]
        out += [head, ""]
        by = {k: [r for r in rows if r.kind == k] for k in KINDS}
        counts = {k: len(by[k]) for k in KINDS}
        counts["tool"] = len([r for r in by["tool"] if not r.aux])
        tests = len([r for r in by["caller"] if r.test])
        if not rows:
            out.append("no uses found" + (" (%s)" % "; ".join(notes) if notes else ""))
            if t.kind in ("member", "symbol", "class") and not t.defs and not notes:
                out[-1] += " (no definition found either)"
            continue
        out += ["| kind | what | where |", "|---|---|---|"]
        for k in KINDS:
            rs = sorted(by[k], key=lambda r: r.order)
            for r in rs[:cap]:
                out.append("| %s | %s | %s |" % (k, esc(r.what), esc(r.where)))
            if len(rs) > cap:
                out.append("| %s | +%d more (narrow the target or raise `impact.cap`) | |" % (k, len(rs) - cap))
        if not by["caller"]:
            out.append("")
            out.append("no callers found" + ("" if t.defs else " (no definition found either)"))
        for n in notes:
            out += ["", "Note: " + n] if n == notes[0] else ["Note: " + n]
        out.append("")
        out.append("Counts (`%s`): %s" % (raw, count_text(counts, tests)))
        for k in KINDS:
            totals[k] += counts[k]
        total_tests += tests
    out += ["", "Counts: " + count_text(totals, total_tests), ""]
    return "\n".join(out)


def count_text(c, tests):
    return ", ".join("%s %d%s" % (k, c[k], " (%d in tests)" % tests if k == "caller" and tests else "") for k in KINDS)


def write_section(path, section, newline):
    old = None
    try:
        with open(path, "rb") as f:
            old = f.read().decode("utf-8")
    except FileNotFoundError:
        pass
    nl = "\r\n" if (old is not None and old.count("\r\n") > old.count("\n") / 2) else ("\r\n" if (old is None and newline == "crlf") else "\n")
    body = section.replace("\n", nl)
    if old is None:
        new = "# Context pack" + nl + nl + body
    else:
        lines = old.split("\n")
        fence, start, end = False, None, None
        for i, ln in enumerate(lines):
            s = ln.rstrip("\r")
            if s.lstrip().startswith(("```", "~~~")):
                fence = not fence
            if fence:
                continue
            if start is None and re.match(r"^##\s+Impact map\s*$", s):
                start = i
            elif start is not None and re.match(r"^##\s", s):
                end = i
                break
        if start is None:
            new = old.rstrip("\r\n") + nl + nl + body
        else:
            before = "".join(x + "\n" for x in lines[:start])
            after = "\n".join(lines[end:]) if end is not None else ""
            new = before + body + (nl + after if after else "")
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".impact-", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(new.encode("utf-8"))
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def load_cfg(root, config_file):
    base = project.DEFAULTS.get("impact", FALLBACK)
    user = {}
    if config_file:
        try:
            with open(config_file, encoding="utf-8") as f:
                data = json.load(f)
            user = data.get("impact", data) if isinstance(data, dict) else {}
        except (OSError, ValueError) as e:
            sys.exit("impact: cannot read --config %s: %s" % (config_file, e))
    else:
        user = project.config(root).get("impact") or {}
    return project._merge(base, user)


def main():
    ap = argparse.ArgumentParser(description="Map what a change touches (callers, endpoints, clients, n8n nodes, MCP tools).")
    ap.add_argument("task_id")
    ap.add_argument("targets", nargs="+", help="repo file path, Class#method, or a bare symbol")
    ap.add_argument("--depth", type=int, choices=(1, 2), default=1)
    ap.add_argument("--print", dest="show", action="store_true", help="print the section instead of writing it")
    ap.add_argument("--config", default="", help="JSON file with the `impact` settings (instead of .claude/project.json)")
    ap.add_argument("--root", default="", help="repo to scan (default: this repo)")
    a = ap.parse_args()

    if not re.match(r"^[\w][\w.\-]*$", a.task_id) or a.task_id in (".", ".."):
        print("impact: bad task id %r" % a.task_id, file=sys.stderr)
        return 1
    here = project.repo_root()
    root = os.path.abspath(a.root) if a.root else here
    if not os.path.isdir(root):
        print("impact: root %s is not a folder" % root, file=sys.stderr)
        return 2
    cfg_root = root if os.path.isfile(os.path.join(root, ".claude", "project.json")) else here
    cfg = load_cfg(cfg_root, a.config)
    global MAPPINGS
    MAPPINGS = set(cfg.get("mappings") or FALLBACK["mappings"])

    t0 = time.time()
    repo = Repo(root, cfg, cfg_root)
    an = Analysis(repo, cfg, a.depth)
    results = []
    for raw in a.targets:
        t, rows, notes = an.analyse(raw)
        results.append((raw, t, rows, notes))
    info = "%d target%s, %d files scanned (%d code, %d client, %d n8n) in %.1fs%s" % (
        len(a.targets), "" if len(a.targets) == 1 else "s", len(repo.text), len(repo.code), len(repo.clients),
        len(repo.n8n), time.time() - t0,
        "; %d file(s) over %d KB skipped" % (repo.too_big, int(cfg["max_kb"])) if repo.too_big else "")
    section = render(an, results, info)
    if a.show:
        print(section)
        return 0
    path = os.path.join(project.work_dir(here), a.task_id, "context.md")
    write_section(path, section, project.config(here).get("newline", "lf"))
    last = [ln for ln in section.split("\n") if ln.startswith("Counts: ")][-1]
    print("impact: wrote ## Impact map to %s (%s)\n%s" % (path, info, last))
    return 0


if __name__ == "__main__":
    sys.exit(main())
