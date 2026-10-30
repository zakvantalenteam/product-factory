#!/usr/bin/env python3
"""Compact symbol index with line ranges for big files (TS/TSX/JS, Java, UI5 XML, CSS).

    codemap.py FILE [--grep PAT] [--max N] [--depth D] [--min-lines N]

    L120-L188  renderLearningPlan(data, opts)

JS/TS function decls, `X.y = function`, `name: function`, `name(...) {` methods, arrow consts,
      classes, `X.extend("...")`, big object literals; TS also interface / type / enum / namespace.
Java  types, methods (nested types indented), endpoints as `METHOD /full/path  name(params)`.
XML   elements with an id (plus root view and fragment/view includes) with a few key attributes.
CSS   section comments and top-level selectors / at-rules (sections only when the file is huge).

FILE is resolved from the cwd, then from the repo root. --grep is a case-insensitive regex on the
displayed text. Output is capped (default 300 lines): the cap lowers the nesting depth first and
says how to narrow it. Exit: 0 ok, 1 file missing / no match, 2 usage.
"""
import argparse
import bisect
import re
import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import project  # noqa: E402
ROOT = Path(project.repo_root())
ID = r"[A-Za-z_$][\w$]*"
PATH = rf"{ID}(?:\s*\.\s*{ID}|\s*\[[^\]\n]*\])*"
KEYWORDS = {"if", "for", "while", "switch", "catch", "function", "return", "else", "with", "do", "typeof",
            "new", "throw", "await", "yield", "synchronized", "try", "finally", "super", "this"}
REGEX_PREV_WORDS = {"return", "typeof", "case", "do", "else", "in", "of", "void", "delete", "throw", "new",
                    "yield", "await", "instanceof"}


# --------------------------------------------------------------------------- masking

STR_DQ = re.compile(r'"(?:\\[\s\S]|[^"\\\n])*"')
STR_SQ = re.compile(r"'(?:\\[\s\S]|[^'\\\n])*'")
TPL_STEP = re.compile(r"\\[\s\S]|`|\$\{")
EXPR_STEP = re.compile(r"[{}`\"'/]")
JS_TOKEN = re.compile(r"//|/\*|[\"'`/]")
JAVA_TOKEN = re.compile(r'//|/\*|"""|["\']')
CSS_TOKEN = re.compile(r"/\*|[\"']")
BLANK = re.compile(r"[^\n]")


def _blank(s):
    return BLANK.sub(" ", s)


def _scan_template(src, i):
    j, n = i + 1, len(src)
    while j < n:
        m = TPL_STEP.search(src, j)
        if not m:
            return n
        t = m.group(0)
        if t == "`":
            return m.end()
        if t == "${":
            j = _scan_expr(src, m.end())
        else:
            j = m.end()
    return n


def _scan_expr(src, j):
    depth, n = 1, len(src)
    while j < n:
        m = EXPR_STEP.search(src, j)
        if not m:
            return n
        c, k = m.group(0), m.start()
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return k + 1
        elif c == "`":
            j = _scan_template(src, k)
            continue
        elif c in "\"'":
            sm = (STR_DQ if c == '"' else STR_SQ).match(src, k)
            j = sm.end() if sm else k + 1
            continue
        elif c == "/" and src[k + 1:k + 2] == "/":
            e = src.find("\n", k)
            j = len(src) if e < 0 else e
            continue
        elif c == "/" and src[k + 1:k + 2] == "*":
            e = src.find("*/", k + 2)
            j = len(src) if e < 0 else e + 2
            continue
        j = k + 1
    return n


def _regex_allowed(src, i):
    k = i - 1
    while k >= 0 and src[k] in " \t\r\n":
        k -= 1
    if k < 0:
        return True
    c = src[k]
    if c in "(,=:[!&|?{};+-*%<>~^":
        return True
    if c.isalnum() or c in "_$":
        e = k
        while k >= 0 and (src[k].isalnum() or src[k] in "_$"):
            k -= 1
        return src[k + 1:e + 1] in REGEX_PREV_WORDS
    return False


def _scan_regex(src, i):
    j, n, in_class = i + 1, len(src), False
    while j < n:
        c = src[j]
        if c == "\n":
            return -1
        if c == "\\":
            j += 2
            continue
        if c == "[":
            in_class = True
        elif c == "]":
            in_class = False
        elif c == "/" and not in_class:
            j += 1
            while j < n and src[j].isalpha():
                j += 1
            return j
        j += 1
    return -1


