"""Check a new product root against base/base-manifest.json - prints every miss and a percentage.

Usage: python scripts/check_base.py <product root> [--section B4] [--package com/talenteam/acme]
                                    [--var productSlug=acme ...] [--out report.md]

Placeholders (BASE-SPEC B0.5) are replaced in path_or_name and must_contain. Their values are read from the
product root; --var overrides any of them:
  {{basePackagePath}} {{basePackage}}  folder of the backend's *Application.java (or --package)
  {{ProductClass}}                      that class name without "Application"
  {{productSlug}}                       Frontend/package.json name without "-frontend"
  {{productName}} {{productTagline}}    Frontend/src/locales/en.json app.name, app.footer.brand
  {{cssPrefix}}                         the most used CSS variable prefix (--<prefix>-...) in Frontend/src

Manifest entries: {"id", "kind", "path_or_name", "must_contain": [...], "source"}
  file      path; must exist and contain each must_contain
  config    "<file>:<key>"; the file exists and defines the key
  label     "<locale file>:<dotted key>"; the key exists in that JSON and in every other locale JSON beside it
  route     URL, must_contain = the route file; the file exists and Frontend/src/routeTree.gen.ts knows the URL
  endpoint  "METHOD /path"; a controller maps it (class + method mapping). An entry whose source says
            "served by TTCommon" passes when the backend pom depends on TTCommon-Core (the jar serves it).
  table     table name, must_contain = columns; a migration creates the table with those columns
"""
import collections
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SKIP_DIRS = {"node_modules", "target", "dist", "build", ".git", ".idea", ".vscode", "releases"}


def read(p):
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def walk(root, exts):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            if f.endswith(exts):
                yield os.path.join(d, f)


def detect_package(root):
    for p in glob.glob(os.path.join(root, "**", "src", "main", "java", "**", "*Application.java"), recursive=True):
        rel = p.replace("\\", "/").split("/src/main/java/", 1)[1]
        return os.path.dirname(rel), os.path.basename(rel)[:-len("Application.java")]
    return "", ""


def placeholders(root, pkg, overrides):
    found_pkg, cls = detect_package(root)
    pkg = pkg or found_pkg
    try:
        slug = json.loads(read(os.path.join(root, "Frontend", "package.json"))).get("name", "")
    except ValueError:
        slug = ""
    slug = re.sub(r"-frontend$", "", slug) or cls.lower()
    try:
        app = json.loads(read(os.path.join(root, "Frontend", "src", "locales", "en.json"))).get("app", {})
    except ValueError:
        app = {}
    name = app.get("name") or cls
    brand = (app.get("footer") or {}).get("brand", "")
    tagline = brand[len(name):].strip() if brand.startswith(name) else brand
    prefixes = collections.Counter()
    for p in walk(os.path.join(root, "Frontend", "src"), (".css", ".ts", ".tsx")):
        prefixes.update(re.findall(r"--([a-z][a-z0-9]{1,5})-[a-z]", read(p)))
    for common in ("tw", "radix", "webkit", "moz"):
        prefixes.pop(common, None)
    values = {"basePackagePath": pkg, "basePackage": pkg.replace("/", "."), "ProductClass": cls,
              "productSlug": slug, "productName": name, "productTagline": tagline,
              "cssPrefix": prefixes.most_common(1)[0][0] if prefixes else ""}
    values.update(overrides)
    return values


def endpoints(root):
    found = set()
    for f in walk(os.path.join(root, "Backend", "src", "main", "java"), (".java",)):
        t = read(f)
        base = re.search(r'@RequestMapping\(\s*(?:value\s*=\s*|path\s*=\s*)?"([^"]*)"', t)
        b = base.group(1) if base else ""
        for m in re.finditer(r'@(Get|Post|Put|Delete|Patch)Mapping(?:\(\s*(?:value\s*=\s*|path\s*=\s*)?"([^"]*)"[^)]*\))?', t):
            found.add((m.group(1).upper(), re.sub(r"\{[^}]*\}", "{}", b + (m.group(2) or ""))))
    return found


def label_has(tree, key):
    cur = tree
    for part in key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return False
        cur = cur[part]
    return True


