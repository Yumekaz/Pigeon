"""Regression test: empty-session-model recovery must be deterministic.

`_recover_empty_session_model` used to pick visible[0] — the first cached
model on the matched endpoint. On aggregators that ordering is arbitrary and
can hand the session a model the account cannot actually use (zenmux returns
HTTP 402 "balance greater than 0" for balance-gated models), and the session
silently switched to it mid-conversation.

Recovery now prefers the user's configured default chat model (settings
`default_model`) when the endpoint serves it, and only falls back to
visible[0] otherwise. It still never overrides a non-empty session model.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import core.database as cdb
import core.session_manager as sm
import routes.chat_routes as chat
import src.settings as settings_mod

ENDPOINT_URL = "https://zenmux.ai/api/v1/chat/completions"


@pytest.fixture
def state(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    cdb.Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    for module in (sm, chat):
        monkeypatch.setattr(module, "SessionLocal", factory)
    with factory() as db:
        db.add(cdb.ModelEndpoint(id="ep", owner="alice", name="zenmux",
                                 base_url=ENDPOINT_URL, is_enabled=True,
                                 cached_models='["mistral-large-4", "claude-haiku-5.5", "other-model"]',
                                 supports_tools=False))
        db.commit()
    manager = sm.SessionManager.__new__(sm.SessionManager)
    manager.sessions = {}
    manager.upload_handler = None
    yield factory, manager
    engine.dispose()


def _empty_session(manager):
    return manager.create_session("s", "Chat", ENDPOINT_URL, "",
                                  owner="alice", endpoint_id="ep")


def test_recovery_prefers_configured_default_model(state, monkeypatch):
    factory, manager = state
    sess = _empty_session(manager)
    monkeypatch.setattr(settings_mod, "get_setting",
                        lambda key, default=None: "claude-haiku-5.5" if key == "default_model" else default)
    assert chat._recover_empty_session_model(sess, "s", "alice") is True
    assert sess.model == "claude-haiku-5.5"
    with factory() as db:
        assert db.get(cdb.Session, "s").model == "claude-haiku-5.5"


def test_recovery_falls_back_to_first_visible_without_default(state, monkeypatch):
    factory, manager = state
    sess = _empty_session(manager)
    monkeypatch.setattr(settings_mod, "get_setting", lambda key, default=None: "")
    assert chat._recover_empty_session_model(sess, "s", "alice") is True
    assert sess.model == "mistral-large-4"


def test_recovery_ignores_default_not_served_by_endpoint(state, monkeypatch):
    factory, manager = state
    sess = _empty_session(manager)
    monkeypatch.setattr(settings_mod, "get_setting",
                        lambda key, default=None: "gpt-5.5" if key == "default_model" else default)
    assert chat._recover_empty_session_model(sess, "s", "alice") is True
    assert sess.model == "mistral-large-4"


def test_recovery_never_overrides_an_explicit_model(state, monkeypatch):
    factory, manager = state
    sess = manager.create_session("s2", "Chat", ENDPOINT_URL, "claude-haiku-5.5",
                                  owner="alice", endpoint_id="ep")
    monkeypatch.setattr(settings_mod, "get_setting",
                        lambda key, default=None: "mistral-large-4" if key == "default_model" else default)
    assert chat._recover_empty_session_model(sess, "s2", "alice") is False
    assert sess.model == "claude-haiku-5.5"
