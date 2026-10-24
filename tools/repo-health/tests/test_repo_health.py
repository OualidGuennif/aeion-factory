#!/usr/bin/env python3
"""Run the real health check in disposable repositories, including its Git error path."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "repo-health"


class RepoHealthTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.tool = self.root / "tools/repo-health/repo-health"
        self.tool.parent.mkdir(parents=True)
        shutil.copy(TOOL, self.tool)

    def check_health(self, *args):
        return subprocess.run([sys.executable, str(self.tool), *args], cwd=self.root,
                              capture_output=True, text=True, timeout=10)

    def test_non_repository_is_not_a_clean_scorecard(self):
        result = self.check_health("--json")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Git", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_valid_repository_produces_a_scorecard(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        result = self.check_health()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("repo-health:", result.stdout)


if __name__ == "__main__":
    unittest.main()
