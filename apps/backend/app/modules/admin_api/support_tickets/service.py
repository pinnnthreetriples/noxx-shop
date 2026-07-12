"""SupportTicket admin service - use-case logic."""
import json
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.redis_client import redis_client
from app.modules.support.models import SupportTicket
from app.modules.support.reply_i18n import nudge_text, open_label
from app.modules.support.repository import SupportTicketRepository, SupportMessageRepository
from app.modules.users.repository import UserRepository
from app.modules.admin_api.support_tickets.repository import SupportTicketAdminRepository
from app.modules.admin_api.filters import AdminListFilters


class SupportTicketAdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SupportTicketAdminRepository(db)
    
    async def list(self, status: Optional[str], sort_field: str, order: str, start: int, end: int) -> Dict[str, Any]:
        f = AdminListFilters(status=status, sort_field=sort_field, order=order, start=start, end=end)
        items, total = await self.repo.list_with_filters(f)
        return {"data": items, "total": total}
    
    async def get(self, id: int) -> Optional[Dict[str, Any]]:
        ticket = await self.repo.get_by_id(id)
        if not ticket:
            return None
        return self._serialize(ticket)

    async def update(self, admin, id: int, payload: dict) -> Optional[Dict[str, Any]]:
        ticket = await self.repo.get_by_id(id)
        if not ticket:
            return None
        await self.repo.update(ticket, {k: v for k, v in payload.items() if hasattr(ticket, k) and k != "id"})
        await self.db.commit()
        # re-fetch with messages eager-loaded: refresh() would expire the
        # relationship and trigger a lazy load that async sessions forbid
        ticket = await self.repo.get_by_id(id)
        return self._serialize(ticket) if ticket else None

    async def reply(self, admin, id: int, text: str) -> Optional[Dict[str, Any]]:
        """Store the owner's reply as an `admin` message, mark the ticket
        answered, and nudge the user (via the bot delivery queue) to open the
        mini-app support screen where the reply text lives."""
        ticket = await self.repo.get_by_id(id)
        if not ticket:
            return None
        user = await UserRepository(self.db).get_by_id(ticket.user_id)
        await SupportMessageRepository(self.db).create(
            ticket_id=id, sender_type="admin", sender_id=admin.id, text=text,
        )
        await SupportTicketRepository(self.db).mark_answered(id)
        await self.db.commit()

        delivered = False
        if user and user.telegram_id:
            lang = user.selected_language or "en"
            webapp = settings.telegram_webapp_url.rstrip("/")
            await redis_client.lpush("deliveries:queue", json.dumps({
                "user_telegram_id": user.telegram_id,
                "message_text": f"🔔 {nudge_text(lang)}",
                "button": {"text": open_label(lang), "url": f"{webapp}/support"},
            }))
            delivered = True

        # Drop cached instances so the re-fetch reloads the messages
        # collection with the new admin reply included.
        self.db.expunge_all()
        ticket = await self.repo.get_by_id(id)
        if ticket is None:  # unreachable — replied to an existing ticket above
            raise RuntimeError("ticket not found after reply")
        result = self._serialize(ticket)
        result["delivered"] = delivered
        return result

    @staticmethod
    def _serialize(t: SupportTicket) -> Dict[str, Any]:
        return {
            "id": t.id,
            "user_id": t.user_id,
            "topic": getattr(t.topic, "value", str(t.topic)),
            "status": getattr(t.status, "value", str(t.status)),
            "created_at": t.created_at,
            "updated_at": t.updated_at,
            "messages": [
                {
                    "id": m.id,
                    "sender_type": m.sender_type,
                    "text": m.text,
                    "file_url": m.file_url,
                    "file_type": m.file_type,
                    "created_at": m.created_at,
                }
                for m in t.messages
            ],
        }