def mask(src, lang):
    """Blank comments, strings, templates and regex literals (keeping newlines and offsets)."""
    tok = {"js": JS_TOKEN, "ts": JS_TOKEN, "java": JAVA_TOKEN, "css": CSS_TOKEN}[lang]
    pieces, last, pos, n = [], 0, 0, len(src)
    while pos < n:
        m = tok.search(src, pos)
        if not m:
            break
        i, t = m.start(), m.group(0)
        j = -1
        if t == "//":
            e = src.find("\n", i)
            j = n if e < 0 else e
        elif t == "/*":
            e = src.find("*/", i + 2)
            j = n if e < 0 else e + 2
        elif t == '"""':
            e = src.find('"""', i + 3)
            j = n if e < 0 else e + 3
        elif t in "\"'":
            mm = (STR_DQ if t == '"' else STR_SQ).match(src, i)
            if mm:
                j = mm.end()
        elif t == "`":
            j = _scan_template(src, i)
        elif t == "/" and _regex_allowed(src, i) and not (lang == "ts" and src[i - 1:i] == "<"):  # `</tag>` in TSX
            j = _scan_regex(src, i)
        if j > i:
            pieces.append(src[last:i])
            pieces.append(_blank(src[i:j]))
            last = j
            pos = j
        else:
            pos = i + 1
    pieces.append(src[last:])
    return "".join(pieces)


def match_table(masked):
    """open index -> close index for () [] {} on masked text."""
    table, stack = {}, []
    pairs = {")": "(", "]": "[", "}": "{"}
    for m in re.finditer(r"[()\[\]{}]", masked):
        c, i = m.group(0), m.start()
        if c in "([{":
            stack.append((c, i))
        else:
            want = pairs[c]
            while stack and stack[-1][0] != want:
                stack.pop()
            if stack:
                table[stack.pop()[1]] = i
    return table


class Src:
    def __init__(self, text, lang):
        self.text = text
        self.lines = text.count("\n") + 1
        self.masked = mask(text, lang)
        self.match = match_table(self.masked)
        self.starts = [0] + [m.end() for m in re.finditer(r"\n", text)]

    def line(self, pos):
        return bisect.bisect_right(self.starts, pos)

    def skip_ws(self, i):
        m = self.masked
        n = len(m)
        while i < n and m[i] in " \t\r\n":
            i += 1
        return i

    def collapse(self, a, b, cap=90):
        s = re.sub(r"\s+", " ", self.text[a:b]).strip()
        return s if len(s) <= cap else s[:cap - 3] + "..."


# --------------------------------------------------------------------------- JS

P_CLASS = re.compile(rf"\s*(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+({ID})(?:\s+extends\s+({PATH}))?")
P_FUNC = re.compile(rf"\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*({ID})\s*\(")
P_EXTEND = re.compile(rf"\s*(?:return\s+|(?:var|let|const)\s+{ID}\s*=\s*|{PATH}\s*=\s*)?({PATH})\.extend\s*\(")
P_ASSIGN_FN = re.compile(rf"\s*(?:(?:export\s+)?(?:const|let|var)\s+)?({PATH})\s*=\s*(?:async\s+)?function\b\s*\*?\s*(?:{ID})?\s*\(")
P_ARROW = re.compile(rf"\s*(?:(?:export\s+)?(?:const|let|var)\s+)?({PATH})\s*=\s*(?:async\s+)?(?:(\()|({ID})\s*=>)")
P_PROP_FN = re.compile(rf"\s*({ID}|\d+)\s*:\s*(?:async\s+)?function\b\s*\*?\s*(?:{ID})?\s*\(")
P_PROP_ARROW = re.compile(rf"\s*({ID}|\d+)\s*:\s*(?:async\s+)?(?:(\()|({ID})\s*=>)")
P_METHOD = re.compile(rf"\s*(?:static\s+)?(?:async\s+)?(?:get\s+|set\s+)?\*?\s*({ID})\s*\(")
P_OBJ = re.compile(rf"\s*(?:(?:const|let|var)\s+)?({PATH})\s*=\s*\{{\s*$")
# TS only (parse_js(s, ts=True)): tried before the JS patterns, so JS files never reach them
P_TS_TYPE = re.compile(rf"\s*(?:export\s+)?(?:default\s+)?(?:declare\s+)?(?:const\s+)?(interface|enum|namespace)\s+({ID})")
P_TS_ALIAS = re.compile(rf"\s*(?:export\s+)?(?:declare\s+)?type\s+({ID})\s*(?:<[^\n]*?>)?\s*=")
P_TS_CLASS = re.compile(rf"\s*(?:export\s+)?(?:default\s+)?(?:declare\s+)?(?:abstract\s+)?class\s+({ID})(?:\s*<[^{{\n]*?>)?(?:\s+extends\s+({PATH}))?")
P_TS_FUNC = re.compile(rf"\s*(?:export\s+)?(?:default\s+)?(?:declare\s+)?(?:async\s+)?function\s*\*?\s*({ID})\s*(?:<[^(\n]*>)?\s*\(")
P_TS_ARROW = re.compile(rf"\s*(?:export\s+)?(?:const|let|var)\s+({ID})\s*(?::\s*(?:[^=\n]|=>)+?)?\s*=\s*(?:async\s+)?(?:<[^(\n]*>\s*)?(?:(\()|({ID})\s*=>)")
P_TS_METHOD = re.compile(rf"\s*(?:(?:public|private|protected|static|override|async)\s+)*(?:get\s+|set\s+)?\*?\s*({ID})\s*(?:<[^(\n]*>)?\s*\(")
P_TS_OBJ = re.compile(rf"\s*(?:export\s+)?(?:const|let|var)\s+({ID})\s*:\s*[^=\n]+=\s*\{{\s*$")


