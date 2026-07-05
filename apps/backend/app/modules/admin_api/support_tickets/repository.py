"""SupportTicket repository - SQL operations only."""
from typing import List, Optional, Tuple
from sqlalchemy import select, func, desc, asc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.support.models import SupportTicket
from app.modules.admin_api.filters import AdminListFilters, apply_sort, count_total, search_ilike, apply_updates


class SupportTicketAdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list_with_filters(self, f: AdminListFilters) -> Tuple[List[SupportTicket], int]:
        stmt = select(SupportTicket)
        if f.status:
            stmt = stmt.where(SupportTicket.status == f.status)
        total = await count_total(self.db, stmt)
        stmt = apply_sort(stmt, SupportTicket, f.sort_field, f.desc_order)
        stmt = stmt.offset(f.offset).limit(f.limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total
    
    async def get_by_id(self, id: int) -> Optional[SupportTicket]:
        result = await self.db.execute(select(SupportTicket).where(SupportTicket.id == id))
        return result.scalars().first()
    
    async def update(self, ticket: SupportTicket, fields: dict) -> SupportTicket:
        apply_updates(ticket, fields)
        return ticket