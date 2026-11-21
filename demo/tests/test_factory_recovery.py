"""State races and recovery must never create a second paid attempt automatically."""
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.manifest import Catalog
from factory.store import Store, StoreError, HELD, LIVE_COMPLETE


class RecoveryTests(unittest.TestCase):
    def test_model_authority_expires_and_is_revoked_by_cancellation(self):
        build=self.first.claim_next(self.catalog)
        attempt,generation=build['attempt_id'],build['attempt_generation']
        self.assertTrue(self.second.attempt_authorized(attempt,generation))
        self.assertFalse(self.second.attempt_authorized(attempt,generation+1))
        self.first.cancel(build['build_id'])
        self.assertFalse(self.second.attempt_authorized(attempt,generation))

    def test_expired_attempt_cannot_authorize_another_model_request(self):
        build=self.first.claim_next(self.catalog,lease_ns=0)
        self.assertFalse(self.first.attempt_authorized(build['attempt_id'],build['attempt_generation']))
        self.assertFalse(self.first.record_progress(
            build['attempt_id'],build['attempt_generation'],'tool.finished',{}))

    def test_preparation_progress_does_not_count_as_author_work_or_resume_on_expiry(self):
        build = self.first.claim_next(self.catalog, lease_ns=100)
        self.first._now = lambda: build['lease_until_ns'] - 1
        for step, phase in enumerate(('preparing', 'model.step.started', 'tool.finished', 'gen_ai.request')):
            self.assertTrue(self.first.record_progress(
                build['attempt_id'], build['attempt_generation'], phase,
                {'model': 'glm-5.3-flash', 'step': step}))
        self.assertEqual(self.first.work_event_count(build['build_id']), 0)
        self.first._now = lambda: build['lease_until_ns']
        self.assertIsNone(self.first.claim_next(self.catalog))
        self.assertEqual(self.first.build(build['build_id'])['hold_reason'], 'reconciliation_needed')

    def test_old_hold_cannot_overwrite_a_reclaimed_attempt(self):
        old = self.first.claim_next(self.catalog)
        for phase in ('building', 'tool.finished'):
            self.assertTrue(self.first.record_progress(old['attempt_id'], old['attempt_generation'], phase, {}))
        self.assertEqual(self.first.work_event_count(old['build_id']), 1)
        self.assertEqual(self.first.resume_interrupted(old['attempt_id'], old['attempt_generation'],
            {'failure': 'CLI_FAILED', 'trigger': 'cli_interrupted'})['status'], 'queued')
        current = self.second.claim_next(self.catalog)
        self.assertNotEqual(old['attempt_id'], current['attempt_id'])
        self.assertEqual(self.first.work_event_count(current['build_id']), 0)
        self.assertEqual(self.first.hold_dispatched(old, 'worker_error')['status'], 'stale_attempt')
        self.assertEqual(self.second.by_attempt(current['attempt_id'])['status'], 'dispatched')

    def test_expired_worker_cannot_report_completion_before_a_restart_reconciles_it(self):
        build=self.first.claim_next(self.catalog,lease_ns=0)
        result=self.first.complete_attempt(build['attempt_id'],build['attempt_generation'],{})
        self.assertEqual(result['status'],'expired_attempt')
        self.assertEqual(self.first.by_attempt(build['attempt_id'])['status'],'dispatched')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'factory.db'
        self.catalog = Catalog({'schema_version': 2, 'count': 1, 'features': [{
            'id': '017', 'title': 'Validation', 'area': 'foundation', 'size': 'S',
            'parallel': False, 'phase': 'P0', 'tier': 3,
            'write_paths': ['demo/forum/product/'], 'depends_on': [], 'file': '017.md'}]})
        self.first, self.second = Store(self.path), Store(self.path)
        self.first.admit(['017'], 'first', self.catalog)

    def interleave(self, action, concurrent):
        # Pause after the first operation has read its precondition. A second Store must
        # wait for that transaction, instead of overwriting its later state with stale data.
        paused, release, other_started = threading.Event(), threading.Event(), threading.Event()
        clock = self.first._now
        def pause_clock():
            paused.set()
            if not release.wait(3):
                raise AssertionError('first transaction was not released')
            return clock()
        self.first._now = pause_clock
        def run_other():
            other_started.set()
            return concurrent()
        with ThreadPoolExecutor(max_workers=2) as pool:
            primary = pool.submit(action)
            self.assertTrue(paused.wait(2))
            other = pool.submit(run_other)
            self.assertTrue(other_started.wait(2))
            try:
                other.result(timeout=0.2)
            except TimeoutError:
                pass  # A correctly serialized second writer waits for the first commit.
            finally:
                release.set()
            return primary.result(timeout=3), other.result(timeout=3)

    def test_two_stores_cannot_claim_the_same_job(self):
        first, second = self.interleave(lambda: self.first.claim_next(self.catalog),
                                        lambda: self.second.claim_next(self.catalog))
        self.assertIsNotNone(first)
        self.assertIsNone(second)
        self.assertEqual(self.first.board()[0]['attempt_id'], first['attempt_id'])

    def test_completion_cannot_overwrite_a_concurrent_cancellation(self):
        build = self.first.claim_next(self.catalog)
        completed, cancelled = self.interleave(
            lambda: self.first.complete_attempt(build['attempt_id'], build['attempt_generation'],
                                                 {}, terminal=LIVE_COMPLETE),
            lambda: self.second.cancel(build['build_id']))
        self.assertEqual(completed['status'], 'completed')
        self.assertEqual(cancelled['status'], 'already_terminal')
        self.assertEqual(self.first.board()[0]['status'], LIVE_COMPLETE)

    def test_restart_holds_an_expired_attempt_without_automatically_spending_again(self):
        build = self.first.claim_next(self.catalog, lease_ns=0)
        reopened = Store(self.path)
        row = reopened.board()[0]
        self.assertEqual(row['status'], HELD)
        self.assertEqual(row['hold_reason'], 'reconciliation_needed')
        self.assertEqual(row['attempt_id'], build['attempt_id'])
        self.assertIsNone(reopened.claim_next(self.catalog))

    def test_a_hold_blocks_another_launch_until_explicitly_cancelled(self):
        build = self.first.claim_next(self.catalog)
        self.first.hold_dispatched(build, 'owner_review_required')
        with self.assertRaisesRegex(StoreError, 'feature_in_progress:017'):
            self.second.admit(['017'], 'second-key', self.catalog)
        info = self.first.feature_availability(self.catalog)['017']
        self.assertFalse(info['selectable'])
        self.assertEqual(info['reason'], 'owner_review_required')
        self.first.cancel(build['build_id'])
        self.assertEqual(self.second.admit(['017'], 'retry-after-cancel', self.catalog)['status'], 'admitted')

    def test_a_hold_keeps_the_attempt_and_bounded_evidence(self):
        build = self.first.claim_next(self.catalog)
        evidence = {'build_id': build['build_id'], 'reason': 'review_input_too_large'}
        self.first.hold_dispatched(build, 'owner_review_required', receipt=evidence)
        row = self.second.board()[0]
        self.assertEqual(row['attempt_id'], build['attempt_id'])
        self.assertIn('review_input_too_large', row['receipt'])


if __name__ == '__main__':
    unittest.main()
