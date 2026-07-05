from datetime import datetime, timezone
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.modules.favorites.models import Favorite, RecentlyViewed
from app.modules.catalog.models import Product


class FavoriteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_user(self, user_id: int) -> List[Tuple[Favorite, Product]]:
        result = await self.db.execute(
            select(Favorite, Product)
            .join(Product, Favorite.product_id == Product.id)
            .where(Favorite.user_id == user_id)
            .order_by(desc(Favorite.created_at))
        )
        return list(result.all())

    async def add(self, user_id: int, product_id: int) -> Favorite:
        result = await self.db.execute(
            select(Favorite).where(Favorite.user_id == user_id, Favorite.product_id == product_id)
        )
        fav = result.scalars().first()
        if not fav:
            fav = Favorite(user_id=user_id, product_id=product_id)
            self.db.add(fav)
            await self.db.flush()
        return fav

    async def remove(self, user_id: int, product_id: int) -> bool:
        result = await self.db.execute(
            select(Favorite).where(Favorite.user_id == user_id, Favorite.product_id == product_id)
        )
        fav = result.scalars().first()
        if fav:
            await self.db.delete(fav)
            await self.db.flush()
            return True
        return False

    async def exists(self, user_id: int, product_id: int) -> bool:
        result = await self.db.execute(
            select(Favorite.id).where(Favorite.user_id == user_id, Favorite.product_id == product_id)
        )
        return result.scalars().first() is not None


class RecentlyViewedRepository:
    """Repository for the RecentlyViewed model (favorites domain)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert(self, user_id: int, product_id: int) -> None:
        result = await self.db.execute(
            select(RecentlyViewed).where(
                RecentlyViewed.user_id == user_id,
                RecentlyViewed.product_id == product_id,
            )
        )
        rv = result.scalars().first()
        if rv:
            rv.viewed_at = datetime.now(timezone.utc)
        else:
            self.db.add(RecentlyViewed(user_id=user_id, product_id=product_id))

    async def list_for_user(self, user_id: int, limit: int = 10) -> List[RecentlyViewed]:
        result = await self.db.execute(
            select(RecentlyViewed)
            .where(RecentlyViewed.user_id == user_id)
            .order_by(desc(RecentlyViewed.viewed_at))
            .limit(limit)
        )
        return list(result.scalars().all())
