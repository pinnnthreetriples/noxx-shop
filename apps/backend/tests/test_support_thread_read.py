"""Regression: GET /support/tickets must return each ticket's full message
thread (incl. the admin reply) without a MissingGreenlet error.

The endpoint used to `select(SupportTicket)` without eager-loading `.messages`,
so iterating them lazily under the async engine raised
`greenlet_spawn has not been called` and 500'd — the mini-app then showed no
thread at all, so admin replies never reached the user.
"""
import pytest
from app.modules.support.router import list_support_tickets
from app.modules.support.models import SupportTicket, SupportMessage, TicketStatus, SupportTopic
from app.modules.users.models import User


@pytest.mark.asyncio
async def test_list_tickets_returns_thread_with_admin_reply(db_session):
    user = User(telegram_id=700100999, first_name="Buyer", selected_language="en")
    db_session.add(user)
    await db_session.flush()
    ticket = SupportTicket(user_id=user.id, topic=SupportTopic.other, status=TicketStatus.answered)
    db_session.add(ticket)
    await db_session.flush()
    db_session.add(SupportMessage(ticket_id=ticket.id, sender_type="user", sender_id=user.id, text="Help me"))
    db_session.add(SupportMessage(ticket_id=ticket.id, sender_type="admin", sender_id=1, text="Here is your link"))
    await db_session.commit()

    out = await list_support_tickets(user=user, db=db_session)

    assert len(out) == 1
    # order-independent: created_at has 1s resolution in SQLite, so two rows in the
    # same second tie — what matters is the thread loads and the admin reply is in it.
    texts = {m.text for m in out[0].messages}
    assert texts == {"Help me", "Here is your link"}  # admin reply is visible to the user
