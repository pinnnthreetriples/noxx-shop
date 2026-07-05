"""PromoCode repository - SQL operations only."""
from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.promos.models import PromoCode
from app.modules.admin_api.filters import AdminListFilters, apply_sort, count_total


class PromoCodeAdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list_with_filters(self, f: AdminListFilters) -> Tuple[List[PromoCode], int]:
        stmt = select(PromoCode)
        total = await count_total(self.db, stmt)
        stmt = apply_sort(stmt, PromoCode, f.sort_field, f.desc_order)
        stmt = stmt.offset(f.offset).limit(f.limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total
    
    async def get_by_id(self, id: int) -> Optional[PromoCode]:
        result = await self.db.execute(select(PromoCode).where(PromoCode.id == id))
        return result.scalars().first()
    
    async def get_by_code(self, code: str) -> Optional[PromoCode]:
        result = await self.db.execute(select(PromoCode).where(PromoCode.code == code))
        return result.scalars().first()
    
    async def create(self, **fields) -> PromoCode:
        pc = PromoCode(**fields)
        self.db.add(pc)
        await self.db.flush()
        return pc
    
    async def update(self, pc: PromoCode, fields: dict) -> PromoCode:
        for k, v in fields.items():
            if k in ("starts_at", "expires_at") and v:
                from datetime import datetime
                v = datetime.fromisoformat(v.replace("Z", "+00:00"))
            if hasattr(pc, k) and k not in ("id", "created_at", "updated_at"):
                setattr(pc, k, v)
        return pc
    
    async def delete(self, pc: PromoCode):
        await self.db.delete(pc)