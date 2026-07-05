"""Tests for SupportTicketOut schema — must use `topic`, not `subject`.

Regression test: schema previously declared `subject: str` while the
underlying SQLAlchemy model uses `topic`. If the schema is ever wired as
a FastAPI response_model, serialization silently fails (KeyError /
ValidationError on Pydantic v2). The fix is to align schema field name
with the model.
"""
from datetime import datetime
from app.modules.admin_api.support_tickets.schemas import SupportTicketOut
from app.modules.support.models import SupportTicket, SupportTopic, TicketStatus


def test_support_ticket_out_uses_topic_field():
    """SupportTicketOut must serialize SupportTicket.topic as 'topic', not 'subject'."""
    ticket = SupportTicket(
        id=1,
        user_id=10,
        topic=SupportTopic.payment,
        status=TicketStatus.open,
        created_at=datetime(2026, 6, 30, 12, 0, 0),
        updated_at=datetime(2026, 6, 30, 12, 0, 0),
    )
    out = SupportTicketOut.model_validate(ticket)
    serialized = out.model_dump()

    assert "topic" in serialized, "SupportTicketOut must serialize `topic`"
    assert "subject" not in serialized, "SupportTicketOut must NOT use `subject`"
    assert serialized["topic"] == "Payment issue"


def test_support_ticket_out_includes_other_required_fields():
    """All other required fields must round-trip correctly."""
    ticket = SupportTicket(
        id=2,
        user_id=20,
        topic=SupportTopic.download,
        status=TicketStatus.closed,
        created_at=datetime(2026, 6, 30, 13, 0, 0),
        updated_at=datetime(2026, 6, 30, 13, 0, 0),
    )
    out = SupportTicketOut.model_validate(ticket)
    s = out.model_dump()
    assert s["id"] == 2
    assert s["user_id"] == 20
    assert s["status"] == "closed"
    assert "created_at" in s
    assert "updated_at" in s