def _body_end(s, q, arrow=False):
    """Absolute end offset of a function body whose params closed just before q."""
    i = s.skip_ws(q)
    if arrow and s.masked.startswith("=>", i):
        i = s.skip_ws(i + 2)
    if i < len(s.masked) and s.masked[i] == "{":
        return s.match.get(i)
    e = s.masked.find("\n", i)
    return len(s.masked) if e < 0 else e


def _ts_sig_end(s, q):
    """Offset of the `{`, `=>` or `;` ending a TS signature whose params closed just before q (skips `: Type`)."""
    m, n = s.masked, len(s.masked)
    i = s.skip_ws(q)
    if i >= n or m[i] != ":":
        return i
    d = 0
    while i + 1 < n:
        i += 1
        c = m[i]
        if c == "=" and m.startswith("=>", i):
            if d == 0:
                return i
            i += 1
        elif c == "<":
            d += 1
        elif c == ">":
            d = max(d - 1, 0)
        elif c in "([":
            i = s.match.get(i, i)
        elif c == "{" and d == 0:
            e = s.match.get(i)
            if e is None or not m.startswith("=>", s.skip_ws(e + 1)):
                return i
            i = e
        elif c == ";" and d == 0:
            return i
        elif c == "\n" and d == 0:
            k = i - 1
            while k > q and m[k] in " \t\r\n":
                k -= 1
            nx = s.skip_ws(i)
            if m[k] not in ":|&,<" and (nx >= n or m[nx] not in "{|&"):
                return i
    return n - 1


def _ts_decl(s, a, line, ln):
    """(text, end, kind) for a TS-only declaration on this line, else (None, None, "fn")."""
    ml = s.masked
    m = P_TS_TYPE.match(line)
    if m:
        ob = ml.find("{", a + m.end())
        return f"{m.group(1)} {m.group(2)}", s.match.get(ob) if ob >= 0 else None, "class"
    m = P_TS_CLASS.match(line)
    if m:
        ob = ml.find("{", a + m.end())
        return f"class {m.group(1)}" + (f" extends {m.group(2)}" if m.group(2) else ""), s.match.get(ob) if ob >= 0 else None, "class"
    m = P_TS_ALIAS.match(line)
    if m:
        ob = ml.find("{", a + m.end(), a + len(line))
        if ob >= 0 and s.match.get(ob) is not None:
            return f"type {m.group(1)}", s.match[ob], "class"
        k = ln  # no braces: run on over continuation lines that start with | or &
        while k < s.lines and ml[s.starts[k]:s.starts[k] + 80].lstrip(" \t")[:1] in ("|", "&"):
            k += 1
        return f"type {m.group(1)}", (s.starts[k] if k < len(s.starts) else len(ml)) - 1, "class"
    m = P_TS_FUNC.match(line)
    if m:
        p = a + m.end() - 1
        c = s.match.get(p)
        if c is not None:
            return f"{m.group(1)}({s.collapse(p + 1, c)})", _body_end(s, _ts_sig_end(s, c + 1)), "fn"
    m = P_TS_ARROW.match(line)
    if m:
        if m.group(2):
            p = a + m.end() - 1
            c = s.match.get(p)
            r = _ts_sig_end(s, c + 1) if c is not None else -1
            if r >= 0 and ml.startswith("=>", r):
                return f"{m.group(1)}({s.collapse(p + 1, c)}) =>", _body_end(s, r, arrow=True), "fn"
        else:
            return f"{m.group(1)}({m.group(3)}) =>", _body_end(s, a + m.end()), "fn"
    m = P_TS_METHOD.match(line)
    if m and m.group(1) not in KEYWORDS:
        p = a + m.end() - 1
        c = s.match.get(p)
        if c is not None and "function" not in ml[p:c] and "=>" not in ml[p:c]:
            r = _ts_sig_end(s, c + 1)
            if r < len(ml) and ml[r] == "{":
                return f"{m.group(1)}({s.collapse(p + 1, c)})", s.match.get(r), "fn"
    m = P_TS_OBJ.match(line)
    if m:
        e = s.match.get(a + line.rindex("{"))
        if e is not None and s.line(e) - ln >= 15:
            return f"{m.group(1)} = {{...}}", e, "obj"
    return None, None, "fn"


