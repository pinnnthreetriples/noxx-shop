"""DB_AUTO_SCHEMA flag: lifespan should only run create_all/_add_missing_columns
when the flag is on, so a deploy with DDL rights revoked (after `alembic upgrade
head` + the least-privilege role) does no runtime DDL at all."""
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.main import app, lifespan


async def _table_count(conn):
    result = await conn.execute(text("select count(*) from sqlite_master where type='table'"))
    return result.scalar()


async def test_lifespan_creates_schema_when_auto_schema_enabled(monkeypatch):
    monkeypatch.setattr(settings, "db_auto_schema", True)
    async with lifespan(app):
        async with engine.connect() as conn:
            count = await _table_count(conn)
    assert count > 0


async def test_lifespan_skips_ddl_when_auto_schema_disabled(monkeypatch):
    monkeypatch.setattr(settings, "db_auto_schema", False)
    async with lifespan(app):
        async with engine.connect() as conn:
            count = await _table_count(conn)
    assert count == 0
