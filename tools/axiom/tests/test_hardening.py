"""Refusals and fail-closed paths found by the 3.0.0 independent review: one test per finding."""
import importlib.machinery
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from support import FACTORY, ledger, pantry_project, pantry_spec
import docs
import evidence
import graph
import spec as specs
import strict
import views


def model_of(root):
    result = specs.Result()
    spec = specs.load_spec(Path(root) / "knowledge/spec/spec.json", result)
    model, _ = specs.validate(spec, result=result)
    return model, result


class InitTests(unittest.TestCase):  # finding 1
    def test_init_keeps_a_projects_own_docs(self):
        project = pantry_project()
        try:
            readme = project.write("docs/README.md", "# Our docs\n")
            api = project.write("docs/generated/api.html", "<html></html>")
            (project.root / "knowledge/spec/spec.json").unlink()
            done = project.run("init")
            self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
            self.assertEqual(readme.read_text(), "# Our docs\n")
            self.assertTrue(api.is_file())
            self.assertIn("was not generated", done.stdout)
        finally:
            project.close()


class SchemaTests(unittest.TestCase):  # finding 2
    def test_template_update_carries_the_axiomspec_package(self):
        path = FACTORY / "tools/agents/template-update"
        loader = importlib.machinery.SourceFileLoader("template_update", str(path))
        module = importlib.util.module_from_spec(importlib.util.spec_from_loader("template_update", loader))
        loader.exec_module(module)
        self.assertFalse(module.owned("knowledge/axiomspec/AxiomSpec/schemas/spec.schema.json"))
        self.assertTrue(module.owned("knowledge/spec/spec.json"))

    def test_a_missing_schema_is_a_g01_error_not_a_crash(self):
        project = pantry_project()
        try:
            shutil.rmtree(project.root / "knowledge/axiomspec/AxiomSpec/schemas")
            done = project.run("validate")
            self.assertEqual(done.returncode, 4, done.stderr)
            self.assertIn("SCHEMA_UNAVAILABLE", done.stdout)
            self.assertNotIn("Traceback", done.stderr)
        finally:
            project.close()


class WindowTests(unittest.TestCase):  # finding 3
    def setUp(self):
        self.spec = ledger()
        self.constraint = next(n for n in self.spec["nodes"] if n["kind"] == "Constraint"
                               and n["data"]["representation"] == "bcir")
        self.scenario = next(n for n in self.spec["nodes"] if n["kind"] == "Scenario" and any(
            e["constraint_id"] == self.constraint["id"] for e in n["data"]["constraint_expectations"]))
        self.expectation = next(e for e in self.scenario["data"]["constraint_expectations"]
                                if e["constraint_id"] == self.constraint["id"])

    def outcome(self, evaluated_at):
        model = specs.Model(self.spec)
        import bcir
        validator = bcir.environment_validator(model.envs[self.scenario["data"]["environment_id"]])
        return specs.expectation_outcome(model, self.scenario, self.expectation, validator, evaluated_at)

    def test_out_of_window_is_not_pass(self):
        self.constraint["data"]["effective_from"] = "2030-01-01T00:00:00Z"
        self.assertEqual(self.outcome("2026-01-01T00:00:00Z")[:2], ("unknown", "NOT_IN_EFFECT"))
        self.assertEqual(self.outcome("garbage")[:2], ("unknown", "APPLICABILITY_UNKNOWN"))
        self.assertIsNone(self.outcome("2031-01-01T00:00:00Z"))

    def test_the_cli_refuses_an_invalid_evaluation_time(self):
        project = pantry_project()
        try:
            done = project.run("validate", "--evaluated-at", "garbage")
            self.assertEqual(done.returncode, 4)
            self.assertIn("EVALUATED_AT", done.stderr)
        finally:
            project.close()


