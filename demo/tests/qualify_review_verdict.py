"""Real Flue finish-hook repair of a missing typed verdict; local scripted inference only."""
from http.server import ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
import threading
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'demo/tests'),str(ROOT/'demo'),str(ROOT/'demo/app')]
import qualify_factory_flue as fixture
from relay import ContextRelay
import runner


def main():
    fixture.review_without_tool_first=True
    server=ThreadingHTTPServer(('127.0.0.1',0),fixture.Inference)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    boundary = 'none'

    class Counter:
        revision = 'synthetic-review-channel'
        requests = 0

        def count(self, _payload):
            self.requests += 1
            if boundary == 'relay' and self.requests == 3:
                return 275000
            if boundary == 'native' and self.requests == 2:
                return 236000
            return 4000

    def local_relay(model,key,limit,checkpoint,event,**kwargs):
        return ContextRelay(model,key,limit,checkpoint,event,**kwargs,
            upstream=f'http://127.0.0.1:{server.server_port}/v1/chat/completions',counter=Counter())
    review=fixture.FixtureReview(cost_limit='1.00')
    review.build_id='f'*32
    review.authorization_check=lambda:True  # This disposable scripted fixture has no Store attempt.
    try:
        with patch.dict(os.environ,{'OPENCODE_API_KEY':'synthetic'}),patch.object(runner,'ContextRelay',side_effect=local_relay):
            result=review('deepseek-4.1-flash','Synthetic fixture: submit an independent verdict through the typed tool.')
            assert result['verdict']=='approve'
            assert fixture.calls['review']==3,fixture.calls
            assert review.last_execution['forwarded_count']==3
            assert review.last_usage['complete'] is True

            for boundary, input_tokens in (('relay', 4000), ('native', 250001)):
                fixture.review_input_at_submission = input_tokens
                fixture.calls['review'] = 0
                result = review('deepseek-4.1-flash', 'Synthetic fixture: judge the frozen packet.')
                assert result['verdict'] == 'approve'
                assert fixture.calls['review'] == review.last_execution['forwarded_count'] == 2
                assert review.last_execution['failure'] == 'AEION_HANDOVER'
                assert review.last_execution['submission_recovered'] is True
                assert review.last_usage['complete'] is True

        print(json.dumps({'status':'passed','synthetic':True,'real_provider_requests':0,
            'missing_verdict_continuations':1,'scripted_requests':7,'typed_result_required':True,
            'context_stopped_acknowledgement_recovered':True}))
    finally:
        server.shutdown();server.server_close()


if __name__=='__main__':main()
