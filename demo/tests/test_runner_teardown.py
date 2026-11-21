"""Sandbox teardown and budget settlement regressions for the live runner.

The sandbox and telemetry are fakes: no OpenShell workload, model or network is used.
"""
import io
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from app import runner as runner_module
from app.runner import Runner, usage_is_complete
from factory.flue_session import new_run, usage


class FakeSpan:
    def set_attribute(self, *args, **kwargs):
        pass

    def set_status(self, *args, **kwargs):
        pass

    def end(self):
        pass


class FakeTelemetry:
    def begin(self, run):
        return FakeSpan()

    def emit(self, *args, **kwargs):
        pass


class FakeSandbox:
    instances = []

    def __init__(self, run, root, role="agent"):
        self.ref = type("Ref", (), {"id": "sandbox-fixture"})()
        self.closed = 0
        self.seed_error = None
        self.collect_error = None
        FakeSandbox.instances.append(self)

    def seed_in(self, files, root):
        if self.seed_error:
            raise self.seed_error
        return len(files)

    def sync_out(self, workspace, root):
        if self.collect_error:
            raise self.collect_error
        return 0

    def close(self):
        self.closed += 1


class FakeBudget:
    def __init__(self):
        self.settled = []

    def settle(self, reservation, actual):
        self.settled.append((reservation.id, actual))
        return Decimal("0")


class RunnerTeardownTests(unittest.TestCase):
    def setUp(self):
        FakeSandbox.instances = []
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.runner = Runner(FakeTelemetry(), lambda run: None, work_root=Path(self.tmp.name))
        self.patches = [
            mock.patch.object(runner_module, "Sandbox", FakeSandbox),
            mock.patch.object(Runner, "copies_out", staticmethod(lambda run: True)),
            mock.patch.object(Runner, "simulate", lambda self, run, workspace, agent: "complete"),
            mock.patch.object(Runner, "verify",
                              lambda self, run, root, workspace: {"passed": True, "failed": []}),
        ]
        for patcher in self.patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        self.run = {
            "id": "run-fixture", "status": "running", "synthetic": True, "started_ns": 0,
            "events": [], "sessions": [], "agents": 0, "human_interventions": 0,
            "postprocessing": True, "usage_complete": True, "task_id": "pricing-js-v1",
            "profile_version": "fixture", "native_cost_usd": "0", "model": "fixture/model",
            "limit": 250000, "metric": "active_context", "runtime": "flue-openshell",
            "trace_id": "trace-fixture", "root_span_id": "span-fixture", "selection": {},
        }

    def test_a_seed_failure_still_closes_the_sandbox(self):
        sandbox = FakeSandbox(self.run, Path(self.tmp.name))
        FakeSandbox.instances = []

        def construct(run, root, role="agent"):
            sandbox.seed_error = RuntimeError("fixture seed failure")
            FakeSandbox.instances.append(sandbox)
            return sandbox

        with mock.patch.object(runner_module, "Sandbox", construct):
            self.runner.run(self.run)

        self.assertEqual(sandbox.closed, 1)
        self.assertIsNone(self.runner.active_sandbox)
        self.assertEqual(self.run["status"], "failed")

    def test_a_collection_failure_still_closes_the_sandbox(self):
        sandbox = FakeSandbox(self.run, Path(self.tmp.name))
        sandbox.collect_error = ValueError("SYNC_OUT_INCOMPLETE")
        FakeSandbox.instances = []

        def construct(run, root, role="agent"):
            FakeSandbox.instances.append(sandbox)
            return sandbox

        with mock.patch.object(runner_module, "Sandbox", construct):
            self.runner.run(self.run)

        self.assertEqual(sandbox.closed, 1)
        self.assertIsNone(self.runner.active_sandbox)
        self.assertEqual(self.run["status"], "failed")

    def test_an_agent_failure_still_closes_the_sandbox(self):
        sandbox = FakeSandbox(self.run, Path(self.tmp.name))
        FakeSandbox.instances = []

        def construct(run, root, role="agent"):
            FakeSandbox.instances.append(sandbox)
            return sandbox

        def explode(self, run, workspace, agent):
            raise RuntimeError("fixture agent failure")

        with mock.patch.object(runner_module, "Sandbox", construct), \
                mock.patch.object(Runner, "simulate", explode):
            self.runner.run(self.run)

        self.assertEqual(sandbox.closed, 1)
        self.assertEqual(self.run["status"], "failed")


