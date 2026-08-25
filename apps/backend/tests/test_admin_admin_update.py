"""POST/PUT /admin/admins write a whitelist of fields, never the second factor.

react-admin echoes the whole record back on save, so the request body carries
every column the list returned. Before AdminUpdate was wired up the handler did
setattr on anything the model had, which meant a PUT could clear totp_enabled /
totp_secret / backup_codes without an OTP and without bumping token_version --
the owner kept a valid session and simply lost 2FA. /auth/2fa/disable exists for
that and demands a code.
"""
from types import SimpleNamespace

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import delete, or_

from app.main import app
from app.auth import get_current_admin
from app.modules.admin.models import Admin

# High ids so they can't collide with the admins /auth/login auto-creates.
TARGET_ID = 8501
FAKE_TOTP = "SECRET"  # not a real secret: only ever compared for equality


@pytest_asyncio.fixture
async def client(db_session):
    app.dependency_overrides[get_current_admin] = lambda: SimpleNamespace(id=1)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(get_current_admin, None)
    # The sqlite DB is session-wide: don't leave rows behind for other tests.
    await db_session.execute(
        delete(Admin).where(or_(Admin.id >= TARGET_ID, Admin.telegram_id >= 850000))
    )
    await db_session.commit()


async def _admin_with_2fa(db_session) -> Admin:
    a = Admin(
        id=TARGET_ID,
        telegram_id=850001,
        name="Owner",
        role="owner",
        active=True,
        totp_enabled=True,
        totp_secret=FAKE_TOTP,
        backup_codes='["hash"]',
        token_version=3,
    )
    db_session.add(a)
    await db_session.commit()
    return a


async def test_put_cannot_strip_the_second_factor(client, db_session):
    await _admin_with_2fa(db_session)
    resp = await client.put(f"/admin/admins/{TARGET_ID}", json={
        "id": TARGET_ID, "name": "Owner", "role": "owner", "active": True,
        "totp_enabled": False, "totp_secret": None,
        "totp_pending_secret": None, "backup_codes": None,
    })
    assert resp.status_code == 200, resp.text[:200]

    db_session.expire_all()
    a = await db_session.get(Admin, TARGET_ID)
    assert a.totp_enabled is True
    assert a.totp_secret == FAKE_TOTP
    assert a.backup_codes == '["hash"]'


async def test_put_cannot_rewrite_token_version_or_telegram_id(client, db_session):
    await _admin_with_2fa(db_session)
    resp = await client.put(f"/admin/admins/{TARGET_ID}", json={
        "id": TARGET_ID, "name": "Owner", "role": "owner", "active": True,
        "token_version": 0, "telegram_id": 111222,
    })
    assert resp.status_code == 200, resp.text[:200]

    db_session.expire_all()
    a = await db_session.get(Admin, TARGET_ID)
    assert a.token_version == 3  # a rolled-back version would resurrect old JWTs
    assert a.telegram_id == 850001  # the identity the bot trusts in support tickets


async def test_put_still_edits_name_role_and_active(client, db_session):
    """The react-admin form sends exactly these three; it must keep working."""
    await _admin_with_2fa(db_session)
    resp = await client.put(f"/admin/admins/{TARGET_ID}", json={
        "id": TARGET_ID, "telegram_id": 850001, "name": "Renamed",
        "role": "support", "active": False, "created_at": "2026-01-01T00:00:00",
    })
    assert resp.status_code == 200, resp.text[:200]

    db_session.expire_all()
    a = await db_session.get(Admin, TARGET_ID)
    assert a.name == "Renamed"
    assert a.role.value == "support"
    assert a.active is False


async def test_put_rejects_a_role_outside_the_enum(client, db_session):
    await _admin_with_2fa(db_session)
    resp = await client.put(f"/admin/admins/{TARGET_ID}", json={"id": TARGET_ID, "role": "superuser"})
    assert resp.status_code == 422, resp.text[:200]

    db_session.expire_all()
    assert (await db_session.get(Admin, TARGET_ID)).role.value == "owner"


async def test_create_ignores_second_factor_fields(client, db_session):
    resp = await client.post("/admin/admins", json={
        "telegram_id": 850002, "name": "New", "role": "support", "active": True,
        "totp_enabled": True, "totp_secret": "PLANTED",
        "backup_codes": '["planted"]', "token_version": 99,
    })
    assert resp.status_code == 200, resp.text[:200]

    db_session.expire_all()
    a = await db_session.get(Admin, resp.json()["id"])
    assert a.telegram_id == 850002 and a.role.value == "support"
    assert a.totp_enabled is False
    assert a.totp_secret is None and a.backup_codes is None
    assert a.token_version == 0


async def test_admin_responses_never_carry_the_2fa_columns(client, db_session):
    """The routes used to serialize the raw ORM row, so a plain GET handed every
    admin the owner's totp_secret (plaintext unless ADMIN_TOTP_ENC_KEY is set),
    the pending secret and the backup-code hashes."""
    await _admin_with_2fa(db_session)
    leaky = {"totp_secret", "totp_pending_secret", "backup_codes", "totp_enabled", "token_version"}

    listed = await client.get("/admin/admins", params={"_sort": "id", "_order": "ASC", "_start": 0, "_end": 100})
    assert listed.status_code == 200, listed.text[:200]
    row = next(r for r in listed.json()["data"] if r["id"] == TARGET_ID)
    assert leaky.isdisjoint(row)
    assert row["telegram_id"] == 850001 and row["role"] == "owner"  # the form's fields survive

    got = await client.get(f"/admin/admins/{TARGET_ID}")
    assert leaky.isdisjoint(got.json())

    saved = await client.put(f"/admin/admins/{TARGET_ID}", json={"id": TARGET_ID, "name": "Renamed"})
    assert leaky.isdisjoint(saved.json())
    assert saved.json()["name"] == "Renamed"
