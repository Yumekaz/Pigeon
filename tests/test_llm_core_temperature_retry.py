"""Regression test: OpenAI-compatible aggregators can deprecate temperature per model.

zenmux.ai returns HTTP 400 "`temperature` is deprecated for this model" for
anthropic/claude-haiku-5.5 whenever the field carries a non-default value,
while the same request without (or with the default) succeeds. That broke
every llm_call_async caller that passes an explicit temperature — the research
endpoint probe (temperature=0), all DeepResearcher steps (0.1-0.5), memory
extraction, and chat auto-naming — while interactive chat (default 1.0) kept
working, which is why Deep Research failed but normal chats did not.

The version-gated omission (_anthropic_rejects_temperature) can't cover this:
it would silently strip a legitimate field from look-alike models on other
providers. Instead llm_call_async reacts to evidence — only when the
upstream's own 400 body names temperature does it drop the field and retry
once, granted outside the caller's retry budget (the probe calls with
max_retries=1 and must still get the retry).
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import asyncio

import pytest
from fastapi import HTTPException

import src.llm_core as llm_core
from src.llm_core import _temperature_rejected_by_upstream


ZENMUX_BODY = '`temperature` is deprecated for this model. (request_id: r1)'


class _FakeResponse:
    def __init__(self, *, ok, status_code=200, text="", payload=None):
        self.is_success = ok
        self.status_code = status_code
        self.text = text
        self._payload = payload or {}

    def json(self):
        return self._payload


def _ok_payload(content="ok"):
    return {"choices": [{"message": {"role": "assistant", "content": content}}]}


# ------------------------------------------------------------------
# _temperature_rejected_by_upstream
# ------------------------------------------------------------------

def test_detects_the_observed_zenmux_body():
    assert _temperature_rejected_by_upstream(400, ZENMUX_BODY) is True


def test_detects_other_explicit_temperature_blame():
    assert _temperature_rejected_by_upstream(
        400, "Parameter 'temperature' is not supported by this model"
    ) is True
    assert _temperature_rejected_by_upstream(
        400, "temperature is unsupported for this model"
    ) is True


def test_ignores_other_fields_and_statuses():
    assert _temperature_rejected_by_upstream(400, "`top_k` is deprecated for this model") is False
    assert _temperature_rejected_by_upstream(500, "temperature is deprecated for this model") is False
    assert _temperature_rejected_by_upstream(400, "") is False
    assert _temperature_rejected_by_upstream(400, None) is False


# ------------------------------------------------------------------
# llm_call_async retry behavior
# ------------------------------------------------------------------

def _run(monkeypatch, responses, model="anthropic/claude-haiku-5.5", **kwargs):
    """Drive llm_call_async against a scripted sequence of responses."""
    seen = []

    async def fake_post(client, url, headers, **kw):
        # Copy: the retry mutates the payload dict in place, so a reference
        # would alias the post-retry state back into earlier snapshots.
        seen.append(dict(kw["json"]))
        return responses[min(len(seen) - 1, len(responses) - 1)]

    monkeypatch.setattr(llm_core, "httpx_post_kimi_aware_async", fake_post)
    llm_core._response_cache.clear()
    out = asyncio.run(llm_core.llm_call_async(
        "https://zenmux.ai/api/v1/chat/completions",
        model,
        [{"role": "user", "content": "hi"}],
        temperature=0,
        max_tokens=5,
        **kwargs,
    ))
    return out, seen


def test_retries_once_without_temperature_and_succeeds(monkeypatch):
    out, seen = _run(
        monkeypatch,
        [
            _FakeResponse(ok=False, status_code=400, text=ZENMUX_BODY),
            _FakeResponse(ok=True, payload=_ok_payload()),
        ],
        max_retries=1,  # the probe's budget — the retry must still happen
    )
    assert out == "ok"
    assert len(seen) == 2
    assert seen[0]["temperature"] == 0
    assert "temperature" not in seen[1]


def test_non_temperature_400_is_not_retried(monkeypatch):
    with pytest.raises(HTTPException) as exc:
        _run(
            monkeypatch,
            [_FakeResponse(ok=False, status_code=400, text="`top_k` is deprecated for this model")],
            max_retries=1,
        )
    assert exc.value.status_code == 400
    assert "top_k" in str(exc.value.detail)


def test_temperature_retry_is_granted_only_once(monkeypatch):
    calls = []

    async def fake_post(client, url, headers, **kw):
        calls.append(dict(kw["json"]))
        return _FakeResponse(ok=False, status_code=400, text=ZENMUX_BODY)

    monkeypatch.setattr(llm_core, "httpx_post_kimi_aware_async", fake_post)
    llm_core._response_cache.clear()
    with pytest.raises(HTTPException):
        asyncio.run(llm_core.llm_call_async(
            "https://zenmux.ai/api/v1/chat/completions",
            "anthropic/claude-haiku-5.5",
            [{"role": "user", "content": "hi"}],
            temperature=0,
            max_tokens=5,
            max_retries=1,
        ))
    # One normal attempt + one temperature retry, then the error surfaces.
    assert len(calls) == 2
    assert "temperature" in calls[0]
    assert "temperature" not in calls[1]


def test_healthy_endpoint_requests_are_unchanged(monkeypatch):
    out, seen = _run(
        monkeypatch,
        [_FakeResponse(ok=True, payload=_ok_payload())],
        model="some-local-model",
    )
    assert out == "ok"
    assert len(seen) == 1
    assert seen[0]["temperature"] == 0
