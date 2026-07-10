"""/health must actually ping the DB (a duplicate route in the settings router
used to shadow it and always answer 200, defeating uptime monitoring)."""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

import app.main as main_module


async def _get_health():
    transport = ASGITransport(app=main_module.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get("/health")


@pytest.mark.asyncio
async def test_health_ok_when_db_answers(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    monkeypatch.setattr(main_module, "engine", engine)
    monkeypatch.setattr(main_module, "_health_ok_until", 0.0)
    try:
        resp = await _get_health()
    finally:
        # An undisposed aiosqlite engine leaves a non-daemon connection
        # thread behind that blocks pytest from ever exiting.
        await engine.dispose()
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_503_when_db_down(monkeypatch):
    class DeadEngine:
        def connect(self):
            raise RuntimeError("db down")

    monkeypatch.setattr(main_module, "engine", DeadEngine())
    monkeypatch.setattr(main_module, "_health_ok_until", 0.0)
    resp = await _get_health()
    assert resp.status_code == 503
    assert resp.json() == {"status": "db_unavailable"}
