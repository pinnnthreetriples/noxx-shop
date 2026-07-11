"""Premium subscription lifecycle: checkout pricing + pending-order re-use,
fulfillment extending user.premium_until (first buy / active stack / expired
restart), charge-id idempotency, the lost-race branch, the underpayment guard,
premium claims, and the /profile is_premium boundary.

No external I/O: empty provider creds make _invoice_for_order fall back to the
locally-built t.me URL (no OrbChain/Telegram HTTP), and the redis delivery
queue is stubbed out.
"""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import delete, select, text

from app.core.config import settings
from app.modules.admin.models import Setting
from app.modules.catalog.models import Product
from app.modules.orders.models import Order, OrderStatus, Payment
from app.modules.orders.service import OrderService
from app.modules.users.models import User


@pytest.fixture
def svc(db_session, monkeypatch):
    monkeypatch.setattr(settings, "orbchain_api_key", "")
    monkeypatch.setattr(settings, "bot_token", "")
    monkeypatch.setattr(settings, "star_usd_rate", 0.02)

    async def _no_enqueue(self, order_id):
        return None

    monkeypatch.setattr(OrderService, "_enqueue_delivery", _no_enqueue)
    return OrderService(db_session)


async def _make_user(db, telegram_id: int) -> User:
    user = User(telegram_id=telegram_id)
    db.add(user)
    await db.commit()
    return user


async def _reset_settings(db, **fields) -> None:
    """Pin the singleton Setting row (the shared test DB persists across test
    files): drop it entirely, or recreate it with explicit overrides."""
    await db.execute(delete(Setting))
    if fields:
        db.add(Setting(id=1, **fields))
    await db.commit()


async def _seed_premium(db, user_id: int, dt: datetime) -> None:
    """Store premium_until as an ISO string WITH the +00:00 offset. SQLAlchemy's
    SQLite DATETIME drops tzinfo when binding a datetime object, and fulfill()
    would then compare a naive DB value against aware now(). The raw string
    parses back timezone-aware, reproducing Postgres timezone=True behavior."""
    await db.execute(
        text("UPDATE users SET premium_until = :v WHERE id = :i"),
        {"v": dt.isoformat(sep=" "), "i": user_id},
    )
    await db.commit()


async def _fulfill(svc, order_id: int, charge: str, paid_usd=None):
    return await svc.fulfill(
        invoice_payload=str(order_id),
        telegram_payment_charge_id=charge,
        provider_payment_charge_id=charge.removeprefix("orb:"),
        total_amount=0,
        paid_usd=paid_usd,
    )


async def _payments(db, order_id: int) -> list:
    result = await db.execute(select(Payment).where(Payment.order_id == order_id))
    return list(result.scalars().all())


def _close(a: datetime, b: datetime, seconds: int = 5) -> bool:
    return abs((a - b).total_seconds()) <= seconds


# ----- Checkout: pricing -----


async def test_checkout_prices_fall_back_to_defaults(svc, db_session):
    await _reset_settings(db_session)  # no Setting row -> hardcoded defaults
    user = await _make_user(db_session, 8880001)
    for plan, stars in {"week": 99, "month": 299, "year": 2499}.items():
        out = await svc.create_subscription_checkout(user, plan)
        order = await db_session.get(Order, out.order_id)
        assert order.paid_stars == stars
        assert order.subscription_plan == plan
        # no provider creds -> locally-built Stars fallback link, no HTTP
        assert out.provider == "telegram"
        assert out.invoice_url.startswith("https://t.me/")


async def test_checkout_price_comes_from_settings(svc, db_session):
    await _reset_settings(db_session, sub_price_month_stars=555)
    user = await _make_user(db_session, 8880002)
    out = await svc.create_subscription_checkout(user, "month")
    assert (await db_session.get(Order, out.order_id)).paid_stars == 555


async def test_checkout_unknown_plan_rejected(svc):
    with pytest.raises(ValueError):
        await svc.create_subscription_checkout(SimpleNamespace(id=1), "decade")


# ----- Checkout: pending-order re-use (double-tap guard) -----


async def test_checkout_reuses_pending_order_for_same_plan(svc, db_session):
    await _reset_settings(db_session)
    user = await _make_user(db_session, 8880003)
    first = await svc.create_subscription_checkout(user, "month")
    second = await svc.create_subscription_checkout(user, "month")
    assert second.order_id == first.order_id  # no pending duplicates
    other = await svc.create_subscription_checkout(user, "year")
    assert other.order_id != first.order_id  # different plan -> new order


async def test_checkout_price_change_makes_new_order(svc, db_session):
    await _reset_settings(db_session)
    user = await _make_user(db_session, 8880004)
    first = await svc.create_subscription_checkout(user, "month")  # 299
    await _reset_settings(db_session, sub_price_month_stars=599)
    second = await svc.create_subscription_checkout(user, "month")
    assert second.order_id != first.order_id


# ----- Fulfillment: premium_until extension -----


async def test_fulfill_first_subscription_sets_premium(svc, db_session):
    await _reset_settings(db_session)
    user = await _make_user(db_session, 8880005)
    out = await svc.create_subscription_checkout(user, "week")
    before = datetime.now(timezone.utc)

    res = await _fulfill(svc, out.order_id, "orb:sub-first")

    assert res["ok"] is True
    assert "Premium activated" in res["message_text"]
    assert _close(user.premium_until, before + timedelta(days=7))
    order = await db_session.get(Order, out.order_id)
    await db_session.refresh(order)  # set_status_paid is a Core UPDATE; ORM copy is stale
    assert order.status == OrderStatus.paid
    payments = await _payments(db_session, out.order_id)
    assert len(payments) == 1
    assert payments[0].telegram_payment_charge_id == "orb:sub-first"


