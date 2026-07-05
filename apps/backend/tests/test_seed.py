"""Tests for the seed script's create_default_admin function.

Regression test for: `make seed` was documented in README but the script
either didn't exist or was broken. We extract `create_default_admin(session)`
as a separately importable function so unit tests can verify admin-creation
without spinning up the whole seed pipeline.
"""
import pytest
from sqlalchemy import select
from importlib import reload
from types import SimpleNamespace


@pytest.mark.asyncio
async def test_create_default_admin_creates_when_missing(db_session, monkeypatch):
    """create_default_admin creates an Admin row from env vars when none exists."""
    monkeypatch.setenv("ADMIN_DEFAULT_TELEGRAM_ID", "123456789")
    monkeypatch.setenv("ADMIN_DEFAULT_EMAIL", "owner@example.com")
    monkeypatch.setenv("ADMIN_DEFAULT_PASSWORD", "secret123")
    # Reload settings to pick up the new env values (pydantic_settings caches).
    from app.core import config as config_module
    reload(config_module)
    from scripts.seed import create_default_admin

    admin = await create_default_admin(db_session)

    assert admin is not None
    assert admin.telegram_id == 123456789
    assert admin.role.value == "owner"
    # Verify it's actually persisted in the DB
    from app.modules.admin.models import Admin
    result = await db_session.execute(select(Admin).where(Admin.telegram_id == 123456789))
    assert result.scalars().first() is not None


@pytest.mark.asyncio
async def test_create_default_admin_idempotent(db_session, monkeypatch):
    """Running seed twice does not create duplicates — same Admin row returned."""
    monkeypatch.setenv("ADMIN_DEFAULT_TELEGRAM_ID", "999111222")
    monkeypatch.setenv("ADMIN_DEFAULT_EMAIL", "owner@example.com")
    monkeypatch.setenv("ADMIN_DEFAULT_PASSWORD", "secret123")
    from app.core import config as config_module
    reload(config_module)
    from scripts.seed import create_default_admin

    first = await create_default_admin(db_session)
    second = await create_default_admin(db_session)

    assert first.id == second.id, "Idempotent: second call must return same admin row"


@pytest.mark.asyncio
async def test_create_default_admin_no_telegram_id_returns_none(db_session, monkeypatch):
    """Without ADMIN_DEFAULT_TELEGRAM_ID, create_default_admin returns None.

    Bypasses pydantic_settings entirely by replacing the `settings` attribute
    on the seed module with a SimpleNamespace. pydantic v2 makes model fields
    immutable by default, so we can't `monkeypatch.setattr(settings, ...)` —
    instead we swap the whole object the seed module sees.
    """
    from scripts import seed as seed_module

    fake_settings = SimpleNamespace(
        admin_default_telegram_id="",
        admin_default_email="",
        admin_default_password="",
    )
    monkeypatch.setattr(seed_module, "settings", fake_settings)

    admin = await seed_module.create_default_admin(db_session)
    assert admin is None