class RunnerSettlementTests(unittest.TestCase):
    def test_usage_completeness_requires_every_forwarded_request(self):
        self.assertTrue(usage_is_complete(2, 2))
        self.assertFalse(usage_is_complete(0, 0))
        self.assertFalse(usage_is_complete(1, 2))
        self.assertFalse(usage_is_complete(2, 2, error="UPSTREAM"))

    def setUp(self):
        self.runner = Runner(FakeTelemetry(), lambda run: None)
        self.runner.budget = FakeBudget()
        self.reservation = type("Reservation", (), {"id": "reservation-fixture"})()
        self.run = {"id": "run-fixture", "budget": {"settled_usd": None},
                    "native_cost_usd": "0", "usage_complete": False}

    def test_unknown_usage_keeps_the_reservation_open(self):
        self.runner._settle(self.run, self.reservation)
        self.assertEqual(self.runner.budget.settled, [])
        self.assertEqual(self.run["budget"]["settled_usd"], "unsettled")

    def test_complete_usage_can_settle_zero(self):
        self.run["usage_complete"] = True
        self.runner._settle(self.run, self.reservation)
        self.assertEqual(self.runner.budget.settled,
                         [("reservation-fixture", Decimal("0"))])
        self.assertEqual(self.run["budget"]["settled_usd"], "0")

    def test_a_proven_no_transport_outcome_can_release_the_reservation(self):
        self.run["budget_release"] = "proven_no_transport"
        self.runner._settle(self.run, self.reservation)
        self.assertEqual(self.runner.budget.settled,
                         [("reservation-fixture", Decimal("0"))])

    def test_author_context_boundary_defers_checkpoint_until_teardown(self):
        run = new_run("claude-haiku-5.5", "fixture-build", "author", "5.00")
        run.update(trace_id="trace-fixture", root_span_id="span-fixture")
        reported = {"complete": True, "input_tokens": 214962, "output_tokens": 629, "cost_usd": "0.20"}
        with (
            tempfile.TemporaryDirectory() as folder,
            mock.patch.dict(runner_module.os.environ, {"OPENCODE_API_KEY": "fixture"}),
            mock.patch.object(runner_module, "HARNESS", Path(folder)),
            mock.patch.object(runner_module, "SandboxBridge") as bridge_factory,
            mock.patch.object(runner_module, "ContextRelay") as relay_factory,
            mock.patch.object(runner_module.subprocess, "Popen") as popen,
            mock.patch.object(self.runner, "prepare_handover") as checkpoint,
        ):
            relay = relay_factory.return_value
            relay.url = "http://localhost:1/v1"
            relay.token = "fixture"
            relay.context_basis = "provider_usage"
            relay.forwarded_count = 1
            relay.reported_usage = [reported]
            relay.accounting_complete = True
            relay.projected_cost = Decimal("0.20")
            relay.provider_retries = 0
            relay.last_http_status = None
            relay.last_error_code = "AEION_HANDOVER"
            process = mock.Mock(pid=1, returncode=1, stderr=io.BytesIO())
            process.poll.return_value = 1

            def halt_before_forward(*_args, **_kwargs):
                relay_factory.call_args.args[3](214962, True)
                return process

            popen.side_effect = halt_before_forward
            self.assertEqual(self.runner.live(run, Path(folder), None,
                prompt="fixture", kind="factory-build"), "handover")
            relay.close.assert_called_once()
            bridge_factory.return_value.close.assert_called_once()
            checkpoint.assert_not_called()
        self.assertEqual(run["pending_author_handover"], (214962, "provider_usage"))
        self.assertTrue(usage(run)["complete"])

    def test_relay_close_failure_cannot_report_zero_transport(self):
        run = new_run("glm-5.3-flash", "fixture-build", "review", "0.05")
        with tempfile.TemporaryDirectory() as folder, \
                mock.patch.dict(runner_module.os.environ, {"OPENCODE_API_KEY": "fixture"}), \
                mock.patch.object(runner_module, "HARNESS", Path(folder)), \
                mock.patch.object(runner_module, "ContextRelay") as relay_factory, \
                mock.patch.object(runner_module.subprocess, "Popen", side_effect=ValueError("CLI_FAILED")):
            relay = relay_factory.return_value
            relay.forwarded_count = 1
            relay.close.side_effect = RuntimeError("relay teardown failed")
            with self.assertRaisesRegex(RuntimeError, "relay teardown failed"):
                self.runner.live(run, Path(folder), None, prompt="fixture", kind="factory-review")

        self.assertFalse(usage(run)["complete"])
        self.assertIsNone(usage(run)["cost_usd"])


if __name__ == "__main__":
    unittest.main()
