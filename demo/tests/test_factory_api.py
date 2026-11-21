from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import tempfile
import threading
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.api import FactoryApp, ApiError
from factory.sse import serve_events, SseHub

LOOP_HOST = "127.0.0.1:8088"
LOOP_ORIGIN = "http://127.0.0.1:8088"


def write_manifest(path):
    data = {
        "schema_version": 2,
        "count": 2,
        "features": [
            {"id": "001", "title": "Root", "area": "foundation", "size": "S", "parallel": False,
             "phase": "P0", "tier": 3, "write_paths": ["demo/forum/product/"], "depends_on": [], "file": "001.md"},
            {"id": "002", "title": "Dep", "area": "foundation", "size": "S", "parallel": False,
             "phase": "P0", "tier": 3, "write_paths": ["demo/forum/product/"], "depends_on": ["001"], "file": "002.md"},
        ],
    }
    path.write_text(json.dumps(data))


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.manifest = Path(self.tmp.name) / "MANIFEST.json"
        write_manifest(self.manifest)
        for fid in ("001", "002"):
            (Path(self.tmp.name) / f"{fid}.md").write_text(f"# {fid}\n")
        self.app = FactoryApp(self.manifest, Path(self.tmp.name) / "state", bootstrap_token="secret")

    def login(self):
        status, body, headers = self.app.login(LOOP_HOST, LOOP_ORIGIN, {"token": "secret"})
        self.assertEqual(status, 200)
        return body, headers

    def test_login_wrong_token_rejected(self):
        with self.assertRaises(ApiError) as ctx:
            self.app.login(LOOP_HOST, LOOP_ORIGIN, {"token": "wrong"})
        self.assertEqual(ctx.exception.status, 401)

    def test_login_returns_csrf_and_sets_cookie(self):
        body, headers = self.login()
        self.assertIn("csrf", body)
        self.assertIn("Set-Cookie", headers)
        session = self.app.authenticate(headers["Set-Cookie"])
        self.assertIsNotNone(session)
        self.assertTrue(self.app.auth.check_csrf(session, body["csrf"]))

    def test_bootstrap_token_is_single_use(self):
        self.login()
        with self.assertRaises(ApiError) as ctx:
            self.app.login(LOOP_HOST, LOOP_ORIGIN, {"token": "secret"})
        self.assertEqual(ctx.exception.status, 401)

    def test_authenticate_missing_cookie_is_none(self):
        self.assertIsNone(self.app.authenticate(None))
        self.assertIsNone(self.app.authenticate("other=1"))

    def test_login_foreign_origin_rejected(self):
        with self.assertRaises(ApiError) as ctx:
            self.app.login("evil.example.com", "http://evil.example.com", {"token": "secret"})
        self.assertEqual(ctx.exception.status, 403)

    def test_queue_requires_csrf(self):
        body, headers = self.login()
        session = self.app.authenticate(headers["Set-Cookie"])
        with self.assertRaises(ApiError) as ctx:
            self.app.queue(LOOP_HOST, LOOP_ORIGIN, session, "wrong", {"ids": ["001"], "idempotency_key": "k1"})
        self.assertEqual(ctx.exception.status, 403)
        self.assertEqual(ctx.exception.code, "csrf_denied")

    def test_queue_admits_with_valid_csrf(self):
        body, headers = self.login()
        session = self.app.authenticate(headers["Set-Cookie"])
        status, result, _ = self.app.queue(LOOP_HOST, LOOP_ORIGIN, session, body["csrf"],
                                           {"ids": ["001"], "idempotency_key": "k1"})
        self.assertEqual(status, 200)
        self.assertEqual(result["status"], "admitted")

    def test_missing_dependency_holds_in_api(self):
        body, headers = self.login()
        session = self.app.authenticate(headers["Set-Cookie"])
        _, result, _ = self.app.queue(LOOP_HOST, LOOP_ORIGIN, session, body["csrf"],
                                      {"ids": ["002"], "idempotency_key": "k2"})
        self.assertEqual(result["status"], "admitted")
        build = self.app.store.board()[0]
        self.assertEqual(build["hold_reason"], "dependency_missing")

    def test_cancel_unknown_build_404(self):
        body, headers = self.login()
        session = self.app.authenticate(headers["Set-Cookie"])
        with self.assertRaises(ApiError) as ctx:
            self.app.cancel(LOOP_HOST, LOOP_ORIGIN, session, body["csrf"], {"build_id": "nope"})
        self.assertEqual(ctx.exception.status, 404)

    def test_the_worker_spends_from_the_forum_purse(self):
        self.assertIs(self.app.worker.budget, self.app.budget)
        self.assertEqual(self.app.worker.budget_scope, "aeion-autonomous-forum")
        self.app.budget.admit("aeion-autonomous-forum", "150.00", note="exhaust")
        self.app.worker.config["cost_reservation_usd"] = "0.01"
        body, headers = self.login()
        session = self.app.authenticate(headers["Set-Cookie"])
        self.app.queue(LOOP_HOST, LOOP_ORIGIN, session, body["csrf"],
                       {"ids": ["001"], "idempotency_key": "k-purse"})
        result = self.app.tick()
        self.assertEqual(result["result"], {"status": "held", "reason": "budget_unavailable"})
        build = self.app.store.board()[0]
        self.assertEqual(build["hold_reason"], "budget_unavailable")

    def test_event_stream_replays_and_closes_without_extending_the_session(self):
        app = self.app

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                serve_events(self, app)

            def respond(self, status, body):
                self.send_error(status, body["error"])

            def log_message(self, *_):
                pass

        with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                now = [0]
                with patch("factory.auth.time.time_ns", side_effect=lambda: now[0]):
                    _, headers = self.login()
                    app.hub = SseHub(max_events=3)
                    for _ in range(5):
                        app.hub.publish("build_progress")
                    cookie = headers["Set-Cookie"].split(";", 1)[0]

                    def request(since, last=None):
                        conn = HTTPConnection("127.0.0.1", server.server_port, timeout=3)
                        self.addCleanup(conn.close)
                        request_headers = {"Cookie": cookie}
                        if last is not None:
                            request_headers["Last-Event-ID"] = last
                        conn.request("GET", f"/api/factory/events?since={since}", headers=request_headers)
                        return conn.getresponse()

                    for cursor in (1, 6):
                        with self.subTest(cursor=cursor), request(cursor) as response:
                            self.assertEqual(response.status, 200)
                            self.assertEqual(response.read(), b"event: reload\ndata: {}\n\n")
                    now[0] = app.auth.idle_ns - 1
                    with request(1, "4") as response:
                        self.assertEqual(response.status, 200)
                        self.assertEqual([response.readline() for _ in range(4)],
                                         [b"id: 5\n", b"event: build_progress\n", b"data: \n", b"\n"])
                        now[0] += 2
                        self.assertEqual(response.read(), b"")
                    with request(0) as response:
                        self.assertEqual(response.status, 401)
            finally:
                server.shutdown()
                thread.join()

    def test_tick_publishes_events(self):
        body, headers = self.login()
        session = self.app.authenticate(headers["Set-Cookie"])
        self.app.queue(LOOP_HOST, LOOP_ORIGIN, session, body["csrf"], {"ids": ["001"], "idempotency_key": "k3"})
        self.app.tick()
        frames = self.app.events_since(0)
        self.assertTrue(any(f["event"] == "build_updated" for f in frames))

    def test_tick_publishes_each_observation_once(self):
        body, headers = self.login()
        session = self.app.authenticate(headers["Set-Cookie"])
        self.app.queue(LOOP_HOST, LOOP_ORIGIN, session, body["csrf"], {"ids": ["001"], "idempotency_key": "k4"})
        self.app.tick()
        first = [f for f in self.app.events_since(0) if f["event"] == "observed"]
        self.assertEqual(len(first), 1)
        self.assertIn("artifact_digest", first[0]["data"])
        self.app.tick()
        second = [f for f in self.app.events_since(0) if f["event"] == "observed"]
        self.assertEqual(len(second), 1)

    def test_login_rate_limited_after_ten_failures(self):
        for _ in range(10):
            with self.assertRaises(ApiError):
                self.app.login(LOOP_HOST, LOOP_ORIGIN, {"token": "wrong"})
        with self.assertRaises(ApiError) as ctx:
            self.app.login(LOOP_HOST, LOOP_ORIGIN, {"token": "secret"})
        self.assertEqual(ctx.exception.status, 429)


if __name__ == "__main__":
    unittest.main()
