"""Underpayment protection for OrbChain crypto payments.

Covers the three ways the guard used to be bypassed:
  * the polling path (`/orders/{id}/check-payment`, hit every 5s by the payment
    screen) fulfilled without ever passing an amount, and it almost always beat
    the webhook to the shared `orb:{track_id}` charge id, so the amount-carrying
    webhook exited on idempotency before reaching the guard;
  * `paid_usd=credited or None` turned "transactions arrived, none CREDITED"
    ($0.00) into "no data, skip the check";
  * the expected amount was recomputed at the live Stars→USD rate instead of the
    rate the invoice was actually cut at, so a rate change inside the invoice's
    60-minute lifetime produced false rejections (and hid real underpayments).

External I/O is stubbed: OrbChain HTTP calls are monkeypatched and the redis
delivery queue is a no-op. Rows use a private id range and are removed in
teardown — the test DB is shared by the whole session.
"""
import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

import app.modules.payments_orbchain.client as orb_client
from app.core.config import settings
from app.main import app
from app.modules.orders.models import Order, OrderStatus, Payment
from app.modules.orders.service import OrderService
from app.modules.payments_orbchain.client import credited_usd, payment_window_open
from app.modules.users.models import User

# Private id range for this file (the DB is shared across the session).
TG_BASE = 8891000
STAR_RATE = 0.02  # 500 stars -> $10.00


@pytest.fixture
def svc(db_session, monkeypatch):
    async def _rate(self):
        return STAR_RATE

    async def _no_enqueue(self, order_id):
        return None

    monkeypatch.setattr(OrderService, "_star_rate", _rate)
    monkeypatch.setattr(OrderService, "_enqueue_delivery", _no_enqueue)
    monkeypatch.setattr(settings, "orbchain_webhook_secret", "test-secret")
    return OrderService(db_session)


@pytest.fixture
async def cleanup(db_session):
    """Drop every row this file created, whichever session wrote it."""
    yield
    users = (await db_session.execute(
        select(User.id).where(User.telegram_id >= TG_BASE, User.telegram_id < TG_BASE + 1000)
    )).scalars().all()
    if users:
        orders = (await db_session.execute(
            select(Order.id).where(Order.user_id.in_(users))
        )).scalars().all()
        if orders:
            await db_session.execute(delete(Payment).where(Payment.order_id.in_(orders)))
            await db_session.execute(delete(Order).where(Order.id.in_(orders)))
        await db_session.execute(delete(User).where(User.id.in_(users)))
    await db_session.commit()


