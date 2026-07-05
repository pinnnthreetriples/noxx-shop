"""AdminLog admin service - use-case logic."""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.admin.models import AdminLog
from app.modules.admin_api.admin_logs.repository import AdminLogAdminRepository
from app.modules.admin_api.filters import AdminListFilters


class AdminLogAdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AdminLogAdminRepository(db)
    
    async def list(self, sort_field: str, order: str, start: int, end: int) -> Dict[str, Any]:
        f = AdminListFilters(sort_field=sort_field, order=order, start=start, end=end)
        items, total = await self.repo.list_with_filters(f)
        return {"data": items, "total": total}
    
    async def get(self, id: int) -> Optional[AdminLog]:
        return await self.repo.get_by_id(id)