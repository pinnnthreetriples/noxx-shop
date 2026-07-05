"""AdminLog repository - SQL operations only."""
from typing import List, Optional, Tuple
from sqlalchemy import select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.admin.models import AdminLog
from app.modules.admin_api.filters import AdminListFilters, apply_sort, count_total


class AdminLogAdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list_with_filters(self, f: AdminListFilters) -> Tuple[List[AdminLog], int]:
        stmt = select(AdminLog)
        total = await count_total(self.db, stmt)
        stmt = apply_sort(stmt, AdminLog, f.sort_field, f.desc_order)
        stmt = stmt.offset(f.offset).limit(f.limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total
    
    async def get_by_id(self, id: int) -> Optional[AdminLog]:
        result = await self.db.execute(select(AdminLog).where(AdminLog.id == id))
        return result.scalars().first()