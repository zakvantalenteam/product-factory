"""Tests for core/scripts/bench.py: case loading, the run list, the scaffold script, the eval suite, the result
summary, the report and the run command's guards.

Run from the repo root (plain unittest, nothing to install):
    python tests/core/scripts/test_bench.py -v
Everything runs on temp folders (a throwaway git repo built here, a fake plugin); the real repos and the real
~/.claude are never touched. No claude CLI is started: `run` is only tried with --dry-run.
"""
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "core", "scripts"))
sys.dont_write_bytecode = True
import bench  # noqa: E402

RUBRIC = "The defect: the icon is wrong.\nPASS if a finding names the icon.\nFAIL if the reply is generic.\n"
GIT_ID = ["-c", "user.name=bench-test", "-c", "user.email=bench-test@example.invalid", "-c", "commit.gpgsign=false"]


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def slurp(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def make_case(repo, cid, folder=None, rubrics=("code-reviewer",), ticket="The ticket: add an icon.\n", **over):
    """Write .claude/bench/cases/<cid>/ in repo; `over` overrides case.json keys (None removes one)."""
    case = {"id": cid, "title": "t", "introduced": "abc", "fixed": "def", "files": ["src/a.js"],
            "defect": {"file": "src/a.js", "mechanism": "wrong icon"}, "caught_at": "code-reviewer"}
    case.update(over)
    case = {k: v for k, v in case.items() if v is not None}
    d = folder or os.path.join(repo, bench.CASES_DIR, cid)
    write(os.path.join(d, "case.json"), json.dumps(case))
    if ticket is not None:
        write(os.path.join(d, "ticket.md"), ticket)
    for s in rubrics:
        write(os.path.join(d, "rubric-%s.md" % s), RUBRIC)
    return d


def fake_plugin(root):
    p = os.path.join(root, "plugin")
    write(os.path.join(p, ".claude-plugin", "plugin.json"),
          json.dumps({"name": "product-factory", "version": "9.9.9", "hooks": "./hooks/hooks.json"}))
    write(os.path.join(p, "agents", "x.md"), "# agent\n")
    write(os.path.join(p, "scripts", "review_pack.py"), "print('stub')\n")
    write(os.path.join(p, "hooks", "hooks.json"), "{}\n")
    write(os.path.join(p, "evals", "old", "case.yaml"), "name: old\n")
    return p


class Tmp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pf-bench-test-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)


class LoadCase(Tmp):
    def load(self, **kw):
        d = make_case(self.tmp, kw.pop("cid", "bug-a"), **kw)
        return bench.load_case(d)

    def has(self, probs, text):
        self.assertTrue(any(text in p for p in probs), "%r not in %r" % (text, probs))

    def test_valid_case_stages_skip_not_applicable(self):
        c, probs = self.load(rubrics=("review-spec", "code-reviewer", "qa-lead"),
                             not_applicable={"review-spec": "no ticket gap"})
        self.assertEqual(probs, [])
        self.assertEqual(set(c["stages"]), {"code-reviewer", "qa-lead"})
        self.assertTrue(c["stages"]["qa-lead"].startswith("The defect:"))
        self.assertTrue(c["folder"].endswith("bug-a"))

    def test_only_the_rubrics_that_exist_are_stages(self):
        c, probs = self.load(rubrics=("qa-lead",), caught_at="qa-lead")
        self.assertEqual(probs, [])
        self.assertEqual(list(c["stages"]), ["qa-lead"])

    def test_missing_ticket(self):
        _c, probs = self.load(ticket=None)
        self.has(probs, "ticket.md missing or empty")

    def test_blank_ticket(self):
        _c, probs = self.load(ticket="  \n")
        self.has(probs, "ticket.md missing or empty")

    def test_caught_at_not_allowed(self):
        _c, probs = self.load(caught_at="nobody")
        self.has(probs, "caught_at must be one of")

    def test_id_is_not_the_folder_name(self):
        d = make_case(self.tmp, "other-id", folder=os.path.join(self.tmp, "folder-name"))
        _c, probs = bench.load_case(d)
        self.has(probs, "id other-id is not the folder name")

    def test_rubric_without_pass_line(self):
        d = make_case(self.tmp, "bug-a")
        write(os.path.join(d, "rubric-code-reviewer.md"), "The defect: x\nFAIL if generic.\n")
        _c, probs = bench.load_case(d)
        self.has(probs, "rubric-code-reviewer.md needs a 'PASS if' and a 'FAIL if' line")

    def test_rubric_without_fail_line(self):
        d = make_case(self.tmp, "bug-a")
        write(os.path.join(d, "rubric-code-reviewer.md"), "The defect: x\nPASS if it names it.\n")
        _c, probs = bench.load_case(d)
        self.has(probs, "needs a 'PASS if' and a 'FAIL if'")

    def test_no_rubric_at_all(self):
        c, probs = self.load(rubrics=())
        self.has(probs, "no rubric-<stage>.md for any stage")
        self.assertEqual(c["stages"], {})

    def test_all_rubrics_not_applicable_is_no_rubric(self):
        _c, probs = self.load(rubrics=("qa-lead",), caught_at="qa-lead", not_applicable={"qa-lead": "n/a"})
        self.has(probs, "no rubric-<stage>.md for any stage")

    def test_not_catchable_needs_no_rubric(self):
        c, probs = self.load(rubrics=(), caught_at="not-catchable")
        self.assertEqual(probs, [])
        self.assertEqual(c["stages"], {})

    def test_case_json_missing(self):
        d = os.path.join(self.tmp, "empty-case")
        os.makedirs(d)
        c, probs = bench.load_case(d)
        self.assertEqual(probs, ["case.json missing or not a JSON object"])
        self.assertEqual(c, {"id": "empty-case", "stages": {}})

    def test_case_json_invalid(self):
        d = os.path.join(self.tmp, "bad-json")
        write(os.path.join(d, "case.json"), "{not json")
        c, probs = bench.load_case(d)
        self.assertEqual(probs, ["case.json missing or not a JSON object"])
        self.assertEqual(c["stages"], {})

    def test_case_json_not_an_object(self):
        d = os.path.join(self.tmp, "a-list")
        write(os.path.join(d, "case.json"), "[1, 2]")
        _c, probs = bench.load_case(d)
        self.assertEqual(probs, ["case.json missing or not a JSON object"])

    def test_missing_required_fields_and_bad_defect(self):
        _c, probs = self.load(fixed=None, defect={"file": "x"}, files="src/a.js")
        self.has(probs, "case.json has no fixed")
        self.has(probs, "defect needs file and mechanism")
        self.has(probs, "files must be a list")


