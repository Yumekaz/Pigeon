"""GPT-6 tool transport recognition without provider calls."""
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest
from src.agent_loop import _agent_route_tool_mode

@pytest.mark.parametrize("model", ["gpt-6-luna", "gpt-6.1-sol", "gpt-6-astra"])
def test_gpt6_models_use_native_tools_through_compatible_proxy(monkeypatch, model):
    import core.database
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []
    monkeypatch.setattr(core.database, "SessionLocal", lambda: db)
    assert _agent_route_tool_mode("http://127.0.0.1:7018/v1/chat/completions", model) == (True, False, False)

def test_explicit_endpoint_tool_disable_still_wins(monkeypatch):
    import core.database
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = [SimpleNamespace(id="test", supports_tools=False)]
    monkeypatch.setattr(core.database, "SessionLocal", lambda: db)
    assert _agent_route_tool_mode("http://127.0.0.1:7018/v1/chat/completions", "gpt-6-luna") == (False, False, False)
