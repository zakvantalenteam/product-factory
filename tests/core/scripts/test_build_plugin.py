"""Tests for core/scripts/build_plugin.py: the missing-file check and the plugin hook launcher.

Run from the repo root (plain unittest, nothing to install):
    python tests/core/scripts/test_build_plugin.py -v
"""
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
import build_plugin  # noqa: E402


def run(args, cwd=None, env=None, stdin=b""):
    p = subprocess.run([sys.executable] + args, input=stdin, capture_output=True, cwd=cwd, env=env, timeout=300)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


class CheckFindsMissingPluginFiles(unittest.TestCase):
    """`build_plugin.py --check` on a copy of this repo's core and plugin (the real ones are never touched)."""

    @classmethod
    def setUpClass(cls):
        cls.home = tempfile.mkdtemp(prefix="pf-build-test-")
        skip = shutil.ignore_patterns("__pycache__", "*.pyc")
        for d in ("core", "plugin", ".claude-plugin"):
            shutil.copytree(os.path.join(REPO, d), os.path.join(cls.home, d), ignore=skip)
        shutil.copyfile(os.path.join(REPO, "README.md"), os.path.join(cls.home, "README.md"))
        cls.script = os.path.join(cls.home, "core", "scripts", "build_plugin.py")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.home, ignore_errors=True)

    def check(self):
        return run([self.script, "--check"], cwd=self.home)

    def test_passes_when_every_named_file_is_there(self):
        code, out, err = self.check()
        self.assertEqual(code, 0, out + err)
        self.assertIn("plugin up to date", out)
        self.assertNotIn("missing", out)

    def test_fails_and_names_the_hook_file_that_is_missing(self):
        path = os.path.join(self.home, "plugin", "hooks", "guard.py")
        keep = path + ".keep"
        os.replace(path, keep)
        try:
            code, out, err = self.check()
        finally:
            os.replace(keep, path)
        self.assertEqual(code, 1, out + err)
        self.assertIn("missing  plugin/hooks/guard.py: hooks/hooks.json names it", out)