def check(it, root, sub, eps, sql, ttcommon):
    """Returns "" when the item passes, else why it misses."""
    kind, name = it["kind"], sub(it["path_or_name"])
    need = [sub(s) for s in (it.get("must_contain") or [])]
    if kind == "file":
        p = os.path.join(root, name)
        if not os.path.isfile(p):
            return "missing file " + name
        lack = [s for s in need if s not in read(p)]
        return "%s lacks %s" % (name, ", ".join(lack)) if lack else ""
    if kind == "config":
        fname, key = name.split(":", 1)
        p = os.path.join(root, fname)
        if not os.path.isfile(p):
            return "missing file " + fname
        text = read(p)
        if re.search(r"^\s*" + re.escape(key) + r"\s*[=:]", text, re.M) or key in text:
            return ""
        return "%s does not define %s" % (fname, key)
    if kind == "label":
        fname, key = name.split(":", 1)
        p = os.path.join(root, fname)
        if not os.path.isfile(p):
            return "missing file " + fname
        for q in [p] + [q for q in glob.glob(os.path.join(os.path.dirname(p), "*.json")) if q != p]:
            try:
                tree = json.loads(read(q))
            except ValueError:
                return "bad json " + q
            if not label_has(tree, key):
                return "label %s missing in %s" % (key, os.path.basename(q))
        return ""
    if kind == "route":
        rf = need[0] if need else ""
        if rf and not os.path.isfile(os.path.join(root, rf)):
            return "missing route file " + rf
        tree = read(os.path.join(root, "Frontend", "src", "routeTree.gen.ts"))
        return "" if ("'" + name + "'") in tree else "route %s not in routeTree.gen.ts" % name
    if kind == "endpoint":
        method, path = name.split(" ", 1)
        if (method, re.sub(r"\{[^}]*\}", "{}", path)) in eps:
            return ""
        if "served by TTCommon" in it.get("source", "") and ttcommon:
            return ""
        return "endpoint %s %s not mapped by a controller" % (method, path)
    if kind == "table":
        hit = [t for _, t in sql if re.search(r"create\s+table\s+(if\s+not\s+exists\s+)?" + re.escape(name) + r"\b", t, re.I)]
        if not hit:
            return "table %s not created by a migration" % name
        lack = [c for c in need if not any(c in t for t in hit)]
        return "table %s lacks columns %s" % (name, ", ".join(lack)) if lack else ""
    return "unknown kind " + kind


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    root = os.path.abspath(argv[0])
    opt = lambda k: argv[argv.index(k) + 1] if k in argv else ""
    section, out = opt("--section"), opt("--out")
    overrides = dict(argv[i + 1].split("=", 1) for i, a in enumerate(argv) if a == "--var" and i + 1 < len(argv))
    values = placeholders(root, opt("--package"), overrides)
    sub = lambda t: re.sub(r"\{\{(\w+)\}\}", lambda m: values.get(m.group(1), m.group(0)), t)
    with open(os.path.join(ROOT, "base", "base-manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    items = manifest if isinstance(manifest, list) else manifest.get("items", [])
    if section:
        items = [i for i in items if re.match(re.escape(section) + r"(\.|$)", i["id"])]
    eps = endpoints(root)
    sql = [(p, read(p)) for p in walk(root, (".sql",))]
    ttcommon = "TTCommon-Core" in read(os.path.join(root, "Backend", "pom.xml")) + read(os.path.join(root, "pom.xml"))
    misses, passed = [], 0
    for it in items:
        why = check(it, root, sub, eps, sql, ttcommon)
        if why:
            misses.append((it["id"], why))
        else:
            passed += 1
    total = len(items)
    pct = 100 if total == 0 else int(passed * 100 / total)
    lines = ["base check: %s%s" % (root, (" section " + section) if section else ""),
             "placeholders: " + ", ".join("%s=%s" % (k, v or "NOT FOUND") for k, v in sorted(values.items())), ""]
    lines += ["MISS %s  %s" % m for m in misses]
    lines += ["", "%d/%d passed - %d%%" % (passed, total, pct)]
    print("\n".join(lines))
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write("```\n" + "\n".join(lines) + "\n```\n")
    return 0 if not misses else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
