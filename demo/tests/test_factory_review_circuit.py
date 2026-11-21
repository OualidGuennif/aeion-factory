"""A valid reviewer vote is a successful reviewer response, not a routing failure."""
import sys
import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.budget import BudgetError
from factory.models import Router, Telemetry
from factory.review_circuit import two_vote_review, MAX_PROMPT_CHARS


FILES = {"demo/forum/product/x.py": "print('ok')\n"}


class CircuitTelemetryTests(unittest.TestCase):
    def test_purse_refusal_retains_earlier_vote_without_model_failure(self):
        telemetry = Telemetry()
        calls = []
        def complete(model, _prompt):
            calls.append(model)
            if len(calls) == 2:
                raise BudgetError("budget_unavailable")
            return {"verdict": "approve", "reason": "fixture"}

        result = two_vote_review('glm-5.3-flash', '001', FILES, Router(telemetry), complete)
        self.assertEqual(result['reason'], 'review_budget_unavailable')
        self.assertEqual([vote['verdict'] for vote in result['votes']], ['approve'])
        self.assertEqual(len(calls), 2)

    def test_failed_vote_keeps_its_actual_typed_channel_diagnostics(self):
        execution={'engine':'flue-pi','failure':'REVIEW_RESULT_MISSING','trace_id':'a'*32,
                   'forwarded_count':1,'usage':{'complete':True,'cost_usd':'0.01'}}
        def fail(*_):raise ValueError('REVIEW_RESULT_MISSING')
        result=two_vote_review('glm-5.3-flash','001',FILES,Router(Telemetry()),fail,
            execution_for_vote=lambda:execution)
        self.assertEqual(result['votes'][0]['execution'],execution)
        self.assertEqual(result['votes'][0]['reason'],'REVIEW_RESULT_MISSING')
    def busy_circuit(self,busy,failure='PROVIDER_RATE_LIMITED',output_tokens=0,**kwargs):
        calls=[];state={}
        def complete(model,_prompt):
            calls.append(model)
            if model in busy:
                state['execution']={'failure':failure,'provider_http_status':429,'provider_retries':2,
                    'forwarded_count':1,'usage':{'complete':False,'input_tokens':0,'output_tokens':output_tokens}}
                raise ValueError(failure)
            state['execution']={'failure':None,'forwarded_count':1,'usage':{'complete':True,'output_tokens':9}}
            return {'verdict':'approve','reason':'fixture'}
        result=two_vote_review('glm-5.3-flash','001',FILES,Router(Telemetry()),complete,
            execution_for_vote=lambda:state['execution'],**kwargs)
        return result,calls

    def test_a_busy_reviewer_hands_its_vote_once_to_the_next_independent_one(self):
        from factory.publisher import independent_circuit
        result,calls=self.busy_circuit({'deepseek-4.1-flash'})
        self.assertEqual(result['status'],'approved')
        self.assertEqual(len(calls),3)
        self.assertEqual([v['model'] for v in result['votes']],[calls[0],calls[2]])
        self.assertNotIn('deepseek-4.1-flash',[v['model'] for v in result['votes']])
        self.assertEqual([(v['model'],v['reason']) for v in result['unavailable_reviewers']],
            [('deepseek-4.1-flash','PROVIDER_RATE_LIMITED')])
        self.assertEqual([v['vote'] for v in result['votes']],[1,2])
        self.assertTrue(independent_circuit(result))

    def test_only_one_substitution_and_never_for_a_refusal_or_a_billed_answer(self):
        result,calls=self.busy_circuit({'deepseek-4.1-flash','claude-haiku-5.5'},failure='PROVIDER_UNAVAILABLE')
        self.assertEqual((result['status'],result['reason'],len(calls)),('held','reviewer_failed',3))
        self.assertEqual(len(result['unavailable_reviewers']),1)
        self.assertEqual(result['votes'][-1]['verdict'],'error')
        for failure,tokens in (('PROVIDER_REJECTED',0),('PROVIDER_TIMEOUT',0),('PROVIDER_RATE_LIMITED',5),
                               ('PROVIDER_RATE_LIMITED',None)):
            with self.subTest(failure=failure,tokens=tokens):
                result,calls=self.busy_circuit({'deepseek-4.1-flash'},failure=failure,output_tokens=tokens)
                self.assertEqual((result['status'],result['reason']),('held','reviewer_failed'))
                self.assertNotIn('unavailable_reviewers',result)

    def test_a_transport_error_retries_the_same_reviewer_until_it_answers(self):
        calls = []
        state = {'n': 0, 'execution': {}}
        def complete(model, _prompt):
            calls.append(model)
            state['n'] += 1
            if state['n'] < 3:
                state['execution'] = {'failure': 'TRANSPORT_ERROR', 'usage': {'complete': False, 'output_tokens': 0}}
                raise ValueError('TRANSPORT_ERROR')
            state['execution'] = {'failure': None, 'usage': {'complete': True, 'output_tokens': 4}}
            return {'verdict': 'approve', 'reason': 'fixture'}
        result = two_vote_review('glm-5.3-flash', '001', FILES, Router(Telemetry()), complete,
                                 execution_for_vote=lambda: state['execution'])
        self.assertEqual(result['status'], 'approved')
        self.assertEqual(calls[0], calls[1])
        self.assertEqual(calls[0], calls[2])

    def test_three_transport_errors_then_hold_the_vote(self):
        calls = []
        state = {}
        def complete(model, _prompt):
            calls.append(model)
            state['execution'] = {'failure': 'TRANSPORT_ERROR', 'usage': {'complete': False, 'output_tokens': 0}}
            raise ValueError('TRANSPORT_ERROR')
        result = two_vote_review('glm-5.3-flash', '001', FILES, Router(Telemetry()), complete,
                                 execution_for_vote=lambda: state['execution'])
        self.assertEqual((result['status'], result['reason']), ('held', 'reviewer_failed'))
        self.assertEqual(len(calls), 3)
        self.assertEqual(len(set(calls)), 1)

    def test_a_pinned_first_reviewer_that_is_busy_is_still_substituted(self):
        result,calls=self.busy_circuit({'deepseek-4.1-flash'},first_reviewer='deepseek-4.1-flash')
        self.assertEqual(calls[0],'deepseek-4.1-flash')
        self.assertEqual(result['status'],'approved')
        self.assertEqual(len(result['votes']),2)

    def test_baseline_diff_distinguishes_inherited_code_and_includes_untracked_additions(self):
        from factory.review_circuit import baseline_diff
        with tempfile.TemporaryDirectory() as folder:
            repo=Path(folder)
            def git(*args):
                return subprocess.check_output(['git','-C',folder,*args],text=True).strip()
            git('init','-q')
            (repo/'settings.properties').write_text('database=sqlite\nlimit=1\n')
            git('add','settings.properties')
            git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','base')
            base=git('rev-parse','HEAD')
            (repo/'settings.properties').write_text('UNTRUSTED WORKTREE BASE\n')
            files={'settings.properties':'database=sqlite\nlimit=2\n','new.txt':'new\n'}
            diff=baseline_diff(repo,base,files)
            self.assertIn(' database=sqlite',diff)
            self.assertIn('-limit=1\n+limit=2',diff)
            self.assertIn('--- /dev/null\n+++ b/new.txt',diff)
            self.assertNotIn('UNTRUSTED',diff)
            seen=[]
            result=two_vote_review('glm-5.3-flash','001',files,Router(Telemetry()),
                lambda model,prompt:seen.append(prompt) or {'verdict':'reject','reason':'fixture'},
                baseline=diff,base_sha=base)
            self.assertTrue(all(diff in prompt for prompt in seen))
            self.assertEqual(result['review_input_version'],2)
            self.assertEqual(result['base_sha'],base)
            self.assertEqual(result['diff_sha256'],hashlib.sha256(diff.encode()).hexdigest())

    def test_unsafe_or_oversized_baseline_never_reaches_a_model(self):
        from factory.review_circuit import baseline_diff, CircuitError
        with tempfile.TemporaryDirectory() as folder:
            for base,files in [('invalid',{'safe.txt':'x'}),('a'*40,{'../private':'x'})]:
                with self.assertRaises(CircuitError):baseline_diff(folder,base,files)
        seen=[]
        result=two_vote_review('glm-5.3-flash','001',FILES,Router(Telemetry()),
            lambda *args:seen.append(args),baseline='x'*(MAX_PROMPT_CHARS+1),base_sha='a'*40)
        self.assertEqual(result['reason'],'review_input_too_large')
        self.assertEqual(seen,[])

    def test_complete_large_reviews_launch_but_utf8_byte_overflow_never_sends_an_excerpt(self):
        seen=[]
        result=two_vote_review('glm-5.3-flash','002',{'src/Migration.java':'x'*30000},Router(Telemetry()),
            lambda model,prompt:seen.append(prompt) or {'verdict':'approve','reason':'Synthetic fixture'})
        self.assertEqual(result['status'],'approved')
        self.assertEqual(len(seen),2)
        self.assertTrue(all('x'*30000 in prompt for prompt in seen))
        seen.clear()
        result=two_vote_review('glm-5.3-flash','002',{'src/Migration.java':'€'*(MAX_PROMPT_CHARS//3+1)},Router(Telemetry()),
            lambda model,prompt:seen.append(prompt) or {'verdict':'approve'})
        self.assertEqual(result['reason'],'review_input_too_large')
        self.assertEqual(seen,[])
    def test_review_covers_the_protected_acceptance_and_excludes_its_preparer(self):
        seen=[]
        def vote(model,prompt):
            seen.append((model,prompt))
            return {'verdict':'approve','reason':'fixture'}
        result=two_vote_review('glm-5.3-flash','007',FILES,Router(Telemetry()),vote,
            acceptance='class IndependentContract {}',preparer_model='qwen-3.8-flash')
        self.assertEqual(result['status'],'approved')
        self.assertEqual({model for model,_ in seen},{'deepseek-4.1-flash','claude-haiku-5.5'})
        self.assertTrue(all('class IndependentContract {}' in prompt for _,prompt in seen))
        self.assertEqual(result['acceptance_digest'],hashlib.sha256(b'class IndependentContract {}').hexdigest())

    def test_zero_forward_preflight_budget_stop_substitutes_but_billed_budget_stop_holds(self):
        calls = []
        state = {}

        def preflight_stop(model, _prompt):
            calls.append(model)
            if model == 'claude-haiku-5.5':
                state['execution'] = {
                    'failure': 'BUDGET_STOP', 'forwarded_count': 0,
                    'usage': {'complete': True, 'cost_usd': '0', 'output_tokens': 0},
                }
                raise ValueError('BUDGET_STOP')
            state['execution'] = {'failure': None, 'forwarded_count': 1, 'usage': {'complete': True, 'output_tokens': 5}}
            return {'verdict': 'approve', 'reason': 'ok'}

        res = two_vote_review('glm-5.3-flash', '005', FILES, Router(Telemetry()), preflight_stop,
                              execution_for_vote=lambda: state['execution'], preparer_model='qwen-3.8-flash')
        self.assertEqual(res['status'], 'approved')
        self.assertIn('claude-haiku-5.5', [u['model'] for u in res['unavailable_reviewers']])
        self.assertEqual([v['model'] for v in res['votes']], ['deepseek-4.1-flash', 'gpt-6-luna'])

        def billed_stop(model, _prompt):
            if model == 'claude-haiku-5.5':
                state['execution'] = {
                    'failure': 'BUDGET_STOP', 'forwarded_count': 1,
                    'usage': {'complete': True, 'cost_usd': '0.15', 'output_tokens': 0},
                }
                raise ValueError('BUDGET_STOP')
            state['execution'] = {'failure': None, 'forwarded_count': 1, 'usage': {'complete': True, 'output_tokens': 5}}
            return {'verdict': 'approve', 'reason': 'ok'}

        held = two_vote_review('glm-5.3-flash', '005', FILES, Router(Telemetry()), billed_stop,
                               execution_for_vote=lambda: state['execution'], preparer_model='qwen-3.8-flash')
        self.assertEqual((held['status'], held['reason']), ('held', 'reviewer_failed'))
        self.assertNotIn('unavailable_reviewers', held)

        ex_res = two_vote_review('glm-5.3-flash', '005', FILES, Router(Telemetry()),
                                 lambda m, p: {'verdict': 'approve', 'reason': 'ok'},
                                 preparer_model='qwen-3.8-flash', exclude_models=('claude-haiku-5.5',))
        self.assertEqual([v['model'] for v in ex_res['votes']], ['deepseek-4.1-flash', 'gpt-6-luna'])
    def test_review_handover_substitutes_only_with_closed_usage(self):
        from factory.publisher import independent_circuit
        for complete_usage, cost, expected in (
            (True, '0.89', 'approved'), (False, None, 'held'), (True, 'NaN', 'held'),
        ):
            with self.subTest(complete_usage=complete_usage, cost=cost):
                calls = []
                handover = {'engine': 'flue-pi', 'role': 'review', 'failure': 'AEION_HANDOVER',
                            'forwarded_count': 2, 'usage': {'complete': complete_usage,
                                                          'cost_usd': cost, 'output_tokens': 66787}}

                def vote(model, prompt):
                    calls.append((model, prompt))
                    if model == 'claude-haiku-5.5':
                        raise ValueError('AEION_HANDOVER')
                    return {'verdict': 'approve', 'reason': 'fixture'}

                result = two_vote_review('glm-5.3-flash', '007', FILES, Router(Telemetry()), vote,
                    preparer_model='qwen-3.8-flash', first_reviewer='claude-haiku-5.5',
                    execution_for_vote=lambda: handover if calls[-1][0] == 'claude-haiku-5.5' else None)
                self.assertEqual(result['status'], expected)
                if expected == 'approved':
                    self.assertTrue(independent_circuit(result))
                    self.assertEqual(len(calls), 3)
                    self.assertEqual(len({prompt for _, prompt in calls}), 1)
                    self.assertEqual(result['unavailable_reviewers'][0]['execution'], handover)
                else:
                    self.assertEqual(len(calls), 1)
                    self.assertEqual(result['votes'][0]['reason'], 'AEION_HANDOVER')

    def test_budget_or_local_preflight_rejection_does_not_become_a_model_failure(self):
        telemetry=Telemetry()
        def fail_before_transport(*_):raise ValueError('budget unavailable')
        result=two_vote_review('glm-5.3-flash','001',FILES,Router(telemetry),fail_before_transport,
                               observed_for_vote=lambda:False)
        self.assertEqual(result['status'],'held')
        self.assertEqual(telemetry.records,[])
    def test_reviewers_receive_and_bind_the_complete_specification(self):
        seen=[]
        spec='# Held posts\nNew submissions must stay hidden until moderation.\n'
        def vote(model,prompt):
            seen.append(prompt)
            return {'verdict':'approve','reason':'fixture'}
        result=two_vote_review('glm-5.3-flash','021',FILES,Router(Telemetry()),vote,specification=spec)
        self.assertEqual(result['status'],'approved')
        self.assertTrue(all(spec in prompt for prompt in seen))
        self.assertEqual(result['spec_digest'],hashlib.sha256(spec.encode()).hexdigest())

    def test_oversized_specification_holds_before_any_vote(self):
        def forbidden(*_):raise AssertionError('truncated review reached transport')
        result=two_vote_review('glm-5.3-flash','021',FILES,Router(Telemetry()),forbidden,
                               specification='x'*(MAX_PROMPT_CHARS+1))
        self.assertEqual(result['reason'],'review_input_too_large')

    def test_two_approvals_are_recorded_as_successes(self):
        telemetry = Telemetry()
        result = two_vote_review("deepseek-4.1-flash", "001", FILES,
                                 Router(telemetry), lambda model, prompt: {"verdict": "approve", "reason": "ok"})
        self.assertEqual(result["status"], "approved")
        self.assertEqual(len(result["votes"]), 2)
        for vote in result["votes"]:
            stats = telemetry.stats(vote["model"], "review")
            self.assertEqual(stats["n"], 1)
            self.assertEqual(stats["success_rate"], 1.0)

    def test_a_valid_rejection_is_also_a_successful_response(self):
        telemetry = Telemetry()
        result = two_vote_review("deepseek-4.1-flash", "001", FILES,
                                 Router(telemetry), lambda model, prompt: {"verdict": "reject", "reason": "no"})
        self.assertEqual(result["status"], "held")
        self.assertEqual(len(result["votes"]), 1)
        stats = telemetry.stats(result["votes"][0]["model"], "review")
        self.assertEqual(stats["n"], 1)
        self.assertEqual(stats["success_rate"], 1.0)

    def test_a_malformed_answer_is_still_a_failure(self):
        telemetry = Telemetry()
        result = two_vote_review("deepseek-4.1-flash", "001", FILES,
                                 Router(telemetry), lambda model, prompt: {"verdict": "maybe"})
        self.assertEqual(result["status"], "held")
        stats = telemetry.stats(result["votes"][0]["model"], "review")
        self.assertEqual(stats["n"], 1)
        self.assertEqual(stats["success_rate"], 0.0)

    def test_baseline_context_includes_unchanged_security_and_resource_files_within_budget(self):
        from factory.review_circuit import baseline_diff, baseline_context
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder)
            def git(*args):
                return subprocess.check_output(['git', '-C', folder, *args], text=True).strip()
            git('init', '-q')
            src_main = repo / 'demo/forum-app/src/main/java/local/aeion/forum'
            src_test = repo / 'demo/forum-app/src/test/java/local/aeion/forum'
            src_main.mkdir(parents=True)
            src_test.mkdir(parents=True)
            (src_main / 'AuthResource.java').write_text('@Path("/api/auth") class AuthResource {}\n')
            (src_main / 'CsrfGuard.java').write_text('@Provider class CsrfGuard { /* COMMITTED_CSRF_GUARD */ }\n')
            (src_test / 'AuthResourceTest.java').write_text('class AuthResourceTest { /* EXISTING_COOKIE_TEST */ }\n')
            (repo / 'demo/forum-app/src/main/resources').mkdir(parents=True)
            (repo / 'demo/forum-app/src/main/resources/.env').write_text('GH_API_KEY=secret1234567890\n')
            git('add', '-A')
            git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'base')
            base = git('rev-parse', 'HEAD')
            # Dirty worktree change must be ignored by baseline_context.
            (src_main / 'CsrfGuard.java').write_text('@Provider class CsrfGuard { /* DIRTY_WORKTREE */ }\n')

            changed = {'demo/forum-app/src/main/java/local/aeion/forum/AuthResource.java': '@Path("/api/auth") class AuthResource { void logoutAll() {} }\n'}
            diff = baseline_diff(repo, base, changed)
            ctx = baseline_context(repo, base, changed)
            self.assertNotIn('demo/forum-app/src/main/java/local/aeion/forum/AuthResource.java', ctx)
            self.assertNotIn('demo/forum-app/src/main/resources/.env', ctx)
            self.assertIn('COMMITTED_CSRF_GUARD', ctx['demo/forum-app/src/main/java/local/aeion/forum/CsrfGuard.java'])
            self.assertNotIn('DIRTY_WORKTREE', ctx['demo/forum-app/src/main/java/local/aeion/forum/CsrfGuard.java'])
            self.assertIn('EXISTING_COOKIE_TEST', ctx['demo/forum-app/src/test/java/local/aeion/forum/AuthResourceTest.java'])

            seen = []
            res = two_vote_review('glm-5.3-flash', '005', changed, Router(Telemetry()),
                                  lambda m, p: seen.append(p) or {'verdict': 'approve', 'reason': 'ok'},
                                  baseline=diff, base_sha=base, base_context=ctx)
            self.assertEqual(res['status'], 'approved')
            self.assertEqual(res['coverage']['files'], sorted(changed))
            self.assertTrue(all('UNCHANGED BASE CONTEXT' in p and 'COMMITTED_CSRF_GUARD' in p for p in seen))
            # Core size enforcement still rejects oversized artifacts even when base_context is supplied.
            over = two_vote_review('glm-5.3-flash', '005', {'src/Big.java': 'x' * (MAX_PROMPT_CHARS + 1)},
                                   Router(Telemetry()), lambda *_: {'verdict': 'approve'},
                                   base_context=ctx)
            self.assertEqual(over['reason'], 'review_input_too_large')

    def test_baseline_context_skips_non_utf8_and_preserves_priority_order(self):
        import subprocess
        import tempfile
        from pathlib import Path
        from factory.review_circuit import _review_input, baseline_context

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / 'repo'
            (repo / 'demo/forum-app/src/main/java/local/aeion/forum').mkdir(parents=True)
            (repo / 'demo/forum-app/src/main/resources/db/migration').mkdir(parents=True)
            bad_props = repo / 'demo/forum-app/src/main/resources/application.properties'
            bad_props.write_bytes(b'# non-utf8 comment \xff\xfe\nquarkus.http.port=8081\n')
            aaa = repo / 'demo/forum-app/src/main/java/local/aeion/forum/AaaHelper.java'
            aaa.write_text('package local.aeion.forum;\npublic class AaaHelper {}\n', encoding='utf-8')
            mig = repo / 'demo/forum-app/src/main/resources/db/migration/V1__init.sql'
            mig.write_text('CREATE TABLE sessions (id BIGINT PRIMARY KEY);\n', encoding='utf-8')
            changed = repo / 'demo/forum-app/src/main/java/local/aeion/forum/Changed.java'
            changed.write_text('package local.aeion.forum;\npublic class Changed {}\n', encoding='utf-8')

            for args in (['init', '-q'], ['config', 'user.name', 'Test'],
                         ['config', 'user.email', 'test@example.invalid'], ['add', '.'],
                         ['commit', '-qm', 'base']):
                subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True)
            base_sha = subprocess.run(
                ['git', '-C', str(repo), 'rev-parse', 'HEAD'],
                check=True, capture_output=True, text=True,
            ).stdout.strip()

            files = {'demo/forum-app/src/main/java/local/aeion/forum/Changed.java': changed.read_text()}
            ctx = baseline_context(repo, base_sha, files)
            mig_rel = 'demo/forum-app/src/main/resources/db/migration/V1__init.sql'
            aaa_rel = 'demo/forum-app/src/main/java/local/aeion/forum/AaaHelper.java'
            self.assertEqual(list(ctx.keys()), [mig_rel, aaa_rel])
            self.assertNotIn('demo/forum-app/src/main/resources/application.properties', ctx)

            core_prompt, core_cov = _review_input('005', files, base_sha=base_sha)
            header = (
                '\nUNCHANGED BASE CONTEXT (read-only committed files from frozen base SHA; '
                'do not require edits unless changed code introduces or exposes a defect):'
            )
            mig_block = f"\n--- {mig_rel} (unchanged base) ---\n{ctx[mig_rel]}"
            tight_limit = core_cov['bytes'] + len(header.encode('utf-8')) + len(mig_block.encode('utf-8'))
            prompt, cov = _review_input('005', files, max_chars=tight_limit, base_sha=base_sha, base_context=ctx)
            self.assertTrue(cov['complete'])
            self.assertIn(mig_rel, prompt)
            self.assertNotIn(aaa_rel, prompt)


if __name__ == "__main__":
    unittest.main()
