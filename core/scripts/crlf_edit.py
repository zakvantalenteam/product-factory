#!/usr/bin/env python3
"""Exact text replacement / append that keeps a file's line endings and encoding byte-for-byte.

    crlf_edit.py FILE --old S --new S [--count N] [--dry-run]
    crlf_edit.py FILE --old-file A --new-file B [--count N] [--chomp] [--dry-run]
    crlf_edit.py FILE --append-file F [--once] [--dry-run]

* Newlines in OLD/NEW match and write as the file's own EOL (CRLF or LF); in a mixed file each
  match uses the EOL it actually matched. Nothing outside the matches is touched.
* Fails (exit 1, nothing written) unless OLD occurs exactly N times (default 1).
* Use -e/--escapes to read \\n, \\t, \\\\ in --old/--new. --chomp drops one final newline from the
  --old-file/--new-file/--append-file contents (editors add one).
* Prints CRLF/LF counts before and after. File must be UTF-8 (a BOM is preserved).
Exit: 0 ok, 1 problem, 2 usage.
"""
import argparse
import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import project  # noqa: E402
ROOT = Path(project.repo_root())


def die(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def eol_counts(text):
    crlf = text.count("\r\n")
    lf = text.count("\n") - crlf
    cr = text.count("\r") - crlf
    return crlf, lf, cr


def dominant(text):
    crlf, lf, _ = eol_counts(text)
    return "\r\n" if crlf > lf else "\n"


def fmt(c):
    s = f"CRLF {c[0]}, LF {c[1]}"
    return s + (f", lone-CR {c[2]}" if c[2] else "")


def unescape(s):
    return re.sub(r"\\([nt\\])", lambda m: {"n": "\n", "t": "\t", "\\": "\\"}[m.group(1)], s)


def norm_nl(s):
    return s.replace("\r\n", "\n").replace("\r", "\n")


def read_text_file(p, chomp):
    path = Path(p)
    if not path.is_file():
        die(f"file not found: {p}")
    try:
        t = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        die(f"{p} is not valid UTF-8")
    if t.startswith("﻿"):
        t = t[1:]
    if chomp:
        if t.endswith("\r\n"):
            t = t[:-2]
        elif t.endswith("\n"):
            t = t[:-1]
    return t


def write_bytes(path, data):
    tmp = path.with_name(path.name + ".crlf_edit.tmp")
    try:
        tmp.write_bytes(data)
        os.replace(tmp, path)
    except OSError:
        path.write_bytes(data)
        try:
            tmp.unlink()
        except OSError:
            pass


def local_eol(text, m_start, m_end, default):
    seg = text[m_start:m_end]
    k = seg.find("\n")
    if k >= 0:
        return "\r\n" if k > 0 and seg[k - 1] == "\r" else "\n"
    k = text.find("\n", m_end)
    if k >= 0:
        return "\r\n" if k > 0 and text[k - 1] == "\r" else "\n"
    return default


def do_replace(text, old, new, count):
    default = dominant(text)
    old_n, new_n = norm_nl(old), norm_nl(new)
    pattern = re.compile(r"\r?\n".join(re.escape(p) for p in old_n.split("\n")))
    matches = list(pattern.finditer(text))
    if len(matches) != count:
        msg = [f"REFUSED: found {len(matches)} match(es), expected {count}. File unchanged."]
        if not matches:
            first = old_n.split("\n")[0].strip()
            if first:
                lines = [i + 1 for i, ln in enumerate(text.splitlines()) if first in ln][:5]
                if lines:
                    msg.append(f"first line of OLD appears on line(s) {lines} - the rest differs "
                               f"(indentation, trailing spaces or wording).")
            loose = re.compile(r"\s+".join(re.escape(p) for p in old_n.split())) if old_n.split() else None
            if loose is not None and loose.search(text):
                msg.append("OLD matches when whitespace is ignored: check tabs vs spaces and line breaks.")
        else:
            lines = [text.count("\n", 0, m.start()) + 1 for m in matches[:10]]
            msg.append(f"matches start on line(s) {lines}; pass --count {len(matches)} to replace all, "
                       f"or make OLD longer to be unique.")
        die("\n".join(msg))
    out, last, removed_crlf, added_crlf = [], 0, 0, 0
    lines_hit = []
    for m in matches:
        eol = local_eol(text, m.start(), m.end(), default)
        rep = new_n.replace("\n", eol)
        out.append(text[last:m.start()])
        out.append(rep)
        removed_crlf += m.group(0).count("\r\n")
        added_crlf += rep.count("\r\n")
        lines_hit.append(text.count("\n", 0, m.start()) + 1)
        last = m.end()
    out.append(text[last:])
    return "".join(out), len(matches), lines_hit, removed_crlf, added_crlf


def main():
    ap = argparse.ArgumentParser(
        description="Exact replacement / append that preserves the file's EOL (CRLF/LF) and UTF-8 encoding.",
        epilog="Example: crlf_edit.py src/main/resources/messages.properties --old-file a.txt --new-file b.txt --chomp")
    ap.add_argument("file", metavar="FILE")
    ap.add_argument("--old", metavar="S")
    ap.add_argument("--new", metavar="S")
    ap.add_argument("--old-file", metavar="A")
    ap.add_argument("--new-file", metavar="B")
    ap.add_argument("--append-file", metavar="F", help="append F's content at the end of FILE")
    ap.add_argument("--count", type=int, default=1, metavar="N", help="required number of matches (default 1)")
    ap.add_argument("--once", action="store_true", help="with --append-file: skip if the text is already present")
    ap.add_argument("--chomp", action="store_true", help="drop one final newline from file-based inputs")
    ap.add_argument("-e", "--escapes", action="store_true", help=r"interpret \n \t \\ in --old/--new")
    ap.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    a = ap.parse_args()

    replace_mode = a.old is not None or a.old_file is not None
    if a.append_file and replace_mode:
        ap.error("--append-file cannot be combined with --old/--old-file")
    if not a.append_file and not replace_mode:
        ap.error("give --old/--new, --old-file/--new-file, or --append-file")
    if replace_mode:
        if (a.old is not None) == (a.old_file is not None):
            ap.error("give exactly one of --old or --old-file")
        if (a.new is not None) == (a.new_file is not None):
            ap.error("give exactly one of --new or --new-file (use --new '' to delete)")
        if (a.old is not None) != (a.new is not None):
            ap.error("--old pairs with --new, and --old-file with --new-file")
    if a.count < 1:
        ap.error("--count must be >= 1")

    path = Path(a.file)
    if not path.is_file():
        path = ROOT / a.file
    if not path.is_file():
        die(f"file not found: {a.file}")
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        die(f"{path.name} is not valid UTF-8 ({e}); refusing to touch it")
    before = eol_counts(text)

    if replace_mode:
        if a.old_file is not None:
            old = read_text_file(a.old_file, a.chomp)
            new = read_text_file(a.new_file, a.chomp)
        else:
            old, new = a.old, a.new
            if a.escapes:
                old, new = unescape(old), unescape(new)
        if old == "":
            die("--old is empty", 2)
        result, n, lines_hit, rem, add = do_replace(text, old, new, a.count)
        action = f"replaced {n} occurrence(s) at line(s) {lines_hit[:10]}" + (" ..." if len(lines_hit) > 10 else "")
        exp_crlf = before[0] - rem + add
    else:
        add_text = norm_nl(read_text_file(a.append_file, a.chomp))
        if add_text == "":
            die("append file is empty; nothing to do")
        eol = dominant(text)
        payload = add_text.replace("\n", eol)
        if a.once and payload in text:
            print(f"{path.name}: already contains the text; skipped (--once)")
            return 0
        sep = eol if text and not text.endswith("\n") else ""
        result = text + sep + payload
        action = f"appended {payload.count(chr(10)) + (0 if payload.endswith(chr(10)) else 1)} line(s)" + \
                 (" (added a line break before them)" if sep else "")
        exp_crlf = before[0] + payload.count("\r\n") + (1 if sep == "\r\n" else 0)

    after = eol_counts(result)
    problems = []
    if after[0] != exp_crlf:
        problems.append(f"CRLF count {after[0]} != expected {exp_crlf}")
    if before[1] == 0 and before[0] > 0 and after[1] != 0:
        problems.append("a pure-CRLF file would gain bare LF")
    if before[0] == 0 and before[1] > 0 and after[0] != 0:
        problems.append("a pure-LF file would gain CRLF")
    if before[2] == 0 and after[2] != 0:
        problems.append("stray CR introduced")
    if problems:
        die("REFUSED (EOL safety): " + "; ".join(problems) + ". File unchanged.")
    data = result.encode("utf-8")
    shown = str(path)
    try:
        shown = str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        pass
    print(f"{shown}: {action}")
    print(f"EOL before: {fmt(before)} | after: {fmt(after)} | bytes {len(raw)} -> {len(data)} ({len(data) - len(raw):+d})")
    if a.dry_run:
        print("dry-run: nothing written")
        return 0
    if path.read_bytes() != raw:
        die("REFUSED: the file changed on disk while editing; re-run.")
    write_bytes(path, data)
    chk = path.read_bytes()
    if chk != data:
        path.write_bytes(raw)
        die("VERIFY FAILED: written bytes differ; original restored.")
    print("written")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