class ItemsFor(Tmp):
    def setUp(self):
        super().setUp()
        self.repo = self.tmp
        make_case(self.repo, "bug-a", rubrics=("code-reviewer", "qa-lead"))
        make_case(self.repo, "bug-b", rubrics=("qa-lead",), caught_at="not-catchable")
        make_case(self.repo, "bug-c", ticket=None)  # invalid
        make_case(self.repo, "pulse-x", rubrics=("qa-lead",), caught_at="qa-lead")
        self.projs = [("proj", self.repo)]

    def keys(self, items):
        return sorted((c["id"], s) for _n, _r, c, s in items)

    def test_default_leaves_out_not_catchable_and_invalid(self):
        items, bad = bench.items_for(self.projs)
        self.assertEqual(self.keys(items), [("bug-a", "code-reviewer"), ("bug-a", "qa-lead"), ("pulse-x", "qa-lead")])
        self.assertEqual([(n, cid) for n, cid, _p in bad], [("proj", "bug-c")])
        self.assertTrue(any("ticket.md" in p for p in bad[0][2]))

    def test_all_cases_includes_not_catchable(self):
        items, _bad = bench.items_for(self.projs, all_cases=True)
        self.assertIn(("bug-b", "qa-lead"), self.keys(items))

    def test_stage_filter(self):
        items, _bad = bench.items_for(self.projs, stage="code-reviewer")
        self.assertEqual(self.keys(items), [("bug-a", "code-reviewer")])
        items, _bad = bench.items_for(self.projs, stage="review-spec")
        self.assertEqual(items, [])

    def test_case_glob(self):
        items, bad = bench.items_for(self.projs, case_glob="pulse-*")
        self.assertEqual(self.keys(items), [("pulse-x", "qa-lead")])
        self.assertEqual(bad, [])  # the invalid case does not match the glob

    def test_invalid_case_is_skipped_not_run_even_with_glob(self):
        items, bad = bench.items_for(self.projs, case_glob="bug-c")
        self.assertEqual(items, [])
        self.assertEqual([cid for _n, cid, _p in bad], ["bug-c"])

    def test_item_shape(self):
        items, _bad = bench.items_for(self.projs, case_glob="pulse-x")
        name, repo, c, stage = items[0]
        self.assertEqual((name, repo, stage), ("proj", self.repo, "qa-lead"))
        self.assertIn("qa-lead", c["stages"])


class GitFixture(Tmp):
    """A throwaway repo: A (project layer, src/a.js), B introduced (a.js changed, new.js added), C fixed (a.js
    changed again, lessons.md added)."""

    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp(prefix="pf-bench-git-")
        cls.repo = os.path.join(cls.root, "repo")
        os.makedirs(cls.repo)

        def g(*args):
            p = subprocess.run(["git"] + GIT_ID + ["-C", cls.repo] + list(args), capture_output=True, timeout=60)
            assert p.returncode == 0, p.stderr.decode("utf-8", "replace")
            return p.stdout.decode("utf-8", "replace").strip()
        g("init", "-q")
        write(os.path.join(cls.repo, ".claude", "project.json"), json.dumps({"work_dir": "wk/tasks"}))
        write(os.path.join(cls.repo, ".claude", "review", "checklist.md"), "- check things\n")
        write(os.path.join(cls.repo, "src", "a.js"), "const icon = 'one';\n")
        g("add", "-A")
        g("commit", "-q", "-m", "A")
        cls.A = g("rev-parse", "HEAD")
        write(os.path.join(cls.repo, "src", "a.js"), "const icon = 'two';\n")
        write(os.path.join(cls.repo, "src", "new.js"), "const n = 1;\n")
        g("add", "-A")
        g("commit", "-q", "-m", "B introduced")
        cls.B = g("rev-parse", "HEAD")
        write(os.path.join(cls.repo, "src", "a.js"), "const icon = 'three';\n")
        write(os.path.join(cls.repo, ".claude", "review", "lessons.md"), "- never use the wrong icon\n")
        g("add", "-A")
        g("commit", "-q", "-m", "C fixed")
        cls.C = g("rev-parse", "HEAD")
        cls.case = {"id": "bug-a", "introduced": cls.B, "fixed": cls.C, "caught_at": "code-reviewer",
                    "files": ["src/a.js", "src/new.js", "src/gone.js"]}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def setUp(self):
        super().setUp()
        self.case_dir = os.path.join(self.tmp, "case")
        write(os.path.join(self.case_dir, "ticket.md"), "TICKET TEXT\n")
        self.plugin = fake_plugin(self.tmp)

    def script(self, stage, case=None):
        return bench.scaffold(self.repo, case or self.case, stage, self.case_dir, self.plugin, "/usr/bin/python3")


