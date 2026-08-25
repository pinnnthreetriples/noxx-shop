"""Three latent breakages that only fire once a rare row (or URL) shows up:

  * media_server checked containment with `startswith(MEDIA_ROOT)`, so a
    traversal to a *sibling* whose name merely starts with "media"
    (/app/media_server.py, any /app/media-*) passed the guard;
  * TicketNotification required `user_telegram_id`, but the service yields None
    when the ticket's user row is gone — one orphan 500'd the whole unnotified
    batch, and since nothing could then be marked notified, ticket
    notifications stopped forever;
  * fulfill() wrote `stars_amount=total_amount`, which is 0 on the crypto path,
    so every OrbChain payment row claimed to be worth nothing.

Rows use a private id range and are removed in teardown — the test DB is
shared by the whole session.
"""
import pytest
from fastapi import HTTPException
from sqlalchemy import delete, select

import app.media_server as media_server
from app.core.config import settings
from app.modules.internal_api.schemas import TicketNotification
from app.modules.internal_api.support import unnotified_tickets
from app.modules.orders.models import Order, OrderStatus, Payment
from app.modules.orders.service import OrderService
from app.modules.support.models import SupportTicket, SupportMessage, SupportTopic, TicketStatus
from app.modules.users.models import User

# Private id range for this file (the DB is shared across the session).
TG_BASE = 8893000


# ----- (3) media server path containment -----


@pytest.fixture
def media_root(tmp_path, monkeypatch):
    root = tmp_path / "media"
    (root / "clips").mkdir(parents=True)
    (root / "clips" / "a.mp4").write_bytes(b"ok")
    # Two decoys a prefix comparison happily accepts.
    (tmp_path / "media_server.py").write_bytes(b"source")
    (tmp_path / "media-public").mkdir()
    (tmp_path / "media-public" / "secret.txt").write_bytes(b"secret")
    monkeypatch.setattr(media_server, "MEDIA_ROOT", str(root))
    return root


def test_media_path_inside_root_is_allowed(media_root):
    assert media_server._get_file_path("clips/a.mp4") == str(media_root / "clips" / "a.mp4")


@pytest.mark.parametrize("path", ["../media_server.py", "../media-public/secret.txt"])
def test_media_path_to_prefix_sibling_is_denied(media_root, path):
    """`startswith` let these through: "<tmp>/media_server.py" does start with
    "<tmp>/media". Containment has to be per path component."""
    with pytest.raises(HTTPException) as exc:
        media_server._get_file_path(path)
    assert exc.value.status_code == 403


def test_media_path_escaping_upwards_is_denied(media_root):
    with pytest.raises(HTTPException) as exc:
        media_server._get_file_path("../../etc/passwd")
    assert exc.value.status_code == 403


# ----- (4) one orphaned ticket must not stall every notification -----


@pytest.fixture
async def support_cleanup(db_session):
    yield
    users = (await db_session.execute(
        select(User.id).where(User.telegram_id >= TG_BASE, User.telegram_id < TG_BASE + 1000)
    )).scalars().all()
    tickets = (await db_session.execute(
        select(SupportTicket.id).where(SupportTicket.user_id.in_([*users, 0]))
    )).scalars().all()
    if tickets:
        await db_session.execute(delete(SupportMessage).where(SupportMessage.ticket_id.in_(tickets)))
        await db_session.execute(delete(SupportTicket).where(SupportTicket.id.in_(tickets)))
    if users:
        await db_session.execute(delete(User).where(User.id.in_(users)))
    await db_session.commit()


def test_ticket_notification_accepts_missing_user(db_session):
    """The schema itself must tolerate the None the service can produce."""
    from datetime import datetime

    n = TicketNotification(
        ticket_id=1, user_telegram_id=None, topic="other", created_at=datetime.now()
    )
    assert n.user_telegram_id is None


async def test_orphaned_ticket_does_not_break_the_batch(db_session, support_cleanup):
    user = User(telegram_id=TG_BASE + 1)
    db_session.add(user)
    await db_session.flush()

    # user_id=0 never exists -> get_by_id returns None -> user_telegram_id None.
    orphan = SupportTicket(user_id=0, topic=SupportTopic.other, status=TicketStatus.open)
    healthy = SupportTicket(user_id=user.id, topic=SupportTopic.payment, status=TicketStatus.open)
    db_session.add_all([orphan, healthy])
    await db_session.commit()

    resp = await unnotified_tickets(after_id=orphan.id - 1, limit=50, db=db_session)

    by_id = {t.ticket_id: t for t in resp.tickets}
    assert orphan.id in by_id and healthy.id in by_id, "the orphan must not drop the batch"
    assert by_id[orphan.id].user_telegram_id is None
    assert by_id[healthy.id].user_telegram_id == user.telegram_id


# ----- (5) crypto payments must not be recorded as worth 0 stars -----


@pytest.fixture
def order_svc(db_session, monkeypatch):
    async def _no_enqueue(self, order_id):
        return None

    monkeypatch.setattr(OrderService, "_enqueue_delivery", _no_enqueue)
    monkeypatch.setattr(settings, "orbchain_api_key", "")
    monkeypatch.setattr(settings, "bot_token", "")
    return OrderService(db_session)


@pytest.fixture
async def orders_cleanup(db_session):
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


async def _pending_order(db, tg_offset: int, paid_stars: int) -> Order:
    user = User(telegram_id=TG_BASE + tg_offset)
    db.add(user)
    await db.flush()
    order = Order(
        user_id=user.id, status=OrderStatus.pending, total_stars=paid_stars,
        paid_stars=paid_stars, subscription_plan="month",
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


async def _payment(db, order_id: int) -> Payment:
    return (await db.execute(select(Payment).where(Payment.order_id == order_id))).scalar_one()


@pytest.mark.parametrize("paid_stars,total_amount,expected", [
    (500, 0, 500),    # crypto: no Telegram amount -> fall back to the order price
    (300, 300, 300),  # Stars: unchanged, total_amount already equals paid_stars
    (0, 0, 0),        # free premium claim: genuinely zero
])
async def test_payment_records_the_order_star_price(
    db_session, order_svc, orders_cleanup, paid_stars, total_amount, expected
):
    order = await _pending_order(db_session, paid_stars + 10, paid_stars)
    charge = f"orb:{order.id}" if total_amount == 0 else f"tg:{order.id}"
    result = await order_svc.fulfill(
        invoice_payload=str(order.id),
        telegram_payment_charge_id=charge,
        provider_payment_charge_id=str(order.id),
        total_amount=total_amount,
    )
    assert result["ok"] is True
    assert (await _payment(db_session, order.id)).stars_amount == expected
