import importlib.util
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("luna_guard", Path(__file__).parents[1] / "scripts/luna_cost_guard.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def ledger(tmp_path, ceiling="0.05", historical="0.001057199"):
    path = tmp_path / "cost.sqlite3"
    guard.initialize(path, {"approved_additional_budget_usd": ceiling, "historical_reserved_usd": historical})
    return path


def test_import_preserves_historical_spend_and_cannot_reset(tmp_path):
    path = ledger(tmp_path)
    assert guard.snapshot(path)["remaining_pico_usd"] == 48_942_801_000
    with pytest.raises(FileExistsError):
        ledger(tmp_path)
    assert guard.snapshot(path)["historical_pico_usd"] == 1_057_199_000


def test_missing_ledger_fails_closed(tmp_path):
    with pytest.raises(guard.BudgetBlocked):
        guard.reserve(10, 512, tmp_path / "missing.sqlite3")


def test_corrupt_ledger_is_a_local_budget_block_not_a_provider_error(tmp_path):
    path = tmp_path / 'corrupt.sqlite3'
    path.write_bytes(b'not a spending ledger')
    with pytest.raises(guard.BudgetBlocked, match='allowance was not reset'):
        guard.snapshot(path)


def test_more_than_sixteen_calls_allowed_if_cost_fits(tmp_path):
    path = ledger(tmp_path)
    for _ in range(30):
        request_id = guard.reserve(100, 512, path)
        guard.settle(request_id, {"input_tokens": 100, "output_tokens": 1}, path)
    assert guard.snapshot(path)["remaining_pico_usd"] > 0


def test_concurrent_background_and_retry_reservations_cannot_overspend(tmp_path):
    path = ledger(tmp_path, "0.001", "0")
    def attempt(_):
        try:
            return guard.reserve(1000, 512, path)
        except guard.BudgetBlocked:
            return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(attempt, range(20)))
    assert sum(bool(r) for r in results) == 2
    assert guard.snapshot(path)["remaining_pico_usd"] >= 0


def test_disconnect_and_restart_retain_reservation(tmp_path):
    path = ledger(tmp_path)
    request_id = guard.reserve(1000, 512, path)
    before = guard.snapshot(path)
    guard.settle(request_id, None, path)
    assert guard.snapshot(path) == before


def test_actual_usage_releases_only_unused_hold(tmp_path):
    path = ledger(tmp_path)
    request_id = guard.reserve(1000, 512, path)
    guard.settle(request_id, {"input_tokens": 1000, "output_tokens": 10}, path)
    assert guard.snapshot(path)["requests_pico_usd"] == 143_000_000
    with pytest.raises(ValueError):
        guard.settle(request_id, {"input_tokens": 0, "output_tokens": 0}, path)


def test_unexpected_usage_freezes_guard(tmp_path):
    path = ledger(tmp_path)
    request_id = guard.reserve(1, 1, path)
    guard.settle(request_id, {"input_tokens": 2, "output_tokens": 2}, path)
    assert guard.snapshot(path)["frozen"]
    with pytest.raises(guard.BudgetBlocked):
        guard.reserve(1, 1, path)


def test_only_luna_text_and_local_functions_with_capped_output():
    base = {"model": "gpt-6-luna", "messages": [{"role": "user", "content": "hello"}], "max_completion_tokens": 10000}
    payload = guard.payload_for(base)
    assert payload["max_output_tokens"] == 512
    assert payload["service_tier"] == "default"
    assert payload["reasoning"] == {"effort": "none"}
    with pytest.raises(ValueError):
        guard.payload_for({**base, "model": "gpt-6-astra"})
    with pytest.raises(ValueError):
        guard.payload_for({**base, "tools": [{"type": "web_search"}]})
    with pytest.raises(ValueError):
        guard.payload_for({**base, "messages": [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": "x"}}]}]})


def test_tool_history_translates_without_losing_call_identity():
    payload = guard.payload_for({"model": "gpt-6-luna", "messages": [
        {"role": "assistant", "content": None, "tool_calls": [{"id": "call1", "type": "function", "function": {"name": "manage_documents", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "call1", "content": "owned document"},
    ]})
    assert payload["input"][0]["call_id"] == payload["input"][1]["call_id"] == "call1"
    assert payload["input"][1]["output"] == "owned document"


def test_forced_tool_choice_survives_transport_adaptation():
    payload = guard.payload_for({"model": "gpt-6-luna", "messages": [{"role": "user", "content": "Suggest an edit"}],
        "tools": [{"type": "function", "function": {"name": "suggest_document", "parameters": {"type": "object", "properties": {}}}}],
        "tool_choice": {"type": "function", "function": {"name": "suggest_document"}}, "parallel_tool_calls": False})
    assert payload["tool_choice"] == {"type": "function", "name": "suggest_document"}
    assert payload["parallel_tool_calls"] is False


@pytest.mark.parametrize("stream", [True, False])
def test_guard_counts_exact_payload_before_forwarding_and_records_usage(tmp_path, monkeypatch, stream):
    import json
    import httpx
    from fastapi.testclient import TestClient
    path = ledger(tmp_path)
    monkeypatch.setattr(guard, "LEDGER", path)
    seen = []
    def upstream(request):
        payload = json.loads(request.content)
        seen.append((request.url.path, payload))
        assert payload["model"] == "gpt-6-luna"
        if request.url.path.endswith("input_tokens"):
            return httpx.Response(200, json={"input_tokens": 20, "object": "response.input_tokens"})
        assert guard.snapshot(path)["requests_pico_usd"] == 20*guard.INPUT_RATE+16*guard.OUTPUT_RATE
        events = [
            {"type": "response.output_text.delta", "delta": "PIGEON works"},
            {"type": "response.completed", "response": {"model": "gpt-6-luna", "service_tier": "default", "usage": {"input_tokens": 20, "output_tokens": 3}}},
        ]
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, content="".join("data: "+json.dumps(e)+"\n\n" for e in events))
    original = httpx.AsyncClient
    monkeypatch.setattr(guard.httpx, "AsyncClient", lambda **kw: original(transport=httpx.MockTransport(upstream), **kw))
    with TestClient(guard.app) as client:
        response = client.post("/v1/chat/completions", headers={"Authorization": "Bearer test-only"}, json={"model": "gpt-6-luna", "messages": [{"role": "user", "content": "hello"}], "stream": stream, "max_completion_tokens": 16})
    assert response.status_code == 200
    assert "PIGEON works" in response.text
    assert seen[0][1]["input"] == seen[1][1]["input"]
    assert guard.snapshot(path)["requests_pico_usd"] == 20*guard.INPUT_RATE+3*guard.OUTPUT_RATE


def test_insufficient_budget_does_not_send_generation(tmp_path, monkeypatch):
    import httpx
    from fastapi.testclient import TestClient
    path = ledger(tmp_path, "0.000001", "0")
    monkeypatch.setattr(guard, "LEDGER", path)
    seen = []
    def upstream(request):
        seen.append(request.url.path)
        return httpx.Response(200, json={"input_tokens": 100})
    original = httpx.AsyncClient
    monkeypatch.setattr(guard.httpx, "AsyncClient", lambda **kw: original(transport=httpx.MockTransport(upstream), **kw))
    with TestClient(guard.app) as client:
        response = client.post("/v1/chat/completions", headers={"Authorization": "Bearer test-only"}, json={"model": "gpt-6-luna", "messages": [{"role": "user", "content": "hello"}]})
    assert response.status_code == 402
    assert response.json()["error"]["origin"] == "pigeon_budget_guard"
    assert seen == ["/v1/responses/input_tokens"]
