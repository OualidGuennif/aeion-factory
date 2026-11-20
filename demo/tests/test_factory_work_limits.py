"""Frozen author bounds stop work before another model/tool session, across handovers."""
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
import base64
from unittest.mock import Mock, patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory.flue_builder import FlueBuilder, BuilderError
from app.runner import factory_work_limit
from factory.agent_files import parse_files


class WorkLimitTests(unittest.TestCase):
    def test_author_window_defaults_to_thirty_minutes_and_is_capped_at_three_hours(self):
        from factory.flue_session import SESSION_TIMEOUT_SECONDS
        from factory.freeze import AUTHOR_TIMEOUT_SECONDS, AUTHOR_TIMEOUT_CEILING_SECONDS
        self.assertEqual(AUTHOR_TIMEOUT_SECONDS,1800)
        self.assertEqual(AUTHOR_TIMEOUT_CEILING_SECONDS,10800)
        self.assertEqual(FlueBuilder.timeout_seconds,AUTHOR_TIMEOUT_SECONDS)
        self.assertEqual(SESSION_TIMEOUT_SECONDS,900)

    def test_interrupted_worker_recovers_only_a_valid_export_with_complete_accounting(self):
        name='demo/forum-app/src/main/java/local/aeion/forum/Partial.java'
        original=b'package local.aeion.forum; class Partial {}\n'
        changed=b'package local.aeion.forum; class Partial { int value=1; }\n'
        for valid,complete,forwards,code,recover in ((True,True,0,'STEP_LIMIT',False),
                (False,True,1,'STEP_LIMIT',False),(True,False,1,'STEP_LIMIT',False),
                (True,True,1,'ATTEMPT_REVOKED',False),(True,True,1,'STEP_LIMIT',True),
                (True,True,1,'handover_limit',True)):
            with self.subTest(valid=valid,complete=complete,forwards=forwards,code=code),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);repo=root/'repo';repo.mkdir()
                (repo/name).parent.mkdir(parents=True);(repo/name).write_bytes(original)
                brief=root/'BRIEF.md';brief.write_text('# Public fixture\n')
                contract=root/'acceptance.mjs';contract.write_text('// Frozen public fixture\n')
                target=SimpleNamespace(seed_files=(),protected_check=SimpleNamespace(id='prepared_product',
                    contract_destination='EXTERNAL.mjs',contract_test=contract))
                frozen=SimpleNamespace(write_scopes=[str(Path(name).parent)+'/'],context_limit=250000,
                    step_cap=200,deadline_ns=900000000000,cost_reservation_usd='0.50')
                runtime=Mock();runtime.live.side_effect=ValueError(code)
                box=Mock();box.collect.return_value={
                    'workspace/'+name:base64.b64encode(changed).decode(),
                    'workspace/FROZEN_ACCEPTANCE.mjs':base64.b64encode(contract.read_bytes()).decode(),
                    **({} if valid else {'workspace/'+str(Path(name).parent)+'/.gitattributes':base64.b64encode(b'forbidden').decode()})}
                seen=[]
                def session(run,*_a,**_k):
                    run['forwarded_count']=forwards;seen.append(run);return runtime
                with patch('factory.flue_builder.public_files',return_value={name:original}), \
                        patch('factory.flue_builder.FactorySession',side_effect=session), \
                        patch('factory.flue_builder.Sandbox',return_value=box), \
                        patch('factory.flue_builder.usage',return_value={'complete':complete,'cost_usd':'0' if complete else None}), \
                        patch('factory.flue_builder.subprocess.run',return_value=SimpleNamespace(returncode=1)):
                    def build():
                        builder=FlueBuilder(root,{})
                        builder.authorization_check=lambda:True
                        return builder.run_build(repo=repo,frozen=frozen,feature={'id':'001','tier':3},
                            brief=brief,target=target,build={'build_id':'a'*32})
                    if recover:self.assertEqual(build(),[name])
                    else:
                        with self.assertRaisesRegex(ValueError,code):build()
                self.assertEqual((repo/name).read_bytes(),changed if valid else original)
                self.assertEqual(seen[0].get('retained_files_count'),1 if valid else None)
                if not valid:self.assertEqual(seen[0]['retained_export'],'unavailable')
                self.assertEqual(seen[0].get('candidate_recovered',False),recover)
                box.close.assert_called_once()

    def test_previous_check_failure_reaches_the_author_as_bounded_data(self):
        from factory.flue_builder import previous_failure_text
        self.assertEqual(previous_failure_text(None),'')
        self.assertEqual(previous_failure_text({'failed_tests':['x']}),'')
        text=previous_failure_text({'reason':'product_unit_tests_failed',
            'failed_tests':['DatabaseLessBootTest > livenessAnswersWithoutADatabase() FAILED'],
            'compiler_errors':['src/main/java/App.java:12']})
        self.assertIn('not instructions',text)
        self.assertIn('product_unit_tests_failed',text)
        self.assertIn('DatabaseLessBootTest > livenessAnswersWithoutADatabase() FAILED',text)
        self.assertIn('src/main/java/App.java:12',text)
        self.assertLess(len(text.encode()),4000)

    def test_transition_file_count_is_bounded_without_changing_write_scopes(self):
        files=[{'path':f'demo/forum-app/src/main/java/Fixture{i}.java','content':'class Fixture {}\n'} for i in range(32)]
        self.assertEqual(len(parse_files({'files':files},['demo/forum-app/src/main/java/'])),32)
        files.append({'path':'demo/forum-app/src/main/java/Extra.java','content':'class Extra {}\n'})
        with self.assertRaisesRegex(BuilderError,'builder_file_count'):
            parse_files({'files':files},['demo/forum-app/src/main/java/'])
    def test_oversized_local_brief_proves_no_transport_without_leaking_a_telemetry_session(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);brief=root/'BRIEF.md';brief.write_text('x'*12001)
            builder=FlueBuilder(root,{})
            with patch('factory.flue_builder.public_files',return_value={'demo/forum-app/A.java':b'class A {}'}), \
                    patch('factory.flue_builder.FactorySession') as session:
                with self.assertRaisesRegex(BuilderError,'brief_unavailable'):
                    builder.run_build(repo=root,frozen=SimpleNamespace(),feature={'id':'007','tier':3},
                        brief=brief,target=object(),build={'build_id':'a'*32})
            session.assert_not_called()
            self.assertTrue(builder.last_usage['complete'])
            self.assertEqual(builder.last_usage['cost_usd'],'0')

    def test_forward_cap_counts_previous_sessions_and_deadline_stops_the_next_request(self):
        run={'step_cap':3,'forwarded_count':2,'factory_deadline':200}
        self.assertIsNone(factory_work_limit(run,0,now=100))
        self.assertEqual(factory_work_limit(run,1,now=100),'STEP_LIMIT')
        self.assertEqual(factory_work_limit(run,0,now=200),'AGENT_DEADLINE')

    def test_three_identical_check_failures_stop_the_next_admission(self):
        from factory.flue_builder import note_check_failure
        import inspect
        run={'seeded_check_digest':'d'*64}
        failed={'status':'failed','reason':'product_unit_tests_failed','artifact_digest':'d'*64,
                'failed_tests':['DatabaseLessBootTest > livenessAnswersWithoutADatabase() FAILED']}
        # The first baseline reproduction on the seeded digest does not count as a strike.
        note_check_failure(run,failed)
        self.assertEqual(run.get('same_check_count',0),0)
        edited={**failed,'artifact_digest':'e'*64}
        for _ in range(2):
            note_check_failure(run,edited)
        # Progress (a different failing test signature) resets the streak to 1.
        note_check_failure(run,{**edited,'failed_tests':['OtherTest > other() FAILED']})
        self.assertEqual(run['same_check_count'],1)
        for _ in range(3):
            note_check_failure(run,{**edited,'failed_tests':['OtherTest > other() FAILED']})
        self.assertIsNone(factory_work_limit({**run,'step_cap':12,'forwarded_count':0},0,now=1))
        note_check_failure(run,{**edited,'failed_tests':['OtherTest > other() FAILED']})
        self.assertEqual(factory_work_limit({**run,'step_cap':12,'forwarded_count':0,'factory_deadline':10**9},0,now=1),
                         'repeated_check_failure')
        source = inspect.getsource(FlueBuilder.run_build)
        self.assertNotIn('as often as you need', source)
        self.assertNotIn('You may not stop', source)
        self.assertIn('three identical failures', source)
        self.assertIn('runtime.last_check = cache[digest]', source)
        self.assertGreaterEqual(source.count("progress('protected_check.finished'"), 3)

    def test_frozen_deadline_and_context_are_used_before_a_sandbox_can_start(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            brief=root/'BRIEF.md';brief.write_text('# Bounded fixture\n')
            frozen=SimpleNamespace(cost_reservation_usd='0.50',write_scopes=['demo/forum-app/src/'],
                                   deadline_ns=500_000_000,context_limit=100000,step_cap=2)
            contract=root/'contract.java';contract.write_text('class Contract {}')
            target=SimpleNamespace(seed_files=(),protected_check=SimpleNamespace(
                id='prepared_gradle',contract_destination='contract.java',contract_test=contract))
            runtime=Mock();runtime.live.side_effect=AssertionError('expired work must not start inference')
            runtime.finish.return_value={'status':'stopped'}
            seen=[]
            def session(run,*_args,**_kwargs):
                seen.append(run)
                return runtime
            with patch('factory.flue_builder.FactorySession',side_effect=session), \
                 patch('factory.flue_builder.public_files',return_value={'demo/forum-app/A.java':b'class A {}'}), \
                 patch('factory.flue_builder.Sandbox') as sandbox, \
                 patch('factory.flue_builder.time.monotonic',side_effect=[100,101]):
                with self.assertRaisesRegex(BuilderError,'agent_deadline'):
                    FlueBuilder(root,{}).run_build(repo=root,frozen=frozen,feature={'id':'007','tier':3},
                        brief=brief,target=target,build={'build_id':'a'*32})
            sandbox.assert_not_called()
            runtime.live.assert_not_called()
            self.assertEqual(seen[0]['limit'],100000)
            self.assertEqual(seen[0]['step_cap'],2)

    def test_prior_candidate_selects_cleanest_validated_candidate_for_same_base_and_spec(self):
        import json, sqlite3
        from factory.flue_builder import prior_candidate
        from factory.review import content_digest
        with tempfile.TemporaryDirectory() as folder:
            state=Path(folder);work=state/'work';work.mkdir()
            conn=sqlite3.connect(state/'factory.db')
            conn.execute('CREATE TABLE builds (build_id TEXT, feature_id TEXT, status TEXT, receipt TEXT, updated_ns INTEGER)')
            path='demo/forum-app/src/A.java'
            for idx,(bid,content,failed) in enumerate((
                    ('1'*32,'class A { int v=1; }\n',['ForumHealthTest > t() FAILED']),
                    ('2'*32,'class A { int v=2; }\n',['ForumHealthTest > t() > initializationError FAILED']))):
                repo=work/bid/'repo';(repo/path).parent.mkdir(parents=True);(repo/path).write_text(content)
                receipt={'base_sha':'b'*40,'spec_digest':'s'*64,
                         'correction':{'candidate_files':[path],'candidate_digest':content_digest({path:content})},
                         'execution':{'check':{'failed_tests':failed}}}
                conn.execute('INSERT INTO builds VALUES (?,?,?,?,?)',(bid,'001','failed',json.dumps(receipt),idx+1))
            conn.commit();conn.close()
            current=work/('3'*32)/'repo';current.mkdir(parents=True)
            frozen=SimpleNamespace(base_sha='b'*40,spec_digest='s'*64,write_scopes=['demo/forum-app/src/'])
            self.assertEqual(prior_candidate(current,frozen,'001'),{path:'class A { int v=1; }\n'})

            # A gate-passed held/cancelled build blocked only by reviewer_failed takes priority over earlier failed builds.
            from factory.flue_builder import previous_failure_text
            hint=previous_failure_text(None,{path:'class A {}'},['demo/forum-app/src/'])
            self.assertIn('PREVIOUS CANDIDATE',hint)

            conn=sqlite3.connect(state/'factory.db')
            good_repo=work/('4'*32)/'repo';(good_repo/path).parent.mkdir(parents=True);(good_repo/path).write_text('class A { int v=9; }\n')
            good_receipt={
                'base_sha':'b'*40,'spec_digest':'s'*64,
                'artifact_digest':content_digest({path:'class A { int v=9; }\n'}),
                'gate':{'status':'passed'},
                'circuit':{'reason':'reviewer_failed','coverage':{'files':[path]}},
            }
            conn.execute('INSERT INTO builds VALUES (?,?,?,?,?)',('4'*32,'001','cancelled',json.dumps(good_receipt),99))
            rej_repo=work/('5'*32)/'repo';(rej_repo/path).parent.mkdir(parents=True);(rej_repo/path).write_text('class A { int v=99; }\n')
            rej_receipt={
                'base_sha':'b'*40,'spec_digest':'s'*64,
                'artifact_digest':content_digest({path:'class A { int v=99; }\n'}),
                'gate':{'status':'passed'},
                'circuit':{'reason':'reviewer_rejected','coverage':{'files':[path]}},
            }
            conn.execute('INSERT INTO builds VALUES (?,?,?,?,?)',('5'*32,'001','cancelled',json.dumps(rej_receipt),100))
            conn.commit();conn.close()
            from factory.flue_builder import _prior_candidate_entry
            self.assertEqual(prior_candidate(current,frozen,'001'),{path:'class A { int v=9; }\n'})
            self.assertEqual(_prior_candidate_entry(current,frozen,'001'),({path:'class A { int v=9; }\n'},True))

    def test_gate_passed_prior_candidate_suppresses_stale_previous_failure_prompt(self):
        import json, sqlite3
        from factory.review import content_digest
        path='demo/forum-app/src/main/java/A.java'
        with tempfile.TemporaryDirectory() as directory:
            state=Path(directory);work=state/'work';work.mkdir()
            current=work/('f'*32)/'repo';(current/path).parent.mkdir(parents=True);(current/path).write_text('class A {}\n')
            brief=work/('f'*32)/'BRIEF.md';brief.write_text('# Public fixture\n')
            contract=state/'acceptance.mjs';contract.write_text('// Frozen public fixture\n')
            frozen=SimpleNamespace(base_sha='b'*40,spec_digest='s'*64,write_scopes=['demo/forum-app/'],
                context_limit=250000,step_cap=200,deadline_ns=900000000000,cost_reservation_usd='0.50')
            target=SimpleNamespace(seed_files=(),protected_check=SimpleNamespace(id='prepared_product',
                contract_destination='EXTERNAL.mjs',contract_test=contract))
            good_repo=work/('4'*32)/'repo';(good_repo/path).parent.mkdir(parents=True);(good_repo/path).write_text('class A { int v=9; }\n')
            good_receipt={'base_sha':'b'*40,'spec_digest':'s'*64,
                'artifact_digest':content_digest({path:'class A { int v=9; }\n'}),
                'gate':{'status':'passed'},'circuit':{'reason':'reviewer_failed','coverage':{'files':[path]}}}
            conn=sqlite3.connect(state/'factory.db')
            conn.execute('CREATE TABLE builds (build_id TEXT, feature_id TEXT, status TEXT, receipt TEXT, updated_ns INTEGER)')
            conn.execute('INSERT INTO builds VALUES (?,?,?,?,?)',('4'*32,'001','cancelled',json.dumps(good_receipt),99))
            conn.commit();conn.close()
            captured=[]
            runtime=Mock()
            def stop_on_live(*_a,**kw):
                captured.append(kw.get('prompt',''))
                raise RuntimeError('captured_prompt')
            runtime.live.side_effect=stop_on_live
            with patch('factory.flue_builder.public_files',return_value={path:b'class A {}\n'}), \
                    patch('factory.flue_builder.FactorySession',return_value=runtime), \
                    patch('factory.flue_builder.Sandbox',return_value=Mock()), \
                    patch('factory.flue_builder.DockerCheckRunner',return_value=Mock(instructions=lambda _t: '')), \
                    patch('factory.flue_builder.usage',return_value={'complete':True,'cost_usd':'0'}):
                builder=FlueBuilder(state,{});builder.authorization_check=lambda:True
                with self.assertRaisesRegex(RuntimeError,'captured_prompt'):
                    builder.run_build(repo=current,frozen=frozen,feature={'id':'001','tier':3,'title':'Test'},
                        brief=brief,target=target,build={'build_id':'f'*32},
                        previous_failure={'reason':'product_unit_tests_failed','failed_tests':['Stale > old() FAILED']})
            self.assertEqual(len(captured),1)
            self.assertIn('PREVIOUS CANDIDATE',captured[0])
            self.assertNotIn('Stale > old() FAILED',captured[0])
            self.assertNotIn('PREVIOUS PROTECTED CHECK FAILURE',captured[0])

    def test_cleared_or_empty_previous_failure_never_seeds_failed_candidate_as_gate_passed(self):
        import json, sqlite3
        from factory.review import content_digest
        from factory.flue_builder import _prior_candidate_entry
        path='demo/forum-app/src/main/java/A.java'
        with tempfile.TemporaryDirectory() as directory:
            state=Path(directory);work=state/'work';work.mkdir()
            current=work/('f'*32)/'repo';(current/path).parent.mkdir(parents=True);(current/path).write_text('class A {}\n')
            brief=work/('f'*32)/'BRIEF.md';brief.write_text('# Public fixture\n')
            contract=state/'acceptance.mjs';contract.write_text('// Frozen public fixture\n')
            frozen=SimpleNamespace(base_sha='b'*40,spec_digest='s'*64,write_scopes=['demo/forum-app/'],
                context_limit=250000,step_cap=200,deadline_ns=900000000000,cost_reservation_usd='0.50')
            target=SimpleNamespace(seed_files=(),protected_check=SimpleNamespace(id='prepared_product',
                contract_destination='EXTERNAL.mjs',contract_test=contract))
            failed_repo=work/('1'*32)/'repo';(failed_repo/path).parent.mkdir(parents=True);(failed_repo/path).write_text('class A { int bad=1; }\n')
            failed_receipt={'base_sha':'b'*40,'spec_digest':'s'*64,
                'correction':{'candidate_files':[path],'candidate_digest':content_digest({path:'class A { int bad=1; }\n'})}}
            stale_revfail={'base_sha':'b'*40,'spec_digest':'s'*64,'artifact_digest':'a'*64,
                'gate':{'status':'passed'},'circuit':{'reason':'reviewer_failed','coverage':{'files':[path]}}}
            conn=sqlite3.connect(state/'factory.db')
            conn.execute('CREATE TABLE builds (build_id TEXT, feature_id TEXT, status TEXT, receipt TEXT, updated_ns INTEGER)')
            conn.execute('INSERT INTO builds VALUES (?,?,?,?,?)',('1'*32,'001','failed',json.dumps(failed_receipt),50))
            conn.execute('INSERT INTO builds VALUES (?,?,?,?,?)',('2'*32,'001','cancelled',json.dumps(stale_revfail),60))
            conn.commit();conn.close()
            self.assertEqual(_prior_candidate_entry(current,frozen,'001',include_failed=False),(None,False))
            self.assertEqual(_prior_candidate_entry(current,frozen,'001',include_failed=True),({path:'class A { int bad=1; }\n'},False))
            for prev in (None,{'failed_tests':['x']}):
                with self.subTest(prev=prev):
                    seen=[]
                    runtime=Mock()
                    def stop_on_live(run,*_a,**kw):
                        seen.append((kw.get('prompt',''),dict(run)))
                        raise RuntimeError('captured_prompt')
                    runtime.live.side_effect=stop_on_live
                    with patch('factory.flue_builder.public_files',return_value={path:b'class A {}\n'}), \
                            patch('factory.flue_builder.FactorySession',return_value=runtime), \
                            patch('factory.flue_builder.Sandbox',return_value=Mock()), \
                            patch('factory.flue_builder.DockerCheckRunner',return_value=Mock(instructions=lambda _t: '')), \
                            patch('factory.flue_builder.usage',return_value={'complete':True,'cost_usd':'0'}):
                        builder=FlueBuilder(state,{});builder.authorization_check=lambda:True
                        with self.assertRaisesRegex(RuntimeError,'captured_prompt'):
                            builder.run_build(repo=current,frozen=frozen,feature={'id':'001','tier':3,'title':'Test'},
                                brief=brief,target=target,build={'build_id':'f'*32},previous_failure=prev)
                    self.assertEqual(len(seen),1)
                    self.assertNotIn('PREVIOUS CANDIDATE',seen[0][0])
                    self.assertNotIn('whose protected gate passed',seen[0][0])
                    self.assertNotIn('seeded_check_digest',seen[0][1])


if __name__=='__main__':unittest.main()