class Scaffold(GitFixture):
    def archive_lines(self, script):
        return [ln for ln in script.splitlines() if " archive " in ln]

    def test_code_archived_at_introducing_commit(self):
        script, _work = self.script("qa-lead")
        code, layer = self.archive_lines(script)
        self.assertIn("archive '%s' -- 'src/a.js' 'src/new.js' | tar -x" % self.B, code)

    def test_review_spec_code_is_the_commit_before(self):
        script, _work = self.script("review-spec")
        code = self.archive_lines(script)[0]
        self.assertIn("archive '%s~1' -- 'src/a.js' | tar -x" % self.B, code)

    def test_path_missing_at_the_revision_is_left_out(self):
        script, _ = self.script("qa-lead")
        self.assertNotIn("gone.js' |", script.split("tar -x")[0])
        self.assertNotIn("'src/gone.js' | tar", script)
        spec, _ = self.script("review-spec")
        self.assertNotIn("new.js' | tar", spec)  # added by the introducing commit itself

    def test_layer_from_just_before_the_fix(self):
        script, _ = self.script("qa-lead")
        layer = self.archive_lines(script)[1]
        self.assertIn("archive '%s~1' --" % self.C, layer)
        self.assertNotIn("archive '%s' --" % self.C, script)
        self.assertIn("'.claude/project.json'", layer)
        self.assertIn("'.claude/review'", layer)
        self.assertNotIn("AGENTS.md", layer)  # not in the repo at that revision

    def test_layer_falls_back_to_introducing_commit_and_honours_override(self):
        no_parent = dict(self.case, fixed=self.A)  # A~1 does not exist
        script, _ = self.script("qa-lead", no_parent)
        self.assertIn("archive '%s' -- '.claude/project.json'" % self.B, script)
        pinned = dict(self.case, layer_rev=self.A)
        script, _ = self.script("qa-lead", pinned)
        self.assertIn("archive '%s' -- '.claude/project.json'" % self.A, script)

    def test_work_dir_from_project_json(self):
        script, work = self.script("qa-lead")
        self.assertEqual(work, "wk/tasks")
        self.assertIn("mkdir -p 'wk/tasks/bench-1'", script)

    def test_work_dir_default_when_project_json_has_none(self):
        self.assertEqual(bench.work_dir_at(self.repo, "%s~1" % self.A), ".claude/work")  # no such revision
        self.assertEqual(bench.work_dir_at(self.repo, self.B), "wk/tasks")

    def test_code_reviewer_runs_review_pack(self):
        script, _ = self.script("code-reviewer")
        line = [ln for ln in script.splitlines() if "review_pack.py" in ln][0]
        self.assertIn("'/usr/bin/python3'", line)
        self.assertIn("review_pack.py' bench-1 --root \"$REPO\"", line)
        self.assertIn("--base '%s~1' --head '%s'" % (self.B, self.B), line)
        self.assertIn("--files 'src/a.js' 'src/new.js' 'src/gone.js'", line)  # the case's own list
        self.assertIn("test -s 'wk/tasks/bench-1/review-pack.md'", script)
        self.assertNotIn("change.diff", script)
        self.assertNotIn("ticket.md", script)

    def test_qa_lead_copies_ticket_and_writes_diff(self):
        script, _ = self.script("qa-lead")
        self.assertRegex(script, r"cp '[^']*/case/ticket\.md' 'wk/tasks/bench-1/ticket\.md'")
        self.assertIn("git -C \"$REPO\" diff '%s~1' '%s' -- 'src/a.js' 'src/new.js' 'src/gone.js' > "
                      "'wk/tasks/bench-1/change.diff'" % (self.B, self.B), script)

    def test_review_spec_copies_ticket_only(self):
        script, _ = self.script("review-spec")
        self.assertIn("ticket.md' 'wk/tasks/bench-1/ticket.md'", script)
        self.assertNotIn("change.diff", script)
        self.assertNotIn("review_pack", script)

    def test_every_path_is_single_quoted(self):
        for stage in bench.STAGES:
            script, _ = self.script(stage)
            self.assertTrue(script.startswith("#!/usr/bin/env bash\n"))
            self.assertIn("set -euo pipefail", script)
            for ln in script.splitlines()[1:]:
                if ln.startswith(("#", "set ")):
                    continue
                if ln.startswith("REPO="):
                    self.assertRegex(ln, r"^REPO='[^']+'$")
                elif " archive " in ln:
                    self.assertRegex(ln, r"^git -C \"\$REPO\" archive '[^']+' -- ('[^']+' ?)+ \| tar -x$")
                elif ln.startswith("mkdir"):
                    self.assertRegex(ln, r"^mkdir -p '[^']+'$")
                elif ln.startswith("cp "):
                    self.assertRegex(ln, r"^cp '[^']+' '[^']+'$")
                elif ln.startswith("test -s"):
                    self.assertRegex(ln, r"^test -s '[^']+'$")
                elif " diff " in ln:
                    self.assertRegex(ln, r"-- ('[^']+' ?)+ > '[^']+'$")
                elif "review_pack.py" in ln:
                    self.assertRegex(ln, r"^CLAUDE_PROJECT_DIR=\"\$PWD\" PYTHONDONTWRITEBYTECODE=1 '[^']+' '[^']+' "
                                         r"bench-1 --root \"\$REPO\" --base '[^']+' --head '[^']+' --files ('[^']+' ?)+"
                                         r" > /dev/null$")
                else:
                    self.fail("unexpected line in %s script: %s" % (stage, ln))

    def test_sq_escapes_a_quote_and_slash_turns_backslashes(self):
        self.assertEqual(bench.sq("it's"), "'it'\\''s'")
        self.assertEqual(bench.sq("a b"), "'a b'")
        self.assertNotIn("\\", bench.slash(os.path.join(self.tmp, "x")))

    def bash_works(self):
        """bash and tar on PATH, and that bash understands this machine's temp paths (not a WSL bash)."""
        if not (shutil.which("bash") and shutil.which("tar")):
            return False
        probe = bench.slash(self.tmp)
        try:
            p = subprocess.run(["bash", "-c", "test -d %s && tar --version > /dev/null" % bench.sq(probe)],
                               capture_output=True, timeout=60)
        except (OSError, subprocess.SubprocessError):
            return False
        return p.returncode == 0

    def run_scaffold(self, stage, ws_name):
        script, work = self.script(stage)
        path = os.path.join(self.tmp, "scaffold-%s.sh" % stage)
        write(path, script)
        ws = os.path.join(self.tmp, ws_name)
        os.makedirs(ws)
        p = subprocess.run(["bash", bench.slash(path)], cwd=ws, capture_output=True, timeout=120)
        self.assertEqual(p.returncode, 0, p.stderr.decode("utf-8", "replace"))
        return ws, work

    def test_qa_lead_scaffold_builds_the_workspace(self):
        if not self.bash_works():
            self.skipTest("no usable bash and tar on PATH")
        ws, work = self.run_scaffold("qa-lead", "ws-qa")
        task = os.path.join(ws, work, "bench-1")
        self.assertEqual(slurp(os.path.join(task, "ticket.md")), "TICKET TEXT\n")
        diff = slurp(os.path.join(task, "change.diff"))
        self.assertTrue(diff.strip())
        self.assertIn("-const icon = 'one';", diff)
        self.assertIn("+const icon = 'two';", diff)
        self.assertEqual(slurp(os.path.join(ws, "src", "a.js")), "const icon = 'two';\n")  # code at B, not C
        self.assertTrue(os.path.isfile(os.path.join(ws, "src", "new.js")))
        self.assertTrue(os.path.isfile(os.path.join(ws, ".claude", "project.json")))
        self.assertTrue(os.path.isfile(os.path.join(ws, ".claude", "review", "checklist.md")))
        self.assertFalse(os.path.exists(os.path.join(ws, ".claude", "review", "lessons.md")))  # added by the fix

    def test_review_spec_scaffold_has_code_before_the_change(self):
        if not self.bash_works():
            self.skipTest("no usable bash and tar on PATH")
        ws, work = self.run_scaffold("review-spec", "ws-spec")
        self.assertEqual(slurp(os.path.join(ws, "src", "a.js")), "const icon = 'one';\n")
        self.assertFalse(os.path.exists(os.path.join(ws, "src", "new.js")))
        self.assertTrue(os.path.isfile(os.path.join(ws, work, "bench-1", "ticket.md")))
        self.assertFalse(os.path.exists(os.path.join(ws, work, "bench-1", "change.diff")))


