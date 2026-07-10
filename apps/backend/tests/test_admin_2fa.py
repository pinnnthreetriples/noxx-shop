"""Admin 2FA (TOTP + backup codes) and JWT revocation via token_version.

Each test uses its own admin_default_telegram_id so the admin rows created by
login don't leak 2FA state between tests (the sqlite test DB is session-wide).
"""
import time
from contextlib import asynccontextmanager

import pyotp
from httpx import ASGITransport, AsyncClient

import app.modules.admin_api.auth.router as auth_router
from app.core.config import settings
from app.main import app

EMAIL = "owner@test.local"
PASSWORD = "test-password"  # noqa: S105 - test-only credential


async def _no_limit(*args, **kwargs):
    return False


def _cfg(monkeypatch, tg_id: int):
    monkeypatch.setattr(settings, "admin_default_email", EMAIL)
    monkeypatch.setattr(settings, "admin_default_password", PASSWORD)
    monkeypatch.setattr(settings, "admin_default_password_hash", "")
    monkeypatch.setattr(settings, "admin_default_telegram_id", str(tg_id))
    # keep the many logins below deterministic if a real redis is running locally
    monkeypatch.setattr(auth_router, "too_many_attempts", _no_limit)


@asynccontextmanager
async def _client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _login(c, **extra):
    return await c.post("/auth/login", json={"email": EMAIL, "password": PASSWORD, **extra})


def _wrong_code(totp: pyotp.TOTP) -> str:
    """A 6-digit code guaranteed outside the valid_window=1 acceptance set."""
    now = time.time()
    valid = {totp.at(now - 30), totp.at(now), totp.at(now + 30)}
    return next(c for c in ("000000", "000001", "000002", "000003") if c not in valid)


async def test_login_without_2fa_still_works(monkeypatch):
    _cfg(monkeypatch, 900001)
    async with _client() as c:
        r = await _login(c)
        assert r.status_code == 200
        me = await c.get("/auth/me", headers={"x-admin-token": r.json()["token"]})
        assert me.status_code == 200


async def test_full_2fa_flow(monkeypatch):
    _cfg(monkeypatch, 900002)
    async with _client() as c:
        token = (await _login(c)).json()["token"]
        h = {"x-admin-token": token}

        assert (await c.get("/auth/2fa/status", headers=h)).json() == {
            "enabled": False,
            "required": False,
        }

        # enable before setup -> 400
        assert (await c.post("/auth/2fa/enable", json={"code": "000000"}, headers=h)).status_code == 400

        setup = (await c.post("/auth/2fa/setup", headers=h)).json()
        totp = pyotp.TOTP(setup["secret"])
        assert setup["otpauth_uri"].startswith("otpauth://totp/")

        bad = await c.post("/auth/2fa/enable", json={"code": _wrong_code(totp)}, headers=h)
        assert bad.status_code == 401
        assert bad.json()["detail"]["code"] == "totp_invalid"

        en = await c.post("/auth/2fa/enable", json={"code": totp.now()}, headers=h)
        assert en.status_code == 200
        backup_codes = en.json()["backup_codes"]
        assert len(backup_codes) == 10
        assert all(len(bc) == 8 for bc in backup_codes)

        # the session that enabled 2FA keeps working (token_version not bumped)
        assert (await c.get("/auth/me", headers=h)).status_code == 200
        assert (await c.get("/auth/2fa/status", headers=h)).json()["enabled"] is True

        # login now requires otp
        r = await _login(c)
        assert r.status_code == 401
        assert r.json()["detail"]["code"] == "totp_required"

        r = await _login(c, otp=_wrong_code(totp))
        assert r.status_code == 401
        assert r.json()["detail"]["code"] == "totp_invalid"

        assert (await _login(c, otp=totp.now())).status_code == 200

        # backup code is one-time
        assert (await _login(c, otp=backup_codes[0])).status_code == 200
        replay = await _login(c, otp=backup_codes[0])
        assert replay.status_code == 401
        assert replay.json()["detail"]["code"] == "totp_invalid"

        # disable accepts totp too, then the old token is revoked
        assert (await c.post("/auth/2fa/disable", json={"code": totp.now()}, headers=h)).status_code == 204
        assert (await c.get("/auth/me", headers=h)).status_code == 401

        # fresh login works again without otp
        assert (await _login(c)).status_code == 200


async def test_disable_accepts_backup_code(monkeypatch):
    _cfg(monkeypatch, 900003)
    async with _client() as c:
        h = {"x-admin-token": (await _login(c)).json()["token"]}
        secret = (await c.post("/auth/2fa/setup", headers=h)).json()["secret"]
        totp = pyotp.TOTP(secret)
        backup_codes = (
            await c.post("/auth/2fa/enable", json={"code": totp.now()}, headers=h)
        ).json()["backup_codes"]

        assert (
            await c.post("/auth/2fa/disable", json={"code": backup_codes[0]}, headers=h)
        ).status_code == 204


async def test_2fa_required_blocks_admin_endpoints_until_setup(monkeypatch):
    _cfg(monkeypatch, 900004)
    async with _client() as c:
        h = {"x-admin-token": (await _login(c)).json()["token"]}
        monkeypatch.setattr(settings, "admin_2fa_required", True)

        for path in ("/auth/me", "/admin/settings"):
            r = await c.get(path, headers=h)
            assert r.status_code == 403, path
            assert r.json()["detail"]["code"] == "totp_setup_required"

        # /auth/2fa/* stays reachable so the admin can actually set 2FA up
        status = await c.get("/auth/2fa/status", headers=h)
        assert status.status_code == 200
        assert status.json() == {"enabled": False, "required": True}
        assert (await c.post("/auth/2fa/setup", headers=h)).status_code == 200
