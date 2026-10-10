import asyncio

import pytest


async def test_manual_run_keeps_serial_slot_and_survives_ui_activity(monkeypatch):
    import core.database as database
    from src.task_scheduler import TaskScheduler, _TASK_FOREGROUND

    class Database:
        def add(self, row): pass
        def commit(self): pass
        def close(self): pass

    monkeypatch.setattr(database, 'SessionLocal', Database)
    scheduler = TaskScheduler(None)
    scheduler._task_needs_model_slot = lambda task_id: True
    scheduler._mark_run_aborted = lambda *args: True
    scheduler._defer_immediately_due_task = lambda *args, **kwargs: None
    started = {'automatic': asyncio.Event(), 'manual': asyncio.Event()}
    release = asyncio.Event()
    gates = {}

    async def execute(task_id, run_id, *, release_executing, gate_foreground):
        assert _TASK_FOREGROUND.get() is (task_id == 'manual')
        gates[task_id] = gate_foreground
        started[task_id].set()
        await release.wait()

    monkeypatch.setattr(scheduler, '_execute_task_locked', execute)
    assert await scheduler.run_task_now('automatic')
    await asyncio.wait_for(started['automatic'].wait(), 2)
    assert await scheduler.run_task_now('manual', foreground=True)
    await asyncio.sleep(0)
    assert not started['manual'].is_set(), 'manual run bypassed the serial slot'
    automatic = scheduler._task_handles['automatic']
    manual = scheduler._task_handles['manual']
    await scheduler.stop_background_tasks_for_foreground(reason='UI polling')
    with pytest.raises(asyncio.CancelledError):
        await automatic
    await asyncio.wait_for(started['manual'].wait(), 2)
    assert gates == {'automatic': True, 'manual': False}
    assert not manual.cancelling()
    assert await scheduler.stop_background_tasks_for_foreground(reason='open activity') == 0
    release.set()
    await asyncio.wait_for(manual, 2)
    assert not scheduler._foreground_tasks
    assert not scheduler._executing
    assert _TASK_FOREGROUND.get() is False