class StageSuite(GitFixture):
    CANARY = "zz-leak-canary"
    BUG_TEXT = "BUGREPORT-SECRET-SENTENCE about the wrong icon"

    def build(self):
        self.proj_repo = os.path.join(self.tmp, "proj")
        d = make_case(self.proj_repo, self.CANARY, rubrics=("review-spec", "code-reviewer", "qa-lead"),
                      introduced=self.B, fixed=self.C, files=["src/a.js"])
        write(os.path.join(d, "bug-report.md"), self.BUG_TEXT + "\n")
        self.items, bad = bench.items_for([("proj", self.proj_repo)])
        self.assertEqual(bad, [])
        # the scaffold reads the fixture git repo
        self.items = [("proj", self.repo, c, s) for _n, _r, c, s in self.items]
        self.root = os.path.join(self.tmp, "stage-root")
        os.makedirs(self.root)
        return bench.stage_suite(self.root, self.plugin, self.items, "/usr/bin/python3")

    def test_suite_has_no_hooks_and_no_old_evals(self):
        suite = self.build()
        self.assertFalse(os.path.exists(os.path.join(suite, "hooks")))
        self.assertTrue(os.path.isfile(os.path.join(suite, "agents", "x.md")))
        self.assertTrue(os.path.isfile(os.path.join(suite, "scripts", "review_pack.py")))
        self.assertFalse(os.path.exists(os.path.join(suite, "evals", "old")))
        manifest = json.loads(slurp(os.path.join(suite, ".claude-plugin", "plugin.json")))
        self.assertNotIn("hooks", manifest)
        self.assertEqual(manifest["version"], "9.9.9")
        # the plugin under test is not changed
        self.assertTrue(os.path.isfile(os.path.join(self.plugin, "hooks", "hooks.json")))
        self.assertIn("hooks", json.loads(slurp(os.path.join(self.plugin, ".claude-plugin", "plugin.json"))))

    def test_one_eval_per_item_with_the_files(self):
        suite = self.build()
        names = sorted(os.listdir(os.path.join(suite, "evals")))
        self.assertEqual(names, sorted("proj--%s--%s" % (self.CANARY, s) for s in bench.STAGES))
        for n in names:
            d = os.path.join(suite, "evals", n)
            yaml = slurp(os.path.join(d, "case.yaml"))
            self.assertIn("name: %s" % n, yaml)
            self.assertIn("scaffold_script: scaffold.sh", yaml)
            for f in ("scaffold.sh", "ticket.md", "prompt.md", os.path.join("graders", "caught.md"),
                      os.path.join("graders", "agent-ran.md")):
                self.assertTrue(os.path.isfile(os.path.join(d, f)), "%s/%s" % (n, f))
            self.assertFalse(os.path.exists(os.path.join(d, "bug-report.md")))

    def test_prompt_names_the_agent_and_leaks_nothing(self):
        suite = self.build()
        for stage, agent in bench.STAGES.items():
            d = os.path.join(suite, "evals", "proj--%s--%s" % (self.CANARY, stage))
            prompt = slurp(os.path.join(d, "prompt.md"))
            head, body = prompt.split("---\n")[1:3]
            tools = re.search(r"^allowed_tools: \[(.*)\]$", head, re.M).group(1).split(", ")
            self.assertEqual(tools, ["Read", "Glob", "Grep", "Agent"])
            for banned in ("Bash", "Write", "Edit"):
                self.assertNotIn(banned, tools)
            self.assertIn("product-factory:%s" % agent, body)
            self.assertIn("bench-1", body)
            self.assertNotIn(self.CANARY, prompt)
            self.assertNotIn("BUGREPORT", prompt)
            self.assertNotIn(self.BUG_TEXT, prompt)
            self.assertIn("wk/tasks/bench-1", body)  # the work dir from the project layer

    def test_graders(self):
        suite = self.build()
        for stage, agent in bench.STAGES.items():
            d = os.path.join(suite, "evals", "proj--%s--%s" % (self.CANARY, stage), "graders")
            caught = slurp(os.path.join(d, "caught.md"))
            self.assertTrue(caught.startswith("---\ntype: llm\n---\n"))
            self.assertIn("PASS if a finding names the icon.", caught)
            ran = slurp(os.path.join(d, "agent-ran.md"))
            self.assertIn("type: tool_used", ran)
            self.assertIn("tool: Agent", ran)
            self.assertIn("input_match: 'product-factory:%s'" % agent, ran)

    def test_scaffold_points_at_the_suite_copy_of_the_review_pack_script(self):
        suite = self.build()
        d = os.path.join(suite, "evals", "proj--%s--code-reviewer" % self.CANARY)
        sh = slurp(os.path.join(d, "scaffold.sh"))
        self.assertIn(bench.slash(os.path.join(suite, "scripts", "review_pack.py")), sh)
        self.assertIn(bench.slash(self.repo), sh)


