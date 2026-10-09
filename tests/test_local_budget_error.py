import json

from src.llm_core import _format_upstream_error, _upstream_error_payload, _stream_error_fallback_override
from src.agent_loop import _local_budget_stream_message


def test_local_budget_block_is_not_an_openai_error_and_cannot_fallback():
    body = json.dumps({"error": {"type": "pigeon_budget_block", "origin": "pigeon_budget_guard", "code": "budget_blocked", "message": "PIGEON local test budget: allowance held. No OpenAI generation request was sent."}})
    payload = _upstream_error_payload(402, body, "http://127.0.0.1:7018/v1/chat/completions")
    assert payload["origin"] == "pigeon_budget_guard"
    chunk = 'event: error\ndata: ' + json.dumps(payload) + '\n\n'
    assert _stream_error_fallback_override(chunk) is False
    assert _local_budget_stream_message(chunk) == payload["text"]
    assert "rate-limit" not in payload["text"]


def test_real_openai_error_keeps_provider_identity():
    body = json.dumps({"error": {"message": "Rate limit exceeded"}})
    assert "OpenAI rate-limited" in _format_upstream_error(429, body, "https://api.openai.com/v1/chat/completions")
    assert "origin" not in _upstream_error_payload(429, body, "https://api.openai.com/v1/chat/completions")


def test_remote_response_cannot_claim_local_budget_origin():
    body = json.dumps({"error": {"type": "pigeon_budget_block", "origin": "pigeon_budget_guard", "message": "blocked"}})
    assert "origin" not in _upstream_error_payload(402, body, "https://api.openai.com/v1/chat/completions")
