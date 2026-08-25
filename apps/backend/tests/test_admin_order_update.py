"""PUT /admin/orders/{id} is a status-only endpoint.

react-admin echoes the whole record back on save, so the request body always
carries the money columns; they must be dropped, "paid" must not be reachable
by hand, and the real change must land in admin_logs.
"""
import json
from types import SimpleNamespace

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.auth import get_current_admin
from app.modules.admin.models import AdminLog
from app.modules.orders.models import Order
from app.modules.users.models import User


@pytest_asyncio.fixture
async def client(db_session):
    app.dependency_overrides[get_current_admin] = lambda: SimpleNamespace(id=1)
    if not await db_session.get(User, 800):
        db_session.add(User(id=800, telegram_id=8000))
    await db_session.commit()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(get_current_admin, None)


async def _order(db_session, id: int, status: str) -> Order:
    order = Order(id=id, user_id=800, status=status, total_stars=500, paid_stars=500 if status == "paid" else 0)
    db_session.add(order)
    await db_session.commit()
    return order


async def test_put_ignores_fields_outside_the_status_whitelist(client, db_session):
    await _order(db_session, 810, "pending")
    resp = await client.put("/admin/orders/810", json={
        "id": 810, "status": "cancelled", "paid_stars": 999999,
        "total_stars": 1, "user_id": 1, "promo_code_id": 7,
    })
    assert resp.status_code == 200, resp.text[:200]

    db_session.expire_all()
    order = await db_session.get(Order, 810)
    assert order.status == "cancelled"
    assert order.paid_stars == 0 and order.total_stars == 500
    assert order.user_id == 800 and order.promo_code_id is None


async def test_put_rejects_manual_transition_to_paid(client, db_session):
    await _order(db_session, 811, "pending")
    resp = await client.put("/admin/orders/811", json={"id": 811, "status": "paid"})
    assert resp.status_code == 400, resp.text[:200]
    assert "payment" in resp.json()["detail"]

    db_session.expire_all()
    assert (await db_session.get(Order, 811)).status == "pending"


async def test_put_on_an_already_paid_order_is_a_no_op(client, db_session):
    await _order(db_session, 812, "paid")
    resp = await client.put("/admin/orders/812", json={"id": 812, "status": "paid"})
    assert resp.status_code == 200, resp.text[:200]

    db_session.expire_all()
    assert (await db_session.get(Order, 812)).status == "paid"
    logs = (await db_session.execute(
        select(AdminLog).where(AdminLog.entity_type == "order", AdminLog.entity_id == 812)
    )).scalars().all()
    assert logs == []  # nothing changed -> nothing to audit


async def test_status_change_is_audited_with_the_changed_field_only(client, db_session):
    await _order(db_session, 813, "pending")
    resp = await client.put("/admin/orders/813", json={"id": 813, "status": "failed", "paid_stars": 42})
    assert resp.status_code == 200, resp.text[:200]

    log = (await db_session.execute(
        select(AdminLog).where(AdminLog.entity_type == "order", AdminLog.entity_id == 813)
    )).scalars().one()
    assert log.action == "update_order" and log.admin_id == 1
    assert json.loads(log.before_data) == {"status": "pending"}
    assert json.loads(log.after_data) == {"status": "failed"}


async def test_list_and_put_expose_the_nested_buyer(client, db_session):
    await _order(db_session, 814, "pending")
    listed = await client.get("/admin/orders", params={"_sort": "id", "_order": "ASC", "_start": 0, "_end": 25})
    assert listed.status_code == 200, listed.text[:200]
    row = next(r for r in listed.json()["data"] if r["id"] == 814)
    assert row["user"]["telegram_id"] == 8000

    saved = await client.put("/admin/orders/814", json={"id": 814, "status": "cancelled"})
    assert saved.status_code == 200, saved.text[:200]
    assert saved.json()["user"]["telegram_id"] == 8000


async def test_put_rejects_a_status_outside_the_enum(client, db_session):
    """An unknown status used to reach the DB and fail on bind as a 500."""
    await _order(db_session, 815, "pending")
    resp = await client.put("/admin/orders/815", json={"id": 815, "status": "shipped"})
    assert resp.status_code == 422, resp.text[:200]

    db_session.expire_all()
    assert (await db_session.get(Order, 815)).status == "pending"


async def test_put_drops_an_explicit_null_status(client, db_session):
    """status is NOT NULL; an explicit null must be dropped, not written."""
    await _order(db_session, 816, "pending")
    resp = await client.put("/admin/orders/816", json={"id": 816, "status": None})
    assert resp.status_code == 200, resp.text[:200]

    db_session.expire_all()
    assert (await db_session.get(Order, 816)).status == "pending"