class DanglingTests(unittest.TestCase):  # finding 4
    def test_only_knowledge_and_docs_cite_the_spec(self):
        project = pantry_project()
        try:
            project.write("knowledge/components/pantry.md", (project.root / "knowledge/components/pantry.md").read_text()
                          .replace("see also `REQ-999` as an example", "nothing else"))
            project.write("notes/meeting.md", "# Meeting\n\nJira ticket CON-1234 and REQ-404.\n")
            model, _ = model_of(project.root)
            self.assertEqual(docs.dangling_ids(project.root, model), [])
            project.write("docs/authored/plan.md", "# Plan\n\nSee REQ-404.\n")
            self.assertEqual(docs.dangling_ids(project.root, model),
                             ["docs/authored/plan.md: cites REQ-404, not in knowledge/spec/spec.json"])
        finally:
            project.close()


class BindingTests(unittest.TestCase):  # finding 5
    def test_a_binding_without_a_symbol_names_the_file(self):
        project = pantry_project()
        try:
            spec = pantry_spec()
            spec["bindings"][0]["symbol"] = None
            project.write("knowledge/spec/spec.json", spec)
            snapshot = graph.snapshot(project.root, project.root / "knowledge/spec/spec.json")
            bound = next(n for n in snapshot["nodes"] if n["id"] == "BIND-001")
            self.assertEqual(bound["resolution"]["status"], "resolved")
            spec["bindings"][1]["symbol"] = None
            project.write("knowledge/spec/spec.json", spec)
            model = specs.Model(spec)
            self.assertEqual(evidence.run(project.root, model, ["TEST-001"]), 2)
            receipt = json.loads((project.root / "knowledge/spec/evidence/TEST-001.json").read_text())
            self.assertIn("names none", receipt["problems"][0])
        finally:
            project.close()


class EnvironmentTests(unittest.TestCase):  # finding 6
    def test_unwalkable_environment_schemas_are_diagnostics(self):
        for broken in ({"type": "object", "additionalProperties": False, "required": ["a"], "properties": {"a": 5}},
                       {"type": "object", "additionalProperties": False, "required": [], "properties": {},
                        "patternProperties": {"(": {"type": "integer"}}}):
            spec = ledger()
            spec["environments"][0]["schema"] = broken
            result = specs.Result()
            specs.validate(spec, result=result)
            self.assertEqual(result.gate_status("G03"), "error")
            self.assertIn(result.gate_status("G06"), ("unknown", "error", "pass"))

    def test_a_relative_unit_pointer_is_a_diagnostic(self):
        spec = ledger()
        if not spec["environments"][0].get("units"):
            self.skipTest("the ledger environment declares no units")
        spec["environments"][0]["units"][0]["pointer"] = "no-leading-slash"
        result = specs.Result()
        specs.validate(spec, result=result)
        self.assertEqual(result.gate_status("G03"), "error")


class StrictTests(unittest.TestCase):  # finding 7
    def test_a_huge_integer_is_an_input_error(self):
        with self.assertRaises(strict.InputError) as caught:
            strict.loads(("[" + "7" * 5000 + "]").encode())
        self.assertEqual(caught.exception.code, "UNSAFE_INTEGER")


class AdapterTests(unittest.TestCase):  # finding 8
    def test_a_project_module_named_like_a_toolkit_module_is_imported(self):
        folder = Path(tempfile.mkdtemp(prefix="axiom-adapter-"))
        try:
            (folder / "tests").mkdir()
            (folder / "tests/common.py").write_text("def helper():\n    return 42\n")
            (folder / "tests/test_x.py").write_text("import unittest\nfrom common import helper\n\n\n"
                                                    "class Case(unittest.TestCase):\n    def test_ok(self):\n"
                                                    "        self.assertEqual(helper(), 42)\n")
            done = subprocess.run([sys.executable, "-I", "-B", str(evidence.ADAPTER_SCRIPT), "tests/test_x.py", "Case.test_ok"],
                                  cwd=folder, capture_output=True, text=True, timeout=60)
            self.assertEqual(json.loads(done.stdout.strip().splitlines()[-1])["results"], {"Case.test_ok": "pass"}, done.stderr)
        finally:
            shutil.rmtree(folder, ignore_errors=True)


