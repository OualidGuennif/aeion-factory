"""The old incomplete review envelope gets one fenced reassessment, never a vote override."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import subprocess
from types import SimpleNamespace
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory.manifest import Catalog
from factory.store import Store
from factory.dispatch import DispatchWorker
from factory.preparation import TaskPreparer,freeze_task
from factory.product_checks import prepared_target
from factory.freeze import freeze_build
from factory.artifact import validate_artifact
from factory.budget import DailyBudget
from factory.review_circuit import CircuitError


class ReviewContextClaimTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=Store(Path(self.temp.name)/'factory.db')
        self.catalog=Catalog({'schema_version':2,'count':1,'features':[{
            'id':'001','title':'Fixture','area':'foundation','size':'S','parallel':False,
            'phase':'P0','tier':3,'write_paths':['demo/forum/product/'],'depends_on':[],'file':'001.md'}]})
        self.store.admit(['001'],'fixture',self.catalog)
        self.build=self.store.claim_next(self.catalog)
        self.receipt={'simulated':False,'author_model':'glm-5.3-flash','artifact_digest':'a'*64,
            'gate':{'status':'passed'},'review':{'status':'approved'},
            'execution':{'build_id':self.build['build_id'],'role':'author','engine':'flue-pi',
                'forwarded_count':1,'usage':{'complete':True,'cost_usd':'0.10'}},
            'circuit':{'status':'held','reason':'reviewer_rejected','votes':[{
                'model':'qwen-3.8-flash','verdict':'reject','reason':'Synthetic fixture',
                'execution':{'role':'review','engine':'flue-pi','forwarded_count':1,
                    'usage':{'complete':True,'cost_usd':'0.01'}}}]}}

    def hold(self,receipt):
        self.store.hold_dispatched(self.build,'owner_review_required',receipt=receipt)
        row=self.store.board()[0]
        return hashlib.sha256(row['receipt'].encode()).hexdigest()

    def test_reassessment_preserves_rejection_and_fences_duplicate_and_old_callbacks(self):
        digest=self.hold(self.receipt)
        claimed=self.store.claim_review_context(self.build['build_id'],self.catalog,digest,10**12)
        self.assertIsNotNone(claimed)
        self.assertEqual(claimed['attempt_generation'],self.build['attempt_generation']+1)
        self.assertFalse(self.store.attempt_authorized(self.build['attempt_id'],self.build['attempt_generation']))
        self.assertTrue(self.store.attempt_authorized(claimed['attempt_id'],claimed['attempt_generation']))
        self.assertIsNone(self.store.claim_review_context(self.build['build_id'],self.catalog,digest,10**12))

        events=self.store.events(self.build['build_id'])
        event=next(x for x in events if x['event']=='review_context_reassessment')
        self.assertEqual(json.loads(event['detail'])['previous_receipt'],self.receipt)
        self.store.hold_dispatched(claimed,'owner_review_required',receipt=json.loads(claimed['receipt']))
        digest=hashlib.sha256(self.store.board()[0]['receipt'].encode()).hexdigest()
        self.assertIsNone(self.store.claim_review_context(claimed['build_id'],self.catalog,digest,10**12))

    def test_missing_usage_new_format_and_changed_receipts_never_rearm(self):
        for path,value in [(('execution','usage','complete'),False),
                           (('execution','failure'),'EXPORT_FAILED'),
                           (('circuit','review_input_version'),2),
                           (('simulated',),True), (('gate','status'),'failed')]:
            with self.subTest(path=path):
                receipt=copy.deepcopy(self.receipt);item=receipt
                for key in path[:-1]:item=item[key]
                item[path[-1]]=value
                digest=self.hold(receipt)
                self.assertIsNone(self.store.claim_review_context(self.build['build_id'],self.catalog,digest,10**12))
                # Restore the dispatched fixture through a new independent temporary store.
                self.setUp()
        digest=self.hold(self.receipt)
        self.assertIsNone(self.store.claim_review_context(self.build['build_id'],self.catalog,'0'*64,10**12))
        self.store.cancel(self.build['build_id'])
        self.assertIsNone(self.store.claim_review_context(self.build['build_id'],self.catalog,digest,10**12))


class ReviewContextDispatchTests(unittest.TestCase):
    """Git/files/state are real; model and isolated checker transports are scripted fixtures."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        architecture=self.root/'demo/forum/ARCHITECTURE.md';architecture.parent.mkdir(parents=True)
        architecture.write_text('Incremental PostgreSQL and React architecture.\n')
        specs=self.root/'specs';specs.mkdir();(specs/'001.md').write_text('# 001\n## Acceptance checks\n- [ ] Bound settings.\n')
        self.catalog=Catalog({'schema_version':2,'count':1,'features':[{
            'id':'001','title':'Settings','area':'foundation','size':'S','phase':'P0','parallel':False,
            'tier':3,'file':'001.md','write_paths':['demo/forum-app/'],'depends_on':[],
            'architecture_digest':hashlib.sha256(architecture.read_bytes()).hexdigest()}]})
        source=self.root/'source';path=source/'demo/forum-app/src/main/resources/settings.properties'
        path.parent.mkdir(parents=True);path.write_text('database=sqlite\nlimit=1\n')
        for args in (['init','-q'],['add','.'],['-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
                    'commit','-qm','base']):
            subprocess.run(['git','-C',str(source),*args],capture_output=True,check=True)
        self.base=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
        self.store=Store(self.root/'factory.db');self.store.admit(['001'],'fixture',self.catalog)
        self.build=self.store.claim_next(self.catalog);folder=self.root/'work'/self.build['build_id']
        prepared=folder/'prepared';prepared.mkdir(parents=True)
        task=freeze_task(self.catalog,'001',specs,architecture,self.base,product=True)
        acceptance='Synthetic fixture contract; the checker transport is scripted.\n'
        target=prepared_target(self.root,source,task,prepared,acceptance)
        target.materialize(folder/'repo')
        self.file=folder/'repo/demo/forum-app/src/main/resources/settings.properties'
        self.file.write_text('database=sqlite\nlimit=2\n')
        (folder/'BRIEF.md').write_text(task.specification)
        self.config={'profile':'fixture','mode':'live','deadline_ns':1800*10**9,'step_cap':200,
            'context_limit':250000,'cost_reservation_usd':'0.50'}
        frozen=freeze_build(self.build,self.catalog,specs,self.base,self.config,
            write_scopes=target.write_paths,spec_path=target.brief,acceptance_path=target.protected_check.contract_test)
        artifact=validate_artifact(folder/'repo',frozen.write_scopes)
        execution={'build_id':self.build['build_id'],'role':'author','engine':'flue-pi',
            'forwarded_count':1,'usage':{'complete':True,'cost_usd':'0.10'}}
        self.prior={'simulated':False,'author_model':'glm-5.3-flash','execution':execution,
            'base_sha':self.base,'frozen_digest':frozen.digest(),'artifact_digest':artifact['digest'],
            'preparation':{**task.identity(),'task_digest':task.digest(),'synthetic':False,
                'acceptance_digest':frozen.acceptance_digest,'preparer_model':None},
            'gate':{'status':'passed'},'review':{'status':'approved'},
            'circuit':{'status':'held','reason':'reviewer_rejected','votes':[{
                'model':'qwen-3.8-flash','verdict':'reject','execution':{**execution,'role':'review'}}]}}
        self.store.hold_dispatched(self.build,'owner_review_required',receipt=self.prior)
        self.checks=[];self.votes=[];self.requests=[]
        checker=SimpleNamespace(check_target=lambda target,repo,frozen:
            (self.checks.append(str(repo)) or True,{'reason':'passed'}))
        outer=self
        class Reviewer:
            paid=True;timeout_seconds=60;cost_limit='0.10';last_usage=None;last_execution=None
            def __call__(self,model,prompt):
                self.last_usage={'complete':True,'cost_usd':'0.01'}
                self.last_execution={'role':'review','engine':'flue-pi','forwarded_count':1,'usage':self.last_usage}
                outer.votes.append((model,prompt))
                if model==outer.failure_model:
                    self.last_execution['failure']=outer.failure_reason
                    if outer.unknown_failure_usage:self.last_usage['complete']=False
                    if outer.zero_forward_failure:
                        self.last_execution['forwarded_count'] = 0
                        self.last_usage.update(cost_usd='0', basis='proven_no_transport', output_tokens=0)
                    raise ValueError(outer.failure_reason)
                return {'verdict':outer.verdict,'reason':'Synthetic fixture'}
        self.verdict='approve'
        self.failure_model=None
        self.failure_reason='REVIEW_RESULT_MISSING'
        self.unknown_failure_usage=False
        self.zero_forward_failure=False
        self.budget=DailyBudget(self.root/'ledger.jsonl')
        self.worker=DispatchWorker(self.store,self.catalog,specs,self.root/'work',self.config,
            builder=SimpleNamespace(paid=True,engine='flue-pi',last_execution=None),
            preparer=TaskPreparer(self.root,source,product=True,synchronize=lambda:self.base),
            check_sandbox=checker,review_complete=Reviewer(),budget=self.budget)
        self.worker.admission_check=lambda:True
        self.worker.publication=SimpleNamespace(stage=lambda build,request,receipt:
            self.requests.append((request,receipt)) or True)

    def test_reassessment_reruns_gate_and_two_fresh_votes_without_author_or_double_charge(self):
        result=self.worker.reassess_review_context(self.build['build_id'])
        self.assertEqual(result['result']['status'],'publication_queued')
        self.assertEqual(len(self.checks),1)
        self.assertEqual([m for m,_ in self.votes],['qwen-3.8-flash','deepseek-4.1-flash'])
        self.assertTrue(all('-limit=1\n+limit=2' in p for _,p in self.votes))
        request,receipt=self.requests[0]
        self.assertEqual(receipt['execution'],self.prior['execution'])
        self.assertTrue(receipt['review_context']['author_reused'])
        self.assertEqual(request['artifact_digest'],self.prior['artifact_digest'])
        self.assertEqual(str(self.budget.spent('aeion-autonomous-forum')),'0.02')

    def test_changed_artifact_or_base_refuses_before_models_or_rearming(self):
        self.file.write_text('changed after original review\n')
        with self.assertRaisesRegex(CircuitError,'artifact_changed'):
            self.worker.reassess_review_context(self.build['build_id'])
        self.assertEqual(self.votes,[]);self.assertEqual(self.store.board()[0]['status'],'held')
        self.worker.preparer.synchronize=lambda:'f'*40
        with self.assertRaisesRegex(CircuitError,'base_changed'):
            self.worker.reassess_review_context(self.build['build_id'])

    def test_a_fresh_rejection_stays_held_and_cannot_be_repeated_as_context_repair(self):
        self.verdict='reject'
        self.worker.reassess_review_context(self.build['build_id'])
        self.assertEqual(self.requests,[])
        self.assertEqual(self.store.board()[0]['status'],'held')
        with self.assertRaisesRegex(CircuitError,'not_eligible'):
            self.worker.reassess_review_context(self.build['build_id'])
        self.assertEqual(len(self.votes),1)
        with self.assertRaisesRegex(CircuitError,'not_eligible'):
            self.worker.reassess_review_context(self.build['build_id'],retry_failed_review=True)
        self.assertEqual(len(self.votes),1)

    def test_one_failed_review_retry_rechecks_and_replaces_both_votes_without_rerunning_author(self):
        self.failure_model='deepseek-4.1-flash'
        self.worker.reassess_review_context(self.build['build_id'])
        self.assertEqual(self.requests,[])
        self.assertEqual([m for m,_ in self.votes],['qwen-3.8-flash','deepseek-4.1-flash'])
        self.failure_model=None
        result=self.worker.reassess_review_context(self.build['build_id'],retry_failed_review=True)
        self.assertEqual(result['result']['status'],'publication_queued')
        self.assertEqual([m for m,_ in self.votes][-2:],['deepseek-4.1-flash','qwen-3.8-flash'])
        self.assertEqual(len(self.checks),2)
        self.assertEqual(str(self.budget.spent('aeion-autonomous-forum')),'0.04')
        self.assertEqual(self.requests[0][1]['execution'],self.prior['execution'])

    def test_a_second_failed_review_stays_held_without_an_unbounded_retry(self):
        self.failure_model='deepseek-4.1-flash'
        self.worker.reassess_review_context(self.build['build_id'])
        self.worker.reassess_review_context(self.build['build_id'],retry_failed_review=True)
        self.assertEqual(len(self.votes),3)
        self.assertEqual(self.requests,[])
        with self.assertRaisesRegex(CircuitError,'not_eligible'):
            self.worker.reassess_review_context(self.build['build_id'],retry_failed_review=True)
        self.assertEqual(len(self.votes),3)

    def test_operator_recovers_one_review_handover_after_the_normal_retry(self):
        import sqlite3
        receipt = {**self.prior, 'review_context': {'retry_failed_review': True, 'author_reused': True}}
        execution = {'role': 'review', 'engine': 'flue-pi', 'failure': 'AEION_HANDOVER',
                     'forwarded_count': 2, 'usage': {'complete': True, 'cost_usd': '0.8938762'}}
        failure = {'model': 'claude-haiku-5.5', 'verdict': 'error', 'reason': 'AEION_HANDOVER',
                   'execution': execution}
        receipt['circuit'] = {'status': 'held', 'reason': 'reviewer_failed', 'review_input_version': 2,
                              'votes': [failure]}

        def save_receipt():
            with sqlite3.connect(self.store.path) as conn:
                conn.execute('UPDATE builds SET receipt=? WHERE build_id=?',
                             (json.dumps(receipt), self.build['build_id']))

        build_id = self.build['build_id']
        save_receipt()
        with self.assertRaisesRegex(CircuitError, 'not_eligible'):
            self.worker.reassess_review_context(build_id, retry_failed_review=True)

        for reason, complete in (('REVIEW_RESULT_MISSING', True), ('AEION_HANDOVER', False)):
            execution.update(failure=reason, usage={'complete': complete, 'cost_usd': '0.8938762'})
            failure['reason'] = reason
            save_receipt()
            with self.assertRaisesRegex(CircuitError, 'not_eligible'):
                self.worker.reassess_review_context(build_id, recover_review_handover=True)
        self.assertEqual(self.votes, [])
        self.assertEqual(self.checks, [])

        execution.update(failure='AEION_HANDOVER', usage={'complete': True, 'cost_usd': '0.8938762'})
        save_receipt()
        self.failure_model = 'claude-haiku-5.5'
        self.verdict = 'reject'
        self.worker.reassess_review_context(build_id, recover_review_handover=True)
        self.assertEqual([(row['build_id'], row['status']) for row in self.store.board()], [(build_id, 'held')])
        self.assertEqual(len(self.checks), 1)
        self.assertEqual([model for model, _ in self.votes], ['qwen-3.8-flash'])
        self.assertEqual(self.requests, [])
        reviewed = json.loads(self.store.board()[0]['receipt'])
        self.assertEqual(reviewed['artifact_digest'], self.prior['artifact_digest'])
        self.assertEqual(reviewed['execution'], self.prior['execution'])
        self.assertTrue(reviewed['review_context']['handover_recovery'])
        events = self.store.events(build_id)
        archived = next(e for e in events if e['event'] == 'review_context_reassessment')
        self.assertEqual(json.loads(archived['detail'])['previous_receipt'], receipt)

        receipt['review_context'] = reviewed['review_context']
        save_receipt()
        with self.assertRaisesRegex(CircuitError, 'not_eligible'):
            self.worker.reassess_review_context(build_id, recover_review_handover=True)
        self.assertEqual(len(self.votes), 1)

    def test_operator_retries_a_budget_hold_once_on_the_same_artifact(self):
        from decimal import Decimal
        from factory.dispatch import review_retry_eligible

        scope = self.worker.budget_scope
        build_id = self.build['build_id']
        self.budget.limits[scope] = Decimal('0.10')
        self.worker.reassess_review_context(build_id)
        held = json.loads(self.store.board()[0]['receipt'])
        self.assertEqual(held['circuit']['reason'], 'review_budget_unavailable')
        self.assertEqual(len(held['circuit']['votes']), 1)
        self.assertFalse(review_retry_eligible(held))
        self.assertEqual(self.requests, [])

        self.budget.limits[scope] = Decimal('1')
        result = self.worker.reassess_review_context(build_id, retry_failed_review=True)
        self.assertEqual(result['result']['status'], 'publication_queued')
        self.assertEqual(len(self.votes), 3)
        _, receipt = self.requests[0]
        self.assertTrue(receipt['review_context']['budget_recovery'])
        self.assertEqual(receipt['artifact_digest'], self.prior['artifact_digest'])
        self.assertEqual(receipt['execution'], self.prior['execution'])
        self.assertEqual(len(receipt['circuit']['votes']), 2)
        claimed = self.store.board()[0]
        self.store.hold_dispatched(claimed, 'owner_review_required',
            receipt={**held, 'review_context': receipt['review_context']})
        with self.assertRaisesRegex(CircuitError, 'not_eligible'):
            self.worker.reassess_review_context(build_id, retry_failed_review=True)
        self.assertEqual(len(self.votes), 3)

    def test_retry_does_not_free_an_old_unknown_review_reservation(self):
        self.failure_model='deepseek-4.1-flash';self.unknown_failure_usage=True
        self.worker.reassess_review_context(self.build['build_id'])
        self.assertEqual(str(self.budget.spent('aeion-autonomous-forum')),'0.11')
        self.failure_model=None
        self.worker.reassess_review_context(self.build['build_id'],retry_failed_review=True)
        self.assertEqual(str(self.budget.spent('aeion-autonomous-forum')),'0.13')

    def test_unaccounted_review_handover_cannot_start_a_retry(self):
        self._assert_review_usage_gap_blocks_retry('AEION_HANDOVER')

    def test_explicit_review_usage_unknown_cannot_start_a_retry(self):
        self._assert_review_usage_gap_blocks_retry('USAGE_UNKNOWN')

    def _assert_review_usage_gap_blocks_retry(self, reason):
        build_id = self.build['build_id']
        self.failure_model = 'deepseek-4.1-flash'
        self.failure_reason = reason
        self.unknown_failure_usage = True
        self.worker.reassess_review_context(build_id)
        held = self.store.build(build_id)
        circuit = json.loads(held['receipt'])['circuit']
        self.assertEqual(circuit['votes'][-1]['reason'], reason)
        self.assertEqual(str(self.budget.spent('aeion-autonomous-forum')), '0.11')

        self.failure_model = None
        self.assertIsNone(self.worker._continue_held_review())
        with self.assertRaisesRegex(CircuitError, 'not_eligible'):
            self.worker.reassess_review_context(build_id, retry_failed_review=True)

        self.assertEqual(self.store.build(build_id)['receipt'], held['receipt'])
        self.assertEqual(len(self.checks), 1)
        self.assertEqual(len(self.votes), 2)
        self.assertEqual(self.requests, [])
        self.assertEqual(str(self.budget.spent('aeion-autonomous-forum')), '0.11')

    def test_proven_zero_forward_review_handover_can_use_a_substitute(self):
        self.failure_model = 'deepseek-4.1-flash'
        self.failure_reason = 'AEION_HANDOVER'
        self.zero_forward_failure = True

        result = self.worker.reassess_review_context(self.build['build_id'])

        self.assertEqual(result['result']['status'], 'publication_queued')
        self.assertEqual(len(self.votes), 3)
        self.assertEqual(str(self.budget.spent('aeion-autonomous-forum')), '0.02')
        circuit = self.requests[0][1]['circuit']
        self.assertEqual(len(circuit['votes']), 2)
        self.assertEqual(circuit['unavailable_reviewers'][0]['reason'], 'AEION_HANDOVER')

    def test_retry_failed_review_excludes_zero_forward_budget_stop_model(self):
        receipt=json.loads(self.store.board()[0]['receipt'])
        receipt['circuit']={
            **receipt['circuit'],
            'review_input_version':2,
            'status':'held','reason':'reviewer_failed',
            'votes':[
                {'vote':1,'model':'deepseek-4.1-flash','family':'deepseek','verdict':'approve','reason':'ok'},
                {'vote':2,'model':'gpt-6-luna','family':'openai','verdict':'error','reason':'BUDGET_STOP',
                 'execution':{'failure':'BUDGET_STOP','forwarded_count':0,
                              'usage':{'complete':True,'cost_usd':'0','output_tokens':0}}},
            ],
        }
        import sqlite3
        conn=sqlite3.connect(self.store.path)
        conn.execute('UPDATE builds SET receipt=? WHERE build_id=?',(json.dumps(receipt),self.build['build_id']))
        conn.commit();conn.close()
        self.failure_model='gpt-6-luna'
        result=self.worker.reassess_review_context(self.build['build_id'],retry_failed_review=True)
        self.assertEqual(result['result']['status'],'publication_queued')
        self.assertNotIn('gpt-6-luna',[m for m,_ in self.votes])


