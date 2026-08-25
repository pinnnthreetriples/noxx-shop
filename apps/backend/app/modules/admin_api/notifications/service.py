"""Notification admin service - use-case logic."""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.notifications.models import Notification
from app.modules.admin_api.notifications.repository import NotificationAdminRepository
from app.modules.admin_api.filters import AdminListFilters

logger = logging.getLogger(__name__)


class NotificationAdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = NotificationAdminRepository(db)
    
    async def list(self, sort_field: str, order: str, start: int, end: int) -> Dict[str, Any]:
        f = AdminListFilters(sort_field=sort_field, order=order, start=start, end=end)
        items, total = await self.repo.list_with_filters(f)
        return {"data": items, "total": total}
    
    async def get(self, id: int) -> Optional[Notification]:
        return await self.repo.get_by_id(id)
    
    async def create(self, admin, payload: dict) -> Notification:
        notif = await self.repo.create(
            title=payload.get("title", ""),
            body=payload.get("body"),
            product_id=payload.get("product_id"),
        )
        # Commit BEFORE queueing: the bot asks the backend for the recipients as
        # soon as it sees the job, and an uncommitted notification reads back as
        # missing — the broadcast then degrades to generic text. Same order as
        # NotificationService.create_and_enqueue.
        await self.db.commit()
        await self.db.refresh(notif)
        # Include the full payload so the bot dispatcher can construct a
        # non-empty message for end users. Regression: previously only
        # notification_id was pushed, which caused blank messages.
        import json
        from app.core.redis_client import redis_client
        try:
            await redis_client.lpush(
                "notifications:queue",
                json.dumps({
                    "notification_id": notif.id,
                    "title": notif.title,
                    "body": notif.body,
                    "product_id": notif.product_id,
                }),
            )
        except Exception as e:
            # The notification row exists but nothing will send it; make that
            # loud instead of failing the admin request after a successful save.
            logger.error("notification %s created but not queued: %s", notif.id, e,
                         exc_info=True)
        return notif
    
    async def delete(self, admin, id: int) -> Optional[Notification]:
        notif = await self.repo.get_by_id(id)
        if not notif:
            return None
        await self.repo.delete(notif)
        await self.db.commit()
        return notif