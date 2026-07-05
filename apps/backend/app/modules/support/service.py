"""
Support use-case service.

Owns support ticket lifecycle, admin replies, and unnotified ticket polling.
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.support.repository import (
    SupportTicketRepository,
    SupportMessageRepository,
)
from app.modules.support.models import TicketStatus
from app.modules.orders.repository import BotMessageMapRepository
from app.modules.admin.repository import AdminRepository
from app.modules.support.schemas import (
    SupportTicketOut,
    SupportTicketDetail,
    SupportMessageOut,
)


class SupportService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ticket_repo = SupportTicketRepository(db)
        self.msg_repo = SupportMessageRepository(db)
        self.bot_msg_repo = BotMessageMapRepository(db)
        self.admin_repo = AdminRepository(db)

    # ----- User-facing -----

    async def create_ticket(self, user, topic: str, message: str) -> SupportTicketOut:
        if user.is_blocked:
            raise PermissionError("User is blocked")
        from app.modules.support.models import SupportTopic
        # Topic may already be an enum or a string; normalise via enum lookup.
        topic_enum = SupportTopic(topic) if topic in SupportTopic.__members__ else SupportTopic.other
        ticket = await self.ticket_repo.create(user.id, topic_enum, message)
        await self.db.commit()
        await self.db.refresh(ticket)
        return SupportTicketOut(
            id=ticket.id,
            topic=ticket.topic.value,
            status=ticket.status.value,
            created_at=ticket.created_at,
        )

    async def list_user_tickets(self, user) -> List[SupportTicketDetail]:
        tickets = await self.ticket_repo.list_for_user(user.id)
        out = []
        for t in tickets:
            msgs = await self._ticket_messages_to_out(t.messages)
            out.append(SupportTicketDetail(
                id=t.id,
                topic=t.topic.value,
                status=t.status.value,
                created_at=t.created_at,
                messages=msgs,
            ))
        return out

    async def add_user_message(
        self, user, ticket_id: int, text: str,
        file_url: Optional[str] = None, file_type: Optional[str] = None,
    ) -> Optional[SupportMessageOut]:
        if user.is_blocked:
            raise PermissionError("User is blocked")
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if not ticket or ticket.user_id != user.id:
            return None
        msg = await self.msg_repo.create(
            ticket_id=ticket_id,
            sender_type="user",
            sender_id=user.id,
            text=text,
            file_url=file_url,
            file_type=file_type,
        )
        ticket.status = TicketStatus.open
        await self.db.commit()
        await self.db.refresh(msg)
        return SupportMessageOut(
            id=msg.id, sender_type=msg.sender_type, text=msg.text,
            file_url=msg.file_url, file_type=msg.file_type, created_at=msg.created_at,
        )

    async def _ticket_messages_to_out(self, messages) -> List[SupportMessageOut]:
        return [
            SupportMessageOut(
                id=m.id, sender_type=m.sender_type, text=m.text,
                file_url=m.file_url, file_type=m.file_type, created_at=m.created_at,
            )
            for m in messages
        ]

    # ----- Internal API: admin reply (moved from bot) -----

    async def admin_reply_by_telegram(
        self,
        admin_telegram_id: int,
        reply_to_message_id: int,
        text: Optional[str],
        file_url: Optional[str],
        file_type: Optional[str],
    ) -> Dict[str, Any]:
        admin = await self.admin_repo.get_by_telegram_id(admin_telegram_id)
        if not admin or not admin.active:
            return {"ok": False, "error": "Admin not found or inactive"}
        ticket_id = await self.bot_msg_repo.get_ticket_id_by_admin_message(reply_to_message_id)
        if ticket_id is None:
            return {"ok": False, "error": "Ticket not linked to this message"}
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            return {"ok": False, "error": "Ticket not found"}
        await self.msg_repo.create(
            ticket_id=ticket_id,
            sender_type="admin",
            sender_id=admin.id,
            text=text,
            file_url=file_url,
            file_type=file_type,
        )
        await self.ticket_repo.mark_answered(ticket_id)
        await self.db.commit()
        return {
            "ok": True,
            "ticket_id": ticket_id,
            "user_telegram_id": None,  # filled by caller if needed
            "text": text,
            "file_url": file_url,
            "file_type": file_type,
        }

    async def record_admin_message_map(
        self, admin_message_id: int, chat_id: int, ticket_id: int,
    ) -> None:
        await self.bot_msg_repo.create(admin_message_id, chat_id, ticket_id)
        await self.db.commit()

    async def get_unnotified_tickets(self, after_id: int, limit: int) -> List[Dict[str, Any]]:
        tickets = await self.ticket_repo.list_unnotified(after_id, limit)
        # Resolve user telegram_ids in one query
        from app.modules.users.repository import UserRepository
        user_repo = UserRepository(self.db)
        result = []
        for t in tickets:
            user = await user_repo.get_by_id(t.user_id)
            result.append({
                "ticket_id": t.id,
                "user_telegram_id": user.telegram_id if user else None,
                "topic": t.topic.value if hasattr(t.topic, "value") else str(t.topic),
                "created_at": t.created_at.isoformat() if t.created_at else None,
            })
        return result

    async def mark_admin_notified(self, ticket_id: int) -> bool:
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            return False
        await self.ticket_repo.mark_admin_notified(ticket_id)
        await self.db.commit()
        return True
