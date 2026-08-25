"""Promo codes: what the admin form may write, and what a buyer may type.

The two /admin/promo_codes writers took a raw dict, so react-admin (which echoes
the whole record back on save) could rewrite used_count, and a typo in
discount_type produced a promo that silently never discounted anything. The
window bounds arrived as bare "YYYY-MM-DD" from the form and were read as
midnight UTC, so a code "valid until 1 September" was already dead on the 1st.
And a code redeemed by any order could not be deleted at all - the FK blew up as
a 500 with no explanation.
"""
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import delete, select

from app.main import app
from app.auth import get_current_admin
from app.modules.orders.models import Order
from app.modules.promos.models import PromoCode
from app.modules.promos.repository import PromoCodeRepository
from app.modules.users.models import User

# High ids: the sqlite DB is shared by the whole session.
BASE_ID = 9100
USER_ID = 9800


@pytest_asyncio.fixture
async def client(db_session):
    app.dependency_overrides[get_current_admin] = lambda: SimpleNamespace(id=1)
    if not await db_session.get(User, USER_ID):
        db_session.add(User(id=USER_ID, telegram_id=980000))
        await db_session.commit()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(get_current_admin, None)
    await db_session.execute(delete(Order).where(Order.user_id == USER_ID))
    await db_session.execute(delete(PromoCode).where(PromoCode.id >= BASE_ID))
    await db_session.execute(delete(PromoCode).where(PromoCode.code.like("TEST9%")))
    await db_session.commit()


async def _promo(db_session, id: int, **fields) -> PromoCode:
    pc = PromoCode(id=id, code=f"TEST9{id}", discount_type="percentage", discount_value=10, **fields)
    db_session.add(pc)
    await db_session.commit()
    return pc


def _utc(value: datetime) -> datetime:
    """sqlite drops the offset on read; postgres timestamptz keeps it."""
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


async def test_create_ignores_fields_outside_the_schema(client, db_session):
    resp = await client.post("/admin/promo_codes", json={
        "code": "TEST9CREATE", "discount_type": "percentage", "discount_value": 15,
        "used_count": 99, "id": BASE_ID + 1,
    })
    assert resp.status_code == 200, resp.text[:300]

    pc = (await db_session.execute(
        select(PromoCode).where(PromoCode.code == "TEST9CREATE")
    )).scalars().one()
    assert pc.used_count == 0  # the counter checkout owns, not a form field
    assert pc.discount_value == 15


async def test_put_cannot_rewrite_used_count(client, db_session):
    await _promo(db_session, BASE_ID + 2, used_count=5, usage_limit=10)
    resp = await client.put(f"/admin/promo_codes/{BASE_ID + 2}", json={
        "id": BASE_ID + 2, "code": f"TEST9{BASE_ID + 2}", "discount_type": "percentage",
        "discount_value": 20, "active": True, "usage_limit": 10, "used_count": 0,
    })
    assert resp.status_code == 200, resp.text[:300]

    db_session.expire_all()
    pc = await db_session.get(PromoCode, BASE_ID + 2)
    assert pc.used_count == 5  # zeroing it would resurrect an exhausted code
    assert pc.discount_value == 20  # the form's own fields still save


