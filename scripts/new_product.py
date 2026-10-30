"""Start a product: creates work/<slug>/ (status, questions, decisions, tracker) and makes it the active one.

Usage: python scripts/new_product.py <slug> "<Product name>" [--root D:/products/<slug>]
       python scripts/new_product.py --use <slug>      (switch the active product)
"""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import tracker  # noqa: E402

ROOT = tracker.ROOT
WORK = tracker.WORK


def write(path, text):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)


def main(argv):
    os.makedirs(WORK, exist_ok=True)
    if argv[:1] == ["--use"] and len(argv) == 2:
        if not os.path.isdir(os.path.join(WORK, argv[1])):
            print("no such product: " + argv[1])
            return 1
        write_active(argv[1])
        return 0
    if len(argv) < 2:
        print(__doc__)
        return 1
    slug, name = argv[0], argv[1]
    with open(os.path.join(ROOT, ".claude", "factory.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    root = argv[argv.index("--root") + 1] if "--root" in argv else cfg["products_root"].rstrip("/") + "/" + slug
    d = os.path.join(WORK, slug)
    os.makedirs(d, exist_ok=True)
    today = datetime.date.today().isoformat()
    gates = "\n".join("- %s %s: open" % (g["id"], g["name"]) for g in tracker.teams()["gates"])
    write(os.path.join(d, "status.md"),
          "# Status - %s (%s)\n\nproduct_root: %s\ncode_writes: closed\nstage: S0 Intake\nsize: not set\n\n"
          "## Gates\n%s\n\n## Log\n- %s created\n" % (name, slug, root, gates, today))
    write(os.path.join(d, "questions.md"), "# Questions - %s\n\nFormat: `- [open|answered] Q<n> from <agent> to "
          "<agent|PO|developer>: <question> - Recommended: <answer>` then `  Answer: ... (by, date)`\n\n" % name)
    write(os.path.join(d, "decisions.md"), "# Decisions - %s\n\nFormat: `- D<n> <date> <decision> - by <who> - "
          "why`. Settled decisions are not reopened unless the user asks.\n\n" % name)
    st = tracker.load(slug)
    st["name"] = name
    tracker.log(st, "product created, root " + root)
    tracker.save(slug, st)
    write_active(slug)
    return 0


def write_active(slug):
    with open(os.path.join(WORK, ".active"), "w", encoding="utf-8") as f:
        f.write(slug)
    print("active product: %s\ntracker: %s" % (slug, tracker.paths(slug)[2]))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
