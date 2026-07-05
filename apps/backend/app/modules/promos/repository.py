from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc, update
from app.modules.promos.models import PromoCode, PromoRedemption


class PromoCodeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_code(self, code: str) -> Optional[PromoCode]:
        result = await self.db.execute(select(PromoCode).where(PromoCode.code == code))
        return result.scalars().first()

    async def get_by_id(self, promo_id: int) -> Optional[PromoCode]:
        result = await self.db.execute(select(PromoCode).where(PromoCode.id == promo_id))
        return result.scalars().first()

    async def list(
        self,
        sort: str = "created_at",
        order: str = "desc",
        start: int = 0,
        end: int = 50,
    ) -> Tuple[List[PromoCode], int]:
        stmt = select(PromoCode)
        
        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0
        
        # Apply sort
        sort_col = getattr(PromoCode, sort, PromoCode.created_at)
        if order == "desc":
            stmt = stmt.order_by(desc(sort_col))
        else:
            stmt = stmt.order_by(asc(sort_col))
        
        stmt = stmt.limit(end - start).offset(start)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def create(
        self,
        code: str,
        discount_type: str = "percentage",
        discount_value: int = 0,
        active: bool = True,
        usage_limit: Optional[int] = None,
        starts_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        first_purchase_only: bool = False,
        min_cart_total: Optional[int] = None,
    ) -> PromoCode:
        from datetime import datetime
        promo = PromoCode(
            code=code,
            discount_type=discount_type,
            discount_value=discount_value,
            active=active,
            usage_limit=usage_limit,
            starts_at=starts_at,
            expires_at=expires_at,
            first_purchase_only=first_purchase_only,
            min_cart_total=min_cart_total,
        )
        self.db.add(promo)
        await self.db.flush()
        return promo

    async def update(self, promo_id: int, fields: dict) -> Optional[PromoCode]:
        result = await self.db.execute(select(PromoCode).where(PromoCode.id == promo_id))
        promo = result.scalars().first()
        if promo:
            for key, value in fields.items():
                setattr(promo, key, value)
            await self.db.flush()
        return promo

    async def delete(self, promo_id: int) -> bool:
        result = await self.db.execute(select(PromoCode).where(PromoCode.id == promo_id))
        promo = result.scalars().first()
        if promo:
            await self.db.delete(promo)
            await self.db.flush()
            return True
        return False

    async def increment_used_count(self, promo_id: int) -> None:
        await self.db.execute(
            update(PromoCode).where(PromoCode.id == promo_id).values(used_count=PromoCode.used_count + 1)
        )


class PromoRedemptionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, promo_code_id: int, user_id: int, order_id: Optional[int] = None) -> PromoRedemption:
        redemption = PromoRedemption(promo_code_id=promo_code_id, user_id=user_id, order_id=order_id)
        self.db.add(redemption)
        await self.db.flush()
        return redemption

    async def exists(self, promo_code_id: int, user_id: int) -> bool:
        result = await self.db.execute(
            select(PromoRedemption).where(PromoRedemption.promo_code_id == promo_code_id, PromoRedemption.user_id == user_id)
        )
        return result.scalars().first() is not None
