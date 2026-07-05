from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.modules.notifications.models import Notification, NotificationRecipient


class NotificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, notification_id: int) -> Optional[Notification]:
        result = await self.db.execute(select(Notification).where(Notification.id == notification_id))
        return result.scalars().first()

    async def list(
        self,
        sort: str = "created_at",
        order: str = "desc",
        start: int = 0,
        end: int = 50,
    ) -> Tuple[List[Notification], int]:
        stmt = select(Notification)
        
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0
        
        sort_col = getattr(Notification, sort, Notification.created_at)
        if order == "desc":
            stmt = stmt.order_by(desc(sort_col))
        else:
            stmt = stmt.order_by(sort_col)
        
        stmt = stmt.limit(end - start).offset(start)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def create(self, title: str, body: Optional[str], product_id: Optional[int]) -> Notification:
        notif = Notification(title=title, body=body, product_id=product_id)
        self.db.add(notif)
        await self.db.flush()
        return notif

    async def delete(self, notification_id: int) -> bool:
        result = await self.db.execute(select(Notification).where(Notification.id == notification_id))
        notif = result.scalars().first()
        if notif:
            await self.db.delete(notif)
            await self.db.flush()
            return True
        return False


class NotificationRecipientRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert(self, notification_id: int, user_id: int, status: str, sent_at: Optional[datetime] = None) -> NotificationRecipient:
        result = await self.db.execute(
            select(NotificationRecipient).where(
                NotificationRecipient.notification_id == notification_id,
                NotificationRecipient.user_id == user_id,
            )
        )
        recipient = result.scalars().first()
        if recipient:
            recipient.status = status
            recipient.sent_at = sent_at
            if status == "failed":
                recipient.error = "Failed to send"
        else:
            recipient = NotificationRecipient(
                notification_id=notification_id,
                user_id=user_id,
                status=status,
                sent_at=sent_at,
            )
            self.db.add(recipient)
        await self.db.flush()
        return recipient

    async def mark_failed(self, notification_id: int, user_id: int, error: str) -> NotificationRecipient:
        return await self.upsert(notification_id, user_id, "failed")


class BotMessageMapRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, admin_message_id: int, chat_id: int, ticket_id: int):
        from app.modules.admin.models import BotMessageMap
        mapping = BotMessageMap(admin_message_id=admin_message_id, chat_id=chat_id, ticket_id=ticket_id)
        self.db.add(mapping)
        await self.db.flush()
        return mapping

    async def get_ticket_id_by_admin_message(self, admin_message_id: int) -> Optional[int]:
        from app.modules.admin.models import BotMessageMap
        result = await self.db.execute(
            select(BotMessageMap.ticket_id).where(BotMessageMap.admin_message_id == admin_message_id)
        )
        return result.scalars().first()

    async def table_check_or_create(self) -> None:
        pass
