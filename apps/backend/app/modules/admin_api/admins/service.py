"""Admin admin service - use-case logic."""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.admin.models import Admin
from app.modules.admin_api.admins.repository import AdminAdminRepository
from app.modules.admin_api.filters import AdminListFilters


class AdminAdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AdminAdminRepository(db)
    
    async def list(self, sort_field: str, order: str, start: int, end: int) -> Dict[str, Any]:
        f = AdminListFilters(sort_field=sort_field, order=order, start=start, end=end)
        items, total = await self.repo.list_with_filters(f)
        return {"data": items, "total": total}
    
    async def get(self, id: int) -> Optional[Admin]:
        return await self.repo.get_by_id(id)
    
    async def create(self, admin, payload: dict) -> Admin:
        a = await self.repo.create(
            telegram_id=payload.get("telegram_id", 0),
            name=payload.get("name"),
            role=payload.get("role", "admin"),
            active=payload.get("active", True),
        )
        await self.db.commit()
        await self.db.refresh(a)
        return a
    
    async def update(self, admin, id: int, payload: dict) -> Optional[Admin]:
        a = await self.repo.get_by_id(id)
        if not a:
            return None
        await self.repo.update(a, {k: v for k, v in payload.items() if hasattr(a, k) and k != "id"})
        await self.db.commit()
        await self.db.refresh(a)
        return a
    
    async def deactivate(self, admin, id: int) -> Optional[Admin]:
        a = await self.repo.get_by_id(id)
        if not a:
            return None
        a.active = False
        await self.db.commit()
        return a