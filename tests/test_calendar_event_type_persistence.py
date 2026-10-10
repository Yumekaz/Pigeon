from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tests.helpers.import_state import clear_fake_database_modules

clear_fake_database_modules()
import core.database as cdb
import routes.calendar_routes as calendar


@pytest.fixture
def routes(tmp_path, monkeypatch):
    engine = create_engine(f'sqlite:///{tmp_path / "calendar.db"}')
    cdb.Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(calendar, 'SessionLocal', factory)
    router = calendar.setup_calendar_routes()
    def endpoint(method, suffix):
        return next(route.endpoint for route in router.routes
                    if method in route.methods and route.path.endswith(suffix))
    yield endpoint
    engine.dispose()


async def test_event_category_create_update_omit_and_clear(routes):
    request = SimpleNamespace(state=SimpleNamespace(current_user='qa-calendar'))
    created = await routes('POST', '/events')(request, calendar.EventCreate(
        summary='Category regression', dtstart='2027-01-10T10:00:00', event_type='work'))
    uid = created['uid']
    assert created['event']['event_type'] == 'work'
    update = routes('PUT', '/events/{uid}')
    read = routes('GET', '/events/{uid}')
    await update(request, uid, calendar.EventUpdate(event_type='personal'))
    assert (await read(request, uid))['event']['event_type'] == 'personal'
    await update(request, uid, calendar.EventUpdate(summary='Retain category'))
    assert (await read(request, uid))['event']['event_type'] == 'personal'
    await update(request, uid, calendar.EventUpdate(event_type=''))
    assert (await read(request, uid))['event']['event_type'] is None
    foreign = SimpleNamespace(state=SimpleNamespace(current_user='other-owner'))
    with pytest.raises(HTTPException):
        await update(foreign, uid, calendar.EventUpdate(event_type='work'))
