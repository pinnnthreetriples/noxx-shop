"""PromoCode admin service - use-case logic."""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.promos.models import PromoCode
from app.modules.admin_api.promo_codes.repository import PromoCodeAdminRepository
from app.modules.admin_api.filters import AdminListFilters


class PromoCodeAdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PromoCodeAdminRepository(db)
    
    async def list(self, sort_field: str, order: str, start: int, end: int) -> Dict[str, Any]:
        f = AdminListFilters(sort_field=sort_field, order=order, start=start, end=end)
        items, total = await self.repo.list_with_filters(f)
        return {"data": items, "total": total}
    
    async def get(self, id: int) -> Optional[PromoCode]:
        return await self.repo.get_by_id(id)
    
    async def create(self, admin, payload: dict) -> PromoCode:
        pc = await self.repo.create(
            code=payload.get("code", ""),
            discount_type=payload.get("discount_type", "percentage"),
            discount_value=payload.get("discount_value", 0),
            active=payload.get("active", True),
            usage_limit=payload.get("usage_limit"),
            first_purchase_only=payload.get("first_purchase_only", False),
            min_cart_total=payload.get("min_cart_total"),
        )
        if payload.get("starts_at"):
            from datetime import datetime
            pc.starts_at = datetime.fromisoformat(payload["starts_at"].replace("Z", "+00:00"))
        if payload.get("expires_at"):
            from datetime import datetime
            pc.expires_at = datetime.fromisoformat(payload["expires_at"].replace("Z", "+00:00"))
        await self.db.commit()
        await self.db.refresh(pc)
        return pc
    
    async def update(self, admin, id: int, payload: dict) -> Optional[PromoCode]:
        pc = await self.repo.get_by_id(id)
        if not pc:
            return None
        await self.repo.update(pc, {k: v for k, v in payload.items() if hasattr(pc, k) and k != "id"})
        await self.db.commit()
        await self.db.refresh(pc)
        return pc
    
    async def delete(self, admin, id: int) -> Optional[PromoCode]:
        pc = await self.repo.get_by_id(id)
        if not pc:
            return None
        await self.repo.delete(pc)
        await self.db.commit()
        return pc