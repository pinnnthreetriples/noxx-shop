"""Admin support reply: stores an `admin` message, marks the ticket answered,
and enqueues a short localized bot nudge (not the reply body) for the author."""
import json
import pytest
from app.modules.support.models import SupportTicket, SupportMessage, TicketStatus, SupportTopic
from app.modules.users.models import User


class FakeRedis:
    """Captures lpush calls for assertion without hitting a real Redis."""
    def __init__(self):
        self.pushed = []

    async def lpush(self, key, value):
        self.pushed.append((key, value))


@pytest.mark.asyncio
async def test_reply_stores_message_marks_answered_and_enqueues(db_session, monkeypatch):
    from app.modules.admin_api.support_tickets.service import SupportTicketAdminService

    user = User(telegram_id=700100200, first_name="Buyer", selected_language="en")
    db_session.add(user)
    await db_session.flush()
    ticket = SupportTicket(user_id=user.id, topic=SupportTopic.other, status=TicketStatus.open)
    db_session.add(ticket)
    await db_session.flush()
    db_session.add(SupportMessage(ticket_id=ticket.id, sender_type="user", sender_id=user.id, text="Help"))
    await db_session.commit()

    fake = FakeRedis()
    import app.modules.admin_api.support_tickets.service as svc_module
    monkeypatch.setattr(svc_module, "redis_client", fake)

    admin = type("Admin", (), {"id": 5})()
    reply_body = "Ваш заказ отправлен"
    result = await SupportTicketAdminService(db_session).reply(admin, ticket.id, reply_body)

    # (a) the full reply is still stored as an admin message (the mini-app reads it)
    admin_msgs = [m for m in result["messages"] if m["sender_type"] == "admin"]
    assert len(admin_msgs) == 1
    assert admin_msgs[0]["text"] == reply_body

    # (b) status flips to answered
    assert result["status"] == TicketStatus.answered.value
    assert result["delivered"] is True

    # (c) the bot gets a short localized nudge + a /support button, NOT the reply body
    assert len(fake.pushed) == 1
    key, value = fake.pushed[0]
    assert key == "deliveries:queue"
    payload = json.loads(value)
    assert payload["user_telegram_id"] == user.telegram_id
    assert reply_body not in payload["message_text"]
    assert payload["message_text"] == "🔔 Reply from support"
    assert payload["button"]["text"] == "View"
    assert payload["button"]["url"].endswith("/support")


@pytest.mark.asyncio
async def test_admin_reply_by_telegram_resolves_user_and_lang(db_session):
    """The bot needs the recipient's telegram_id and language to deliver the
    reply with a localized «Посмотреть» button (was hardcoded to None)."""
    from app.modules.admin.models import Admin
    from app.modules.orders.repository import BotMessageMapRepository
    from app.modules.support.service import SupportService

    user = User(telegram_id=700100300, first_name="Buyer", selected_language="ru")
    admin = Admin(telegram_id=900100300, name="Owner")
    db_session.add_all([user, admin])
    await db_session.flush()
    ticket = SupportTicket(user_id=user.id, topic=SupportTopic.other, status=TicketStatus.open)
    db_session.add(ticket)
    await db_session.flush()
    await BotMessageMapRepository(db_session).create(admin_message_id=42, chat_id=1, ticket_id=ticket.id)
    await db_session.commit()

    result = await SupportService(db_session).admin_reply_by_telegram(
        admin_telegram_id=admin.telegram_id, reply_to_message_id=42,
        text="Готово", file_url=None, file_type=None,
    )
    assert result["ok"] is True
    assert result["user_telegram_id"] == user.telegram_id
    assert result["user_lang"] == "ru"


@pytest.mark.asyncio
async def test_reply_missing_ticket_returns_none(db_session, monkeypatch):
    from app.modules.admin_api.support_tickets.service import SupportTicketAdminService

    fake = FakeRedis()
    import app.modules.admin_api.support_tickets.service as svc_module
    monkeypatch.setattr(svc_module, "redis_client", fake)

    admin = type("Admin", (), {"id": 5})()
    result = await SupportTicketAdminService(db_session).reply(admin, 999999, "hi")
    assert result is None
    assert fake.pushed == []
