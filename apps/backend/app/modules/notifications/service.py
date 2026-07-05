"""Notifications use-case service."""
from __future__ import annotations
import json
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.redis_client import redis_client
from app.modules.notifications.repository import NotificationRepository, NotificationRecipientRepository
from app.modules.admin.models import AdminLog

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = NotificationRepository(db)
        self.recipient_repo = NotificationRecipientRepository(db)

    async def create_and_enqueue(self, admin, title: str, body: Optional[str], product_id: Optional[int]):
        notification = await self.repo.create(title=title, body=body, product_id=product_id)
        self.db.add(AdminLog(
            admin_id=admin.id,
            action="create_notification",
            entity_type="notification",
            entity_id=notification.id,
        ))
        await self.db.commit()
        await self.db.refresh(notification)
        try:
            payload = {"notification_id": notification.id, "title": notification.title, "body": notification.body, "product_id": notification.product_id}
            await redis_client.lpush("notifications:queue", json.dumps(payload))
        except Exception as e:
            logger.warning("redis push failed: %s", e)
        return notification

    async def mark_sent(self, notification_id: int, user_id: int):
        await self.recipient_repo.upsert(notification_id, user_id, "sent", datetime.now(timezone.utc))
        await self.db.commit()

    async def mark_failed(self, notification_id: int, user_id: int, error: str):
        await self.recipient_repo.mark_failed(notification_id, user_id, error)
        await self.db.commit()