"""Admin support reply: stores an `admin` message, marks the ticket answered,
and enqueues a bot delivery for the ticket author."""
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

    user = User(telegram_id=700100200, first_name="Buyer")
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
    result = await SupportTicketAdminService(db_session).reply(admin, ticket.id, "Ваш заказ отправлен")

    # (a) an admin message is stored
    admin_msgs = [m for m in result["messages"] if m["sender_type"] == "admin"]
    assert len(admin_msgs) == 1
    assert admin_msgs[0]["text"] == "Ваш заказ отправлен"

    # (b) status flips to answered
    assert result["status"] == TicketStatus.answered.value
    assert result["delivered"] is True

    # (c) a {user_telegram_id, message_text} is enqueued on deliveries:queue
    assert len(fake.pushed) == 1
    key, value = fake.pushed[0]
    assert key == "deliveries:queue"
    payload = json.loads(value)
    assert payload["user_telegram_id"] == user.telegram_id
    assert payload["message_text"] == "Ответ поддержки:\nВаш заказ отправлен"


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