class Summarize(Tmp):
    def setUp(self):
        super().setUp()
        self.replies = os.path.join(self.tmp, "replies")

    def items(self, *ids):
        return [("proj", self.tmp, {"id": i, "caught_at": "code-reviewer"}, "code-reviewer") for i in ids]

    @staticmethod
    def run_of(ran=True, caught=True, trace="", cost=0.5):
        gs = [{"name": "agent-ran", "passed": ran}, {"name": "caught", "passed": caught}]
        return {"graders": gs, "tracePath": trace, "costUsd": cost, "judgeCostUsd": 0.1}

    @staticmethod
    def agg(**by_case):
        return {"cases": [{"name": "proj--%s--code-reviewer" % k, "arms": {"with": v}} for k, v in by_case.items()]}

    def test_verdicts(self):
        r = self.run_of
        agg = self.agg(**{"two": [r(), r(), r(caught=False)], "one": [r(caught=False), r(), r(caught=False)],
                          "none": [r(caught=False)] * 3, "all": [r()] * 3})
        rows = {x["case"]: x for x in bench.summarize(agg, self.items("two", "one", "none", "all"), self.replies)}
        self.assertEqual((rows["two"]["verdict"], rows["two"]["passed"], rows["two"]["runs"]), ("caught", 2, 3))
        self.assertEqual((rows["one"]["verdict"], rows["one"]["passed"]), ("missed", 1))
        self.assertEqual(rows["none"]["verdict"], "missed")
        self.assertEqual(rows["all"]["verdict"], "caught")
        self.assertEqual(rows["two"]["agent"], "code-reviewer")
        self.assertEqual(rows["two"]["caught_at"], "code-reviewer")
        self.assertEqual(rows["two"]["cost_usd"], 1.8)  # 3 x (0.5 + 0.1)

    def test_agent_that_did_not_run_is_invalid_not_a_catch(self):
        r = self.run_of
        # the judge said "caught" on the run where the agent never started: that must not count
        agg = self.agg(inv=[r(), r(ran=False, caught=True), r(caught=False)])
        row = bench.summarize(agg, self.items("inv"), self.replies)[0]
        self.assertEqual((row["passed"], row["invalid"], row["runs"]), (1, 1, 3))
        self.assertEqual(row["verdict"], "missed")  # 1 of 2 valid runs

    def test_invalid_runs_are_left_out_of_the_vote(self):
        r = self.run_of
        agg = self.agg(inv=[r(), r(), r(ran=False, caught=False)])
        row = bench.summarize(agg, self.items("inv"), self.replies)[0]
        self.assertEqual((row["passed"], row["invalid"], row["verdict"]), (2, 1, "caught"))

    def test_run_with_an_error_and_no_graders_is_invalid(self):
        agg = self.agg(err=[{"error": "boom"}, {"error": "boom"}])
        row = bench.summarize(agg, self.items("err"), self.replies)[0]
        self.assertEqual((row["invalid"], row["verdict"]), (2, "not run"))
        text = slurp(os.path.join(self.replies, "proj--err--code-reviewer--1.md"))
        self.assertIn("(no reply: boom)", text)

    def test_item_with_no_runs_is_not_run(self):
        row = bench.summarize({"cases": []}, self.items("ghost"), self.replies)[0]
        self.assertEqual((row["runs"], row["verdict"], row["cost_usd"]), (0, "not run", 0))

    def test_reply_is_the_last_assistant_text(self):
        trace = os.path.join(self.tmp, "trace.jsonl")
        lines = [{"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "prompt"}]}},
                 {"type": "assistant", "message": {"content": [{"type": "text", "text": "first answer"}]}},
                 "not json at all",
                 {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Agent", "input": {}}]}},
                 {"type": "assistant", "message": {"content": [{"type": "text", "text": "   "}]}},
                 {"type": "assistant", "message": {"content": [{"type": "text", "text": "final answer"}]}},
                 {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "later user"}]}}]
        write(trace, "\n".join(x if isinstance(x, str) else json.dumps(x) for x in lines) + "\n")
        self.assertEqual(bench.final_reply(trace), "final answer")
        self.assertEqual(bench.final_reply(os.path.join(self.tmp, "none.jsonl")), "")
        r = self.run_of(trace=trace)
        agg = self.agg(rep=[r, self.run_of(caught=False)])
        bench.summarize(agg, self.items("rep"), self.replies)
        first = slurp(os.path.join(self.replies, "proj--rep--code-reviewer--1.md"))
        self.assertTrue(first.startswith("# proj--rep--code-reviewer run 1: caught"))
        self.assertIn("final answer", first)
        self.assertNotIn("first answer", first)
        second = slurp(os.path.join(self.replies, "proj--rep--code-reviewer--2.md"))
        self.assertIn("run 2: missed", second)
        self.assertIn("(no reply: ?)", second)

    def test_verdict_function(self):
        self.assertEqual(bench.verdict(0, 0), "not run")
        self.assertEqual(bench.verdict(2, 3), "caught")
        self.assertEqual(bench.verdict(1, 2), "missed")
        self.assertEqual(bench.verdict(1, 3), "missed")
        self.assertEqual(bench.verdict(1, 1), "caught")


