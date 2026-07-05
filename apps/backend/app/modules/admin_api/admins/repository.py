"""Admin repository - SQL operations only."""
from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.admin.models import Admin
from app.modules.admin_api.filters import AdminListFilters, apply_sort, count_total, apply_updates


class AdminAdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list_with_filters(self, f: AdminListFilters) -> Tuple[List[Admin], int]:
        stmt = select(Admin)
        total = await count_total(self.db, stmt)
        stmt = apply_sort(stmt, Admin, f.sort_field, f.desc_order)
        stmt = stmt.offset(f.offset).limit(f.limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total
    
    async def get_by_id(self, id: int) -> Optional[Admin]:
        result = await self.db.execute(select(Admin).where(Admin.id == id))
        return result.scalars().first()
    
    async def create(self, **fields) -> Admin:
        admin = Admin(**fields)
        self.db.add(admin)
        await self.db.flush()
        return admin
    
    async def update(self, admin: Admin, fields: dict) -> Admin:
        apply_updates(admin, fields)
        return admin