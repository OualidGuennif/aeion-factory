#!/usr/bin/env python3
"""Boundary, recovery and refusal regressions for the real budget implementation."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

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

    def test_handover_is_created_only_when_closure_needs_it(self):
        handover = budget.handover_path(self.root, "test-session")
        start = self.call(hook_event_name="SessionStart", source="startup")
        self.assertNotIn("Recovery", start["hookSpecificOutput"]["additionalContext"])
        self.call()
        self.assertFalse(handover.exists())
        self.observe(250000)
        self.assertIn(str(handover.relative_to(self.root)), self.call()["systemMessage"])
        self.assertIn("TODO", handover.read_text())
        resume = self.call(hook_event_name="SessionStart", source="resume")
        self.assertIn("Recovery", resume["hookSpecificOutput"]["additionalContext"])

    def test_refused_compaction_and_checkpoint_create_the_skeleton_to_fill(self):
        handover = budget.handover_path(self.root, "test-session")
        self.call()
        with self.assertRaisesRegex(ValueError, "handover sections"):
            budget.checkpoint(self.root, "test-session", "HEAD")
        handover.unlink()
        self.assertIn(str(handover.relative_to(self.root)), self.call(hook_event_name="PreCompact")["reason"])
        self.assertTrue(handover.is_file())

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

    def test_synthetic_records_do_not_hide_the_latest_request(self):
        synthetic = json.dumps({"type": "assistant", "message": {"model": "<synthetic>",
                                                                 "usage": dict.fromkeys(budget.FIELDS, 0)}}) + "\n"
        self.observe(1000)
        self.transcript.write_text(self.transcript.read_text() + synthetic * 2)
        self.assertEqual(budget.native_usage(self.transcript, "test-session"), 1000)
        self.call(hook_event_name="UserPromptSubmit")
        self.assertEqual(self.call(hook_event_name="UserPromptSubmit"), {})
        self.transcript.write_text(synthetic)
        self.assertIsNone(budget.native_usage(self.transcript, "test-session"))
        # A compaction boundary still hides the older request, and a skipped record cannot lift a stop.
        boundary = json.dumps({"type": "system", "subtype": "compact_boundary"}) + "\n"
        self.observe(1000)
        self.transcript.write_text(self.transcript.read_text() + boundary + synthetic)
        self.assertIsNone(budget.native_usage(self.transcript, "test-session"))
        self.observe(300000)
        self.transcript.write_text(self.transcript.read_text() + synthetic)
        self.assertFalse(self.call()["continue"])

    def test_missing_usage_stops_after_one_prompt_bootstrap(self):
        self.transcript.write_text("")
        self.assertEqual(self.call(hook_event_name="UserPromptSubmit"), {})
        self.assertFalse(self.call(hook_event_name="UserPromptSubmit")["continue"])

    def test_delayed_native_usage_blocks_work_without_poisoning_session(self):
        self.transcript.write_text("")
        self.call(hook_event_name="SessionStart", source="startup")
        self.assertEqual(self.call(hook_event_name="UserPromptSubmit"), {})
        # The tool call is denied, but the agent keeps running so it can retry the call.
        self.assertEqual(self.call()["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertNotIn("continue", self.call())
        self.assertEqual(self.call(hook_event_name="PostToolUse"), {})
        self.observe(1000)
        self.assertEqual(self.call(), {})

    def test_delayed_usage_after_compaction_can_recover_without_new_prompt(self):
        self.call(hook_event_name="SessionStart", source="compact")
        self.transcript.write_text(json.dumps({"type": "system", "subtype": "compact_boundary"}) + "\n")
        self.assertEqual(self.call()["hookSpecificOutput"]["permissionDecision"], "deny")
        self.observe(1000)
        self.assertEqual(self.call(), {})

    def test_precompact_latches_warning_and_delivers_it_at_next_supported_event(self):
        self.observe(250000)
        self.assertEqual(self.call(hook_event_name="PreCompact")["decision"], "block")
        state = json.loads((self.root / ".aeion/context/test-session.json").read_text())
        self.assertEqual(state["state"], "HANDOVER_REQUIRED")
        self.assertIn("250k", self.call(tool_name="Read")["systemMessage"])

    def test_resume_does_not_claim_an_unverified_compaction(self):
        self.observe(250000)
        self.call(hook_event_name="PreCompact")
        result = self.call(hook_event_name="SessionStart", source="resume")
        self.assertIn("closure remains required", result["systemMessage"])
        self.assertNotIn("verified handover was retained", result["systemMessage"])

    def test_untracked_code_requires_current_task_update_before_checkpoint(self):
        (self.root / '.gitignore').write_text('.aeion/\nwork/handovers/\n*.jsonl\n')
        (self.root / 'work').mkdir(exist_ok=True)
        current = self.root / 'work/current.md'
        current.write_text('# Current work\n')
        budget.git(self.root, 'add', '.gitignore', 'work/current.md')
        budget.git(self.root, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'task fixture')
        self.call()
        handover = budget.ensure_handover(self.root, 'test-session')
        handover.write_text(handover.read_text().replace('TODO', 'Fixture evidence'))
        (self.root / 'new-feature.py').write_text('value = 1\n')
        actual_run = subprocess.run

        def run(command, **options):
            return actual_run(command, **options) if command[0] == 'git' else subprocess.CompletedProcess(command, 0)

        with patch.object(budget.subprocess, 'run', side_effect=run):
            with self.assertRaisesRegex(ValueError, 'work/current.md'):
                budget.checkpoint(self.root, 'test-session', 'HEAD')
            # Local play keeps no task entry, so its checkpoint does not ask for one.
            budget.git(self.root, 'config', 'aeion.mode', 'local')
            budget.checkpoint(self.root, 'test-session', 'HEAD')
            budget.git(self.root, 'config', '--unset', 'aeion.mode')
            # An included file cannot switch the mode: only the repository's own config counts.
            outside = tempfile.TemporaryDirectory()
            self.addCleanup(outside.cleanup)
            included = Path(outside.name) / 'mode.cfg'
            included.write_text('[aeion]\n\tmode = local\n')
            budget.git(self.root, 'config', 'include.path', str(included))
            with self.assertRaisesRegex(ValueError, 'work/current.md'):
                budget.checkpoint(self.root, 'test-session', 'HEAD')
            budget.git(self.root, 'config', '--unset', 'include.path')
            current.write_text('# Current work\nTask updated.\n')
            budget.checkpoint(self.root, 'test-session', 'HEAD')

    def test_launcher_enters_its_project_before_executing_runtime(self):
        launcher = MODULE.parent / "run"
        fake = self.root / "claude"
        fake.write_text("#!/usr/bin/env python3\nimport os\nprint(os.getcwd())\n")
        fake.chmod(0o755)
        # The baseline subprocess is an independent gate, replaced only in this launcher fixture.
        code = "import runpy,subprocess; from unittest.mock import patch; "
        code += f"\nwith patch('subprocess.run', return_value=subprocess.CompletedProcess([], 0)):\n runpy.run_path({str(launcher)!r}, run_name='__main__')\n"
        result = subprocess.run(["python3", "-c", code], cwd=self.root,
                                env={**budget.os.environ, "PATH": str(self.root) + budget.os.pathsep + budget.os.environ["PATH"]},
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(MODULE.parents[2]))

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
        state_file = self.root / ".aeion/context/test-session.json"
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
                        "git status --short && echo unsafe", "tools/knowledge/doc-links\nrm -rf x", "echo 'unterminated"):
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
        self.transcript.write_text('{"type":\n')
        self.assertFalse(self.call()["continue"])
        self.observe(1)
        self.assertFalse(self.call()["continue"])
        adapter = MODULE.parents[1].parent / ".claude/hooks/context-budget.py"
        result = subprocess.run(["python3", str(adapter)], input="invalid", capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertFalse(json.loads(result.stdout)["continue"])

    def test_child_uses_own_usage_and_cannot_stop_or_inherit_parent_budget(self):
        self.observe(250000)
        self.call()
        child = self.root / "test-session/subagents/agent-child1.jsonl"
        child.parent.mkdir(parents=True)
        usage = {**dict.fromkeys(budget.FIELDS, 0), "input_tokens": 100}
        child.write_text(json.dumps({"type": "assistant", "message": {"usage": usage}}) + "\n")
        event = {"agent_id": "child1", "agent_transcript_path": str(child)}
        self.assertEqual(self.call(**event), {})
        usage["input_tokens"] = 300000
        child.write_text(json.dumps({"type": "assistant", "message": {"usage": usage}}) + "\n")
        self.assertFalse(self.call(**event)["continue"])
        self.assertFalse(self.call(agent_id="agent-child1", agent_transcript_path=str(child), hook_event_name="SubagentStop")["continue"])
        self.assertEqual(len(list((self.root / ".aeion/context").glob("*.json"))), 2)
        parent = json.loads((self.root / ".aeion/context/test-session.json").read_text())
        self.assertEqual(parent["state"], "HANDOVER_REQUIRED")

    def test_missing_child_transcript_refuses_child_without_stopping_parent(self):
        self.assertEqual(self.call(agent_id="missing-child")["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(self.call(), {})


if __name__ == "__main__":
    unittest.main()
