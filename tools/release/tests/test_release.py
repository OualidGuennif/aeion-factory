#!/usr/bin/env python3
"""Run the real release tool on disposable plain folders (no git needed)."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "release"
HEAD = "# Changelog\n\n## [Unreleased]\n"


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def release(self, *args):
        return subprocess.run([sys.executable, str(TOOL), "--root", str(self.root), "--date", "2026-10-28", *args],
                              capture_output=True, text=True, timeout=10)

    def write(self, version, changelog):
        (self.root / "VERSION").write_text(version)
        (self.root / "CHANGELOG.md").write_text(changelog)

    def test_minor_release_dates_unreleased_and_keeps_history(self):
        self.write("1.2.0\n", HEAD + "\n### Added\n- Develop flow.\n\n## [1.2.0] - 2026-10-01\n\n- Old.\n")
        result = self.release("minor")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "VERSION").read_text(), "1.3.0\n")
        self.assertEqual((self.root / "CHANGELOG.md").read_text(),
                         HEAD + "\n## [1.3.0] - 2026-10-28\n\n### Added\n- Develop flow.\n\n## [1.2.0] - 2026-10-01\n\n- Old.\n")
        self.assertTrue(result.stdout.startswith("Release v1.3.0\n\n### Added\n- Develop flow."))
        notes = self.release("--notes", "1.3.0")
        self.assertEqual(notes.stdout, "### Added\n- Develop flow.\n")

    def test_major_and_patch_bumps(self):
        self.write("1.3.4\n", HEAD + "- Fix.\n")
        self.assertEqual(self.release("patch").returncode, 0)
        self.assertEqual((self.root / "VERSION").read_text(), "1.3.5\n")
        self.write("1.3.4\n", HEAD + "- Break.\n")
        self.assertEqual(self.release("major").returncode, 0)
        self.assertEqual((self.root / "VERSION").read_text(), "2.0.0\n")

    def test_refusals_change_nothing(self):
        self.write("1.2.0\n", HEAD + "\n## [1.2.0] - 2026-10-01\n\n- Old.\n")
        self.assertIn("no lines under", self.release("minor").stderr)
        self.assertEqual((self.root / "VERSION").read_text(), "1.2.0\n")
        self.write("v1.2\n", HEAD + "- Fix.\n")
        self.assertIn("not MAJOR.MINOR.PATCH", self.release("patch").stderr)
        self.assertEqual(self.release("--notes", "9.9.9").returncode, 1)


if __name__ == "__main__":
    unittest.main()
