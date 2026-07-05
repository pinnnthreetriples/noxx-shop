"""SupportTicket admin service - use-case logic."""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.support.models import SupportTicket
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
    
    async def get(self, id: int) -> Optional[SupportTicket]:
        return await self.repo.get_by_id(id)
    
    async def update(self, admin, id: int, payload: dict) -> Optional[SupportTicket]:
        ticket = await self.repo.get_by_id(id)
        if not ticket:
            return None
        await self.repo.update(ticket, {k: v for k, v in payload.items() if hasattr(ticket, k) and k != "id"})
        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket