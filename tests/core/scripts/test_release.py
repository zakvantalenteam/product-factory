"""Tests for core/scripts/release.py: the version check, the dry run and the exact-file commit lines.

Run from the repo root (plain unittest, nothing to install):
    python tests/core/scripts/test_release.py -v
Everything runs on temp folders (a copy of core/ and plugin/); the real repos are never touched and no git command
runs that changes anything.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "core", "scripts"))
sys.dont_write_bytecode = True
import install  # noqa: E402
import release  # noqa: E402

ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
ENV.pop("CLAUDE_PROJECT_DIR", None)


def run(args, cwd):
    p = subprocess.run([sys.executable] + args, capture_output=True, cwd=cwd, env=ENV, timeout=300)
    return p.returncode, p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")


def snapshot(*folders):
    """{path: sha256} for every file under the folders."""
    out = {}
    for f in folders:
        for top, _, names in os.walk(f):
            for n in names:
                p = os.path.join(top, n)
                with open(p, "rb") as fh:
                    out[p] = hashlib.sha256(fh.read()).hexdigest()
    return out


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


class TempHome(unittest.TestCase):
    """A copy of the home repo's core/, plugin/, .claude-plugin/ and README.md in a temp folder (no git there), with
    one empty product repo and a targets file naming both."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="pf-release-test-")
        cls.home = os.path.join(cls.tmp, "home")
        skip = shutil.ignore_patterns("__pycache__", "*.pyc")
        for d in ("core", "plugin", ".claude-plugin"):
            shutil.copytree(os.path.join(REPO, d), os.path.join(cls.home, d), ignore=skip)
        shutil.copyfile(os.path.join(REPO, "README.md"), os.path.join(cls.home, "README.md"))
        cls.product = os.path.join(cls.tmp, "product")
        write(os.path.join(cls.product, "README.md"), "a product\n")
        cls.targets = os.path.join(cls.tmp, "targets.json")
        write(cls.targets, json.dumps({"repos": [{"name": "home", "path": cls.home},
                                                 {"name": "product", "path": cls.product}]}))
        cls.script = os.path.join(cls.home, "core", "scripts", "release.py")
        with open(os.path.join(cls.home, "core", "VERSION"), encoding="utf-8") as fh:
            cls.version = fh.read().strip()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def release(self, *args):
        return run([self.script] + list(args) + ["--summary", "a test", "--targets", self.targets], cwd=self.tmp)

    def higher(self):
        major, minor, patch = release.parse(self.version)
        return "%d.%d.%d" % (major, minor + 1, 0)


class RefusesAVersionThatIsNotHigher(TempHome):
    def test_lower_version_is_refused_and_nothing_changes(self):
        before = snapshot(self.home, self.product)
        rc, out = self.release("0.0.1")
        self.assertEqual(rc, 1, out)
        self.assertIn("not higher than the current core version %s" % self.version, out)
        self.assertEqual(before, snapshot(self.home, self.product))

    def test_same_version_is_refused_without_an_earlier_run(self):
        rc, out = self.release(self.version)
        self.assertEqual(rc, 1, out)
        self.assertIn("not higher", out)

    def test_not_x_y_z_is_refused(self):
        rc, out = self.release("2.0")
        self.assertEqual(rc, 1, out)
        self.assertIn("is not X.Y.Z", out)

    def test_check_version_against_a_committed_version(self):
        orig = release.current_versions
        try:
            release.current_versions = lambda: ("1.16.2", "1.16.1")
            with self.assertRaises(release.Stop):
                release.check_version("1.16.1", None)  # not above the committed one
            with self.assertRaises(release.Stop):
                release.check_version("1.16.0", None)
            self.assertEqual(release.check_version("1.16.2", None), ("1.16.2", "1.16.1"))  # a rerun of the bump
            self.assertEqual(release.check_version("1.17.0", None), ("1.16.2", "1.16.1"))
        finally:
            release.current_versions = orig