def parse_js(s, ts=False):
    out, bad = [], 0
    ml = s.masked
    for ln in range(1, s.lines + 1):
        a = s.starts[ln - 1]
        b = s.starts[ln] if ln < len(s.starts) else len(ml)
        line = ml[a:b]
        if not line.strip():
            continue
        text, end, kind = _ts_decl(s, a, line, ln) if ts else (None, None, "fn")
        m = P_CLASS.match(line) if text is None else None
        if m:
            ob = ml.find("{", a + m.end())
            end = s.match.get(ob) if ob >= 0 else None
            text = f"class {m.group(1)}" + (f" extends {m.group(2)}" if m.group(2) else "")
            kind = "class"
        if text is None:
            m = P_FUNC.match(line)
            if m:
                p = a + m.end() - 1
                c = s.match.get(p)
                if c is not None:
                    end = _body_end(s, c + 1)
                    text = f"{m.group(1)}({s.collapse(p + 1, c)})"
        if text is None:
            m = P_EXTEND.match(line)
            if m:
                q = re.search(r"""\.extend\s*\(\s*["']([^"']+)["']""", s.text[a:b])
                p = a + m.end() - 1
                c = s.match.get(p)
                if c is not None:
                    end = c
                    text = f"{m.group(1)}.extend({q.group(1) if q else '...'})"
                    kind = "class"
        if text is None:
            m = P_ASSIGN_FN.match(line)
            if m:
                p = a + m.end() - 1
                c = s.match.get(p)
                if c is not None:
                    end = _body_end(s, c + 1)
                    text = f"{re.sub(r'\s+', '', m.group(1))}({s.collapse(p + 1, c)})"
        if text is None:
            m = P_ARROW.match(line)
            if m:
                if m.group(2):
                    p = a + m.end() - 1
                    c = s.match.get(p)
                    j = s.skip_ws(c + 1) if c is not None else -1
                    if c is not None and ml.startswith("=>", j):
                        end = _body_end(s, c + 1, arrow=True)
                        text = f"{re.sub(r'\s+', '', m.group(1))}({s.collapse(p + 1, c)}) =>"
                else:
                    end = _body_end(s, a + m.end(), arrow=False)
                    text = f"{re.sub(r'\s+', '', m.group(1))}({m.group(3)}) =>"
        if text is None:
            m = P_PROP_FN.match(line)
            if m:
                p = a + m.end() - 1
                c = s.match.get(p)
                if c is not None:
                    end = _body_end(s, c + 1)
                    text = f"{m.group(1)}({s.collapse(p + 1, c)})"
        if text is None:
            m = P_PROP_ARROW.match(line)
            if m:
                if m.group(2):
                    p = a + m.end() - 1
                    c = s.match.get(p)
                    j = s.skip_ws(c + 1) if c is not None else -1
                    if c is not None and ml.startswith("=>", j):
                        end = _body_end(s, c + 1, arrow=True)
                        text = f"{m.group(1)}({s.collapse(p + 1, c)}) =>"
                else:
                    end = _body_end(s, a + m.end())
                    text = f"{m.group(1)}({m.group(3)}) =>"
        if text is None:
            m = P_METHOD.match(line)
            if m and m.group(1) not in KEYWORDS:
                p = a + m.end() - 1
                c = s.match.get(p)
                if c is not None:
                    j = s.skip_ws(c + 1)
                    if j < len(ml) and ml[j] == "{" and "function" not in ml[p:c] and "=>" not in ml[p:c]:
                        end = s.match.get(j)
                        text = f"{m.group(1)}({s.collapse(p + 1, c)})"
        if text is None:
            m = P_OBJ.match(line)
            if m:
                ob = a + line.rindex("{")
                e = s.match.get(ob)
                if e is not None and s.line(e) - ln >= 15:
                    end = e
                    text = f"{re.sub(r'\s+', '', m.group(1))} = {{...}}"
                    kind = "obj"
        if text is None:
            continue
        if end is None:
            bad += 1
            end_line = ln
        else:
            end_line = max(s.line(end), ln)
        out.append({"start": ln, "end": end_line, "text": text, "kind": kind,
                    "a": a + (len(line) - len(line.lstrip())), "b": end if end is not None else a})
    return out, bad