def row(case, stage, caught_at, verdict, passed=2, runs=3, invalid=0):
    return {"case": case, "stage": stage, "caught_at": caught_at, "verdict": verdict, "passed": passed,
            "runs": runs, "invalid": invalid, "agent": bench.STAGES[stage], "project": "proj", "cost_usd": 1.0}


class Report(unittest.TestCase):
    def setUp(self):
        self.rows = [row("a", "code-reviewer", "code-reviewer", "caught"),
                     row("b", "code-reviewer", "qa-lead", "missed", passed=0),
                     row("c", "qa-lead", "qa-lead", "missed", passed=1),
                     row("d", "qa-lead", "qa-lead", "not run", passed=0, runs=3, invalid=3)]
        self.cur = {"stamp": "2026-11-13-1000", "plugin_version": "1.2.3", "runs": 3, "cost_usd": 4.5, "results": self.rows}

    def test_expected_total_counts_only_the_expected_stage(self):
        self.assertEqual(bench.expected_total(self.rows), [1, 2])  # a caught, c missed; b is another stage; d not run
        self.assertEqual(bench.expected_total([]), [0, 0])
        self.assertEqual(bench.expected_total(iter(self.rows)), [1, 2])

    def test_rates_leave_out_not_run(self):
        self.assertEqual(bench.rates(self.rows, "stage"), {"code-reviewer": [1, 2], "qa-lead": [0, 1]})

    def test_pct(self):
        self.assertEqual(bench.pct([1, 3]), "1/3 (33%)")
        self.assertEqual(bench.pct([0, 0]), "-")
        self.assertEqual(bench.pct(None), "-")

    def test_report_without_history(self):
        out = bench.render_report("proj", self.cur, None)
        self.assertIn("### proj: bench 2026-11-13-1000 (plugin 1.2.3, 3 runs each, $4.50)", out)
        self.assertNotIn("Compared with", out)
        self.assertIn("| code-reviewer (code-reviewer) | 1/2 (50%) | - |", out)
        self.assertIn("| qa-lead (qa-lead) | 0/1 (0%) | - |", out)
        self.assertNotIn("review-spec (spec-analyst)", out)
        self.assertIn("| at the stage where it should have been caught | 1/2 (50%) | - |", out)
        self.assertIn("| a | code-reviewer (expected) | 2/3 | caught | - |", out)
        self.assertIn("| b | code-reviewer | 0/3 | missed | - |", out)
        self.assertIn("| d | qa-lead (expected) | 0/3, 3 invalid | not run | - |", out)
        self.assertNotIn("<- changed", out)

    def test_report_against_previous_marks_changes(self):
        prev = {"stamp": "2026-10-01-0900", "plugin_version": "1.1.0",
                "results": [row("a", "code-reviewer", "code-reviewer", "missed", passed=0),
                            row("b", "code-reviewer", "qa-lead", "missed", passed=0),
                            row("c", "qa-lead", "qa-lead", "missed", passed=0)]}
        out = bench.render_report("proj", self.cur, prev)
        self.assertIn("Compared with 2026-10-01-0900 (plugin 1.1.0).", out)
        self.assertIn("| a | code-reviewer (expected) | 2/3 | caught | missed <- changed |", out)
        self.assertIn("| b | code-reviewer | 0/3 | missed | missed |", out)
        self.assertIn("| c | qa-lead (expected) | 1/3 | missed | missed |", out)
        self.assertIn("| code-reviewer (code-reviewer) | 1/2 (50%) | 0/2 (0%) |", out)
        self.assertIn("| at the stage where it should have been caught | 1/2 (50%) | 0/2 (0%) |", out)
        self.assertEqual(out.count("<- changed"), 1)  # only a; d is new (no previous row), b and c are the same

    def test_partial_run_is_marked(self):
        out = bench.render_report("proj", dict(self.cur, partial=True), None)
        self.assertIn("$4.50, PARTIAL)", out)


