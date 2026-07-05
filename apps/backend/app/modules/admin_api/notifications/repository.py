"""Notification repository - SQL operations only."""
from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.notifications.models import Notification
from app.modules.admin_api.filters import AdminListFilters, apply_sort, count_total


class NotificationAdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list_with_filters(self, f: AdminListFilters) -> Tuple[List[Notification], int]:
        stmt = select(Notification)
        total = await count_total(self.db, stmt)
        stmt = apply_sort(stmt, Notification, f.sort_field, f.desc_order)
        stmt = stmt.offset(f.offset).limit(f.limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total
    
    async def get_by_id(self, id: int) -> Optional[Notification]:
        result = await self.db.execute(select(Notification).where(Notification.id == id))
        return result.scalars().first()
    
    async def create(self, **fields) -> Notification:
        notif = Notification(**fields)
        self.db.add(notif)
        await self.db.flush()
        return notif
    
    async def delete(self, notif: Notification):
        await self.db.delete(notif)