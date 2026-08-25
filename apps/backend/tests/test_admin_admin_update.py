"""POST/PUT /admin/admins write a whitelist of fields, never the second factor.

react-admin echoes the whole record back on save, so the request body carries
every column the list returned. Before AdminUpdate was wired up the handler did
setattr on anything the model had, which meant a PUT could clear totp_enabled /
totp_secret / backup_codes without an OTP and without bumping token_version --
the owner kept a valid session and simply lost 2FA. /auth/2fa/disable exists for
that and demands a code.
"""
from types import SimpleNamespace

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import delete, or_, select, update

from app.main import app
from app.auth import get_current_admin
from app.modules.admin.models import Admin, AdminRole

# High ids so they can't collide with the admins /auth/login auto-creates.
TARGET_ID = 8501
FAKE_TOTP = "SECRET"  # not a real secret: only ever compared for equality


@pytest_asyncio.fixture
async def client(db_session):
    app.dependency_overrides[get_current_admin] = lambda: SimpleNamespace(id=1, role=AdminRole.owner)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(get_current_admin, None)
    # The sqlite DB is session-wide: don't leave rows behind for other tests.
    await db_session.execute(
        delete(Admin).where(or_(Admin.id >= TARGET_ID, Admin.telegram_id >= 850000))
    )
    await db_session.commit()