class PaidAuth(unittest.TestCase):
    """paid_auth(cli, env): '' only for a claude.ai sign-in with no pay-per-call variable set. subprocess.run is
    patched, so no real claude CLI is started."""

    @staticmethod
    def cli_prints(text, returncode=0):
        return mock.patch.object(bench.subprocess, "run", return_value=subprocess.CompletedProcess(
            ["claude"], returncode, stdout=text.encode("utf-8"), stderr=b""))

    def test_each_paid_variable_gives_a_reason_naming_it_without_calling_the_cli(self):
        self.assertEqual(set(bench.PAID_ENV), {"ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_USE_BEDROCK",
                                               "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY"})
        for name in bench.PAID_ENV:
            with self.subTest(name=name), mock.patch.object(bench.subprocess, "run") as run:
                why = bench.paid_auth("claude", {name: "1"})
                self.assertIn(name, why)
                self.assertIn("pay per call", why)
                run.assert_not_called()

    def test_empty_paid_variable_is_not_set(self):
        with self.cli_prints('{"loggedIn": true, "authMethod": "claude.ai"}'):
            self.assertEqual(bench.paid_auth("claude", {n: "" for n in bench.PAID_ENV}), "")

    def test_not_logged_in(self):
        with self.cli_prints('{"loggedIn": false}'):
            why = bench.paid_auth("claude", {})
        self.assertIn("not signed in", why)

    def test_other_auth_method_is_named(self):
        for method in ("api_key", "oauth_token", "bedrock"):
            with self.subTest(method=method), self.cli_prints(json.dumps({"loggedIn": True, "authMethod": method})):
                why = bench.paid_auth("claude", {})
                self.assertIn(method, why)
                self.assertIn("not a claude.ai subscription", why)

    def test_logged_in_without_a_method_is_refused(self):
        with self.cli_prints('{"loggedIn": true}'):
            self.assertIn("not a claude.ai subscription", bench.paid_auth("claude", {}))

    def test_claude_ai_subscription_is_allowed(self):
        with self.cli_prints('{"loggedIn": true, "authMethod": "claude.ai"}') as run:
            self.assertEqual(bench.paid_auth("claude", {"PATH": "x"}), "")
        self.assertEqual(run.call_args[0][0], ["claude", "auth", "status"])

    def test_cli_that_prints_non_json_could_not_be_read(self):
        with self.cli_prints("Error: something broke"):
            self.assertIn("could not read", bench.paid_auth("claude", {}))

    def test_cli_that_fails_to_start_or_times_out_could_not_be_read(self):
        for exc in (OSError("no such file"), subprocess.TimeoutExpired("claude", 60)):
            with self.subTest(exc=type(exc).__name__), mock.patch.object(bench.subprocess, "run", side_effect=exc):
                self.assertIn("could not read", bench.paid_auth("claude", {}))

    def test_a_real_fake_cli_script(self):
        """End to end through a real process: a python script as the CLI (no patching of subprocess)."""
        tmp = tempfile.mkdtemp(prefix="pf-bench-test-")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        script = os.path.join(tmp, "fake_claude.py")
        write(script, "import sys\nprint('{\"loggedIn\": true, \"authMethod\": \"claude.ai\"}' "
                      "if sys.argv[1:] == ['auth', 'status'] else 'bad')\n")
        if os.name == "nt":
            cli = os.path.join(tmp, "claude.cmd")
            write(cli, '@"%s" "%s" %%*\r\n' % (sys.executable, script))
        else:
            cli = os.path.join(tmp, "claude")
            write(cli, '#!/bin/sh\nexec "%s" "%s" "$@"\n' % (sys.executable, script))
            os.chmod(cli, 0o755)
        clean = {k: v for k, v in os.environ.items() if k not in bench.PAID_ENV}
        self.assertEqual(bench.paid_auth(cli, clean), "")


