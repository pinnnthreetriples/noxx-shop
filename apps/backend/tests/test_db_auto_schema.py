"""DB_AUTO_SCHEMA flag: lifespan should only run create_all/_add_missing_columns
when the flag is on, so a deploy with DDL rights revoked (after `alembic upgrade
head` + the least-privilege role) does no runtime DDL at all."""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

import app.main as app_main
from app.core.config import settings
from app.main import app, lifespan


async def _table_count(engine):
    async with engine.connect() as conn:
        result = await conn.execute(text("select count(*) from sqlite_master where type='table'"))
        return result.scalar()


def _test_engine(monkeypatch):
    # Own in-memory engine, independent of DATABASE_URL (CI has no live DB).
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    monkeypatch.setattr(app_main, "engine", engine)
    return engine


async def test_lifespan_creates_schema_when_auto_schema_enabled(monkeypatch):
    engine = _test_engine(monkeypatch)
    monkeypatch.setattr(settings, "db_auto_schema", True)
    async with lifespan(app):
        count = await _table_count(engine)
    assert count > 0


async def test_lifespan_skips_ddl_when_auto_schema_disabled(monkeypatch):
    engine = _test_engine(monkeypatch)
    monkeypatch.setattr(settings, "db_auto_schema", False)
    async with lifespan(app):
        count = await _table_count(engine)
    assert count == 0
