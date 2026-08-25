"""PromoCode admin service - use-case logic."""
from typing import Optional, Dict, Any
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.promos.models import PromoCode
from app.modules.admin_api.promo_codes.repository import PromoCodeAdminRepository
from app.modules.admin_api.filters import AdminListFilters

# Columns the form may legitimately blank out. Everything else is NOT NULL, so a
# null coming back from react-admin (which echoes the whole record) is "not set",
# not "clear it".
CLEARABLE = {"usage_limit", "min_cart_total", "starts_at", "expires_at"}


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
        # payload comes from PromoCodeCreate: only real columns, dates already
        # parsed into aware UTC datetimes, used_count not among them.
        pc = await self.repo.create(**payload)
        await self.db.commit()
        await self.db.refresh(pc)
        return pc
    
    async def update(self, admin, id: int, payload: dict) -> Optional[PromoCode]:
        pc = await self.repo.get_by_id(id)
        if not pc:
            return None
        fields = {k: v for k, v in payload.items() if v is not None or k in CLEARABLE}
        await self.repo.update(pc, fields)
        await self.db.commit()
        await self.db.refresh(pc)
        return pc
    
    async def delete(self, admin, id: int) -> Optional[PromoCode]:
        pc = await self.repo.get_by_id(id)
        if not pc:
            return None
        # orders.promo_code_id has no ON DELETE, so deleting a redeemed code used
        # to surface as an unexplained 500. The order history is the reason the
        # row has to stay: say so instead.
        used = await self.repo.count_orders_using(id)
        if used:
            raise ValueError(
                f"Promo code is used in {used} order(s) and cannot be deleted. "
                "Deactivate it instead."
            )
        await self.repo.delete(pc)
        try:
            await self.db.commit()
        except IntegrityError as e:  # e.g. still attached to somebody's cart
            await self.db.rollback()
            raise ValueError("Promo code is still referenced elsewhere and cannot be deleted.") from e
        return pc