# --------------------------------------------------------------------------- Java

TYPE_RE = re.compile(r"(?<![\w$])(class|interface|enum|record|@interface)\s+([A-Za-z_$][\w$]*)")
MAPPINGS = {"GetMapping": "GET", "PostMapping": "POST", "PutMapping": "PUT", "DeleteMapping": "DELETE",
            "PatchMapping": "PATCH", "RequestMapping": None}
SHOW_ANN = {"Scheduled", "Async", "Transactional", "PreAuthorize", "McpTool", "CheckPermission", "EventListener",
            "Bean", "ExceptionHandler", "ResponseBody"}
CLASS_ANN = {"RestController", "Controller", "Service", "Component", "Repository", "Entity", "Configuration",
             "ControllerAdvice", "RestControllerAdvice"}


def _ann_path(args):
    m = re.search(r'(?:value|path)\s*=\s*\{?\s*"([^"]*)"', args) or re.search(r'"([^"]*)"', args)
    return m.group(1) if m else ""


def _ann_http(name, args):
    if MAPPINGS.get(name):
        return MAPPINGS[name]
    m = re.search(r"RequestMethod\.(\w+)", args)
    return m.group(1) if m else "ANY"


def _join_path(a, b):
    if not a:
        return b or "/"
    return "/" + "/".join(x.strip("/") for x in (a, b) if x.strip("/"))


def _java_annotations(s, seg_a, seg_b):
    """[(name, args_text, start, end)] and a copy of the masked segment with annotations blanked."""
    head = list(s.masked[seg_a:seg_b])
    anns, i = [], seg_a
    while True:
        m = re.compile(r"@([A-Za-z_$][\w$.]*)").search(s.masked, i, seg_b)
        if not m:
            break
        name = m.group(1).split(".")[-1]
        end = m.end()
        j = end
        while j < seg_b and s.masked[j] in " \t\r\n":
            j += 1
        args = ""
        if j < seg_b and s.masked[j] == "(" and j in s.match:
            c = s.match[j]
            args = s.text[j + 1:c]
            end = c + 1
        if name != "interface":
            anns.append((name, args, m.start(), end))
            for k in range(m.start(), end):
                if head[k - seg_a] != "\n":
                    head[k - seg_a] = " "
        i = end
    return anns, "".join(head)


def _java_members(s, a, b, out, depth, prefix, kind):
    i, seg = a, a
    m = s.masked
    seen_semi = kind != "enum"
    while i < b:
        c = m[i]
        if c in "([":
            i = s.match.get(i, i) + 1
            continue
        if c == "{" or c == ";":
            seg_end = i
            body_end = s.match.get(i) if c == "{" else None
            if c == ";" and not seen_semi:
                seen_semi = True
                seg = i + 1
                i += 1
                continue
            if seen_semi:
                _java_member(s, seg, seg_end, body_end, c, out, depth, prefix)
            i = (body_end + 1) if c == "{" and body_end is not None else i + 1
            seg = i
            continue
        i += 1