class DryRunChangesNothing(TempHome):
    def test_dry_run_writes_nothing(self):
        before = snapshot(self.home, self.product)
        rc, out = self.release(self.higher(), "--dry-run")
        self.assertEqual(rc, 0, out)
        self.assertIn("would set core/VERSION: %s -> %s" % (self.version, self.higher()), out)
        self.assertIn("dry run: nothing written", out)
        self.assertEqual(before, snapshot(self.home, self.product))
        self.assertFalse(os.path.exists(os.path.join(self.home, ".release")))

    def test_missing_targets_file_stops_with_a_plain_message(self):
        rc, out = run([self.script, self.higher(), "--summary", "x", "--targets",
                       os.path.join(self.tmp, "none.json"), "--dry-run"], cwd=self.tmp)
        self.assertEqual(rc, 1, out)
        self.assertIn("release.local.example.json", out)

    def test_unknown_repo_name_is_refused(self):
        rc, out = self.release(self.higher(), "--dry-run", "--repos", "nope")
        self.assertEqual(rc, 1, out)
        self.assertIn("unknown repo name(s) nope", out)


class ExactFileAddLines(unittest.TestCase):
    """classify() on a temp repo with given uncommitted entries and committed texts (no git)."""

    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="pf-release-classify-")

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)

    def put(self, rel, text):
        write(os.path.join(self.repo, *rel.split("/")), text)

    def head(self, committed):
        return lambda rel: committed.get(rel)

    def test_only_the_release_files_are_added_and_the_rest_is_left_out(self):
        self.put(".claude/project.json", json.dumps({"name": "P", "commit_prefix": "TICK-1"}))
        self.put(".claude/core/core.lock", json.dumps({"version": "9.9.9", "files": {
            ".claude/agents/a.md": "x", ".claude/core/VERSION": "y", ".claude/core/templates/new.md": "t"}}))
        self.put(".claude/core/templates/new.md", "a core file from an earlier release, never committed\n")
        self.put(".claude/core/VERSION", "9.9.9\n")
        self.put(".claude/agents/a.md", "core agent\n")
        self.put(".claude/agents/own.md", "the repo's own agent, edited\n")
        self.put(".cursor/agents/own.md", "Generated by the agent core's cursor_sync.py from .claude/agents/own.md\n")
        self.put(".cursor/agents/a.md", "Generated by the agent core's cursor_sync.py from .claude/agents/a.md\n")
        self.put(".cursor/runtime/VERSION", "9.9.9\n")
        self.put(".cursor/rules/mine.mdc", "a hand-made Cursor rule\n")
        with open(os.path.join(install.CORE, "templates", "accepted.md"), encoding="utf-8") as fh:
            self.put(".claude/review/accepted.md", fh.read())
        self.put(".claude/smoke.md", "the project's own smoke pack\n")
        old_agents = "# P\n\nOwn text.\n\n<!-- core:start -->\nold block\n<!-- core:end -->\n"
        self.put("AGENTS.md", install.agents_md(old_agents, "P"))
        self.put(".gitignore", "build/\n.claude/core-backup/\n")
        self.put("notes/my work.txt", "another session's work\n")
        self.put("src/app.py", "print(1)\n")
        entries = [(" M", ".claude/agents/a.md"), (" M", ".claude/core/VERSION"), (" M", ".claude/core/core.lock"),
                   (" D", ".claude/core/scripts/gone.py"), (" M", ".claude/agents/own.md"),
                   (" M", ".cursor/agents/own.md"), (" M", ".cursor/agents/a.md"), (" M", ".cursor/runtime/VERSION"),
                   ("??", ".cursor/rules/mine.mdc"), ("??", ".claude/review/accepted.md"), ("??", ".claude/smoke.md"),
                   (" M", "AGENTS.md"), (" M", ".gitignore"), ("??", "notes/my work.txt"), (" M", "src/app.py"),
                   ("??", "core/scripts/x.py"), ("??", ".claude/core/templates/new.md")]
        committed = {".claude/core/core.lock": json.dumps({"version": "9.9.8", "files": {
            ".claude/core/scripts/gone.py": "z"}}), "AGENTS.md": old_agents, ".gitignore": "build/\n"}
        add, left = release.classify(self.repo, entries, home=False, head=self.head(committed))
        added = [f for f, _ in add]
        self.assertEqual(added, [
            ".claude/agents/a.md", ".claude/core/VERSION", ".claude/core/core.lock", ".claude/core/scripts/gone.py",
            ".claude/core/templates/new.md", ".claude/review/accepted.md", ".cursor/agents/a.md", ".cursor/runtime/VERSION", ".gitignore", "AGENTS.md"])
        self.assertEqual(left, [".claude/agents/own.md", ".claude/smoke.md", ".cursor/agents/own.md",
                                ".cursor/rules/mine.mdc", "core/scripts/x.py", "notes/my work.txt", "src/app.py"])

        lines = release.add_lines(self.repo, added)
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("git -C %s add " % release.ps(os.path.normpath(self.repo))), lines[0])
        named = lines[0].split(" add ", 1)[1].split(" ")
        self.assertEqual(named, added)  # the exact files, in order: no folder, nothing else
        self.assertEqual(release.subject(self.repo, False, "1.2.3", 'a "quoted" one'),
                         "TICK-1 AI dev setup: agent core 1.2.3 - a 'quoted' one")

    def test_agents_md_and_gitignore_with_other_changes_are_left_out(self):
        old_agents = "# P\n\n<!-- core:start -->\nold\n<!-- core:end -->\n"
        self.put("AGENTS.md", install.agents_md(old_agents, "P").replace("# P", "# P renamed"))
        self.put(".gitignore", "build/\nsecret-stuff/\n")
        add, left = release.classify(self.repo, [(" M", "AGENTS.md"), (" M", ".gitignore")], home=False,
                                     head=self.head({"AGENTS.md": old_agents, ".gitignore": "build/\n"}))
        self.assertEqual(add, [])
        self.assertEqual(left, [".gitignore", "AGENTS.md"])

    def test_home_repo_adds_core_plugin_tests_and_include(self):
        entries = [(" M", "core/scripts/x.py"), ("??", "plugin/scripts/x.py"), ("??", "tests/core/scripts/test_x.py"),
                   (" M", "README.md"), ("??", "work/a/status.json"), (" M", "docs/guide.md")]
        add, left = release.classify(self.repo, entries, home=True, include=["./docs/guide.md"],
                                     head=self.head({}))
        self.assertEqual([f for f, _ in add], ["core/scripts/x.py", "docs/guide.md", "plugin/scripts/x.py",
                                               "tests/core/scripts/test_x.py"])
        self.assertEqual(left, ["README.md", "work/a/status.json"])

    def test_readme_with_only_the_agents_table_changed_is_added(self):
        marks = release.README_MARKS
        old = "# Home\n\n%s -->\n| old |\n%s\n\nmore\n" % (marks[0], marks[1])
        self.put("README.md", old.replace("| old |", "| new |"))
        add, _ = release.classify(self.repo, [(" M", "README.md")], home=True, head=self.head({"README.md": old}))
        self.assertEqual(add, [("README.md", "agents table")])
        self.put("README.md", old.replace("more", "edited by hand"))
        add, left = release.classify(self.repo, [(" M", "README.md")], home=True, head=self.head({"README.md": old}))
        self.assertEqual((add, left), ([], ["README.md"]))

    def test_paths_are_quoted_for_powershell_and_split_into_lines(self):
        files = ["a/f%02d.md" % i for i in range(release.PER_LINE + 3)] + ["n8n/My Flow.json", "o'brien.md"]
        lines = release.add_lines("D:\\r", files)
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[1].endswith("'n8n/My Flow.json' 'o''brien.md'"), lines[1])
        self.assertEqual(release.ps("D:\\product-factory\\repo"), "D:\\product-factory\\repo")

    def test_commit_block_has_one_command_per_line_and_lists_left_out(self):
        block = release.commit_block("p", "D:\\p", False, "1.2.3", "x", [("a.md", "core file")], ["b.md"], "1.2.2")
        text = "\n".join(block)
        self.assertIn("also carries core 1.2.2", text)
        self.assertIn("git -C D:\\p add a.md\ngit -C D:\\p commit -m 'AI dev setup: agent core 1.2.3 - x'", text)
        self.assertIn("Left out (1, not part of the release): b.md", text)
        self.assertNotIn("push", text)
        home = "\n".join(release.commit_block("h", "D:\\h", True, "1.2.3", "x", [("core/a.py", "")], [], None))
        self.assertIn("commit -m 'core 1.2.3: x'\ngit -C D:\\h push", home)


if __name__ == "__main__":
    unittest.main()
