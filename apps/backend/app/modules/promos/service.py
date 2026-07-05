"""Promo use-case service."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.promos.repository import PromoCodeRepository
from app.modules.promos.schemas import PromoValidateOut


class PromoService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PromoCodeRepository(db)

    async def validate(self, user, code: str, cart_total: int) -> PromoValidateOut:
        promo = await self.repo.get_by_code(code)
        if not promo or not promo.active:
            return PromoValidateOut(valid=False, discount_type=None, discount_value=None, message="Promo not found or inactive")
        now = datetime.now(timezone.utc)
        if promo.starts_at and promo.starts_at > now:
            return PromoValidateOut(valid=False, discount_type=None, discount_value=None, message="Promo not yet active")
        if promo.expires_at and promo.expires_at < now:
            return PromoValidateOut(valid=False, discount_type=None, discount_value=None, message="Promo expired")
        if promo.usage_limit is not None and promo.used_count >= promo.usage_limit:
            return PromoValidateOut(valid=False, discount_type=None, discount_value=None, message="Usage limit reached")
        if user is not None:
            from app.modules.promos.repository import PromoRedemptionRepository
            if await PromoRedemptionRepository(self.db).exists(promo.id, user.id):
                return PromoValidateOut(valid=False, discount_type=None, discount_value=None, message="Already used")
        if promo.first_purchase_only and user is not None:
            from app.modules.orders.repository import OrderItemRepository
            if await OrderItemRepository(self.db).count_paid_items_for_user(user.id) > 0:
                return PromoValidateOut(valid=False, discount_type=None, discount_value=None, message="First purchase only")
        if promo.min_cart_total is not None and cart_total < promo.min_cart_total:
            return PromoValidateOut(valid=False, discount_type=None, discount_value=None, message=f"Min cart {promo.min_cart_total}")
        return PromoValidateOut(valid=True, discount_type=promo.discount_type, discount_value=promo.discount_value, message=None)