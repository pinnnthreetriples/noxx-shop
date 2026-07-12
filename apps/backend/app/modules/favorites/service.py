"""Favorites use-case service."""
from __future__ import annotations
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.favorites.repository import FavoriteRepository, RecentlyViewedRepository
from app.modules.catalog.service import _to_list_item, resolve_language
from app.modules.catalog.schemas import ProductListItem, FavoriteToggleOut
from app.modules.pricing import load_commission


class FavoriteService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = FavoriteRepository(db)
        self.recently_viewed_repo = RecentlyViewedRepository(db)

    async def list_for_user(self, user) -> List[ProductListItem]:
        rows = await self.repo.list_for_user(user.id)
        lang = resolve_language(user)
        commission = await load_commission(self.db)
        return [_to_list_item(p, lang, commission) for (_fav, p) in rows]

    async def add(self, user, product_id: int) -> FavoriteToggleOut:
        exists = await self.repo.exists(user.id, product_id)
        if not exists:
            await self.repo.add(user.id, product_id)
            await self.db.commit()
        return FavoriteToggleOut(is_favorite=True)

    async def remove(self, user, product_id: int) -> FavoriteToggleOut:
        await self.repo.remove(user.id, product_id)
        await self.db.commit()
        return FavoriteToggleOut(is_favorite=False)

    async def record_view(self, user, product_id: int) -> None:
        """Record that a user viewed a product (upsert into recently_viewed) and
        bump the product's real_views counter (admin-only analytics)."""
        from app.modules.catalog.repository import ProductRepository
        await self.recently_viewed_repo.upsert(user.id, product_id)
        await ProductRepository(self.db).increment_views(product_id)
        await self.db.commit()