def _java_member(s, seg_a, seg_b, body_end, term, out, depth, prefix):
    anns, head = _java_annotations(s, seg_a, seg_b)
    if not head.strip():
        return
    first = seg_a + (len(head) - len(head.lstrip()))
    if anns:
        first = min(first, anns[0][2])
    tm = TYPE_RE.search(head)
    pre_paren = head.split("(")[0]
    if tm and "=" not in pre_paren and term == "{":
        kind, name = tm.group(1), tm.group(2)
        cprefix, tags = "", []
        for an, args, _, _ in anns:
            if an == "RequestMapping":
                cprefix = _ann_path(args)
                tags.append(cprefix or "/")
            elif an in CLASS_ANN:
                tags.append("@" + an)
        end_line = s.line(body_end) if body_end is not None else s.line(seg_b)
        ext = re.search(r"\bextends\s+([\w$.<>, ]+?)(?=\s+implements|\s*$)", head[tm.end():])
        label = f"{kind} {name}" + (f" extends {ext.group(1).strip()}" if ext and kind == "class" else "")
        if tags:
            label += "  " + " ".join(tags)
        out.append({"start": s.line(first), "end": end_line, "text": label, "kind": "class", "a": first, "b": body_end or seg_b})
        if body_end is not None:
            _java_members(s, seg_b + 1, body_end, out, depth + 1, cprefix, kind)
        return
    p = head.find("(")
    if p <= 0 or "=" in head[:p]:
        return
    nm = re.search(r"([A-Za-z_$][\w$]*)\s*$", head[:p])
    if not nm or nm.group(1) in KEYWORDS:
        return
    before = head[:nm.start()]
    if re.search(r"\b(new|return|throw|else)\b|->", before):
        return
    abs_p = seg_a + p
    close = s.match.get(abs_p)
    if close is None:
        return
    params = re.sub(r"@[\w.]+(?:\([^)]*\))?\s*", "", s.text[abs_p + 1:close])
    params = re.sub(r"\s+", " ", params).strip()
    if len(params) > 90:
        params = params[:87] + "..."
    label = f"{nm.group(1)}({params})"
    http = None
    extra = []
    for an, args, _, _ in anns:
        if an in MAPPINGS:
            http = (_ann_http(an, args), _ann_path(args))
        elif an in SHOW_ANN:
            sv = re.search(r'"([^"]{1,40})"', args)
            extra.append("@" + an + (f" {sv.group(1)}" if sv else ""))
    if http:
        label = f"{http[0]} {_join_path(prefix, http[1])}  {label}"
    if extra:
        label += "  " + " ".join(extra)
    end_line = s.line(body_end) if body_end is not None else s.line(seg_b)
    out.append({"start": s.line(first), "end": end_line, "text": label,
                "kind": "endpoint" if http else "method", "a": first, "b": body_end or seg_b})


def parse_java(s):
    out = []
    _java_members(s, 0, len(s.masked), out, 0, "", "file")
    return out, 0


# --------------------------------------------------------------------------- XML (UI5 views/fragments)

TAG_RE = re.compile(r"<(/?)([\w:.\-]+)((?:\s+[\w:.\-]+\s*=\s*(?:\"[^\"]*\"|'[^']*'))*)\s*(/?)>")
ATTR_RE = re.compile(r"([\w:.\-]+)\s*=\s*(\"[^\"]*\"|'[^']*')")
XML_MASK = re.compile(r"<!--[\s\S]*?-->|<!\[CDATA\[[\s\S]*?\]\]>")
EXTRA_ATTRS = ("controllerName", "fragmentName", "viewName", "title", "text", "press", "items", "value", "icon")
VOID = {"br", "hr", "img", "input", "meta", "link"}


def parse_xml(text, is_html=False):
    masked = XML_MASK.sub(lambda m: _blank(m.group(0)), text)
    starts = [0] + [m.end() for m in re.finditer(r"\n", text)]
    ln = lambda pos: bisect.bisect_right(starts, pos)  # noqa: E731
    stack, items, first = [], [], True
    for m in TAG_RE.finditer(masked):
        closing, name, attrs, selfc = m.group(1), m.group(2), m.group(3), m.group(4)
        if closing:
            for k in range(len(stack) - 1, -1, -1):
                if stack[k]["name"] == name:
                    for e in stack[k:]:
                        e["end"] = ln(m.start())
                    del stack[k:]
                    break
            continue
        d = dict(ATTR_RE.findall(attrs))
        d = {k: v[1:-1] for k, v in d.items()}
        node = {"name": name, "start": ln(m.start()), "end": ln(m.end() - 1), "attrs": d}
        interesting = ("id" in d) or first or "fragmentName" in d or "viewName" in d
        first = False
        if interesting:
            items.append(node)
        if not selfc and not (is_html and name.lower() in VOID) and not name.startswith("?"):
            stack.append(node)
    out = []
    bounds = []
    for e in items:
        while bounds and bounds[-1] < e["start"]:
            bounds.pop()
        d = e["attrs"]
        label = e["name"] + (f" id={d['id']}" if "id" in d else "")
        n = 0
        for k in EXTRA_ATTRS:
            if k in d and n < 2:
                v = d[k]
                label += f" {k}={v[:40]}" + ("..." if len(v) > 40 else "")
                n += 1
        out.append({"start": e["start"], "end": e["end"] if not is_html else e["start"], "text": label,
                    "kind": "el", "depth_hint": len(bounds)})
        bounds.append(e["end"])
    return out


# --------------------------------------------------------------------------- CSS

