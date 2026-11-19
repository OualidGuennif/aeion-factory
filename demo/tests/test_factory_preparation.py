"""Automatic MD preparation freezes real Git bytes and refuses ineffective acceptance.

Inference and the compiler/check process are synthetic unit-test boundaries here.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.budget import DailyBudget
from factory.manifest import Catalog
from factory.models import Router
from factory.preparation import TaskPreparer, PreparationError, freeze_task

CONTRACT = '''package local.aeion.forum;
class FactoryAcceptance007Test {
    @Test void rejectsUntrustedHtml() { assertEquals("safe", "unsafe"); }
}
'''


class ScriptedRole:
    paid = False
    last_execution = None

    def __init__(self, cost='0', complete=True):
        self.calls = []
        self.cost,self.complete=cost,complete
        self.last_usage = None

    def __call__(self, model, prompt, build_id):
        self.last_usage = {'complete': self.complete, 'cost_usd': self.cost}
        self.calls.append((model, prompt, build_id))
        return {'status': 'ready', 'contract': CONTRACT, 'reason': 'Synthetic fixture'}


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        architecture = self.root / 'demo/forum/ARCHITECTURE.md'
        architecture.parent.mkdir(parents=True)
        architecture.write_text('Approved Java/PostgreSQL/React product architecture.\n')
        self.architecture = architecture
        self.specs = self.root / 'specs'
        self.specs.mkdir()
        self.spec = self.specs / '007.md'
        self.spec.write_text('# 007\n## Acceptance checks\n- [ ] Unsafe HTML is removed.\n')
        self.catalog = Catalog({'schema_version': 2, 'count': 1, 'features': [{
            'id': '007', 'title': 'Sanitize HTML', 'area': 'foundation', 'size': 'S',
            'phase': 'P0', 'parallel': False, 'tier': 3, 'file': '007.md',
            'write_paths': ['demo/forum-app/'], 'depends_on': [],
            'architecture_digest': hashlib.sha256(architecture.read_bytes()).hexdigest()}]})
        self.source = self.root / 'product'
        (self.source / 'demo/forum-app').mkdir(parents=True)
        (self.source / 'demo/forum-app/build.gradle').write_text('// Trusted baseline fixture\n')
        for command in (['init', '-q'], ['config', 'user.name', 'Fixture'],
                        ['config', 'user.email', 'fixture@example.invalid'], ['add', '.'],
                        ['commit', '-qm', 'baseline']):
            self.git(*command)
        self.base = self.git('rev-parse', 'HEAD').stdout.strip()
        self.role = ScriptedRole()
        self.budget = DailyBudget(self.root / 'ledger.jsonl')

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.source), *args],
                              capture_output=True, text=True, check=True)

    def checker(self, command, **kwargs):
        self.assertIn('--offline', command)
        self.assertNotIn('GH_API_KEY', kwargs['env'])
        report=Path(kwargs['cwd']) / 'demo/forum-app/build/test-results/test/TEST-local.aeion.forum.FactoryAcceptance007Test.xml'
        report.parent.mkdir(parents=True)
        report.write_text('<testsuite><testcase classname="local.aeion.forum.FactoryAcceptance007Test">'
                          '<failure type="java.lang.AssertionError" /></testcase></testsuite>')
        return subprocess.CompletedProcess(command, 1,
            stdout='FactoryAcceptance007Test > rejectsUntrustedHtml FAILED\n', stderr='')

    def prepare(self, checker=None, authorized=lambda: True, synchronize=None, base_ref='HEAD'):
        return TaskPreparer(self.root, self.source, role=self.role,
            checker=checker or self.checker, base_ref=base_ref,synchronize=synchronize).prepare(
                build={'feature_id':'007', 'build_id':'a'*32, 'attempt_id':'b'*32},
                catalog=self.catalog, spec_dir=self.specs, destination=self.root / 'prepared',
                budget=self.budget, router=Router(), authorized=authorized)

    def test_synchronized_main_is_frozen_and_a_sync_failure_never_spends_model_budget(self):
        self.git('update-ref','refs/remotes/origin/main',self.base)
        path=self.source/'demo/forum-app/new-baseline.txt';path.write_text('new remote commit\n')
        self.git('add','.');self.git('commit','-qm','new main')
        latest=self.git('rev-parse','HEAD').stdout.strip()
        def sync():
            self.git('update-ref','refs/remotes/origin/main',latest,self.base)
            return latest
        target,_=self.prepare(synchronize=sync,base_ref='refs/remotes/origin/main')
        self.assertEqual(target.base_sha,latest)
        from factory.source import SourceSyncError
        def unavailable():raise SourceSyncError('source_fetch_failed')
        before=len(self.role.calls)
        with self.assertRaisesRegex(PreparationError,'source_fetch_failed'):
            self.prepare(synchronize=unavailable,base_ref='refs/remotes/origin/main')
        self.assertEqual(len(self.role.calls),before)
        self.assertEqual(self.budget.summary()['aeion-autonomous-forum']['spent_usd'],'0.00')

    def test_complete_md_architecture_base_scopes_and_contract_are_bound_without_manual_target_json(self):
        target, evidence = self.prepare()
        self.assertEqual(target.base_sha, self.base)
        self.assertEqual(target.brief.read_bytes(), self.spec.read_bytes())
        self.assertEqual(evidence['spec_digest'], hashlib.sha256(self.spec.read_bytes()).hexdigest())
        self.assertEqual(evidence['acceptance_digest'], hashlib.sha256(CONTRACT.encode()).hexdigest())
        self.assertEqual(evidence['negative_control'], 'failed_contract_assertion')
        self.assertTrue(all('/src/' in scope for scope in target.write_paths))
        self.assertNotIn('build.gradle', ' '.join(target.write_paths))
        self.assertNotEqual(target.protected_check.contract_test.parent, self.source)
        self.assertEqual(json.loads((self.root / 'prepared/task.json').read_text()), evidence)
        self.assertEqual(self.git('status', '--porcelain').stdout, '')
        self.assertEqual(len(self.role.calls), 1)

    def test_already_passing_baseline_is_not_evidence_of_a_new_feature(self):
        def already_passes(command, **kwargs):
            return subprocess.CompletedProcess(command, 0, stdout='', stderr='')
        with self.assertRaisesRegex(PreparationError, 'negative_control_missing'):
            self.prepare(checker=already_passes)

    def test_preparer_sees_complete_public_interfaces_from_the_pinned_commit_only(self):
        path=self.source / 'demo/forum-app/src/main/java/local/aeion/forum/ApiResource.java'
        path.parent.mkdir(parents=True)
        path.write_text('@Path("/api/fixture") class ApiResource { /* COMMITTED_PUBLIC_INTERFACE */ }\n')
        self.git('add','.');self.git('commit','-qm','public interface')
        path.write_text('@Path("/api/fixture") class ApiResource { /* UNCOMMITTED_CANARY */ }\n')
        self.prepare()
        prompt=self.role.calls[0][1]
        self.assertIn('COMMITTED_PUBLIC_INTERFACE',prompt)
        self.assertNotIn('UNCOMMITTED_CANARY',prompt)

    def test_public_http_routes_are_selected_by_annotation_instead_of_filename_suffix(self):
        folder=self.source/'demo/forum-app/src/main/java/local/aeion/forum'
        folder.mkdir(parents=True)
        (folder/'SchemaEndpoint.java').write_text('@Path("/api/schema") class SchemaEndpoint { /* SCHEMA_HTTP_CONTRACT */ }\n')
        (folder/'InternalResource.java').write_text('class InternalResource { /* NOT_AN_HTTP_INTERFACE */ }\n')
        self.git('add','.');self.git('commit','-qm','HTTP interface naming fixture')
        self.prepare()
        prompt=self.role.calls[0][1]
        self.assertIn('SCHEMA_HTTP_CONTRACT',prompt)
        self.assertNotIn('NOT_AN_HTTP_INTERFACE',prompt)

    def test_compiler_or_unrelated_test_failure_does_not_qualify_acceptance(self):
        def broken(command, **kwargs):
            return subprocess.CompletedProcess(command, 1,
                stdout='OtherTest > unrelated FAILED\nBroken.java:3: error: missing type\n', stderr='')
        with self.assertRaisesRegex(PreparationError, 'negative_control_missing'):
            self.prepare(checker=broken)

    def test_initialization_failure_is_not_a_load_bearing_acceptance_assertion(self):
        def failed_startup(command,**kwargs):
            result=self.checker(command,**kwargs)
            report=Path(kwargs['cwd']) / 'demo/forum-app/build/test-results/test/TEST-local.aeion.forum.FactoryAcceptance007Test.xml'
            report.write_text('<testsuite><testcase classname="local.aeion.forum.FactoryAcceptance007Test">'
                              '<failure type="java.lang.RuntimeException" /></testcase></testsuite>')
            return result
        with self.assertRaisesRegex(PreparationError,'negative_control_missing'):
            self.prepare(checker=failed_startup)

    def test_architecture_drift_and_symlinked_md_are_refused_before_inference_or_spend(self):
        self.architecture.write_text('Changed architecture')
        with self.assertRaisesRegex(PreparationError, 'architecture_changed'):
            self.prepare()
        self.assertEqual(self.role.calls, [])
        self.spec.unlink()
        self.spec.symlink_to(self.architecture)
        with self.assertRaises(PreparationError):
            freeze_task(self.catalog, '007', self.specs, self.architecture, self.base)

    def test_web_scope_is_not_silently_certified_by_a_java_check(self):
        self.catalog.by_id['007']['write_paths'] = ['demo/forum-web/']
        self.catalog = Catalog(self.catalog.raw)  # This scope was declared before admission.
        with self.assertRaisesRegex(PreparationError, 'profile_unavailable'):
            self.prepare()
        self.assertEqual(self.role.calls, [])

    def test_revocation_stops_preparation_before_any_model_call(self):
        with self.assertRaisesRegex(PreparationError, 'revoked'):
            self.prepare(authorized=lambda: False)
        self.assertEqual(self.role.calls, [])

    def test_unknown_preparer_usage_keeps_its_own_reservation_open(self):
        self.role = ScriptedRole(cost=None, complete=False)
        with self.assertRaisesRegex(PreparationError,'preparation_usage_unknown'):
            self.prepare()
        self.assertEqual(str(self.budget.spent('aeion-autonomous-forum')), '0.50')

    def _contract(self, feature='007', spec='# 007\n', acceptance='export function ready() {}\n',
                  paths=None):
        folder = self.root / 'prepared' / feature
        if folder.exists():
            raise AssertionError('fixture folder already exists')
        folder.mkdir(parents=True)
        paths = paths or ['demo/forum-app/src/main/java/local/aeion/forum/']
        identity = {'feature_id': feature, 'catalog_digest': 'a' * 64, 'spec_digest': _sha(spec),
                    'architecture_digest': 'b' * 64, 'base_sha': self.base, 'write_paths': list(paths)}
        evidence = {**identity, 'task_digest': _sha(json.dumps(identity, sort_keys=True, separators=(',', ':'))),
                    'acceptance_digest': _sha(acceptance), 'preparer_model': 'glm-5.3-flash',
                    'negative_control': 'failed_contract_assertion', 'synthetic': True}
        (folder / 'task.json').write_text(json.dumps(evidence), encoding='utf-8')
        (folder / 'BRIEF.md').write_text(spec, encoding='utf-8')
        (folder / 'acceptance.mjs').write_text(acceptance, encoding='utf-8')
        return folder

    def _preparer(self):
        preparer = TaskPreparer(self.root, self.source, role=self.role, product=True)
        preparer.last_model = 'glm-5.3-flash'
        self.role.last_execution = {'forwarded_count': 4}
        self.role.last_usage = {'complete': True, 'cost_usd': '0.50'}
        return preparer

    def test_a_product_resume_reuses_the_prepared_contract_without_a_model(self):
        folder = self._contract()
        preparer = self._preparer()
        target, evidence = preparer.resume_prepared(folder)
        self.assertEqual(target.feature_id, '007')
        self.assertEqual(target.brief, folder / 'BRIEF.md')
        self.assertEqual(target.protected_check.contract_test, folder / 'acceptance.mjs')
        self.assertEqual(evidence['feature_id'], '007')
        self.assertIsNone(preparer.last_model)
        self.assertIsNone(self.role.last_execution)
        self.assertIsNone(self.role.last_usage)

    def test_a_linked_or_altered_prepared_contract_is_refused(self):
        folder = self._contract()
        preparer = self._preparer()
        linked = self.root / 'linked-prepared'
        linked.symlink_to(folder, target_is_directory=True)
        with self.assertRaisesRegex(PreparationError, 'preparation_workspace_refused'):
            preparer.resume_prepared(linked)
        brief = folder / 'BRIEF.md'
        brief.write_text(brief.read_text() + '\n', encoding='utf-8')
        with self.assertRaisesRegex(PreparationError, 'preparation_workspace_refused'):
            preparer.resume_prepared(folder)
        for feature in ('002', '003', '014'):
            with self.assertRaisesRegex(PreparationError, 'preparation_workspace_refused'):
                preparer.resume_prepared(self._contract(feature=feature))
        plain = TaskPreparer(self.root, self.source, role=self.role, product=False)
        with self.assertRaisesRegex(PreparationError, 'preparation_workspace_refused'):
            plain.resume_prepared(self._contract(feature='008'))

    def test_previous_feature_feedback_extracts_author_and_reviewer_notes(self):
        import sqlite3
        from factory.preparation import previous_feature_feedback
        db_dir = self.root / 'demo/.local/factory'
        db_dir.mkdir(parents=True, exist_ok=True)
        db_path = db_dir / 'factory.db'
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE builds (build_id TEXT, feature_id TEXT, status TEXT, receipt TEXT, updated_ns INTEGER);")
        receipt = json.dumps({
            "feedback": {
                "author": "Hard point: CSRF token needed",
                "reviewers": [{"model": "gpt-6-luna", "text": "Tokenless requests bypass guard"}]
            }
        })
        conn.execute("INSERT INTO builds VALUES ('b1', '003', 'failed', ?, 100);", (receipt,))
        conn.commit()
        conn.close()

        fb = previous_feature_feedback(self.root, '003')
        self.assertIsNotNone(fb)
        self.assertIn("Author finding: Hard point: CSRF token needed", fb)
        self.assertIn("Reviewer (gpt-6-luna): Tokenless requests bypass guard", fb)

    def test_acceptance_prompt_includes_security_rules_and_feedback(self):
        from factory.product_checks import acceptance_prompt
        from factory.preparation import Task
        task = Task('003', 'cat_digest', 'Spec text', 'Arch text', 'base_sha', ['scope/'])
        prompt = acceptance_prompt(task, 'INTERFACES', feedback='Prior feedback line')
        self.assertIn('X-CSRF-Token', prompt)
        self.assertIn('422', prompt)
        self.assertIn('STRICT FEATURE BOUNDS & NEGATIVE CONSTRAINTS', prompt)
        self.assertIn('16KiB', prompt)
        self.assertIn('JUnit/Quarkus fixture', prompt)
        self.assertIn('PREVIOUS ATTEMPT FINDINGS & VERIFIER CONFLICTS', prompt)
        self.assertIn('Prior feedback line', prompt)

    def test_previous_feature_feedback_extracts_circuit_rejection_reasons(self):
        from factory.preparation import previous_feature_feedback
        db_dir = self.root / 'demo/.local/factory'
        db_dir.mkdir(parents=True, exist_ok=True)
        db_path = db_dir / 'factory.db'
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE builds (feature_id TEXT, receipt TEXT, status TEXT, updated_ns INTEGER)")
        receipt = {
            "feedback": {"author": "Forced changes"},
            "circuit": {"votes": [{"model": "deepseek-4.1-flash", "verdict": "reject", "reason": "Out-of-scope changes"}]}
        }
        conn.execute(
            "INSERT INTO builds VALUES ('003', ?, 'failed', 200)",
            (json.dumps(receipt),)
        )
        conn.commit()
        conn.close()

        fb = previous_feature_feedback(self.root, '003')
        self.assertIsNotNone(fb)
        self.assertIn("Author finding: Forced changes", fb)
        self.assertIn("Reviewer rejection (deepseek-4.1-flash): Out-of-scope changes", fb)

    def test_product_prepare_retries_when_baseline_passes_unexpectedly_and_succeeds(self):
        contracts = [
            "import test from 'node:test';\nimport assert from 'node:assert/strict';\ntest('existing', () => { assert.equal(1, 1); });\n",
            "import test from 'node:test';\nimport assert from 'node:assert/strict';\ntest('missing delta', () => { assert.equal(1, 2); });\n",
        ]
        calls = []

        class RetryingRole:
            paid = False
            last_execution = None
            last_usage = None

            def __call__(_, model, prompt, build_id):
                calls.append((model, prompt, build_id))
                _.last_usage = {'complete': True, 'cost_usd': '0'}
                idx = min(len(calls) - 1, len(contracts) - 1)
                return {'status': 'ready', 'contract': contracts[idx], 'reason': 'Synthetic retry fixture'}

        class BaselineChecker:
            def __init__(self):
                self.runs = 0

            def check_target(self, target, repo, frozen):
                self.runs += 1
                if self.runs == 1:
                    return True, {'reason': 'passed', 'contract_assertion_failures': 0}
                return False, {'reason': 'acceptance_failed', 'contract_assertion_failures': 1}

        checker = BaselineChecker()
        preparer = TaskPreparer(self.root, self.source, role=RetryingRole(), checker=checker, base_ref='HEAD', product=True)
        target, evidence = preparer.prepare(
            build={'feature_id': '007', 'build_id': 'a' * 32, 'attempt_id': 'b' * 32},
            catalog=self.catalog,
            spec_dir=self.specs,
            destination=self.root / 'prepared-retry',
            budget=self.budget,
            router=Router(),
            authorized=lambda: True,
        )
        self.assertEqual(len(calls), 2)
        self.assertNotEqual(calls[0][0], calls[1][0])
        self.assertIn('BASELINE CHECK RETRY FEEDBACK', calls[1][1])
        self.assertIn('PASSED on the untouched baseline', calls[1][1])
        self.assertEqual(evidence['negative_control'], 'failed_contract_assertion')
        self.assertEqual(target.feature_id, '007')

    def test_product_prepare_fails_when_all_retries_pass_on_baseline(self):
        passing_contract = "import test from 'node:test';\nimport assert from 'node:assert/strict';\ntest('always passes', () => { assert.equal(1, 1); });\n"

        class AlwaysPassingRole:
            paid = False
            last_execution = None
            last_usage = None

            def __init__(self):
                self.calls = 0

            def __call__(self, model, prompt, build_id):
                self.calls += 1
                self.last_usage = {'complete': True, 'cost_usd': '0'}
                return {'status': 'ready', 'contract': passing_contract, 'reason': 'Always passes'}

        class AlwaysPassingChecker:
            def check_target(self, target, repo, frozen):
                return True, {'reason': 'passed', 'contract_assertion_failures': 0}

        role = AlwaysPassingRole()
        preparer = TaskPreparer(self.root, self.source, role=role, checker=AlwaysPassingChecker(), base_ref='HEAD', product=True)
        with self.assertRaisesRegex(PreparationError, 'preparation_negative_control_missing'):
            preparer.prepare(
                build={'feature_id': '007', 'build_id': 'a' * 32, 'attempt_id': 'b' * 32},
                catalog=self.catalog,
                spec_dir=self.specs,
                destination=self.root / 'prepared-exhausted',
                budget=self.budget,
                router=Router(),
                authorized=lambda: True,
            )
        self.assertGreaterEqual(role.calls, 2)

    def test_validate_acceptance_accepts_destructured_and_named_strict_asserts_and_rejects_noop(self):
        from factory.product_checks import validate_acceptance
        valid_contracts = (
            'import test from "node:test";\nimport assert from "node:assert/strict";\n'
            'const { ok, equal } = assert;\ntest("destructured", () => { ok(true); equal(1, 2); });\n',
            'import test from "node:test";\nimport assert from "node:assert/strict";\n'
            'const { strictEqual: eq } = assert;\ntest("aliased destructured", () => { eq(1, 2); });\n',
            'import { describe, it } from "node:test";\nimport { strictEqual, rejects } from "node:assert/strict";\n'
            'it("named", async () => { strictEqual(1, 2); await rejects(Promise.reject(new Error("x"))); });\n',
            'import test from "node:test";\nimport strictAssert from "node:assert/strict";\n'
            'test("aliased default", () => { strictAssert.equal(1, 2); });\n',
            'import test from "node:test";\nimport assert from "node:assert/strict";\n'
            '// Diagnostic only: verify skip: label inside strings and nested templates is allowed\n'
            'const { ok } = assert;\ntest("comments and strings", () => {\n'
            '  const bad = /[/*]/; /* block after regex */\n'
            '  const q = /[\'"]/.test("x");\n'
            '  const nested = `${[1].map(x => `only: ${x}`)}`;\n'
            '  ok(!q && /https?:\\/\\//.test("http://x") && bad.test("/") && nested);\n'
            '});\n',
            'import test from "node:test";\nimport*as $assert from "node:assert/strict";\n'
            'const { ok: $ok } = $assert;\ntest("dollar and namespace", () => { $assert.equal(1, 2); $ok(true); });\n',
            'import test from "node:test";\nimport assert from "node:assert/strict";\n'
            'const { default: a } = { default: assert };\nconst re = assert;\nconst eq = re.equal;\n'
            'const { ok } = re;\ntest("rebound aliases", () => { ok(true); eq(1, 2); });\n',
        )
        for contract in valid_contracts:
            validate_acceptance(contract)

        invalid_contracts = (
            'import test from "node:test";\nimport assert from "node:assert/strict";\n'
            'const { ok, equal } = assert;\ntest("noop", () => {});\n',
            'import test from "node:test";\nimport assert from "node:assert/strict";\n'
            'const { ok } = unrelatedObject;\ntest("unrelated", () => { ok(true); });\n',
            'import test from "node:test";\nimport assert from "node:assert/strict";\n'
            'test("commented", () => { /* assert.ok(true); */ });\n',
            'import test from "node:test";\nimport assert from "node:assert/strict";\n'
            'test("comment after regex", () => { const r = /[/*]/; /* assert.ok(true); */ });\n',
        )
        for contract in invalid_contracts:
            with self.assertRaisesRegex(PreparationError, 'preparation_acceptance_assertions_missing'):
                validate_acceptance(contract)

        with self.assertRaisesRegex(PreparationError, 'preparation_acceptance_skips_forbidden'):
            validate_acceptance(
                'import test from "node:test";\nimport assert from "node:assert/strict";\n'
                'test("real", { skip: true }, () => { assert.ok(true); });\n'
            )

        with self.assertRaisesRegex(PreparationError, 'preparation_acceptance_skips_forbidden'):
            validate_acceptance(
                'import test from "node:test";\nimport assert from "node:assert/strict";\n'
                'const msg = `${test.skip("inner", () => assert.ok(true))}`;\n'
                'test("outer", () => { assert.ok(msg); });\n'
            )

    def test_product_prepare_retries_invalid_contract_shape_and_succeeds(self):
        contracts = [
            "import test from 'node:test';\nimport assert from 'node:assert/strict';\ntest('no assertions', () => {});\n",
            "import test from 'node:test';\nimport assert from 'node:assert/strict';\ntest('real check', () => { assert.equal(1, 2); });\n",
        ]
        calls = []

        class RetryingShapeRole:
            paid = False
            last_execution = None
            last_usage = None

            def __call__(_, model, prompt, build_id):
                calls.append((model, prompt, build_id))
                _.last_usage = {'complete': True, 'cost_usd': '0'}
                idx = min(len(calls) - 1, len(contracts) - 1)
                return {'status': 'ready', 'contract': contracts[idx], 'reason': 'Synthetic shape retry'}

        class FailingBaselineChecker:
            def check_target(self, target, repo, frozen):
                return False, {'reason': 'acceptance_failed', 'contract_assertion_failures': 1}

        preparer = TaskPreparer(self.root, self.source, role=RetryingShapeRole(),
                                checker=FailingBaselineChecker(), base_ref='HEAD', product=True)
        target, evidence = preparer.prepare(
            build={'feature_id': '007', 'build_id': 'a' * 32, 'attempt_id': 'b' * 32},
            catalog=self.catalog,
            spec_dir=self.specs,
            destination=self.root / 'prepared-shape-retry',
            budget=self.budget,
            router=Router(),
            authorized=lambda: True,
        )
        self.assertEqual(len(calls), 2)
        self.assertNotEqual(calls[0][0], calls[1][0])
        self.assertIn('CONTRACT SHAPE RETRY FEEDBACK', calls[1][1])
        self.assertIn('preparation_acceptance_assertions_missing', calls[1][1])
        self.assertEqual(evidence['negative_control'], 'failed_contract_assertion')
        self.assertEqual(target.feature_id, '007')

    def test_product_prepare_exhausts_retries_on_repeated_invalid_contract_shape(self):
        skipped_contract = (
            "import test from 'node:test';\nimport assert from 'node:assert/strict';\n"
            "test('real', () => { assert.equal(1, 2); });\n"
            "test.skip('skipped', () => { assert.equal(1, 2); });\n"
        )

        class AlwaysInvalidRole:
            paid = False
            last_execution = None
            last_usage = None

            def __init__(self):
                self.calls = 0

            def __call__(self, model, prompt, build_id):
                self.calls += 1
                self.last_usage = {'complete': True, 'cost_usd': '0'}
                return {'status': 'ready', 'contract': skipped_contract, 'reason': 'Always skipped'}

        class NeverReachedChecker:
            def check_target(self, target, repo, frozen):
                raise AssertionError('baseline checker must not run for invalid acceptance shape')

        role = AlwaysInvalidRole()
        preparer = TaskPreparer(self.root, self.source, role=role,
                                checker=NeverReachedChecker(), base_ref='HEAD', product=True)
        with self.assertRaisesRegex(PreparationError, 'preparation_acceptance_skips_forbidden'):
            preparer.prepare(
                build={'feature_id': '007', 'build_id': 'a' * 32, 'attempt_id': 'b' * 32},
                catalog=self.catalog,
                spec_dir=self.specs,
                destination=self.root / 'prepared-shape-exhausted',
                budget=self.budget,
                router=Router(),
                authorized=lambda: True,
            )
        self.assertGreaterEqual(role.calls, 2)

    def test_paid_dispatch_worker_exhausted_preparation_records_telemetry_without_conflict(self):
        from factory.dispatch import DispatchWorker
        from factory.store import Store, HELD

        bad_contract = (
            "import test from 'node:test';\nimport assert from 'node:assert/strict';\n"
            "test('no assertions', () => {});\n"
        )

        class PaidShapeRole:
            paid = True
            last_execution = None
            last_usage = None

            def __init__(self, cost='0.04'):
                self.calls = []
                self.cost = cost

            def __call__(self, model, prompt, build_id):
                self.calls.append(model)
                self.last_execution = {'build_id': build_id, 'forwarded_count': 1}
                self.last_usage = {'complete': True, 'cost_usd': self.cost}
                return {'status': 'ready', 'contract': bad_contract, 'reason': 'No assertions'}

        class StubBuilder:
            paid = True
            engine = 'flue-pi'
            timeout_seconds = 60

        class NeverReachedChecker:
            def check_target(self, target, repo, frozen):
                raise AssertionError('baseline checker must not run')

        store = Store(self.root / 'dispatch-exhaust.db')
        store.admit(['007'], 'k-exhaust', self.catalog)
        role = PaidShapeRole()
        preparer = TaskPreparer(self.root, self.source, role=role,
                                checker=NeverReachedChecker(), base_ref='HEAD', product=True)
        worker = DispatchWorker(
            store, self.catalog, self.specs, self.root / 'work-exhaust',
            {'profile': 'flue-pi', 'mode': 'live', 'deadline_ns': 60_000_000_000,
             'step_cap': 100, 'context_limit': 250_000, 'cost_reservation_usd': '1.00'},
            builder=StubBuilder(), preparer=preparer, budget=self.budget,
            allow_unbudgeted=False, require_circuit=False,
        )
        result = worker.run_once()
        self.assertEqual(result['result'], {'status': 'held', 'reason': 'preparation_unavailable'})
        build = store.board()[0]
        self.assertEqual(build['status'], HELD)
        self.assertGreaterEqual(len(role.calls), 2)
        self.assertEqual(len(worker.router.telemetry.records), len(role.calls))
        self.assertTrue(all(r['outcome'] == 'error' for r in worker.router.telemetry.records))

        # If attempt 0 fails shape retry and attempt 1 hits BudgetError, last_model is cleared
        # so dispatch.py does not re-record attempt 0 or uncalled attempt 1.
        budget2 = DailyBudget(self.root / 'ledger-cap.jsonl')
        budget2.admit('aeion-autonomous-forum', '149.20', note='preseed')
        store2 = Store(self.root / 'dispatch-budget-stop.db')
        store2.admit(['007'], 'k-budget-stop', self.catalog)
        role2 = PaidShapeRole(cost='0.35')
        preparer2 = TaskPreparer(self.root, self.source, role=role2,
                                 checker=NeverReachedChecker(), base_ref='HEAD', product=True)
        worker2 = DispatchWorker(
            store2, self.catalog, self.specs, self.root / 'work-budget-stop',
            {'profile': 'flue-pi', 'mode': 'live', 'deadline_ns': 60_000_000_000,
             'step_cap': 100, 'context_limit': 250_000, 'cost_reservation_usd': '1.00'},
            builder=StubBuilder(), preparer=preparer2, budget=budget2,
            allow_unbudgeted=False, require_circuit=False,
        )
        result2 = worker2.run_once()
        self.assertEqual(result2['result'], {'status': 'held', 'reason': 'preparation_unavailable'})
        self.assertEqual(len(role2.calls), 1)
        self.assertIsNone(preparer2.last_model)
        self.assertEqual(len(worker2.router.telemetry.records), 1)
        self.assertEqual(worker2.router.telemetry.records[0]['model'], role2.calls[0])

    def test_product_preparer_sees_provider_filters_and_service_constants_from_pinned_base(self):
        folder = self.source / 'demo/forum-app/src/main/java/local/aeion/forum'
        folder.mkdir(parents=True)
        (folder / 'AuthResource.java').write_text('@Path("/api/auth") class AuthResource { /* HTTP_ROUTE */ }\n')
        (folder / 'CsrfGuard.java').write_text('@Provider public class CsrfGuard { /* PROVIDER_CSRF_FILTER */ }\n')
        (folder / 'AuthService.java').write_text(
            '@ApplicationScoped public class AuthService {\n'
            '    private static final int MIN_PASSWORD = 12;\n'
            '    /* SERVICE_CONSTANTS_MARKER */\n'
            '}\n'
        )
        (folder / 'InternalHelper.java').write_text('class InternalHelper { /* EXCLUDED_HELPER */ }\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'base interfaces and services')
        (folder / 'CsrfGuard.java').write_text('@Provider public class CsrfGuard { /* UNCOMMITTED_GUARD */ }\n')

        node_contract = "import test from 'node:test';\nimport assert from 'node:assert/strict';\ntest('x', () => { assert.equal(1, 2); });\n"
        calls = []

        class CapturingRole:
            paid = False
            last_execution = None
            last_usage = None

            def __call__(_, model, prompt, build_id):
                calls.append(prompt)
                _.last_usage = {'complete': True, 'cost_usd': '0'}
                return {'status': 'ready', 'contract': node_contract, 'reason': 'Fixture'}

        class FailingChecker:
            def check_target(self, target, repo, frozen):
                return False, {'reason': 'acceptance_failed', 'contract_assertion_failures': 1}

        preparer = TaskPreparer(self.root, self.source, role=CapturingRole(), checker=FailingChecker(),
                                base_ref='HEAD', product=True)
        preparer.prepare(
            build={'feature_id': '007', 'build_id': 'c' * 32, 'attempt_id': 'd' * 32},
            catalog=self.catalog, spec_dir=self.specs, destination=self.root / 'prepared-prod-ifaces',
            budget=self.budget, router=Router(), authorized=lambda: True,
        )
        prompt = calls[0]
        self.assertIn('HTTP_ROUTE', prompt)
        self.assertIn('PROVIDER_CSRF_FILTER', prompt)
        self.assertIn('MIN_PASSWORD = 12', prompt)
        self.assertIn('SERVICE_CONSTANTS_MARKER', prompt)
        self.assertNotIn('EXCLUDED_HELPER', prompt)
        self.assertNotIn('UNCOMMITTED_GUARD', prompt)

    def test_acceptance_prompt_includes_twelve_char_password_rule(self):
        from factory.product_checks import acceptance_prompt
        from factory.preparation import Task
        task = Task('005', 'cat_digest', 'Spec text', 'Arch text', 'base_sha', ['scope/'])
        prompt = acceptance_prompt(task, 'INTERFACES')
        self.assertIn('12', prompt)
        self.assertIn('***', prompt)

    def test_correction_after_gate_failure_reprepares_only_on_frozen_contract_conflict(self):
        import sqlite3
        node_contract = "import test from 'node:test';\nimport assert from 'node:assert/strict';\ntest('x', () => { assert.equal(1, 2); });\n"
        new_contract = "import test from 'node:test';\nimport assert from 'node:assert/strict';\ntest('new', () => { assert.equal(2, 3); });\n"
        calls = []

        class RecordingRole:
            paid = False
            last_execution = None
            last_usage = None

            def __call__(_, model, prompt, build_id):
                calls.append(prompt)
                _.last_usage = {'complete': True, 'cost_usd': '0'}
                return {'status': 'ready', 'contract': new_contract, 'reason': 'Reprepared'}

        class FailingChecker:
            def check_target(self, target, repo, frozen):
                return False, {'reason': 'acceptance_failed', 'contract_assertion_failures': 1}

        task = freeze_task(self.catalog, '007', self.specs, self.architecture, self.base, product=True)
        evidence = {**task.identity(), 'task_digest': task.digest(), 'acceptance_digest': _sha(node_contract),
                    'preparer_model': 'glm-5.3-flash', 'negative_control': 'failed_contract_assertion', 'synthetic': True}

        db_dir = self.root / 'demo/.local/factory'
        db_dir.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_dir / 'factory.db'))
        conn.execute('CREATE TABLE builds (build_id TEXT, feature_id TEXT, status TEXT, receipt TEXT, updated_ns INTEGER)')

        def setup_prev(build_id, author_note):
            prev_dir = self.root / 'work' / build_id / 'prepared'
            prev_dir.mkdir(parents=True, exist_ok=True)
            (prev_dir / 'task.json').write_text(json.dumps(evidence), encoding='utf-8')
            (prev_dir / 'BRIEF.md').write_text(task.specification, encoding='utf-8')
            (prev_dir / 'acceptance.mjs').write_text(node_contract, encoding='utf-8')
            receipt = json.dumps({'gate': {'status': 'failed'}, 'feedback': {'author': author_note}})
            conn.execute('INSERT INTO builds VALUES (?, ?, ?, ?, ?)', (build_id, '007', 'failed', receipt, 100))

        setup_prev('prev_ordinary_fail', 'Fixed typo in Java handler; check failed on assertion.')
        setup_prev('prev_policy_conflict', 'Still blocked: read-only acceptance password violates 12-character password policy.')
        conn.commit()
        conn.close()

        preparer = TaskPreparer(self.root, self.source, role=RecordingRole(), checker=FailingChecker(),
                                base_ref='HEAD', product=True)
        _, reused_ev = preparer.prepare(
            build={'feature_id': '007', 'build_id': 'c1' * 16, 'attempt_id': 'd1' * 16,
                   'idempotency_key': 'factory-correction:prev_ordinary_fail'},
            catalog=self.catalog, spec_dir=self.specs, destination=self.root / 'work/c1/prepared',
            budget=self.budget, router=Router(), authorized=lambda: True,
        )
        self.assertEqual(len(calls), 0)
        self.assertEqual(reused_ev['acceptance_digest'], _sha(node_contract))

        _, rep_ev = preparer.prepare(
            build={'feature_id': '007', 'build_id': 'c2' * 16, 'attempt_id': 'd2' * 16,
                   'idempotency_key': 'factory-correction:prev_policy_conflict'},
            catalog=self.catalog, spec_dir=self.specs, destination=self.root / 'work/c2/prepared',
            budget=self.budget, router=Router(), authorized=lambda: True,
        )
        self.assertEqual(len(calls), 1)
        self.assertEqual(rep_ev['acceptance_digest'], _sha(new_contract))

    def test_correction_reprepare_with_failed_first_author_pins_round_author_in_dispatch(self):
        from factory.models import RoutingError, family
        from factory.routing import OutcomeTelemetry, cohort_for
        from factory.store import FAILED, Store

        store = Store(self.root / 'factory.db')
        cohort = cohort_for(self.catalog.by_id['007'], 'product')
        telemetry = OutcomeTelemetry(store, cohort, 'prior-attempt', synthetic=False)
        telemetry.record('glm-5.3-flash', 'author', 'failed', latency_ms=100, cost_usd='0.01')
        router = Router(telemetry=telemetry)
        self.assertEqual(router.select('author', require_role='author'), 'qwen-3.8-flash')

        b1_id = store.admit(['007'], 'owner-launch-1', self.catalog)['build_ids'][0]
        b1 = store.claim_next(self.catalog)
        self.assertEqual(b1['build_id'], b1_id)

        preparer = TaskPreparer(self.root, self.source, role=self.role, checker=self.checker, base_ref='HEAD')
        b1_dir = self.root / 'work' / b1_id / 'prepared'
        preparer.prepare(
            build=b1, catalog=self.catalog, spec_dir=self.specs, destination=b1_dir,
            budget=self.budget, router=router, authorized=lambda: True, store=store,
        )
        self.assertEqual(len(self.role.calls), 1)
        self.assertFalse((b1_dir / 'reprepare_needed').exists())

        done = store.complete_attempt(
            b1['attempt_id'], b1['attempt_generation'],
            receipt={
                'author_model': 'glm-5.3-flash',
                'gate': {'status': 'failed'},
                'feedback': {'author': 'blocked: forced by the frozen acceptance contract'},
            },
            terminal=FAILED,
        )
        self.assertEqual(done['status'], 'completed')

        b2_id = store.admit(
            ['007'], f'factory-correction:{b1_id}', self.catalog,
            actor='supervisor', correction={'previous_build_id': b1_id, 'attempt': 1, 'round': 1},
        )['build_ids'][0]
        b2 = store.claim_next(self.catalog)
        self.assertEqual(b2['build_id'], b2_id)

        b2_dir = self.root / 'work' / b2_id / 'prepared'
        preparer.prepare(
            build=b2, catalog=self.catalog, spec_dir=self.specs, destination=b2_dir,
            budget=self.budget, router=router, authorized=lambda: True, store=store,
        )
        self.assertEqual(len(self.role.calls), 2)
        self.assertNotEqual(family(preparer.last_model), 'zhipu')
        # Match FlueBuilder continuation pinning: round > 0 must still allow glm-5.3-flash.
        author_b2 = router.select(
            'author', require_role='author',
            exclude_models=[m for m in router.models if m != 'glm-5.3-flash'],
            exclude_families=[family(preparer.last_model)],
        )
        self.assertEqual(author_b2, 'glm-5.3-flash')

        # Also verify attempt 2 (round == 0) reads the correction chain and does not pick an excluded author's preparer conflict.
        done2 = store.complete_attempt(
            b2['attempt_id'], b2['attempt_generation'],
            receipt={
                'author_model': 'glm-5.3-flash',
                'gate': {'status': 'failed'},
                'feedback': {'author': 'forced by the frozen acceptance contract'},
            },
            terminal=FAILED,
        )
        self.assertEqual(done2['status'], 'completed')
        b3_id = store.admit(
            ['007'], f'factory-correction:{b2_id}', self.catalog,
            actor='supervisor', correction={'previous_build_id': b2_id, 'attempt': 2, 'round': 0},
        )['build_ids'][0]
        b3 = store.claim_next(self.catalog)
        self.assertEqual(b3['build_id'], b3_id)
        preparer.prepare(
            build=b3, catalog=self.catalog, spec_dir=self.specs,
            destination=self.root / 'work' / b3_id / 'prepared',
            budget=self.budget, router=router, authorized=lambda: True, store=store,
        )
        self.assertEqual(len(self.role.calls), 3)
        self.assertNotEqual(family(preparer.last_model), 'qwen')
        try:
            author_b3 = router.select(
                'author', require_role='author',
                exclude_models=['glm-5.3-flash'],
                exclude_families=[family(preparer.last_model)],
            )
        except RoutingError as err:
            self.fail(f'Unexpected RoutingError after round=0 reprepare: {err}')
        self.assertEqual(author_b3, 'qwen-3.8-flash')

    def test_validate_acceptance_rejects_masked_literals_and_syntax_errors_and_retries(self):
        from factory.preparation import PreparationError, TaskPreparer
        from factory.product_checks import validate_acceptance

        valid_js = (
            "import test from 'node:test';\n"
            "import assert from 'node:assert/strict';\n"
            "const PW = 'ForumUserPass01!';\n"
            "const note = (raw) => `${raw.slice(0, 240)}…`;\n"
            "test('works', () => { assert.equal(PW.length >= 12, true); assert.ok(note('abc')); });\n"
        )
        self.assertIsNone(validate_acceptance(valid_js))

        for bad_name, bad_js in (
            ('star_cookie', valid_js.replace("'ForumUserPass01!'", "'***'")),
            ('ellipsis_pw', valid_js.replace("'ForumUserPass01!'", "'Agora…ss_001!'")),
        ):
            with self.subTest(case=bad_name), self.assertRaisesRegex(PreparationError, 'preparation_acceptance_masked_literal'):
                validate_acceptance(bad_js)

        bad_syntax = valid_js.replace('});\n', '')
        with self.assertRaisesRegex(PreparationError, 'preparation_acceptance_syntax_invalid'):
            validate_acceptance(bad_syntax)

        calls = []

        class RetryingShapeRole:
            paid = False
            last_execution = None
            last_usage = None

            def __call__(_, model, prompt, build_id):
                calls.append((model, prompt))
                _.last_usage = {'complete': True, 'cost_usd': '0'}
                contract = bad_syntax if len(calls) == 1 else valid_js
                return {'status': 'ready', 'contract': contract, 'reason': 'Fixture'}

        class FailingChecker:
            def check_target(self, target, repo, frozen):
                return False, {'reason': 'acceptance_failed', 'contract_assertion_failures': 1}

        preparer = TaskPreparer(self.root, self.source, role=RetryingShapeRole(), checker=FailingChecker(),
                                base_ref='HEAD', product=True)
        preparer.prepare(
            build={'feature_id': '007', 'build_id': '1' * 32, 'attempt_id': '2' * 32},
            catalog=self.catalog, spec_dir=self.specs, destination=self.root / 'prepared-shape-retry',
            budget=self.budget, router=Router(), authorized=lambda: True,
        )
        self.assertEqual(len(calls), 2)
        self.assertNotEqual(calls[0][0], calls[1][0])
        self.assertIn('preparation_acceptance_syntax_invalid', calls[1][1])

    def test_product_baseline_rejects_test_error_even_with_failing_assertions_and_retries(self):
        from factory.models import family
        from factory.preparation import TaskPreparer, _baseline_ok

        self.assertFalse(_baseline_ok(True, False, {
            'reason': 'acceptance_failed', 'contract_assertion_failures': 1, 'test_errors': 0,
            'test_counts': {'tests': 6, 'failed': 1, 'skipped': 1, 'cancelled': 0, 'todo': 0},
        }, 'C', None, '005')[0])
        self.assertFalse(_baseline_ok(True, False, {
            'reason': 'acceptance_failed', 'contract_assertion_failures': 1,
            'test_counts': {'tests': 6, 'failed': 6, 'skipped': 0, 'cancelled': 0, 'todo': 0},
        }, 'C', None, '005')[0])
        self.assertTrue(_baseline_ok(True, False, {
            'reason': 'acceptance_failed', 'contract_assertion_failures': 1, 'test_errors': 0,
            'test_counts': {'tests': 2, 'failed': 2, 'skipped': 0, 'cancelled': 0, 'todo': 0},
            'failed_tests': [{'line': 4, 'code': 'assertion_failed', 'error_type': 'AssertionError'}],
        }, 'C', None, '005')[0])

        good_js = (
            "import test from 'node:test';\nimport assert from 'node:assert/strict';\n"
            "test('baseline', () => { assert.equal(404, 200); });\n"
        )
        calls = []

        class BaselineRetryRole:
            paid = False
            last_execution = None
            last_usage = None

            def __call__(_, model, prompt, build_id):
                calls.append((model, prompt))
                _.last_usage = {'complete': True, 'cost_usd': '0'}
                return {'status': 'ready', 'contract': good_js, 'reason': 'Fixture'}

        class CheckerWithRuntimeCrashFirst:
            def __init__(self):
                self.n = 0

            def check_target(self, target, repo, frozen):
                self.n += 1
                if self.n == 1:
                    return False, {
                        'reason': 'acceptance_failed', 'contract_assertion_failures': 1, 'test_errors': 5,
                        'test_counts': {'tests': 6, 'failed': 6, 'skipped': 0, 'cancelled': 0, 'todo': 0},
                        'failed_tests': [
                            {'line': 60, 'code': 'test_error', 'error_type': 'TypeError'},
                            {'line': 95, 'code': 'assertion_failed', 'error_type': 'AssertionError'},
                        ],
                    }
                return False, {
                    'reason': 'acceptance_failed', 'contract_assertion_failures': 1, 'test_errors': 0,
                    'test_counts': {'tests': 6, 'failed': 1, 'skipped': 0, 'cancelled': 0, 'todo': 0},
                    'failed_tests': [{'line': 95, 'code': 'assertion_failed', 'error_type': 'AssertionError'}],
                }

        preparer = TaskPreparer(self.root, self.source, role=BaselineRetryRole(),
                                checker=CheckerWithRuntimeCrashFirst(), base_ref='HEAD', product=True)
        preparer.prepare(
            build={'feature_id': '007', 'build_id': '3' * 32, 'attempt_id': '4' * 32},
            catalog=self.catalog, spec_dir=self.specs, destination=self.root / 'prepared-baseline-err',
            budget=self.budget, router=Router(), authorized=lambda: True,
        )
        self.assertEqual(len(calls), 2)
        self.assertNotEqual(family(calls[0][0]), family(calls[1][0]))
        self.assertIn('5 test_error(s)', calls[1][1])
        self.assertIn('line 60 (TypeError)', calls[1][1])

    def test_reprepare_triggers_on_runtime_crash_and_passes_supervisor_feedback(self):
        from factory.preparation import TaskPreparer, freeze_task
        from factory.store import FAILED, Store

        node_contract = (
            "import test from 'node:test';\nimport assert from 'node:assert/strict';\n"
            "test('x', () => { assert.equal(1, 2); });\n"
        )
        new_contract = (
            "import test from 'node:test';\nimport assert from 'node:assert/strict';\n"
            "test('fixed', () => { assert.equal(2, 3); });\n"
        )
        calls = []

        class RecordingRole:
            paid = False
            last_execution = None
            last_usage = None

            def __call__(_, model, prompt, build_id):
                calls.append(prompt)
                _.last_usage = {'complete': True, 'cost_usd': '0'}
                return {'status': 'ready', 'contract': new_contract, 'reason': 'Fixed'}

        class FailingChecker:
            def check_target(self, target, repo, frozen):
                return False, {'reason': 'acceptance_failed', 'contract_assertion_failures': 1, 'test_errors': 0}

        store = Store(self.root / 'reprepare.db')
        task = freeze_task(self.catalog, '007', self.specs, self.architecture, self.base, product=True)
        evidence = {**task.identity(), 'task_digest': task.digest(), 'acceptance_digest': _sha(node_contract),
                    'preparer_model': 'glm-5.3-flash', 'negative_control': 'failed_contract_assertion', 'synthetic': True}

        b1_id = store.admit(['007'], 'launch-crash-1', self.catalog)['build_ids'][0]
        b1 = store.claim_next(self.catalog)
        b1_dir = self.root / 'work' / b1_id / 'prepared'
        b1_dir.mkdir(parents=True, exist_ok=True)
        (b1_dir / 'task.json').write_text(json.dumps(evidence), encoding='utf-8')
        (b1_dir / 'BRIEF.md').write_text(task.specification, encoding='utf-8')
        (b1_dir / 'acceptance.mjs').write_text(node_contract, encoding='utf-8')
        store.complete_attempt(
            b1['attempt_id'], b1['attempt_generation'],
            receipt={
                'reason': 'builder_error',
                'execution': {'check': {
                    'status': 'failed', 'reason': 'acceptance_failed',
                    'contract_assertion_failures': 0, 'test_errors': 6,
                    'failed_tests': ['line 134: test_error (TypeError)'],
                }},
                'feedback': {'author': 'Repeated check failure'},
            },
            terminal=FAILED,
        )

        b2_id = store.admit(
            ['007'], f'factory-correction:{b1_id}', self.catalog,
            actor='supervisor', correction={'previous_build_id': b1_id, 'attempt': 1, 'round': 1},
        )['build_ids'][0]
        b2 = store.claim_next(self.catalog)
        preparer = TaskPreparer(self.root, self.source, role=RecordingRole(), checker=FailingChecker(),
                                base_ref='HEAD', product=True)
        _, rep_ev = preparer.prepare(
            build=b2, catalog=self.catalog, spec_dir=self.specs,
            destination=self.root / 'work' / b2_id / 'prepared',
            budget=self.budget, router=Router(), authorized=lambda: True, store=store,
        )
        self.assertEqual(len(calls), 1)
        self.assertEqual(rep_ev['acceptance_digest'], _sha(new_contract))
        self.assertIn('Supervisor verifier: acceptance_failed with test_error (line 134: test_error (TypeError))', calls[0])

        from factory.preparation import _extract_runtime_crash
        self.assertIsNone(_extract_runtime_crash({
            'gate': {'status': 'failed', 'results': {'prepared_product': {'status': 'failed', 'detail': {
                'reason': 'acceptance_failed', 'contract_assertion_failures': 1, 'test_errors': 0,
            }}}},
            'execution': {'check': {
                'status': 'failed', 'reason': 'acceptance_failed',
                'contract_assertion_failures': 0, 'test_errors': 6,
                'failed_tests': ['line 134: test_error (TypeError)'],
            }},
        }))
        self.assertIsNone(_extract_runtime_crash({
            'gate': {'status': 'passed'},
            'execution': {'check': {
                'status': 'failed', 'reason': 'acceptance_failed',
                'contract_assertion_failures': 0, 'test_errors': 6,
                'failed_tests': ['line 134: test_error (TypeError)'],
            }},
        }))


def _sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


if __name__ == '__main__':
    unittest.main()
