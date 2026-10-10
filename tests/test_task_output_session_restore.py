from types import SimpleNamespace

import pytest

from core.session_manager import SessionManager


def test_task_output_restores_persisted_session_before_creating():
    manager = SessionManager.__new__(SessionManager)
    manager.sessions = {}
    restored = SimpleNamespace(owner='qa')
    loaded = []
    manager.get_session = lambda sid: (loaded.append(sid) or restored)
    def duplicate(*args, **kwargs):
        raise AssertionError('attempted a duplicate insert')
    manager.create_session = duplicate
    assert manager.ensure_task_session('persisted', 'Task', 'http://fixture', 'fixture', owner='qa') is restored
    assert loaded == ['persisted']
    with pytest.raises(PermissionError):
        manager.ensure_task_session('persisted', 'Task', 'http://fixture', 'fixture', owner='other')


def test_missing_task_output_is_created_with_its_owner():
    manager = SessionManager.__new__(SessionManager)
    def missing(sid): raise KeyError(sid)
    manager.get_session = missing
    created = []
    manager.create_session = lambda *args, **kwargs: (created.append((args, kwargs)) or SimpleNamespace(owner='qa'))
    result = manager.ensure_task_session('new', 'Task', 'http://fixture', 'fixture', owner='qa')
    assert result.owner == 'qa'
    assert created[0][1]['owner'] == 'qa'
