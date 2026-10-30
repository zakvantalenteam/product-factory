"""Run one characterization test for this repo (commands.char_run: python .claude/scripts/char_run.py "{file}").

A Java test is one class with a main() in the session scratchpad that calls the shared methods a change touches and
prints their outputs (Mockito from the test classpath for collaborators). It is compiled against the classes the IDE
already built (target/classes, target/test-classes) and the Maven dependency classpath, so nothing runs `mvn compile`
while the app is up. .js/.mjs tests run with node. The dependency classpath is cached next to the test as
.classpath.txt and rebuilt when pom.xml is newer (mvn -o dependency:build-classpath: offline, writes no repo file).
"""
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
# the Maven project: Backend/ when it has its own pom (a root pom there only aggregates), else the repo root
BASE = os.path.join(ROOT, "Backend") if os.path.isfile(os.path.join(ROOT, "Backend", "pom.xml")) else ROOT


def dep_classpath(folder):
    cache = os.path.join(folder, ".classpath.txt")
    pom = os.path.join(BASE, "pom.xml")
    if not os.path.isfile(cache) or os.path.getmtime(cache) < os.path.getmtime(pom):
        p = subprocess.run("mvn -o -q dependency:build-classpath \"-Dmdep.outputFile=%s\"" % cache, shell=True,
                           cwd=BASE, capture_output=True, text=True)
        if p.returncode != 0 or not os.path.isfile(cache):
            sys.exit("could not build the dependency classpath: " + " ".join((p.stdout + p.stderr).split())[:300])
    return open(cache, encoding="utf-8").read().strip()


def run_java(path):
    folder = os.path.dirname(path)
    src = open(path, encoding="utf-8").read()
    pkg = re.search(r"^\s*package\s+([\w.]+)\s*;", src, re.M)
    main = (pkg.group(1) + "." if pkg else "") + os.path.splitext(os.path.basename(path))[0]
    out = os.path.join(folder, ".classes")
    cp = os.pathsep.join([os.path.join(BASE, "target", "classes"), os.path.join(BASE, "target", "test-classes"),
                          dep_classpath(folder)])
    c = subprocess.run(["javac", "-encoding", "UTF-8", "-nowarn", "-cp", cp, "-d", out, path], capture_output=True,
                       text=True)
    if c.returncode != 0:
        sys.stderr.write(c.stdout + c.stderr)
        sys.exit(c.returncode)
    r = subprocess.run(["java", "-cp", out + os.pathsep + cp, main], cwd=BASE)
    sys.exit(r.returncode)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = os.path.abspath(sys.argv[1])
    ext = os.path.splitext(path)[1].lower()
    if ext == ".java":
        run_java(path)
    elif ext in (".js", ".mjs", ".cjs"):
        sys.exit(subprocess.run(["node", path], cwd=ROOT).returncode)
    sys.exit("no runner for %s files" % ext)


if __name__ == "__main__":
    main()