async def test_fulfill_extends_active_premium(svc, db_session):
    await _reset_settings(db_session)
    user = await _make_user(db_session, 8880006)
    active_until = datetime.now(timezone.utc) + timedelta(days=5)
    await _seed_premium(db_session, user.id, active_until)
    out = await svc.create_subscription_checkout(user, "month")

    res = await _fulfill(svc, out.order_id, "orb:sub-extend")

    assert res["ok"] is True
    # stacked on the remaining time, not restarted from now
    assert _close(user.premium_until, active_until + timedelta(days=30))


async def test_fulfill_restarts_expired_premium_from_now(svc, db_session):
    await _reset_settings(db_session)
    user = await _make_user(db_session, 8880007)
    await _seed_premium(db_session, user.id, datetime.now(timezone.utc) - timedelta(days=3))
    out = await svc.create_subscription_checkout(user, "month")
    before = datetime.now(timezone.utc)

    res = await _fulfill(svc, out.order_id, "orb:sub-expired")

    assert res["ok"] is True
    assert _close(user.premium_until, before + timedelta(days=30))


# ----- Fulfillment: idempotency and the lost race -----


async def test_fulfill_idempotent_for_same_charge_id(svc, db_session):
    await _reset_settings(db_session)
    user = await _make_user(db_session, 8880008)
    out = await svc.create_subscription_checkout(user, "week")

    first = await _fulfill(svc, out.order_id, "orb:test1")
    until_after_first = user.premium_until
    second = await _fulfill(svc, out.order_id, "orb:test1")

    assert first["ok"] is True
    assert second["ok"] is True
    assert user.premium_until == until_after_first  # extended exactly once
    assert len(await _payments(db_session, out.order_id)) == 1


async def test_fulfill_race_loser_returns_winner_result(svc, db_session):
    await _reset_settings(db_session)
    user = await _make_user(db_session, 8880009)
    out = await svc.create_subscription_checkout(user, "week")

    winner = await _fulfill(svc, out.order_id, "orb:winner")
    until_after_winner = user.premium_until
    # different charge id, but the order is already paid -> loser branch
    loser = await _fulfill(svc, out.order_id, "orb:loser")

    assert winner["ok"] is True
    assert loser["ok"] is True
    assert loser["order_id"] == out.order_id
    assert user.premium_until == until_after_winner  # no double extension
    assert len(await _payments(db_session, out.order_id)) == 1  # no second Payment


# ----- Fulfillment: underpayment guard -----


async def test_fulfill_rejects_underpayment(svc, db_session):
    await _reset_settings(db_session)
    user = await _make_user(db_session, 8880010)
    out = await svc.create_subscription_checkout(user, "month")  # 299 stars -> $5.98

    res = await _fulfill(svc, out.order_id, "orb:short", paid_usd=1.00)

    assert res["ok"] is False
    assert res["error"] == "underpaid"
    order = await db_session.get(Order, out.order_id)
    await db_session.refresh(order)
    assert order.status == OrderStatus.pending  # still payable
    assert user.premium_until is None
    assert await _payments(db_session, out.order_id) == []


# ----- Premium claim perk -----


async def test_claim_requires_active_premium(svc, db_session):
    user = await _make_user(db_session, 8880011)  # premium_until is None
    with pytest.raises(ValueError):
        await svc.claim_with_premium(user, product_id=920)


async def test_claim_premium_video_free_paid_order(svc, db_session):
    user = await _make_user(db_session, 8880012)
    db_session.add(Product(id=920, slug="sub-claim-premium", status="published",
                           price_stars=500, is_premium=True))
    db_session.add(Product(id=921, slug="sub-claim-regular", status="published",
                           price_stars=300, is_premium=False))
    await db_session.commit()
    user.premium_until = datetime.now(timezone.utc) + timedelta(days=2)

    res = await svc.claim_with_premium(user, product_id=920)

    assert res["ok"] is True
    order = await db_session.get(Order, res["order_id"])
    await db_session.refresh(order)
    assert order.status == OrderStatus.paid
    assert order.paid_stars == 0  # free for subscribers

    again = await svc.claim_with_premium(user, product_id=920)
    assert again["order_id"] == res["order_id"]  # already owned -> same order

    with pytest.raises(ValueError):  # not a premium video
        await svc.claim_with_premium(user, product_id=921)


# ----- /profile is_premium boundary -----


async def test_profile_is_premium_boundary(db_session):
    from httpx import ASGITransport, AsyncClient

    from app.auth import get_current_user
    from app.main import app

    user = await _make_user(db_session, 8880013)

    async def _override():
        return user

    app.dependency_overrides[get_current_user] = _override
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            assert (await c.get("/profile")).json()["is_premium"] is False  # None
            user.premium_until = datetime.now(timezone.utc) - timedelta(seconds=5)
            assert (await c.get("/profile")).json()["is_premium"] is False  # just expired
            user.premium_until = datetime.now(timezone.utc) + timedelta(days=1)
            assert (await c.get("/profile")).json()["is_premium"] is True
    finally:
        app.dependency_overrides.pop(get_current_user, None)