def parse_css(text):
    masked = mask(text, "css")
    s = Src.__new__(Src)
    s.text, s.masked = text, masked
    s.starts = [0] + [m.end() for m in re.finditer(r"\n", text)]
    s.lines = len(s.starts)
    s.match = match_table(masked)
    out = []
    # section comments (top level only)
    events = [(m.start(), m.group(0)) for m in re.finditer(r"[{}]", masked)]
    cum, d, idx = [], 0, []
    for pos, ch in events:
        d += 1 if ch == "{" else -1
        idx.append(pos)
        cum.append(d)
    for c in re.finditer(r"/\*([\s\S]*?)\*/", text):
        k = bisect.bisect_left(idx, c.start())
        depth = cum[k - 1] if k > 0 else 0
        if depth != 0:
            continue
        body = c.group(1)
        parts = [re.sub(r"^[\s*=\-_#~]+|[\s*=\-_#~]+$", "", p) for p in body.split("\n")]
        parts = [p for p in parts if p]
        if not parts:
            continue
        title = parts[0]
        decorated = bool(re.search(r"[=\-_#~*]{4,}", body))
        if not decorated and (len(parts) > 3 or len(title) > 60 or title.endswith(".") or ". " in title):
            continue
        line_start = text.rfind("\n", 0, c.start()) + 1
        if text[line_start:c.start()].strip():
            continue
        out.append({"start": s.line(c.start()), "end": s.line(c.start()), "text": "/* " + title[:80] + " */",
                    "kind": "section"})
    # top-level rules / at-rules
    i, seg, n = 0, 0, len(masked)
    while i < n:
        ch = masked[i]
        if ch == ";":
            sel = masked[seg:i].strip()
            if sel.startswith("@"):
                out.append({"start": s.line(seg + len(masked[seg:i]) - len(masked[seg:i].lstrip())),
                            "end": s.line(i), "text": re.sub(r"\s+", " ", sel)[:90], "kind": "at"})
            seg = i + 1
        elif ch == "{":
            close = s.match.get(i)
            sel = re.sub(r"\s+", " ", masked[seg:i]).strip()
            first = seg + (len(masked[seg:i]) - len(masked[seg:i].lstrip()))
            if sel:
                is_at = sel.startswith("@")
                out.append({"start": s.line(first), "end": s.line(close) if close else s.line(i),
                            "text": sel if len(sel) <= 90 else sel[:87] + "...", "kind": "at" if is_at else "rule"})
                if is_at and close and re.match(r"@(media|supports|layer|container)\b", sel):
                    j, sseg = i + 1, i + 1
                    while j < close:
                        if masked[j] == "{":
                            cl = s.match.get(j)
                            sub = re.sub(r"\s+", " ", masked[sseg:j]).strip()
                            if sub and cl:
                                f2 = sseg + (len(masked[sseg:j]) - len(masked[sseg:j].lstrip()))
                                out.append({"start": s.line(f2), "end": s.line(cl),
                                            "text": sub if len(sub) <= 90 else sub[:87] + "...",
                                            "kind": "rule", "depth_hint": 1})
                            j = (cl or j) + 1
                            sseg = j
                            continue
                        elif masked[j] == ";":
                            sseg = j + 1
                        j += 1
            i = (close or i) + 1
            seg = i
            continue
        i += 1
    out.sort(key=lambda e: (e["start"], 0 if e["kind"] == "section" else 1))
    return out


# --------------------------------------------------------------------------- output

def assign_depth(entries):
    """Nesting depth by range containment (JS/Java) or by depth_hint (XML/CSS).

    depth  = number of enclosing entries (drives indentation).
    fdepth = number of enclosing function-like entries; classes and object literals do not count,
             so a controller's methods stay at fdepth 0 and only inner callbacks are dropped first.
    """
    stack = []
    for e in sorted(entries, key=lambda x: (x["start"], -x["end"])):
        if "depth_hint" in e:
            e["depth"] = e["fdepth"] = e["depth_hint"]
            continue
        while stack and stack[-1]["end"] < e["start"]:
            stack.pop()
        e["depth"] = len(stack)
        e["fdepth"] = sum(1 for x in stack if x["kind"] not in ("class", "obj"))
        if e["end"] > e["start"]:
            stack.append(e)
    return entries


def render(entries, indent=True):
    entries = sorted(entries, key=lambda x: (x["start"], x["end"] * -1 if x["end"] != x["start"] else 0))
    rng = [f"L{e['start']}" if e["end"] == e["start"] else f"L{e['start']}-L{e['end']}" for e in entries]
    w = max((len(r) for r in rng), default=0)
    return [f"{r:<{w}}  {'  ' * e['depth'] if indent else ''}{e['text']}" for r, e in zip(rng, entries)]