async def _user(db, n: int) -> User:
    user = User(telegram_id=TG_BASE + n)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _order(db, user: User, *, approx_usd: Optional[float] = 10.0,
                 paid_stars: int = 500, track: str = "trk") -> Order:
    """A pending crypto subscription order (itemless: fulfillment extends
    premium instead of needing a product catalogue)."""
    order = Order(
        user_id=user.id, status=OrderStatus.pending, total_stars=paid_stars,
        paid_stars=paid_stars, approx_usd=approx_usd, subscription_plan="month",
        orbchain_track_id=f"{track}_{user.telegram_id}",
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


def _status(**over: Any) -> Dict[str, Any]:
    """An OrbChain status-API `data` object reporting the invoice as paid."""
    data: Dict[str, Any] = {"status": "Paid", "expires_at": int(time.time()) + 1800}
    data.update(over)
    return data


def _txs(amount: str, status: str = "CREDITED") -> Dict[str, Any]:
    return {"transactions": [{"amount_usd": amount, "status": status}]}


def _poll_returns(monkeypatch, data: Dict[str, Any]) -> None:
    async def _get_payment(track_id: str):
        return data

    monkeypatch.setattr(orb_client, "get_payment", _get_payment)


async def _reload(db, order: Order) -> Order:
    await db.commit()  # end this session's snapshot, then read the row back
    await db.refresh(order)
    return order


# ----- amount extraction: "no money" vs "no data" -----


def test_credited_usd_tells_zero_apart_from_unknown():
    assert credited_usd(_txs("10.00")) == 10.0
    # transactions present, none CREDITED -> $0.00 credited, a hard signal
    assert credited_usd(_txs("10.00", "PENDING")) == 0.0
    assert credited_usd({"amount_usd": "12.50"}) == 12.5
    # nothing about amounts at all -> unknown, not zero
    assert credited_usd({"status": "Paid"}) is None
    assert credited_usd({"amount_usd": None}) is None


def test_payment_window_open_only_on_a_readable_future_expiry():
    assert payment_window_open({"expires_at": time.time() + 60}) is True
    assert payment_window_open({"expires_at": time.time() - 60}) is False
    assert payment_window_open({}) is False
    assert payment_window_open({"expires_at": "not-a-number"}) is False
    # milliseconds (or any other unit) must not read as a window open for years
    assert payment_window_open({"expires_at": (time.time() + 60) * 1000}) is False


# ----- checkout snapshots the invoiced amount -----


async def test_checkout_stores_the_invoiced_usd_on_the_order(svc, db_session, monkeypatch, cleanup):
    user = await _user(db_session, 1)
    order = await _order(db_session, user, approx_usd=None, track="new")
    billed = {}

    async def _create_invoice(**kwargs):
        billed.update(kwargs)
        return {"track_id": "trk_created", "payment_url": "https://pay.example/x"}

    monkeypatch.setattr(orb_client, "create_invoice", _create_invoice)

    url = await svc._create_orbchain_invoice(order.id, 500)

    assert url == "https://pay.example/x"
    assert billed["amount_usd"] == 10.0
    fresh = await _reload(db_session, order)
    assert float(fresh.approx_usd) == 10.0
    assert fresh.orbchain_track_id == "trk_created"


# ----- polling path: the guard now runs there too -----


async def test_polled_underpayment_is_rejected(svc, db_session, monkeypatch, cleanup):
    user = await _user(db_session, 2)
    order = await _order(db_session, user)
    _poll_returns(monkeypatch, _status(**_txs("6.00")))

    result = await svc.check_orbchain_payment(user, order.id)

    assert result == {"paid": False, "status": "underpaid"}
    assert (await _reload(db_session, order)).status == OrderStatus.pending
    assert (await db_session.execute(
        select(Payment).where(Payment.order_id == order.id)
    )).scalars().first() is None


async def test_polled_full_payment_fulfills(svc, db_session, monkeypatch, cleanup):
    user = await _user(db_session, 3)
    order = await _order(db_session, user)
    _poll_returns(monkeypatch, _status(**_txs("10.00")))

    result = await svc.check_orbchain_payment(user, order.id)

    assert result == {"paid": True, "status": "paid"}
    assert (await _reload(db_session, order)).status == OrderStatus.paid


async def test_polled_transactions_without_credited_do_not_fulfill(svc, db_session, monkeypatch, cleanup):
    """$0.00 credited is a reason to withhold the goods, not to skip the check."""
    user = await _user(db_session, 4)
    order = await _order(db_session, user)
    _poll_returns(monkeypatch, _status(**_txs("10.00", "PENDING")))

    result = await svc.check_orbchain_payment(user, order.id)

    assert result["paid"] is False
    assert (await _reload(db_session, order)).status == OrderStatus.pending


async def test_payment_state_endpoint_also_guards(svc, db_session, monkeypatch, cleanup):
    """The other polling entry point (`GET /orders/{id}/payment`) shares the guard."""
    user = await _user(db_session, 5)
    order = await _order(db_session, user)
    _poll_returns(monkeypatch, _status(address="TAddr1", pay_currency="USDT_TRC20", **_txs("1.00")))

    state = await svc.get_orbchain_payment(user, order.id)

    assert state.paid is False
    assert state.status == "underpaid"
    assert state.amount_usd == 10.0  # the invoiced amount, not a live recompute
    assert state.address == "TAddr1"  # deposit panel survives, the screen resumes
    assert (await _reload(db_session, order)).status == OrderStatus.pending


# ----- rate changes must not manufacture a verdict -----


async def test_rate_change_after_checkout_does_not_reject_full_payment(svc, db_session, monkeypatch, cleanup):
    """Invoice cut at $10.00; the admin then doubles the Stars→USD rate. The
    customer paid the invoice in full and must still be served."""
    user = await _user(db_session, 6)
    order = await _order(db_session, user)  # approx_usd 10.00, 500 stars

    async def _doubled(self):
        return STAR_RATE * 2  # recompute would demand $20.00

    monkeypatch.setattr(OrderService, "_star_rate", _doubled)
    _poll_returns(monkeypatch, _status(**_txs("10.00")))

    result = await svc.check_orbchain_payment(user, order.id)

    assert result == {"paid": True, "status": "paid"}
    assert (await _reload(db_session, order)).status == OrderStatus.paid


async def test_rate_change_after_checkout_does_not_hide_underpayment(svc, db_session, monkeypatch, cleanup):
    """The mirror case: the rate is halved, so a live recompute would accept
    $5.00 for a $10.00 invoice. The snapshot still rejects it."""
    user = await _user(db_session, 7)
    order = await _order(db_session, user)

    async def _halved(self):
        return STAR_RATE / 2  # recompute would demand only $5.00

    monkeypatch.setattr(OrderService, "_star_rate", _halved)
    _poll_returns(monkeypatch, _status(**_txs("5.00")))

    result = await svc.check_orbchain_payment(user, order.id)

    assert result["paid"] is False
    assert (await _reload(db_session, order)).status == OrderStatus.pending


# ----- orders predating the snapshot -----


async def test_legacy_order_without_snapshot_falls_back_to_the_live_rate(svc, db_session, monkeypatch, cleanup):
    """approx_usd is NULL on every order created before this change. Those keep
    the old behaviour — expected amount recomputed at the current rate — which
    still blocks underpayment and still fulfills an honest payment."""
    user = await _user(db_session, 8)
    short = await _order(db_session, user, approx_usd=None, track="legacy_a")
    _poll_returns(monkeypatch, _status(**_txs("4.00")))
    assert (await svc.check_orbchain_payment(user, short.id))["paid"] is False
    assert (await _reload(db_session, short)).status == OrderStatus.pending

    full = await _order(db_session, user, approx_usd=None, track="legacy_b")
    _poll_returns(monkeypatch, _status(**_txs("10.00")))  # == 500 stars * 0.02
    assert (await svc.check_orbchain_payment(user, full.id))["paid"] is True
    assert (await _reload(db_session, full)).status == OrderStatus.paid


# ----- amount unknown: hand over to the webhook, but never strand the order -----


async def test_unknown_amount_waits_for_the_webhook_while_the_invoice_is_open(
    svc, db_session, monkeypatch, cleanup
):
    user = await _user(db_session, 9)
    order = await _order(db_session, user)
    _poll_returns(monkeypatch, _status())  # no transactions, no amount_usd

    result = await svc.check_orbchain_payment(user, order.id)

    assert result == {"paid": False, "status": "confirming"}
    assert (await _reload(db_session, order)).status == OrderStatus.pending


async def test_flat_amount_on_the_status_api_is_not_taken_for_a_credited_amount(
    svc, db_session, monkeypatch, cleanup
):
    """A bare amount_usd on the status response is as likely to be the invoiced
    amount as the received one — trusting it would compare the invoice against
    itself and pass everything, so it counts as no data."""
    user = await _user(db_session, 14)
    order = await _order(db_session, user)
    _poll_returns(monkeypatch, _status(amount_usd="10.00"))

    result = await svc.check_orbchain_payment(user, order.id)

    assert result == {"paid": False, "status": "confirming"}
    assert (await _reload(db_session, order)).status == OrderStatus.pending


async def test_unknown_amount_fulfills_once_the_invoice_window_has_closed(
    svc, db_session, monkeypatch, cleanup
):
    """Backstop: a webhook that never arrives must not cost the buyer the goods."""
    user = await _user(db_session, 10)
    order = await _order(db_session, user)
    _poll_returns(monkeypatch, _status(expires_at=int(time.time()) - 10))

    result = await svc.check_orbchain_payment(user, order.id)

    assert result == {"paid": True, "status": "paid"}
    assert (await _reload(db_session, order)).status == OrderStatus.paid


async def test_unknown_amount_fulfills_when_no_webhook_is_configured(
    svc, db_session, monkeypatch, cleanup
):
    """Without a webhook secret no webhook can ever be accepted, so polling is
    the only path and holding the order back would break payments outright."""
    monkeypatch.setattr(settings, "orbchain_webhook_secret", "")
    user = await _user(db_session, 11)
    order = await _order(db_session, user)
    _poll_returns(monkeypatch, _status())

    result = await svc.check_orbchain_payment(user, order.id)

    assert result == {"paid": True, "status": "paid"}
    assert (await _reload(db_session, order)).status == OrderStatus.paid


# ----- webhook path, end to end -----


async def _post_webhook(order: Order, tx_status: str) -> int:
    body = json.dumps({
        "type": "payment", "status": "Paid", "amount": None,
        "order_id": str(order.id), "track_id": order.orbchain_track_id,
        "transactions": [{"amount_usd": "10.00", "status": tx_status}],
    }).encode()
    sig = hmac.new(b"test-secret", body, hashlib.sha512).hexdigest()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post("/webhook/orbchain", content=body, headers={"hmac": sig})
    return resp.status_code


@pytest.mark.parametrize(
    "tx_status,expected",
    [("PENDING", OrderStatus.pending), ("CREDITED", OrderStatus.paid)],
    ids=["nothing-credited-blocks", "credited-fulfills"],
)
async def test_webhook_fulfills_only_what_was_actually_credited(
    svc, db_session, monkeypatch, cleanup, tx_status, expected
):
    """Same $10.00 event twice, differing only in whether the transaction settled.
    The CREDITED leg is the control: it proves the blocked leg is blocked by the
    guard and not by a broken request."""
    user = await _user(db_session, 12 if tx_status == "PENDING" else 13)
    order = await _order(db_session, user, track="hook")
    await db_session.commit()  # release the shared sqlite connection for the app session

    assert await _post_webhook(order, tx_status) == 200
    assert (await _reload(db_session, order)).status == expected
