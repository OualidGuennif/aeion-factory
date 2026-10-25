#!/usr/bin/env python3
"""Regression tests for real scope, diff, evidence and receipt refusal boundaries."""
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import sys
import time

SCRIPT = Path(__file__).resolve().parents[1] / "refresh"
sys.path.insert(0, str(SCRIPT.parent))
from process import run
loader = importlib.machinery.SourceFileLoader("refresh", str(SCRIPT))
spec = importlib.util.spec_from_loader("refresh", loader)
refresh = importlib.util.module_from_spec(spec)
loader.exec_module(refresh)


class RefreshTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        self.config = {"scope": ["*.md", "src/**"], "architecture_spec": "architecture.md"}
        self.write("architecture.md", "# Architecture\n")
        self.write("README.md", "# Read me\n")
        self.write("src/app.py", "def run():\n    return 1\n")
        self.base = self.commit()

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True, text=True).stdout.strip()

    def write(self, path, text):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text)

    def commit(self):
        self.git("add", ".")
        self.git("commit", "-qm", "test")
        return self.git("rev-parse", "HEAD")

    def test_scope_uses_committed_bytes_and_excludes_symlinks(self):
        (self.root / "alias.md").symlink_to(self.root / "README.md")
        target = self.commit()
        self.write("new.md", "not committed")
        manifest, excluded = refresh.scope(self.root, target, self.config)
        self.assertEqual({item["path"] for item in manifest}, {"README.md", "architecture.md", "src/app.py"})
        self.assertEqual(excluded, ["alias.md"])

    def test_tracked_secrets_refuse_analysis_before_clone(self):
        self.write(".env", "FAKE_TEST_VALUE=example\n")
        target = self.commit()
        with self.assertRaisesRegex(ValueError, "tracked secret"):
            refresh.scope(self.root, target, self.config)

    def test_changed_set_preserves_added_and_deleted_rename_sides(self):
        self.git("mv", "src/app.py", "src/renamed.py")
        target = self.commit()
        self.assertEqual(set(refresh.changed_paths(self.root, self.base, target)), {"src/app.py", "src/renamed.py"})

    def test_missing_ref_is_not_an_empty_change_set(self):
        with self.assertRaises(subprocess.CalledProcessError):
            refresh.changed_paths(self.root, "missing", self.base)

    def test_runtime_change_requires_updated_architecture(self):
        self.write("src/app.py", "def run():\n    return 2\n")
        target = self.commit()
        changed = refresh.changed_paths(self.root, self.base, target)
        with self.assertRaisesRegex(ValueError, "architecture spec"):
            refresh.spec_coverage(self.root, self.base, target, changed, self.config)
        self.write("architecture.md", "# Architecture\nThe return value is now 2.\n")
        target = self.commit()
        refresh.spec_coverage(self.root, self.base, target, refresh.changed_paths(self.root, self.base, target), self.config)

    def test_docs_only_change_does_not_demand_fictitious_architecture_edits(self):
        self.write("README.md", "# Read me\nMore explanation.\n")
        target = self.commit()
        refresh.spec_coverage(self.root, self.base, target, refresh.changed_paths(self.root, self.base, target), self.config)

    def test_evidence_anchors_resolve_against_exact_source_and_missing_is_refused(self):
        view = {"meta": {}, "components": [{"id": "app", "sources": [{"path": "src/app.py", "anchor": "def run():"}]}]}
        result = refresh.candidate(view, self.root, self.base, "https://github.com/example/example")
        self.assertEqual(result["components"][0]["sources"][0]["line"], 1)
        self.assertNotIn("line", view["components"][0]["sources"][0])
        self.write("src/app.py", "changed\n")
        with self.assertRaisesRegex(ValueError, "anchor"):
            refresh.candidate(view, self.root, self.base, "https://github.com/example/example")

    def test_external_evidence_path_is_refused(self):
        view = {"meta": {}, "components": [{"sources": [{"path": "../outside.py", "anchor": "anything"}]}]}
        with self.assertRaisesRegex(ValueError, "unsafe"):
            refresh.candidate(view, self.root, self.base, "https://github.com/example/example")

    def test_receipt_requires_all_named_artifacts_and_current_hashes(self):
        folder = self.root / "analysis"
        artifacts = {}
        required = ["graph/graph.json", "graph/coverage.json", "source-manifest.json"]
        required += [f"{name}.{suffix}" for name in ("architecture", "workflow", "lifecycle") for suffix in ("html", "json", "finalize-summary.json", "delivery.json")]
        for rel in required:
            payload = {"status": "pass", "gates": dict.fromkeys(("validate", "deliver", "check", "browser-check"), "pass")} if rel.endswith("finalize-summary.json") else {}
            self.write(f"analysis/{rel}", json.dumps(payload) + "\n")
            artifacts[rel] = refresh.digest(folder / rel)
        self.write("analysis/receipt.json", json.dumps({"schema_version": 2, "status": "PASS", "target": self.base,
                   "integrations": self.config, "artifacts": artifacts}))
        self.assertTrue(refresh.valid_receipt(folder, self.base, self.config))
        self.write("analysis/graph/graph.json", "tampered\n")
        self.assertFalse(refresh.valid_receipt(folder, self.base, self.config))
        self.assertFalse(refresh.valid_receipt(folder, "another-commit", self.config))

    def test_timed_out_integrations_cannot_leave_descendants_writing(self):
        marker = self.root / "late-write"
        child = f"import time; from pathlib import Path; time.sleep(0.5); Path({str(marker)!r}).touch()"
        parent = f"import subprocess,time,sys; subprocess.Popen([sys.executable,'-c',{child!r}]); time.sleep(5)"
        with self.assertRaises(subprocess.TimeoutExpired):
            run([sys.executable, "-c", parent], timeout=0.1)
        time.sleep(0.7)
        self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
