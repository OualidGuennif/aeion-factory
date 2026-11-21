"""Bounded server-sent-event hub for the factory board.

Events are metadata only: a monotonic sequence plus an event name and a JSON-safe
payload. A bounded ring buffer keeps a reconnect cursor window; a client that falls
behind the window is told to reload instead of receiving a partial history.
"""
import json
import re
import threading
import time
from collections import deque
from urllib.parse import parse_qs, urlparse

from .auth import host_origin_ok


class SseHub:
    def __init__(self, max_events=200):
        self.max_events = max_events
        self._lock = threading.Lock()
        self._buffer = deque(maxlen=max_events)
        self._seq = 0

    def publish(self, event, data=None):
        with self._lock:
            self._seq += 1
            frame = {"seq": self._seq, "event": event, "data": data}
            self._buffer.append(frame)
            return dict(frame)

    def earliest_seq(self):
        with self._lock:
            if not self._buffer:
                return self._seq
            return self._buffer[0]["seq"]

    def replay(self, since=0):
        """Return the remaining frames or signal a required reload with None."""
        with self._lock:
            oldest = self._buffer[0]["seq"] if self._buffer else self._seq + 1
            if since and not (oldest - 1 <= since <= self._seq):
                return None
            return [dict(f) for f in self._buffer if f["seq"] > since]


def serve_events(handler, factory):
    """Serve one authenticated stream without extending the session deadline."""
    if not host_origin_ok(handler.headers.get("Host", "")):
        handler.respond(403, {"error": "origin_denied"})
        return
    cookie = handler.headers.get("Cookie")
    if factory.authenticate(cookie, touch=False) is None:
        handler.respond(401, {"error": "unauthorized"})
        return
    query = parse_qs(urlparse(handler.path).query)
    cursor = handler.headers.get("Last-Event-ID") or query.get("since", ["0"])[0]
    if not re.fullmatch(r"[0-9]{1,20}", cursor):
        handler.respond(400, {"error": "invalid_since"})
        return
    since = int(cursor)
    handler.close_connection = True
    handler.send_response(200)
    handler.send_header("Content-Type", "text/event-stream")
    handler.send_header("Cache-Control", "no-cache")
    handler.send_header("Connection", "close")
    handler.send_header("X-Accel-Buffering", "no")
    handler.send_header("Content-Security-Policy", "default-src 'none'")
    handler.end_headers()
    try:
        last_write = time.monotonic()
        while factory.authenticate(cookie, touch=False) is not None:
            frames = factory.events_since(since)
            if frames is None:
                handler.wfile.write(b"event: reload\ndata: {}\n\n")
                handler.wfile.flush()
                return
            for frame in frames:
                data = json.dumps(frame["data"], separators=(",", ":")) if frame["data"] is not None else ""
                handler.wfile.write(f"id: {frame['seq']}\nevent: {frame['event']}\ndata: {data}\n\n".encode())
                since = frame["seq"]
            if frames:
                last_write = time.monotonic()
            elif time.monotonic() - last_write >= 15:
                handler.wfile.write(b": keepalive\n\n")
                last_write = time.monotonic()
            handler.wfile.flush()
            time.sleep(0.4)
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass
