"""Tests for core/scripts/doctor.py: it finds every copy and flags a missing hook file, a version mismatch and the
plugin on twice, without writing anywhere.

Run from the repo root (plain unittest, nothing to install):
    python tests/core/scripts/test_doctor.py -v
Everything runs on a fake machine in a temp folder: a fake ~/.claude, a fake claude.ai folder, a fake home repo and
two fake product repos. The real copies are never read or touched.
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
DOCTOR = os.path.join(REPO, "core", "scripts", "doctor.py")
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
ENV.pop("CLAUDE_PROJECT_DIR", None)
ENV.pop("PRODUCT_FACTORY_HOME", None)
HOOKS = {"hooks": {"PreToolUse": [{"hooks": [{"type": "command", "command": "python",
                                              "args": ["${CLAUDE_PLUGIN_ROOT}/hooks/guard.py"]}]}]}}


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def snapshot(folder):
    out = {}
    for top, _, names in os.walk(folder):
        for n in names:
            p = os.path.join(top, n)
            with open(p, "rb") as fh:
                out[p] = hashlib.sha256(fh.read()).hexdigest()
    return out


def plugin_copy(folder, version, guard=True):
    write(os.path.join(folder, ".claude-plugin", "plugin.json"), json.dumps({"name": "product-factory",
                                                                             "version": version}))
    write(os.path.join(folder, "VERSION"), version + "\n")
    write(os.path.join(folder, "hooks", "hooks.json"), json.dumps(HOOKS))
    write(os.path.join(folder, "scripts", "doctor.py"), "# a copy\n")
    if guard:
        write(os.path.join(folder, "hooks", "guard.py"), "# guard\n")


def repo_copy(repo, version, files=None):
    files = files or {".claude/core/VERSION": "a", ".claude/core/hooks/guard.py": "b"}
    write(os.path.join(repo, ".claude", "core", "VERSION"), version + "\n")
    write(os.path.join(repo, ".claude", "core", "hooks", "guard.py"), "# guard\n")
    write(os.path.join(repo, ".claude", "core", "core.lock"), json.dumps({"version": version, "files": files}))


class FakeMachine(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pf-doctor-test-")
        self.claude = os.path.join(self.tmp, "dot-claude")
        self.data = os.path.join(self.tmp, "Claude-Data")
        self.home = os.path.join(self.tmp, "home")
        self.repo_a = os.path.join(self.tmp, "product-a")
        self.repo_b = os.path.join(self.tmp, "product-b")
        self.cache = os.path.join(self.claude, "plugins", "cache", "mk", "product-factory", "1.2.0")
        os.makedirs(self.data)
        self.versions("1.2.0", "1.2.0", "1.2.0", "1.2.0")
        write(os.path.join(self.home, ".claude-plugin", "marketplace.json"), json.dumps({"name": "mk", "plugins": [
            {"name": "product-factory", "source": "./plugin"}]}))
        write(os.path.join(self.claude, "plugins", "installed_plugins.json"), json.dumps({"version": 2, "plugins": {
            "product-factory@mk": [{"scope": "user", "installPath": self.cache, "version": "1.2.0"}]}}))
        write(os.path.join(self.claude, "settings.json"), json.dumps({"enabledPlugins": {"product-factory@mk": True}}))
        plugin_copy(os.path.join(self.claude, "plugins", "cache", "mk", "product-factory", "1.1.0"), "1.1.0")
        self.targets = os.path.join(self.home, "release.local.json")
        write(self.targets, json.dumps({"repos": [{"name": "home", "path": self.home},
                                                  {"name": "a", "path": self.repo_a},
                                                  {"name": "b", "path": self.repo_b}]}))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def versions(self, source, plugin, a, b):
        write(os.path.join(self.home, "core", "VERSION"), source + "\n")
        plugin_copy(os.path.join(self.home, "plugin"), source)
        plugin_copy(self.cache, plugin)
        repo_copy(self.home, source)
        repo_copy(self.repo_a, a)
        repo_copy(self.repo_b, b)

    def doctor(self):
        p = subprocess.run([sys.executable, DOCTOR, "--home", self.home, "--claude-home", self.claude,
                            "--claude-data", self.data], capture_output=True, cwd=self.tmp, env=ENV, timeout=120)
        return p.returncode, p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")

    def test_clean_machine_exits_0_and_lists_every_copy(self):
        rc, out = self.doctor()
        self.assertEqual(rc, 0, out)
        self.assertIn("no problems", out)
        for label in ("marketplace product-factory@mk", "repo home", "repo a", "repo b"):
            self.assertIn(label, out)
        self.assertIn("older marketplace cache, not in use: 1 versions (1.1.0 to 1.1.0)", out)

    def test_missing_hook_file_is_flagged_with_a_fix(self):
        os.remove(os.path.join(self.cache, "hooks", "guard.py"))
        rc, out = self.doctor()
        self.assertEqual(rc, 1, out)
        self.assertIn("marketplace product-factory@mk 1.2.0 is missing 1 file: hooks/guard.py", out)
        self.assertIn("Fix: claude plugin update product-factory@mk", out)

    def test_repo_core_missing_a_file_is_flagged(self):
        os.remove(os.path.join(self.repo_a, ".claude", "core", "hooks", "guard.py"))
        rc, out = self.doctor()
        self.assertEqual(rc, 1, out)
        self.assertIn("repo a 1.2.0 is missing 1 file: .claude/core/hooks/guard.py", out)
        self.assertIn("install.py", out)

    def test_version_mismatch_between_repos_and_with_the_source(self):
        self.versions("1.3.0", "1.3.0", "1.3.0", "1.2.0")
        rc, out = self.doctor()
        self.assertEqual(rc, 1, out)
        self.assertIn("the repo cores differ", out)
        self.assertIn("b has 1.2.0", out)
        self.assertIn("release.py 1.3.0", out)

    def test_plugin_older_than_the_repo_cores(self):
        self.versions("1.3.0", "1.2.0", "1.3.0", "1.3.0")
        rc, out = self.doctor()
        self.assertEqual(rc, 1, out)
        self.assertIn("is older than the repo cores (1.3.0)", out)
        self.assertIn("claude plugin marketplace update mk", out)

    def test_two_copies_on_at_once(self):
        rpm = os.path.join(self.data, "acct", "rpm", "x1", "y1")
        plugin_copy(os.path.join(rpm, "plugin_01abc"), "1.2.0")
        write(os.path.join(rpm, "manifest.json"), json.dumps({"plugins": [{"id": "plugin_01abc",
                                                                           "name": "product-factory"}]}))
        rc, out = self.doctor()
        self.assertEqual(rc, 1, out)
        self.assertIn("the plugin is on twice", out)
        self.assertIn("claude.ai plugin_01abc", out)

    def test_claude_ai_copy_missing_guard_is_flagged(self):
        rpm = os.path.join(self.data, "acct", "rpm", "x1", "y1")
        plugin_copy(os.path.join(rpm, "plugin_01abc"), "1.2.0", guard=False)
        rc, out = self.doctor()
        self.assertEqual(rc, 1, out)
        self.assertIn("claude.ai plugin_01abc 1.2.0 is missing 1 file: hooks/guard.py", out)
        self.assertIn("turn it off on claude.ai", out)

    def test_doctor_writes_nothing(self):
        os.remove(os.path.join(self.cache, "hooks", "guard.py"))
        before = snapshot(self.tmp)
        self.doctor()
        self.assertEqual(before, snapshot(self.tmp))


if __name__ == "__main__":
    unittest.main()
