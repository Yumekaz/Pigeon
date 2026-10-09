"""A deterministic OpenAI-compatible provider for the smoke suite.

Every scenario that needs a model talks to this instead of a real
endpoint. It binds an ephemeral port on loopback, so no scenario depends
on network egress, on a model being downloaded, or on two runs on the
same machine picking the same port.

It answers the two routes the app needs to treat it as a local
OpenAI-compatible server: ``GET /v1/models`` for discovery and probing,
and ``POST /v1/chat/completions`` for both the buffered and the streamed
turn. Each reply is a fixed marker plus the model id, so a test can tell
the two models apart in a blind comparison; every request is recorded so
a test can assert the user's message actually reached the provider
rather than only that some text came back.
"""
from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Two model ids so the Compare area has something to reveal.
MODEL_PRIMARY = "odysseus-smoke-primary"
MODEL_SECONDARY = "odysseus-smoke-secondary"
MODEL_LUNA = "gpt-6-luna"
MODELS = (MODEL_PRIMARY, MODEL_SECONDARY, MODEL_LUNA)

# The marker each reply starts with. Distinctive enough that finding it
# in a response body cannot be a coincidence, and short enough to read
# in a failure message.
REPLY_MARKER = "ODYSSEUS-SMOKE-REPLY"

# Bind on loopback, kernel-assigned port. No literal port anywhere.
BIND_HOST = "127.0.0.1"
BIND_PORT = 0


def reply_for(model: str) -> str:
    """The exact assistant text this provider returns for ``model``."""
    return f"{REPLY_MARKER} {model}"


class _Recorder:
    """Requests the provider has served, for assertions after the fact."""

    def __init__(self):
        self._lock = threading.Lock()
        self._calls = []
        self.native_document_id = None
        self.native_suggestion_args = None
        self.native_document_reply = "PIGEON native tool fixture."

    def record(self, payload: dict) -> None:
        with self._lock:
            self._calls.append(payload)

    @property
    def calls(self) -> list[dict]:
        with self._lock:
            return list(self._calls)

    def prompts(self) -> list[str]:
        """Every user message this provider has been sent."""
        out = []
        for call in self.calls:
            for message in call.get("messages") or []:
                if message.get("role") == "user":
                    out.append(str(message.get("content") or ""))
        return out

    def clear(self) -> None:
        with self._lock:
            self._calls.clear()


def _handler_for(recorder: _Recorder):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args):  # noqa: D102 - silence stderr access log
            pass

        def _send_json(self, status: int, body: dict) -> None:
            raw = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):  # noqa: N802 - BaseHTTPRequestHandler's contract
            if self.path.rstrip("/").endswith("/models"):
                self._send_json(200, {
                    "object": "list",
                    "data": [{"id": name, "object": "model", "owned_by": "smoke"}
                             for name in MODELS],
                })
                return
            self._send_json(404, {"error": {"message": f"no route {self.path}"}})

        def do_POST(self):  # noqa: N802 - BaseHTTPRequestHandler's contract
            length = int(self.headers.get("Content-Length") or 0)
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
            except ValueError:
                payload = {}
            if not isinstance(payload, dict):
                payload = {}
            recorder.record(payload)

            model = str(payload.get("model") or MODEL_PRIMARY)
            text = reply_for(model)
            if recorder.native_suggestion_args and model == MODEL_LUNA:
                self._send_tool_stream(model, {"index": 0, "id": "smoke-suggestion-" + str(time.time_ns()),
                    "type": "function", "function": {"name": "suggest_document", "arguments": json.dumps(recorder.native_suggestion_args)}})
                return
            if recorder.native_document_id and model == MODEL_LUNA:
                results = [str(m.get("content") or "") for m in payload.get("messages", []) if m.get("role") == "tool"]
                if results:
                    text = recorder.native_document_reply if any(recorder.native_document_reply in result for result in results) else "STUB-DOCUMENT-READ-FAILED"
                elif any(t.get("function", {}).get("name") == "manage_documents" for t in payload.get("tools", [])):
                    call = {"index": 0, "id": "smoke-document-read-" + recorder.native_document_id, "type": "function", "function": {
                        "name": "manage_documents", "arguments": json.dumps({"action": "read", "document_id": recorder.native_document_id})}}
                    self._send_tool_stream(model, call)
                    return
            if payload.get("stream"):
                self._send_stream(model, text)
                return
            self._send_json(200, {
                "id": "smoke-completion",
                "object": "chat.completion",
                "model": model,
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": text},
                    "finish_reason": "stop",
                }],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            })

        def _send_tool_stream(self, model, call):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Connection", "close")
            self.end_headers()
            for chunk in [
                {"choices": [{"index": 0, "delta": {"tool_calls": [call]}}], "model": model},
                {"choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls"}], "model": model},
            ]:
                self.wfile.write(b"data: " + json.dumps(chunk).encode("utf-8") + b"\n\n")
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()

        def _send_stream(self, model: str, text: str) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()
            for chunk in (
                {"choices": [{"index": 0, "delta": {"content": text}}], "model": model},
                {"choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}], "model": model},
            ):
                self.wfile.write(b"data: " + json.dumps(chunk).encode("utf-8") + b"\n\n")
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()

    return Handler


class StubProvider:
    """A running stub provider. Use as a context manager."""

    def __init__(self):
        self.recorder = _Recorder()
        self._server = ThreadingHTTPServer((BIND_HOST, BIND_PORT), _handler_for(self.recorder))
        self._server.daemon_threads = True
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def port(self) -> int:
        return self._server.server_address[1]

    @property
    def base_url(self) -> str:
        """The OpenAI-compatible base the app should be pointed at."""
        return f"http://{BIND_HOST}:{self.port}/v1"

    def start(self) -> "StubProvider":
        self._thread.start()
        return self

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)

    def __enter__(self) -> "StubProvider":
        return self.start()

    def __exit__(self, *exc) -> None:
        self.stop()
