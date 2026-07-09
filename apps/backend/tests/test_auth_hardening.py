"""Tests for the admin-auth hardening pass:
- login rejects a wrong password and accepts the correct bcrypt-hashed one
- create_admin_token / decode_admin_token round-trip; exp reflects the hours arg
- invalid Telegram initData is rejected (ValueError -> 401 in get_current_user)

We monkeypatch the `settings` object the code under test holds (via the
security module) rather than `app.core.config.settings`: another test reloads
the config module, which rebinds that name to a fresh object while the already
imported modules keep the original reference.
"""
import pytest
from fastapi import HTTPException

from app.auth import get_current_user
from app.core import security as security_module
from app.core.security import (
    create_admin_token,
    decode_admin_token,
    get_user_from_init_data,
    hash_password,
)
from app.modules.admin_api.auth.service import AdminAuthService

settings = security_module.settings


async def _aret(v):
    return v


async def test_login_rejects_wrong_and_accepts_hashed_password(monkeypatch):
    monkeypatch.setattr(settings, "admin_jwt_secret", "x" * 32)  # noqa: S106
    monkeypatch.setattr(settings, "admin_default_email", "owner@example.com")
    monkeypatch.setattr(settings, "admin_default_telegram_id", "123")
    monkeypatch.setattr(settings, "admin_default_password_hash", hash_password("secret"))  # noqa: S106
    monkeypatch.setattr(settings, "admin_default_password", "")

    svc = AdminAuthService(db=None)
    admin = type("A", (), {"id": 7})()
    monkeypatch.setattr(svc.repo, "get_by_telegram_id", lambda *_: _aret(admin))

    assert await svc.login("owner@example.com", "wrong") is None  # noqa: S106
    token = await svc.login("owner@example.com", "secret")  # noqa: S106
    assert token and decode_admin_token(token)["sub"] == "7"


def test_admin_token_roundtrip_and_ttl(monkeypatch):
    monkeypatch.setattr(settings, "admin_jwt_secret", "x" * 32)  # noqa: S106
    payload1 = decode_admin_token(create_admin_token(42, hours=1))
    payload2 = decode_admin_token(create_admin_token(42, hours=2))
    assert payload1["sub"] == "42"
    # one extra hour on the second token -> exp ~3600s further out
    assert 3500 < (payload2["exp"] - payload1["exp"]) < 3700


def test_invalid_init_data_raises_value_error():
    with pytest.raises(ValueError):
        get_user_from_init_data("not-valid-init-data")


async def test_get_current_user_401_on_bad_init_data():
    request = type("R", (), {"headers": {"x-telegram-init-data": "not-valid-init-data"}})()
    with pytest.raises(HTTPException) as exc:
        await get_current_user(request=request, credentials=None, db=None)
    assert exc.value.status_code == 401
