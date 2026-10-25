#!/usr/bin/env python3
"""Boundary, recovery and refusal regressions for the real budget implementation."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / "budget.py"
spec = importlib.util.spec_from_file_location("budget", MODULE)
budget = importlib.util.module_from_spec(spec)
spec.loader.exec_module(budget)


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                        "commit", "-qm", "initial", "--allow-empty"], check=True)
        self.transcript = self.root / "test-session.jsonl"
        self.event = {"session_id": "test-session", "hook_event_name": "PreToolUse", "tool_name": "Edit",
                      "tool_input": {"file_path": str(self.root / "src.py")}, "transcript_path": str(self.transcript)}
        self.observe(10)

    def observe(self, tokens):
        usage = dict.fromkeys(budget.FIELDS, 0)
        usage["input_tokens"] = tokens
        self.transcript.write_text(json.dumps({"type": "assistant", "message": {"usage": usage}}) + "\n")

    def call(self, **changes):
        return budget.handle(self.root, {**self.event, **changes})

    def test_warning_boundary_and_latched_closure(self):
        self.observe(249999)
        self.assertEqual(self.call(), {})
        self.observe(250000)
        first = self.call()
        self.assertIn("250k", first["systemMessage"])
        self.assertEqual(first["hookSpecificOutput"]["permissionDecision"], "deny")
        again = self.call()
        self.assertNotIn("systemMessage", again)
        self.observe(100)
        self.assertEqual(self.call()["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_observed_limit_stops_and_cannot_be_reset_by_resume_or_compact(self):
        self.observe(300000)
        self.assertFalse(self.call()["continue"])
        self.observe(1)
        for source in ("resume", "compact"):
            self.assertFalse(self.call(hook_event_name="SessionStart", source=source)["continue"])

    def test_cache_counts_once_per_latest_request(self):
        usage = {"input_tokens": 1000, "cache_creation_input_tokens": 4000,
                 "cache_read_input_tokens": 244000, "output_tokens": 1000}
        record = json.dumps({"type": "assistant", "message": {"usage": usage}}) + "\n"
        self.transcript.write_text(record * 2)
        self.assertEqual(budget.native_usage(self.transcript, "test-session"), 250000)

    def test_missing_usage_stops_after_one_prompt_bootstrap(self):
        self.transcript.write_text("")
        self.assertEqual(self.call(hook_event_name="UserPromptSubmit"), {})
        self.assertFalse(self.call(hook_event_name="UserPromptSubmit")["continue"])

    def test_invalid_counts_and_cross_session_paths_are_refused(self):
        for value in (True, -1, "1"):
            self.transcript.write_text(json.dumps({"type": "assistant", "message": {
                "usage": {**dict.fromkeys(budget.FIELDS, 0), "input_tokens": value}}}) + "\n")
            with self.assertRaises(ValueError):
                budget.native_usage(self.transcript, "test-session")
        with self.assertRaises(ValueError):
            budget.native_usage(self.transcript, "other-session")
        with self.assertRaises(ValueError):
            budget.session_id("../../secret")

    def test_compaction_boundary_does_not_reuse_old_usage(self):
        self.transcript.write_text(self.transcript.read_text() + json.dumps({"type": "system", "subtype": "compact_boundary"}) + "\n")
        self.assertIsNone(budget.native_usage(self.transcript, "test-session"))

    def test_precompact_always_requires_current_checkpoint(self):
        result = self.call(hook_event_name="PreCompact")
        self.assertEqual(result["decision"], "block")
        handover = budget.handover_path(self.root, "test-session")
        state_file = self.root / ".factory/context/test-session.json"
        state = json.loads(state_file.read_text())
        state["checkpoint"] = {"tree": budget.fingerprint(self.root),
                               "handover": budget.hashlib.sha256(handover.read_bytes()).hexdigest()}
        budget.atomic(state_file, json.dumps(state))
        self.assertEqual(self.call(hook_event_name="PreCompact"), {})
        (self.root / "new.py").write_text("print('change')\n")
        self.assertEqual(self.call(hook_event_name="PreCompact")["decision"], "block")

    def test_document_edits_allowed_and_shell_injection_denied_during_closure(self):
        self.observe(250000)
        self.assertNotIn("permissionDecision", self.call(tool_input={"file_path": str(self.root / "knowledge/policy.md")}).get("hookSpecificOutput", {}))
        for command in ("tools/knowledge/doc-links; touch /tmp/unsafe", "python3 -c 'print(1)'",
                        "git status --short && echo unsafe", "tools/knowledge/doc-links\nrm -rf x"):
            self.assertEqual(self.call(tool_name="Bash", tool_input={"command": command})["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(self.call(tool_name="Bash", tool_input={"command": "tools/knowledge/doc-links"}), {})

    def test_sessions_are_isolated(self):
        self.observe(300000)
        self.call()
        other = self.root / "other.jsonl"
        other.write_text(json.dumps({"type": "assistant", "message": {"usage": {
            **dict.fromkeys(budget.FIELDS, 0), "input_tokens": 100}}}) + "\n")
        self.assertEqual(self.call(session_id="other", transcript_path=str(other)), {})

    def test_strict_launcher_refuses_before_any_external_execution(self):
        run = subprocess.run([str(MODULE.parent / "run"), "--strict"], capture_output=True, text=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("UNSUPPORTED", run.stderr)

    def test_malformed_usage_latches_stop_and_hook_returns_processable_json(self):
        self.transcript.write_text('{"type":')
        self.assertFalse(self.call()["continue"])
        self.observe(1)
        self.assertFalse(self.call()["continue"])
        adapter = MODULE.parents[1].parent / ".claude/hooks/context-budget.py"
        result = subprocess.run(["python3", str(adapter)], input="invalid", capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertFalse(json.loads(result.stdout)["continue"])


if __name__ == "__main__":
    unittest.main()