class RetryUnavailableReviewerTests(unittest.TestCase):
    """Retrying a failed review preserves 0-forward exclusions across votes and unavailable_reviewers."""
    def test_retry_excludes_zero_forward_unavailable_reviewers_alongside_votes(self):
        from unittest.mock import patch
        from factory.review import content_digest
        cases = (
            ('votes_zero_forward_budget_stop',
             {'failure': 'BUDGET_STOP', 'forwarded_count': 0, 'usage': {'cost_usd': '0', 'output_tokens': 0}},
             None),
            ('accounted_context_stop_excludes_reviewer',
             {'engine': 'flue-pi', 'role': 'review', 'failure': 'AEION_HANDOVER', 'forwarded_count': 2,
              'usage': {'complete': True, 'cost_usd': '0.8938762'}},
             None),
            ('votes_forwarded_timeout_keeps_first_reviewer',
             {'failure': 'CLI_TIMEOUT', 'forwarded_count': 1, 'usage': {'cost_usd': '0.02', 'output_tokens': 5}},
             'gpt-6-luna'),
        )
        for name, vote2_exec, expected_first in cases:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                arch = root / 'demo/forum/ARCHITECTURE.md'; arch.parent.mkdir(parents=True)
                arch.write_text('Architecture.\n')
                specs = root / 'specs'; specs.mkdir()
                (specs / '001.md').write_text('# 001\n## Acceptance checks\n- [ ] Check.\n')
                catalog = Catalog({'schema_version': 2, 'count': 1, 'features': [{
                    'id': '001', 'title': 'Settings', 'area': 'foundation', 'size': 'S', 'phase': 'P0',
                    'parallel': False, 'tier': 3, 'file': '001.md', 'write_paths': ['demo/forum-app/'],
                    'depends_on': [], 'architecture_digest': hashlib.sha256(arch.read_bytes()).hexdigest()}]})
                source = root / 'source'; rel = 'demo/forum-app/src/main/resources/settings.properties'
                (source / rel).parent.mkdir(parents=True); (source / rel).write_text('k=1\n')
                for args in (['init', '-q'], ['add', '.'], ['-c', 'user.name=T', '-c', 'user.email=t@e.invalid', 'commit', '-qm', 'base']):
                    subprocess.run(['git', '-C', str(source), *args], capture_output=True, check=True)
                base = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
                store = Store(root / 'factory.db'); store.admit(['001'], 'fixture', catalog)
                build = store.claim_next(catalog); folder = root / 'work' / build['build_id']
                prepared = folder / 'prepared'; prepared.mkdir(parents=True)
                task = freeze_task(catalog, '001', specs, arch, base, product=True)
                target = prepared_target(root, source, task, prepared, 'Synthetic acceptance.\n')
                target.materialize(folder / 'repo')
                (folder / 'repo' / rel).write_text('k=2\n')
                (folder / 'BRIEF.md').write_text(task.specification)
                (prepared / 'acceptance.mjs').write_text('Synthetic acceptance.\n')
                cfg = {'architecture': arch, 'profile': 'flue-pi', 'mode': 'live',
                       'deadline_ns': 10 ** 12, 'step_cap': 50, 'context_limit': 250000,
                       'cost_reservation_usd': '0.50'}
                frozen = freeze_build(store.build(build['build_id']), catalog, specs, base,
                    {**cfg, **({'dependency_changes': dict(target.dependency_changes)} if target.dependency_changes else {})},
                    write_scopes=target.write_paths, spec_path=target.brief, acceptance_path=target.protected_check.contract_test)
                artifact = validate_artifact(folder / 'repo', frozen.write_scopes)
                spec_digest = hashlib.sha256(task.specification.encode('utf-8')).hexdigest()
                acc_digest = hashlib.sha256('Synthetic acceptance.\n'.encode('utf-8')).hexdigest()
                receipt = {
                    'simulated': False, 'base_sha': base, 'task_digest': task.digest(),
                    'frozen_digest': frozen.digest(), 'spec_digest': spec_digest, 'acceptance_digest': acc_digest,
                    'architecture_digest': catalog.features[0]['architecture_digest'],
                    'author_model': 'glm-5.3-flash', 'artifact_digest': artifact['digest'],
                    'preparation': {**task.identity(), 'task_digest': task.digest(),
                                    'acceptance_digest': acc_digest, 'preparer_model': 'qwen-3.8-flash', 'synthetic': False},
                    'gate': {'status': 'passed', 'results': {}},
                    'review': {'status': 'approved'},
                    'execution': {'build_id': build['build_id'], 'role': 'author', 'engine': 'flue-pi',
                                  'forwarded_count': 1, 'usage': {'complete': True, 'cost_usd': '0.10'}},
                    'circuit': {
                        'status': 'held', 'reason': 'reviewer_failed', 'review_input_version': 2,
                        'coverage': {'files': [rel]},
                        'unavailable_reviewers': [{
                            'model': 'claude-haiku-5.5', 'verdict': 'error',
                            'execution': {'failure': 'BUDGET_STOP', 'forwarded_count': 0,
                                          'usage': {'cost_usd': '0', 'output_tokens': 0}},
                        }],
                        'votes': [
                            {'vote': 1, 'model': 'deepseek-4.1-flash', 'verdict': 'approve'},
                            {'vote': 2, 'model': 'gpt-6-luna', 'verdict': 'error', 'execution': vote2_exec},
                        ],
                    },
                }
                store.hold_dispatched(build, 'owner_review_required', receipt=receipt)
                seen = {}
                def fake_two_vote(*_a, **kw):
                    seen['first_reviewer'] = kw.get('first_reviewer')
                    seen['exclude_models'] = kw.get('exclude_models')
                    return {'status': 'approved', 'reason': 'approved',
                            'votes': [{'vote': 1, 'model': 'deepseek-4.1-flash', 'verdict': 'approve'},
                                      {'vote': 2, 'model': 'minimax-m2.7', 'verdict': 'approve'}],
                            'spec_digest': spec_digest, 'acceptance_digest': acc_digest,
                            'coverage': {'files': [rel]}}
                worker = DispatchWorker(store, catalog, specs, root / 'work', target_repo=source,
                    check_sandbox=SimpleNamespace(check_target=lambda _t, _r, _f: (True, {'check': 'prepared_product'})),
                    review_complete=lambda *_a, **_k: None, require_circuit=True, config=cfg,
                    budget=DailyBudget(root / 'budget.json'))
                worker.paid = True
                worker.preparer = TaskPreparer(root, source, synchronize=lambda: base, product=True)
                worker.admission_check = lambda: True
                with patch('factory.dispatch.two_vote_review', side_effect=fake_two_vote), \
                        patch('factory.dispatch.baseline_context', return_value={}):
                    worker.reassess_review_context(build['build_id'], retry_failed_review=True)
                self.assertEqual(seen['first_reviewer'], expected_first)
                if expected_first is None:
                    self.assertEqual(seen['exclude_models'], ('gpt-6-luna', 'claude-haiku-5.5'))
                else:
                    self.assertEqual(seen['exclude_models'], ('claude-haiku-5.5',))


if __name__=='__main__':unittest.main()