class ReportTests(unittest.TestCase):  # finding 9
    def test_gates_after_a_g01_failure_are_not_run(self):
        result = specs.Result()
        result.add("G01", "error", "TOO_DEEP", "nesting too deep")
        report = specs.report(result, "design_ready", list(specs.DESIGN_GATES), None, "2026-11-10T00:00:00Z")
        later = [c for c in report["checks"] if c["gate"] != "G01"]
        self.assertTrue(later and all(c["status"] == "unknown" for c in later))
        self.assertEqual(report["status"], "error")


class SpecPathTests(unittest.TestCase):  # finding 10
    def test_implementation_gates_read_the_given_spec(self):
        project = pantry_project()
        try:
            other = pantry_spec()
            other["bindings"][0]["path"] = "app/missing.py"
            path = project.write("alt/spec.json", other)
            done = project.run("--spec", str(path), "validate", "--phase", "implementation")
            self.assertIn("G09 fail", done.stdout)
        finally:
            project.close()


class ExportTests(unittest.TestCase):  # finding 11
    def test_a_profile_cannot_rename_the_exported_file(self):
        project = pantry_project()
        try:
            model, _ = model_of(project.root)
            profile = project.write("profile.json", {"format": "aeion-export-profile/0.1", "name": "evil",
                                                     "frontmatter": {"file": "../../ESCAPED.md", "id": "999"}})
            # ../../ESCAPED.md from root/a/out would land in root itself: inside this test's own folder.
            out = project.root / "a/out"
            self.assertEqual(docs.export(project.root, model, None, True, profile, out), 0)
            self.assertFalse((project.root / "ESCAPED.md").exists())
            row = json.loads((out / "features.json").read_text())["features"][0]
            self.assertEqual((row["file"], row["id"]), ("001-never-overdraw-stock.md", "001"))
        finally:
            project.close()


class ObservationTests(unittest.TestCase):  # finding 12
    def test_malformed_observation_files_are_input_errors(self):
        project = pantry_project()
        try:
            for value in ([], {"cases": [{"scenario_id": "SCN-001"}]}, {"cases": "x"}):
                path = project.write("obs.json", value)
                done = project.run("evaluate", "--observations", str(path))
                self.assertEqual(done.returncode, 4, (value, done.stderr))
                self.assertNotIn("Traceback", done.stderr)
        finally:
            project.close()


class SequenceTests(unittest.TestCase):  # finding 13
    def test_malformed_steps_are_view_errors(self):
        base = {"format": views.FORMAT, "kind": "sequence",
                "participants": [{"id": "a", "label": "A", "type": "actor"}, {"id": "b", "label": "B", "type": "participant"}]}
        for steps in ([{"note": 5, "over": ["a"]}], [{"fragment": "alt", "branches": ["x"]}], ["x"],
                      [{"from": ["a"], "to": "b"}]):
            with self.assertRaises(views.ViewError, msg=steps):
                views.render(dict(base, steps=steps), "T", "Q")


class ReceiptTests(unittest.TestCase):  # finding 14
    def test_a_receipt_counts_only_for_its_own_test(self):
        project = pantry_project()
        try:
            spec = pantry_spec()
            model = specs.Model(spec)
            self.assertEqual(evidence.run(project.root, model, []), 0)
            folder = project.root / "knowledge/spec/evidence"
            receipt = json.loads((folder / "TEST-001.json").read_text())
            receipt["test_id"] = "TEST-002"
            (folder / "TEST-001.json").write_text(json.dumps(receipt))
            self.assertEqual(evidence.receipts_state(project.root, model)["TEST-001"][0], "failed")
            (folder / "TEST-001.json").write_text("[1, 2]")
            self.assertEqual(evidence.receipts_state(project.root, model)["TEST-001"][0], "failed")
        finally:
            project.close()


if __name__ == "__main__":
    unittest.main()