class Main(Tmp):
    def run_main(self, argv, env=None):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, env or {}), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = bench.main(argv)
        return rc, out.getvalue(), err.getvalue()

    def product_repo(self):
        repo = os.path.join(self.tmp, "product")
        os.makedirs(os.path.join(repo, ".claude", "core"))
        make_case(repo, "bug-a", rubrics=("code-reviewer",))
        return repo

    def env(self, repo):
        e = {"CLAUDE_PROJECT_DIR": repo, "CLAUDE_CONFIG_DIR": os.path.join(self.tmp, "claude-home")}
        return e

    def test_run_without_max_cost_is_a_usage_error(self):
        repo = self.product_repo()
        rc, out, err = self.run_main(["run", "--dry-run"], self.env(repo))
        self.assertEqual(rc, 2)
        self.assertIn("--max-cost-usd is required", err)
        self.assertFalse(os.path.exists(os.path.join(repo, bench.HISTORY_DIR)))

    def test_run_with_zero_cost_is_a_usage_error(self):
        rc, _out, err = self.run_main(["run", "--max-cost-usd", "0"], self.env(self.product_repo()))
        self.assertEqual(rc, 2)
        self.assertIn("--max-cost-usd is required", err)

    def test_jobs_and_runs_ranges(self):
        env = self.env(self.product_repo())
        self.assertEqual(self.run_main(["run", "--max-cost-usd", "5", "-j", "9"], env)[0], 2)
        self.assertEqual(self.run_main(["run", "--max-cost-usd", "5", "--runs", "0"], env)[0], 2)

    def test_dry_run_prints_projected_cost_and_writes_nothing_in_the_repo(self):
        repo = self.product_repo()
        plugin = fake_plugin(self.tmp)
        work = os.path.join(self.tmp, "work")
        os.makedirs(work)
        before = sorted(os.path.join(t, n) for t, _d, ns in os.walk(repo) for n in ns)
        rc, out, err = self.run_main(["run", "--dry-run", "--plugin", plugin, "--max-cost-usd", "5", "--work", work],
                                     self.env(repo))
        self.assertEqual(rc, 0, out + err)
        self.assertIn("bench: 1 case-stages x 3 runs = 3 runs, plugin product-factory 9.9.9; "
                      "projected usage about $2.25 at list price (subscription tokens, not a bill), "
                      "ceiling $5.00", out)
        self.assertIn("dry run: suite staged in", out)
        self.assertIn("plugin eval", out)
        self.assertIn("--max-cost-usd 5.0", out)
        self.assertFalse(os.path.exists(os.path.join(repo, bench.HISTORY_DIR)))
        self.assertFalse(os.path.exists(os.path.join(repo, bench.RUNS_DIR)))
        self.assertEqual(sorted(os.path.join(t, n) for t, _d, ns in os.walk(repo) for n in ns), before)
        staged = [d for d in os.listdir(work) if d.startswith("pf-bench-")]
        self.assertEqual(len(staged), 1)
        evals = os.listdir(os.path.join(work, staged[0], "suite", "evals"))
        self.assertEqual(len(evals), 1)
        self.assertTrue(evals[0].endswith("--bug-a--code-reviewer"))

    def test_dry_run_projection_uses_the_latest_history(self):
        repo = self.product_repo()
        write(os.path.join(repo, bench.HISTORY_DIR, "2026-10-01-0900.json"),
              json.dumps({"results": [row("bug-a", "code-reviewer", "code-reviewer", "caught", runs=3)]}))
        plugin = fake_plugin(self.tmp)
        work = os.path.join(self.tmp, "work")
        os.makedirs(work)
        rc, out, err = self.run_main(["run", "--dry-run", "--plugin", plugin, "--max-cost-usd", "5", "--work", work],
                                     self.env(repo))
        self.assertEqual(rc, 0, out + err)
        self.assertIn("projected usage about $1.00 at list price", out)  # 1.0 cost / 3 runs x 3 runs

    def test_run_with_a_paid_api_key_is_refused_before_any_eval_starts(self):
        repo = self.product_repo()
        plugin = fake_plugin(self.tmp)
        work = os.path.join(self.tmp, "work")
        os.makedirs(work)
        real_popen = subprocess.Popen
        started = []

        def popen(args, *a, **kw):  # subprocess.run uses Popen too: git for staging is fine, the CLI is not
            if args and args[0] == "claude-fake":
                started.append(args)
                raise AssertionError("the claude CLI was started (auth status or eval) with a paid key set")
            return real_popen(args, *a, **kw)
        with mock.patch.object(bench.doctor, "find_cli", return_value="claude-fake"), \
                mock.patch.object(bench.subprocess, "Popen", side_effect=popen):
            rc, out, err = self.run_main(["run", "--plugin", plugin, "--max-cost-usd", "5", "--work", work],
                                         dict(self.env(repo), ANTHROPIC_API_KEY="sk-test-not-real"))
        self.assertEqual(rc, 2, out + err)
        self.assertIn("never real money", out + err)
        self.assertIn("ANTHROPIC_API_KEY", out + err)
        self.assertEqual(started, [])
        self.assertEqual(os.listdir(work), [])  # the staged suite is removed
        self.assertFalse(os.path.exists(os.path.join(repo, bench.HISTORY_DIR)))
        self.assertFalse(os.path.exists(os.path.join(repo, bench.RUNS_DIR)))

    def test_run_with_a_plugin_that_has_no_manifest_is_a_usage_error(self):
        repo = self.product_repo()
        rc, _out, err = self.run_main(["run", "--dry-run", "--plugin", self.tmp, "--max-cost-usd", "5"], self.env(repo))
        self.assertEqual(rc, 2)
        self.assertIn("no .claude-plugin/plugin.json", err)

    def test_run_with_nothing_to_run_is_a_usage_error(self):
        repo = self.product_repo()
        rc, _out, err = self.run_main(["run", "--max-cost-usd", "5", "--case", "nomatch-*"], self.env(repo))
        self.assertEqual(rc, 2)
        self.assertIn("nothing to run", err)

    def test_check_flags_an_invalid_case_and_cases_lists_it(self):
        repo = self.product_repo()
        make_case(repo, "bug-bad", ticket=None)
        env = self.env(repo)
        rc, out, _err = self.run_main(["check"], env)
        self.assertEqual(rc, 1)
        self.assertIn("FAIL", out)
        self.assertIn("ticket.md missing or empty", out)
        rc, out, _err = self.run_main(["cases"], env)
        self.assertEqual(rc, 0)
        self.assertIn("bug-bad", out)
        self.assertIn("(invalid:", out)


if __name__ == "__main__":
    unittest.main()