def resolve(arg):
    p = Path(arg)
    for cand in (p, ROOT / arg):
        if cand.is_file():
            return cand.resolve()
    return None


def main():
    ap = argparse.ArgumentParser(
        description="Compact symbol index with line ranges for big TS / JS / Java / UI5 XML / CSS files.",
        epilog="Example: codemap.py src/main/resources/static/js/AISearch/AISearch.widgets.js --grep render")
    ap.add_argument("file", metavar="FILE")
    ap.add_argument("--grep", metavar="PAT", help="case-insensitive regex on the displayed text")
    ap.add_argument("--max", type=int, default=300, metavar="N", help="output line cap (default 300)")
    ap.add_argument("--depth", type=int, default=None, metavar="D", help="max nesting depth shown (0 = top level)")
    ap.add_argument("--min-lines", type=int, default=0, metavar="N", help="only symbols spanning at least N lines")
    a = ap.parse_args()
    path = resolve(a.file)
    if path is None:
        print(f"file not found: {a.file}", file=sys.stderr)
        return 1
    raw = path.read_bytes()
    text = raw.decode("utf-8", "replace")
    if text.startswith("\ufeff"):
        text = text[1:]
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    ext = path.suffix.lower()
    warn = ""
    if ext in (".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".mts", ".cts"):
        ts = ext in (".ts", ".tsx", ".mts", ".cts")
        s = Src(text, "ts" if ts else "js")
        entries, bad = parse_js(s, ts)
        lang, nlines = "ts" if ts else "js", s.lines
        if bad:
            warn = f" ({bad} with unmatched braces)"
    elif ext == ".java":
        s = Src(text, "java")
        entries, _ = parse_java(s)
        lang, nlines = "java", s.lines
    elif ext in (".xml", ".html", ".htm"):
        entries = parse_xml(text, is_html=ext != ".xml")
        lang, nlines = "xml", text.count("\n") + 1
    elif ext == ".css":
        entries = parse_css(text)
        lang, nlines = "css", text.count("\n") + 1
    else:
        print(f"unsupported file type '{ext}' (supported: .ts .tsx .js .jsx .java .xml .html .css)", file=sys.stderr)
        return 2
    total = len(entries)
    assign_depth(entries)
    if a.min_lines:
        entries = [e for e in entries if e["end"] - e["start"] + 1 >= a.min_lines]
    grep = None
    if a.grep:
        try:
            grep = re.compile(a.grep, re.I)
        except re.error as e:
            print(f"bad regex: {e}", file=sys.stderr)
            return 2
        entries = [e for e in entries if grep.search(e["text"])]
    try:
        shown_path = path.relative_to(ROOT)
    except ValueError:
        shown_path = path
    head = f"# {str(shown_path).replace(chr(92), '/')}: {nlines} lines, {total} symbols [{lang}]{warn}"
    if grep and not entries:
        print(head)
        print(f"no symbol matches /{a.grep}/")
        return 1
    note = ""
    depth_cap = a.depth
    if depth_cap is not None:
        entries = [e for e in entries if e["fdepth"] <= depth_cap]
    elif len(entries) > a.max:
        top = max((e["fdepth"] for e in entries), default=0)
        d = top
        while d > 0 and sum(1 for e in entries if e["fdepth"] <= d) > a.max:
            d -= 1
        if d < top:
            hidden = sum(1 for e in entries if e["fdepth"] > d)
            entries = [e for e in entries if e["fdepth"] <= d]
            note = f"depth limited to {d} to fit {a.max} lines ({hidden} nested symbols hidden; --depth N or --grep PAT)"
    if lang == "css" and len(entries) > a.max and not grep:
        secs = [e for e in entries if e["kind"] == "section"]
        if secs:
            allr = sorted(entries, key=lambda x: x["start"])
            for k, sec in enumerate(secs):
                nxt = secs[k + 1]["start"] if k + 1 < len(secs) else 10 ** 9
                cnt = sum(1 for e in allr if e["kind"] in ("rule", "at") and sec["start"] < e["start"] < nxt and e["depth"] == 0)
                sec["text"] += f"  [{cnt} rules]"
            entries = secs
            note = f"{total} entries: showing sections only; use --grep PAT to list selectors"
    lines = render(entries, indent=not grep)
    print(head)
    if len(lines) > a.max:
        print("\n".join(lines[:a.max]))
        print(f"... {len(lines) - a.max} more; narrow with --grep PAT, --depth N, --min-lines N or raise --max")
    else:
        print("\n".join(lines))
        if note:
            print(f"({note})")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