async def _admin_with_2fa(db_session, role: str = "owner") -> Admin:
    a = Admin(
        id=TARGET_ID,
        telegram_id=850001,
        name="Owner",
        role=role,
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
    """The react-admin form sends exactly these three; it must keep working.

    Deliberately not an owner: demoting/deactivating the last active owner is
    refused by its own guard, which has nothing to do with the whitelist."""
    await _admin_with_2fa(db_session, role="admin")
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


def _acting_as(role: AdminRole) -> None:
    """Swap the authenticated admin's role. The `client` fixture drops the
    override in teardown."""
    app.dependency_overrides[get_current_admin] = lambda: SimpleNamespace(id=1, role=role)


NON_OWNERS = [AdminRole.admin, AdminRole.support, AdminRole.content_manager]


@pytest.mark.parametrize("role", NON_OWNERS)
async def test_non_owner_cannot_touch_the_admin_roster(client, db_session, role):
    """AdminRole was declared on the model and read nowhere: get_current_admin
    only checks active + token_version. So any admin could POST a new row with
    role=owner and a telegram_id of their choosing -- and telegram_id is what
    the bot trusts to let an account answer support tickets. Straight
    privilege escalation."""
    await _admin_with_2fa(db_session)
    _acting_as(role)

    created = await client.post("/admin/admins", json={
        "telegram_id": 850009, "name": "Mine", "role": "owner", "active": True,
    })
    assert created.status_code == 403, created.text[:200]
    assert created.json()["detail"] == "Owner role required"
    assert (await client.put(f"/admin/admins/{TARGET_ID}", json={"role": "support"})).status_code == 403
    assert (await client.delete(f"/admin/admins/{TARGET_ID}")).status_code == 403

    db_session.expire_all()
    assert (await db_session.execute(
        select(Admin.id).where(Admin.telegram_id == 850009)
    )).first() is None  # no row was created
    target = await db_session.get(Admin, TARGET_ID)
    assert target.role == AdminRole.owner and target.active is True


@pytest.mark.parametrize("role", NON_OWNERS)
async def test_non_owner_can_still_read_the_roster(client, db_session, role):
    """The gate is on writes only: AdminOut already hides the 2FA columns, and
    the react-admin list page is how a non-owner sees who to ask."""
    await _admin_with_2fa(db_session)
    _acting_as(role)

    listed = await client.get("/admin/admins", params={"_start": 0, "_end": 100})
    assert listed.status_code == 200, listed.text[:200]
    assert (await client.get(f"/admin/admins/{TARGET_ID}")).status_code == 200


async def test_owner_still_manages_admins(client, db_session):
    """The `client` fixture authenticates as an owner -- the role every
    bootstrap path assigns (scripts/seed.py, the /auth/login auto-create and
    the model default all say owner), so the gate must not lock them out."""
    created = await client.post("/admin/admins", json={
        "telegram_id": 850010, "name": "Helper", "role": "support", "active": True,
    })
    assert created.status_code == 200, created.text[:200]
    new_id = created.json()["id"]

    assert (await client.put(f"/admin/admins/{new_id}", json={"name": "Renamed"})).status_code == 200
    assert (await client.delete(f"/admin/admins/{new_id}")).status_code == 200

    db_session.expire_all()
    a = await db_session.get(Admin, new_id)
    assert a.name == "Renamed" and a.active is False


async def test_duplicate_telegram_id_is_a_409_and_leaves_the_session_usable(client, db_session):
    """telegram_id is unique and nothing caught the IntegrityError: the flush
    blew up as a 500 and left the request-scoped session poisoned, so every
    later statement on it failed too."""
    await _admin_with_2fa(db_session)  # telegram_id 850001

    dup = await client.post("/admin/admins", json={
        "telegram_id": 850001, "name": "Clone", "role": "admin", "active": True,
    })
    assert dup.status_code == 409, dup.text[:200]
    assert "telegram_id" in dup.json()["detail"]

    # the rollback left the session healthy: the very next write still works
    ok = await client.post("/admin/admins", json={
        "telegram_id": 850011, "name": "Fresh", "role": "admin", "active": True,
    })
    assert ok.status_code == 200, ok.text[:200]


SECOND_OWNER_ID = TARGET_ID + 1


@pytest_asyncio.fixture
async def sole_owner(db_session):
    """Make the admin created by the test the only active owner in the DB.

    The last-owner guard counts every active owner there is, and the sqlite
    test DB is session-wide: other modules' logins leave owner rows behind, so
    without this the guard would find a spare owner and never fire. Park them
    for the duration of the test and hand them back afterwards.
    """
    parked = [
        a.id for a in (await db_session.execute(
            select(Admin).where(Admin.active.is_(True), Admin.role == AdminRole.owner)
        )).scalars().all()
    ]
    await db_session.execute(update(Admin).where(Admin.id.in_(parked)).values(active=False))
    await db_session.commit()
    yield
    await db_session.execute(update(Admin).where(Admin.id.in_(parked)).values(active=True))
    await db_session.commit()


async def test_the_last_owner_cannot_be_deactivated(client, db_session, sole_owner):
    """Roster writes are owner-only, so deactivating the last owner locks the
    roster for good: no endpoint can grant the role back, and the /auth/login
    auto-create only fires when the ADMIN_DEFAULT_TELEGRAM_ID row is missing."""
    await _admin_with_2fa(db_session)

    gone = await client.delete(f"/admin/admins/{TARGET_ID}")
    assert gone.status_code == 409, gone.text[:200]
    assert gone.json()["detail"] == "Cannot remove the last active owner"

    # the same loss through the edit form
    via_form = await client.put(f"/admin/admins/{TARGET_ID}", json={"id": TARGET_ID, "active": False})
    assert via_form.status_code == 409, via_form.text[:200]

    db_session.expire_all()
    assert (await db_session.get(Admin, TARGET_ID)).active is True


async def test_the_last_owner_cannot_be_demoted(client, db_session, sole_owner):
    """The other way to lose the owner: keep the row active, change its role."""
    await _admin_with_2fa(db_session)

    demoted = await client.put(f"/admin/admins/{TARGET_ID}", json={"id": TARGET_ID, "role": "admin"})
    assert demoted.status_code == 409, demoted.text[:200]

    db_session.expire_all()
    assert (await db_session.get(Admin, TARGET_ID)).role == AdminRole.owner

    # harmless edits to the last owner still go through
    renamed = await client.put(f"/admin/admins/{TARGET_ID}", json={"id": TARGET_ID, "name": "Still Owner"})
    assert renamed.status_code == 200, renamed.text[:200]
    db_session.expire_all()
    assert (await db_session.get(Admin, TARGET_ID)).name == "Still Owner"


async def test_owners_cannot_deactivate_each_other_down_to_zero(client, db_session, sole_owner):
    """Why the guard counts owners instead of just refusing self-edits: two
    owners taking turns on each other never touch their own row, and would
    otherwise empty the roster between them."""
    await _admin_with_2fa(db_session)
    db_session.add(Admin(id=SECOND_OWNER_ID, telegram_id=850021, name="Co-owner", role="owner", active=True))
    await db_session.commit()

    # with a spare owner around, either one may step down
    assert (await client.delete(f"/admin/admins/{TARGET_ID}")).status_code == 200
    # the survivor is the last one and stays put
    assert (await client.delete(f"/admin/admins/{SECOND_OWNER_ID}")).status_code == 409
    # ...and cannot be demoted out of the role either
    assert (await client.put(
        f"/admin/admins/{SECOND_OWNER_ID}", json={"id": SECOND_OWNER_ID, "role": "support"}
    )).status_code == 409

    db_session.expire_all()
    survivor = await db_session.get(Admin, SECOND_OWNER_ID)
    assert survivor.active is True and survivor.role == AdminRole.owner


async def test_the_guard_does_not_block_non_owners(client, db_session, sole_owner):
    """A support admin is not an owner, so nothing about them is protected -
    the guard must not turn into a blanket freeze on the roster."""
    await _admin_with_2fa(db_session)
    db_session.add(Admin(id=SECOND_OWNER_ID, telegram_id=850022, name="Helper", role="support", active=True))
    await db_session.commit()

    assert (await client.put(
        f"/admin/admins/{SECOND_OWNER_ID}", json={"id": SECOND_OWNER_ID, "role": "content_manager"}
    )).status_code == 200
    assert (await client.delete(f"/admin/admins/{SECOND_OWNER_ID}")).status_code == 200
