"""Offline HTML copy of a factory document: python scripts/md_to_html.py <file.md> [more.md ...]

Writes <file>.html next to it: no CDN, light/dark, impact words (BLOCKER, HIGH, MEDIUM, LOW, MUST, SHOULD,
PASS, FAIL) shown as badges. Supports headings, paragraphs, nested lists, tables, code, bold, italic, links.
"""
import html
import os
import re
import sys

CSS = """
:root{--bg:#fff;--text:#1c1917;--muted:#78716c;--line:#e7e5e4;--code:#f5f5f4;--accent:#2563eb;
--bad:#b91c1c;--bad-bg:#fef2f2;--warn:#b45309;--warn-bg:#fffbeb;--mid:#1d4ed8;--mid-bg:#eff6ff;
--ok:#15803d;--ok-bg:#f0fdf4}
@media (prefers-color-scheme:dark){:root{--bg:#0c0a09;--text:#f5f5f4;--muted:#a8a29e;--line:#292524;
--code:#1c1917;--accent:#60a5fa;--bad:#f87171;--bad-bg:#450a0a;--warn:#fbbf24;--warn-bg:#422006;
--mid:#93c5fd;--mid-bg:#172554;--ok:#4ade80;--ok-bg:#052e16}}
body{margin:0;background:var(--bg);color:var(--text);font:14px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:860px;margin:0 auto;padding:24px 16px}h1{font-size:22px;font-weight:500}
h2{font-size:16px;font-weight:500;margin-top:28px;padding-bottom:4px;border-bottom:1px solid var(--line)}
h3{font-size:14px;font-weight:500}a{color:var(--accent)}code{background:var(--code);padding:1px 4px;border-radius:4px}
pre{background:var(--code);padding:10px;border-radius:6px;overflow:auto}table{border-collapse:collapse;width:100%;
display:block;overflow-x:auto}th,td{border:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top}
th{font-weight:500}li{margin:3px 0}.b{font-size:11px;font-weight:500;padding:1px 6px;border-radius:4px}
.BLOCKER,.FAIL,.MUST{color:var(--bad);background:var(--bad-bg)}.HIGH{color:var(--warn);background:var(--warn-bg)}
.MEDIUM,.SHOULD{color:var(--mid);background:var(--mid-bg)}.LOW{color:var(--muted);background:var(--code)}
.PASS{color:var(--ok);background:var(--ok-bg)}
"""
BADGES = ("BLOCKER", "HIGH", "MEDIUM", "LOW", "MUST", "SHOULD", "PASS", "FAIL")


def inline(s):
    codes = []
    s = re.sub(r"`([^`]+)`", lambda m: codes.append(m.group(1)) or "\x00%d\x00" % (len(codes) - 1), s)
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(%s)\*\*" % "|".join(BADGES), r'<span class="b \1">\1</span>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)\*(?!\w)", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', s)
    return re.sub(r"\x00(\d+)\x00", lambda m: "<code>%s</code>" % html.escape(codes[int(m.group(1))]), s)


def convert(md):
    out, lines, i = [], md.replace("\r\n", "\n").split("\n"), 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            out.append("<pre><code>%s</code></pre>" % html.escape("\n".join(lines[i + 1:j])))
            i = j + 1
            continue
        m = re.match(r"(#{1,4})\s+(.*)", ln)
        if m:
            n = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (n, inline(m.group(2)), n))
            i += 1
            continue
        if ln.strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            cells = lambda r: [c.strip() for c in r.strip().strip("|").split("|")]
            rows = ["<tr>%s</tr>" % "".join("<th>%s</th>" % inline(c) for c in cells(ln))]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in cells(lines[i])))
                i += 1
            out.append("<table>%s</table>" % "".join(rows))
            continue
        if re.match(r"\s*([-*]|\d+\.)\s+", ln):
            stack = []
            while i < len(lines) and (re.match(r"\s*([-*]|\d+\.)\s+", lines[i]) or
                                      (lines[i].startswith("  ") and lines[i].strip() and stack)):
                m = re.match(r"(\s*)([-*]|\d+\.)\s+(.*)", lines[i])
                if not m:
                    out[-1] = out[-1][:-5] + "<br>" + inline(lines[i].strip()) + "</li>"
                    i += 1
                    continue
                depth, tag = len(m.group(1)) // 2, "ol" if m.group(2)[0].isdigit() else "ul"
                while len(stack) > depth + 1 or (stack and len(stack) == depth + 1 and stack[-1] != tag):
                    out.append("</%s>" % stack.pop())
                while len(stack) < depth + 1:
                    stack.append(tag)
                    out.append("<%s>" % tag)
                out.append("<li>%s</li>" % inline(m.group(3)))
                i += 1
            while stack:
                out.append("</%s>" % stack.pop())
            continue
        if re.match(r"^\s*(---|\*\*\*)\s*$", ln):
            out.append("<hr>")
        elif ln.strip():
            para = [ln.strip()]
            while i + 1 < len(lines) and lines[i + 1].strip() and not re.match(
                    r"\s*(#|```|\||[-*]\s|\d+\.\s)", lines[i + 1]):
                i += 1
                para.append(lines[i].strip())
            out.append("<p>%s</p>" % inline(" ".join(para)))
        i += 1
    return "\n".join(out)


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    for src in argv:
        with open(src, encoding="utf-8") as f:
            md = f.read()
        title = re.search(r"^#\s+(.+)$", md, re.M)
        page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" '
                'content="width=device-width,initial-scale=1"><title>%s</title><style>%s</style></head>'
                '<body><main>%s</main></body></html>') % (
            html.escape(title.group(1) if title else os.path.basename(src)), CSS, convert(md))
        dst = os.path.splitext(src)[0] + ".html"
        with open(dst, "w", encoding="utf-8") as f:
            f.write(page)
        print("wrote " + dst)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
