#!/usr/bin/env python3
"""The owner's settings: the reader every hook shares, the tools/aeion-settings switch and the
session-start line, against a local stand-in for the aeion-framework readiness probe."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".claude/hooks"))
import aeion_settings as settings  # noqa: E402

CLI = ROOT / "tools/aeion-settings"
# Built by concatenation so the template's own code never carries an annotation.
ANNOTATION = "# " + "@req" + " CORE-001\n"


class Service:
    """A readiness probe that answers what a test sets, and remembers each request's headers."""

    def __init__(self):
        self.status, self.body, self.seen = 200, {"status": "ready", "version": settings.TESTED, "mode": "local"}, []
        service = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                service.seen.append((self.path, self.headers.get("Authorization")))
                raw = json.dumps(service.body).encode() if service.path_ok(self.path) else b"{}"
                self.send_response(service.status if service.path_ok(self.path) else 404)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    @staticmethod
    def path_ok(path):
        return path == "/health/ready"

    def close(self):
        self.server.shutdown()
        self.server.server_close()


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.service = Service()
        self.addCleanup(self.service.close)
        # The tests set the environment they need; the owner's own address never leaks in.
        clean = {k: v for k, v in os.environ.items() if k not in ("AEION_FRAMEWORK_URL", "AEION_FRAMEWORK_TOKEN")}
        patcher = patch.dict(os.environ, clean, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, text):
        (self.root / ".aeion").mkdir(exist_ok=True)
        (self.root / settings.SETTINGS).write_text(text, encoding="utf-8")

    def cli(self, *args, env=None):
        environment = {k: v for k, v in os.environ.items() if k not in ("AEION_FRAMEWORK_URL", "AEION_FRAMEWORK_TOKEN")}
        return subprocess.run([sys.executable, str(CLI), "--root", str(self.root), *args], capture_output=True, text=True,
                              stdin=subprocess.DEVNULL, env={**environment, **(env or {})}, timeout=30)

    # The reader.
    def test_a_missing_file_is_empty_and_valid(self):
        self.assertEqual(settings.load(self.root), ({}, None))
        self.assertEqual(settings.doc_gate(self.root), ("enforce", None))
        self.assertEqual(settings.framework(self.root), (None, None, None))

    def test_an_unreadable_file_fails_closed(self):
        for text in ("{", "[]", "\"warn\""):
            self.write(text)
            mode, problem = settings.doc_gate(self.root)
            self.assertEqual(mode, "enforce")
            self.assertIn(settings.SETTINGS, problem)
            url, _, problem = settings.framework(self.root)
            self.assertIsNone(url)
            self.assertIn("framework mode is off", problem)

    def test_the_gate_takes_only_its_three_modes(self):
        for mode in settings.GATES:
            self.write(json.dumps({"doc_gate": mode}))
            self.assertEqual(settings.doc_gate(self.root), (mode, None))
        for mode in ("OFF", "", None, 0, "disabled"):
            self.write(json.dumps({"doc_gate": mode}))
            gate, problem = settings.doc_gate(self.root)
            self.assertEqual(gate, "enforce", mode)
            self.assertIn("the gate enforces", problem)

    def test_an_address_is_an_http_url_without_secrets(self):
        for url in ("http://127.0.0.1:8787", "https://axiom.example.invalid/base", " http://h:1/ "):
            self.assertIsNone(settings.address_problem(url), url)
        for url in ("", " ", None, 7, "ftp://h", "h:8787", "http://", "http://u:p@h", "http://u@h", "http://h/?a=1",
                    "http://h/#x", "http://h/" + "a" * 2048, "file:///etc/hosts", "javascript:alert(1)"):
            self.assertIsNotNone(settings.address_problem(url), url)

    def test_the_address_is_the_switch(self):
        self.write(json.dumps({"framework": "http://127.0.0.1:8787/"}))
        self.assertEqual(settings.framework(self.root), ("http://127.0.0.1:8787", "file", None))
        self.write(json.dumps({"framework": "http://u:p@h"}))
        url, source, problem = settings.framework(self.root)
        self.assertEqual((url, source), (None, "file"))
        self.assertIn("credentials", problem)

    def test_the_environment_wins_over_the_file(self):
        self.write(json.dumps({"framework": "http://127.0.0.1:1"}))
        with patch.dict(os.environ, {"AEION_FRAMEWORK_URL": "http://10.0.0.2:8787/"}):
            self.assertEqual(settings.framework(self.root), ("http://10.0.0.2:8787", "env", None))
        with patch.dict(os.environ, {"AEION_FRAMEWORK_URL": "nope"}):
            url, source, problem = settings.framework(self.root)
            self.assertEqual((url, source), (None, "env"))
            self.assertIn("AEION_FRAMEWORK_URL", problem)

    def test_the_supported_range(self):
        for version in ("1.1.0", "1.1.9", "1.9.0", "1.1.9-rc1", "1.2"):
            self.assertTrue(settings.supported(version), version)
        for version in ("1.0.9", "0.3.0", "2.0.0", "10.1.0", "", "x", "1", None):
            self.assertFalse(settings.supported(version), version)

    # The readiness probe.
    def test_a_ready_supported_service(self):
        self.assertEqual(settings.health(self.service.url), (settings.TESTED, None))

    def test_a_service_that_is_not_ready_or_too_old_or_absent(self):
        self.service.status = 503
        self.assertIn("503", settings.health(self.service.url)[1])
        self.service.status, self.service.body = 200, {"status": "ready", "version": "1.0.4"}
        version, problem = settings.health(self.service.url)
        self.assertIsNone(version)
        self.assertIn(f"tested {settings.TESTED}", problem)
        self.service.body = ["not", "an", "object"]
        self.assertIsNone(settings.health(self.service.url)[0])
        version, problem = settings.health("http://127.0.0.1:9")
        self.assertIsNone(version)
        self.assertIn("unreachable", problem)

    def test_the_token_travels_only_in_the_header(self):
        settings.health(self.service.url)
        self.assertIsNone(self.service.seen[-1][1])
        with patch.dict(os.environ, {"AEION_FRAMEWORK_TOKEN": "t0ken"}):
            settings.health(self.service.url)
        self.assertEqual(self.service.seen[-1], ("/health/ready", "Bearer t0ken"))

    def test_the_probe_is_remembered_ten_minutes_per_address(self):
        self.assertEqual(settings.cached_health(self.root, self.service.url, now=1000), (settings.TESTED, None))
        self.assertEqual(settings.cached_health(self.root, self.service.url, now=1000 + settings.HEALTH_SECONDS - 1),
                         (settings.TESTED, None))
        self.assertEqual(len(self.service.seen), 1)
        settings.cached_health(self.root, self.service.url, now=1000 + settings.HEALTH_SECONDS)
        self.assertEqual(len(self.service.seen), 2)
        # Another address, or a clock that went back, asks again.
        settings.cached_health(self.root, self.service.url + "/", now=1000 + settings.HEALTH_SECONDS)
        settings.cached_health(self.root, self.service.url, now=10)
        self.assertEqual(len(self.service.seen), 4)
        (self.root / settings.HEALTH_CACHE).write_text("{", encoding="utf-8")
        self.assertEqual(settings.cached_health(self.root, self.service.url, now=1000), (settings.TESTED, None))

    # The @req hint.
    def test_annotations_are_found_in_code_only(self):
        for git in (False, True):
            with self.subTest(git=git), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                (root / "notes.md").write_text(ANNOTATION)
                (root / "skills/x").mkdir(parents=True)
                (root / "skills/x/run.py").write_text(ANNOTATION)
                (root / "src").mkdir()
                (root / "src/app.py").write_text("x = 1  # @req is a word here\n")
                self.track(root, git)
                self.assertFalse(settings.annotated(root))
                (root / "src/app.py").write_text(ANNOTATION)
                self.track(root, git)
                self.assertTrue(settings.annotated(root))

    @staticmethod
    def track(root, git):
        if git:
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)

    # The switch.
    def test_show_names_each_setting_and_its_source(self):
        result = self.cli()
        self.assertEqual(result.returncode, 0)
        self.assertIn("doc gate: enforce", result.stdout)
        self.assertIn("framework: off (no API address", result.stdout)
        result = self.cli(env={"AEION_FRAMEWORK_URL": "http://10.0.0.2:8787"})
        self.assertIn("framework: on → http://10.0.0.2:8787 (from AEION_FRAMEWORK_URL)", result.stdout)

    def test_the_gate_is_saved_beside_other_settings(self):
        self.write(json.dumps({"framework": "http://127.0.0.1:8787"}))
        result = self.cli("doc-gate", "warn")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads((self.root / settings.SETTINGS).read_text()),
                         {"doc_gate": "warn", "framework": "http://127.0.0.1:8787"})
        self.assertEqual(stat.S_IMODE((self.root / settings.SETTINGS).stat().st_mode), 0o644)
        self.assertEqual(self.cli("doc-gate", "never").returncode, 2)
        self.assertEqual(sorted(p.name for p in (self.root / ".aeion").iterdir()), ["settings.json"])

    def test_connect_saves_a_ready_service_and_prints_the_mcp_line(self):
        result = self.cli("framework", self.service.url + "/")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads((self.root / settings.SETTINGS).read_text()), {"framework": self.service.url})
        self.assertIn(f"aeion-framework {settings.TESTED}, ready", result.stdout)
        self.assertIn(f"claude mcp add --transport http aeion-axiom {self.service.url}/mcp/ --scope local", result.stdout)
        result = self.cli("framework", "off")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads((self.root / settings.SETTINGS).read_text()), {})

    def test_connect_refuses_and_saves_nothing(self):
        self.service.body = {"status": "ready", "version": "0.3.0"}
        for args in ((self.service.url,), ("http://127.0.0.1:9",), ("http://u:p@127.0.0.1:1",), ("ftp://h",)):
            result = self.cli("framework", *args)
            self.assertEqual(result.returncode, 1, args)
            self.assertIn("refused", result.stderr)
            self.assertFalse((self.root / settings.SETTINGS).exists(), args)
        # Without a terminal, no address is ever guessed.
        result = self.cli("framework")
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / settings.SETTINGS).exists())

    def test_session_start_names_a_ready_service(self):
        repo = self.root / "repo"
        for rel in (".claude/hooks/session-start.py", ".claude/hooks/project_files.py", ".claude/hooks/aeion_settings.py",
                    "tools/repo-health/repo-health"):
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / rel, repo / rel)
        (repo / ".aeion").mkdir()
        (repo / settings.SETTINGS).write_text(json.dumps({"framework": self.service.url, "doc_gate": "off"}))
        environment = {k: v for k, v in os.environ.items() if k not in ("AEION_FRAMEWORK_URL", "AEION_FRAMEWORK_TOKEN")}
        result = subprocess.run([sys.executable, str(repo / ".claude/hooks/session-start.py")], capture_output=True,
                                text=True, cwd=repo, env=environment, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"doc gate: off; framework: on → {self.service.url} (aeion-framework {settings.TESTED}, ready)",
                      result.stdout)


if __name__ == "__main__":
    unittest.main()