class PluginFilesMissing(unittest.TestCase):
    """plugin_files_missing reads hooks/hooks.json and .claude-plugin/plugin.json."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="pf-files-test-")
        os.makedirs(os.path.join(self.dir, "hooks"))
        os.makedirs(os.path.join(self.dir, ".claude-plugin"))
        open(os.path.join(self.dir, "hooks", "here.py"), "w").close()
        self.write("hooks/hooks.json", {"hooks": {"PreToolUse": [{"hooks": [
            {"type": "command", "command": "python", "args": ["${CLAUDE_PLUGIN_ROOT}/hooks/here.py"]}]}]}})
        self.write(".claude-plugin/plugin.json", {"name": "x", "version": "1.0.0"})

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def write(self, rel, data):
        with open(os.path.join(self.dir, rel), "w", encoding="utf-8") as fh:
            json.dump(data, fh)

    def test_nothing_missing(self):
        self.assertEqual(build_plugin.plugin_files_missing(self.dir), [])

    def test_hook_command_string_naming_a_missing_file(self):
        self.write("hooks/hooks.json", {"hooks": {"Stop": [{"hooks": [
            {"type": "command", "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/gone.py\" stop"}]}]}})
        self.assertEqual(build_plugin.plugin_files_missing(self.dir), [("hooks/gone.py", "hooks/hooks.json")])

    def test_plugin_json_naming_a_missing_file(self):
        self.write(".claude-plugin/plugin.json", {"name": "x", "version": "1.0.0", "mcpServers": {
            "s": {"command": "python", "args": ["${CLAUDE_PLUGIN_ROOT}/servers/s.py"]}}})
        self.assertEqual(build_plugin.plugin_files_missing(self.dir),
                         [("servers/s.py", ".claude-plugin/plugin.json")])

    def test_missing_hooks_json(self):
        os.remove(os.path.join(self.dir, "hooks", "hooks.json"))
        self.assertEqual(build_plugin.plugin_files_missing(self.dir), [("hooks/hooks.json", "the build")])


class Launcher(unittest.TestCase):
    """The `python -c` launcher every plugin hook entry runs."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pf-launcher-test-")
        self.project = os.path.join(self.tmp, "repo")
        os.makedirs(os.path.join(self.project, ".claude"))
        with open(os.path.join(self.project, ".claude", "project.json"), "w") as fh:
            fh.write("{}")
        self.plain = os.path.join(self.tmp, "plain")  # a folder that has not opted in to the core
        os.makedirs(self.plain)
        # a marketplace-style copy: <config>/plugins/cache/<marketplace>/<name>/<version>/
        self.copy = os.path.join(self.tmp, "plugins", "cache", "mkt", "pf", "9.9.9")
        os.makedirs(os.path.join(self.copy, "hooks"))
        with open(os.path.join(self.copy, "VERSION"), "w") as fh:
            fh.write("9.9.9\n")
        with open(os.path.join(self.copy, "hooks", "echo.py"), "w") as fh:
            fh.write("import sys\nsys.stdout.write(sys.stdin.read().upper() + ' ' + ' '.join(sys.argv[1:]))\n"
                     "sys.stderr.write('note')\nsys.exit(3)\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def launch(self, mode, rel, project, *args):
        env = dict(os.environ, CLAUDE_PROJECT_DIR=project)
        return run(["-c", build_plugin.LAUNCHER, mode, os.path.join(self.copy, rel)] + list(args),
                   env=env, stdin=b"{\"a\": 1}")

    def test_existing_file_runs_unchanged(self):
        direct = run([os.path.join(self.copy, "hooks", "echo.py"), "x", "y"], stdin=b"{\"a\": 1}")
        for mode in ("block", "warn", "quiet"):
            self.assertEqual(self.launch(mode, "hooks/echo.py", self.project, "x", "y"), direct)
        self.assertEqual(direct, (3, "{\"A\": 1} x y", "note"))

    def test_block_mode_missing_file_blocks_and_names_copy_file_and_fix(self):
        code, out, err = self.launch("block", "hooks/guard.py", self.project)
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("Blocked: the marketplace copy of the pf plugin (pf@mkt 9.9.9) is missing hooks/guard.py", err)
        self.assertIn(self.copy, err)
        self.assertIn("Fix: turn it off or update it in the plugin manager (/plugin).", err)

    def test_warn_mode_missing_file_warns(self):
        code, out, err = self.launch("warn", "hooks/session_start.py", self.project)
        self.assertEqual(code, 0, err)
        msg = json.loads(out)
        self.assertIn("is missing hooks/session_start.py", msg["systemMessage"])
        self.assertEqual(msg["hookSpecificOutput"]["hookEventName"], "SessionStart")

    def test_quiet_mode_missing_file_is_silent(self):
        self.assertEqual(self.launch("quiet", "hooks/live.py", self.project), (0, "", ""))

    def test_folder_without_project_json_lets_the_call_through(self):
        self.assertEqual(self.launch("block", "hooks/guard.py", self.plain), (0, "", ""))

    def test_launcher_has_no_shell_special_characters(self):
        self.assertEqual([c for c in "\"$%^&|<>!`\\" if c in build_plugin.LAUNCHER], [])

    def test_built_hooks_use_the_launcher_with_the_right_mode(self):
        with open(os.path.join(REPO, "plugin", "hooks", "hooks.json"), encoding="utf-8") as fh:
            cfg = json.load(fh)
        modes = {}
        for entries in cfg["hooks"].values():
            for entry in entries:
                for h in entry["hooks"]:
                    self.assertEqual(h["args"][:2], ["-c", build_plugin.LAUNCHER])
                    modes.setdefault(h["args"][2], set()).add(h["args"][3])
        self.assertEqual(modes["block"], {"${CLAUDE_PLUGIN_ROOT}/hooks/guard.py"})
        self.assertEqual(modes["warn"], {"${CLAUDE_PLUGIN_ROOT}/hooks/session_start.py"})


if __name__ == "__main__":
    unittest.main()
