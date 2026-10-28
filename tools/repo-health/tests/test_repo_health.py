#!/usr/bin/env python3
"""Run the real health check in disposable repositories and plain folders."""
import shutil
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "repo-health"
FILES = Path(__file__).resolve().parents[3] / ".claude/hooks/project_files.py"


class RepoHealthTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.tool = self.root / "tools/repo-health/repo-health"
        self.tool.parent.mkdir(parents=True)
        shutil.copy(TOOL, self.tool)
        (self.root / ".claude/hooks").mkdir(parents=True)
        shutil.copy(FILES, self.root / ".claude/hooks/project_files.py")

    def check_health(self, *args):
        return subprocess.run([sys.executable, str(self.tool), *args], cwd=self.root,
                              capture_output=True, text=True, timeout=10)

    def test_plain_folder_is_walked_without_git(self):
        # Many users have no git: the caps still apply to the files on disk, dependencies excluded.
        (self.root / "big.py").write_text("value = 1\n" * 1501)
        (self.root / "node_modules").mkdir()
        (self.root / "node_modules/huge.js").write_text("x\n" * 5000)
        result = self.check_health("--json")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("big.py", result.stdout)
        self.assertNotIn("huge.js", result.stdout)

    def test_broken_repository_still_fails(self):
        (self.root / ".git").write_text("gitdir: /nonexistent\n")
        result = self.check_health("--json")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")

    def test_valid_repository_produces_a_scorecard(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        result = self.check_health()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("repo-health:", result.stdout)

    def test_accented_source_is_checked_against_the_size_cap(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        source = self.root / "café.py"
        source.write_text("value = 1\n" * 1501)
        subprocess.run(["git", "add", "café.py"], cwd=self.root, check=True)
        result = self.check_health("--json")
        self.assertEqual(result.returncode, 1)
        card = json.loads(result.stdout)
        self.assertEqual(card["files_over_1500_lines"], ["café.py"])
        self.assertEqual(card["source_files_checked"], 1)
        self.assertIn(".py", card["source_suffixes"])


    def test_extensionless_script_is_checked_and_plain_text_is_not(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.root / "refresh").write_text("#!/usr/bin/env python3\n" + "value = 1\n" * 1501)
        (self.root / "LICENSE").write_text("text\n" * 1501)
        subprocess.run(["git", "add", "refresh", "LICENSE"], cwd=self.root, check=True)
        result = self.check_health("--json")
        self.assertEqual(result.returncode, 1)
        card = json.loads(result.stdout)
        self.assertEqual(card["files_over_1500_lines"], ["refresh"])
        self.assertEqual(card["source_files_checked"], 1)


if __name__ == "__main__":
    unittest.main()