async def test_put_can_still_clear_the_nullable_window(client, db_session):
    await _promo(db_session, BASE_ID + 3, expires_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
    resp = await client.put(f"/admin/promo_codes/{BASE_ID + 3}", json={
        "id": BASE_ID + 3, "expires_at": None, "usage_limit": None,
    })
    assert resp.status_code == 200, resp.text[:300]

    db_session.expire_all()
    pc = await db_session.get(PromoCode, BASE_ID + 3)
    assert pc.expires_at is None
    assert pc.code == f"TEST9{BASE_ID + 3}"  # an explicit null on a NOT NULL column is dropped


async def test_create_rejects_an_unsupported_discount_type(client, db_session):
    for bad in ("percent", "fixed", "PERCENTAGE"):
        resp = await client.post("/admin/promo_codes", json={
            "code": f"TEST9{bad}", "discount_type": bad, "discount_value": 10,
        })
        assert resp.status_code == 422, f"{bad}: {resp.text[:300]}"

    assert (await db_session.execute(
        select(PromoCode).where(PromoCode.code.like("TEST9%"))
    )).scalars().all() == []


async def test_put_rejects_an_unsupported_discount_type(client, db_session):
    await _promo(db_session, BASE_ID + 4)
    resp = await client.put(f"/admin/promo_codes/{BASE_ID + 4}", json={
        "id": BASE_ID + 4, "discount_type": "fixed", "discount_value": 300,
    })
    assert resp.status_code == 422, resp.text[:300]

    db_session.expire_all()
    pc = await db_session.get(PromoCode, BASE_ID + 4)
    assert pc.discount_type == "percentage" and pc.discount_value == 10


async def test_lookup_ignores_case_and_surrounding_spaces(client, db_session):
    await _promo(db_session, BASE_ID + 5)
    stored = f"TEST9{BASE_ID + 5}"
    repo = PromoCodeRepository(db_session)

    for typed in (stored, stored.lower(), stored.upper(), f"  {stored.lower()}  "):
        found = await repo.get_by_code(typed)
        assert found is not None and found.id == BASE_ID + 5, typed
    assert await repo.get_by_code("TEST9nope") is None


async def test_a_date_only_window_covers_the_whole_last_day(client, db_session):
    resp = await client.post("/admin/promo_codes", json={
        "code": "TEST9WINDOW", "discount_type": "percentage", "discount_value": 10,
        "starts_at": "2026-08-01", "expires_at": "2026-09-01",
    })
    assert resp.status_code == 200, resp.text[:300]

    pc = (await db_session.execute(
        select(PromoCode).where(PromoCode.code == "TEST9WINDOW")
    )).scalars().one()
    starts_at, expires_at = _utc(pc.starts_at), _utc(pc.expires_at)

    # The promo opens at the very start of 1 August...
    assert starts_at == datetime(2026, 8, 1, 0, 0, tzinfo=timezone.utc)
    # ...and is still live at the last minute of 1 September, dead on the 2nd.
    assert expires_at > datetime(2026, 9, 1, 23, 59, tzinfo=timezone.utc)
    assert expires_at < datetime(2026, 9, 2, 0, 0, tzinfo=timezone.utc)


async def test_a_timestamp_window_keeps_its_own_time(client, db_session):
    resp = await client.post("/admin/promo_codes", json={
        "code": "TEST9EXACT", "discount_type": "percentage", "discount_value": 10,
        "expires_at": "2026-09-01T10:30:00Z",
    })
    assert resp.status_code == 200, resp.text[:300]

    pc = (await db_session.execute(
        select(PromoCode).where(PromoCode.code == "TEST9EXACT")
    )).scalars().one()
    assert _utc(pc.expires_at) == datetime(2026, 9, 1, 10, 30, tzinfo=timezone.utc)


async def test_delete_refuses_a_promo_used_in_an_order(client, db_session):
    await _promo(db_session, BASE_ID + 6, used_count=1)
    db_session.add(Order(id=BASE_ID + 6, user_id=USER_ID, status="paid", promo_code_id=BASE_ID + 6))
    await db_session.commit()

    resp = await client.delete(f"/admin/promo_codes/{BASE_ID + 6}")
    assert resp.status_code == 409, resp.text[:300]
    assert "order" in resp.json()["detail"].lower()

    assert await db_session.get(PromoCode, BASE_ID + 6) is not None


async def test_delete_of_an_unused_promo_still_works(client, db_session):
    await _promo(db_session, BASE_ID + 7)
    resp = await client.delete(f"/admin/promo_codes/{BASE_ID + 7}")
    assert resp.status_code == 200, resp.text[:300]

    db_session.expire_all()
    assert await db_session.get(PromoCode, BASE_ID + 7) is None
