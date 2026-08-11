from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import ColumnElement, select, desc, func, or_, and_, update
from app.modules.admin.models import Setting
from app.modules.catalog.models import Product, Category, Tag, ProductTag, ProductTranslation
from app.modules.favorites.models import RecentlyViewed
from app.modules.catalog.models import ProductStatus

# The one fake product the storefront shows while demo mode is on. It lives as a
# normal row with status `hidden`, so with demo mode off every existing query
# skips it — including checkout, which is why it can never be bought.
DEMO_PRODUCT_SLUG = "demo-preview"

# Only en/ru: every other language falls back to en in the catalog service.
_DEMO_TRANSLATIONS = {
    "en": (
        "Demo product",
        "A demonstration item shown while the shop is in demo mode. "
        "It is not for sale — the real catalog is hidden.",
    ),
    "ru": (
        "Демонстрационный товар",
        "Демонстрационная позиция, которая показывается, пока магазин в демо-режиме. "
        "Она не продаётся — реальный каталог скрыт.",
    ),
}


async def storefront_filter(db: AsyncSession) -> ColumnElement[bool]:
    """What the storefront may show: in demo mode only the demo product, otherwise
    every published product. Single source of truth so the catalog list and the
    product page can't disagree."""
    row = (await db.execute(select(Setting.demo_mode_enabled).limit(1))).first()
    if row and row[0]:
        return Product.slug == DEMO_PRODUCT_SLUG
    return Product.status == ProductStatus.published


async def ensure_demo_product(db: AsyncSession) -> Product:
    """Create the demo product, or revive it if it was soft-deleted. Idempotent:
    called every time demo mode is switched on, which is what heals it after a
    full data reset wiped the products table."""
    product = (await db.execute(
        select(Product).where(Product.slug == DEMO_PRODUCT_SLUG)
    )).scalars().first()
    if product is not None:
        if product.status == ProductStatus.deleted:
            product.status = ProductStatus.hidden
        return product
    product = Product(
        slug=DEMO_PRODUCT_SLUG,
        status=ProductStatus.hidden,
        price_stars=250,
        display_views=1284,
        display_purchases=317,
    )
    db.add(product)
    await db.flush()
    for lang, (title, description) in _DEMO_TRANSLATIONS.items():
        db.add(ProductTranslation(
            product_id=product.id, language_code=lang, title=title, description=description,
        ))
    return product


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_published(
        self,
        category_id: Optional[int] = None,
        tag_id: Optional[int] = None,
        search: Optional[str] = None,
        sort: str = "trend_score",
        limit: int = 20,
        offset: int = 0,
        premium_only: bool = False,
        language_code: str = "en",
    ) -> Tuple[List[Product], int]:
        stmt = select(Product).where(await storefront_filter(self.db))

        if category_id:
            stmt = stmt.where(Product.category_id == category_id)
        if premium_only:
            stmt = stmt.where(Product.is_premium.is_(True))
        if tag_id:
            stmt = stmt.join(ProductTag).where(ProductTag.tag_id == tag_id)
        if search:
            like = f"%{search}%"
            sub = select(ProductTranslation.product_id).where(
                and_(
                    ProductTranslation.language_code == language_code,
                    or_(
                        ProductTranslation.title.ilike(like),
                        ProductTranslation.description.ilike(like),
                    ),
                )
            ).scalar_subquery()
            stmt = stmt.where(Product.id.in_(sub))
        
        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0
        
        # Apply sorting
        sort_col = getattr(Product, sort, Product.trend_score)
        stmt = stmt.order_by(desc(sort_col)).limit(limit).offset(offset)
        
        result = await self.db.execute(stmt)
        products = result.scalars().all()
        return list(products), total

    async def get_by_slug(self, slug: str) -> Optional[Product]:
        result = await self.db.execute(
            select(Product).where(Product.slug == slug, await storefront_filter(self.db))
        )
        return result.scalars().first()

    async def get_by_id(self, product_id: int) -> Optional[Product]:
        result = await self.db.execute(select(Product).where(Product.id == product_id))
        return result.scalars().first()

    async def increment_purchases(self, product_id: int, quantity: int = 1) -> None:
        await self.db.execute(
            update(Product).where(Product.id == product_id).values(real_purchases=Product.real_purchases + quantity)
        )

    async def increment_views(self, product_id: int) -> None:
        await self.db.execute(
            update(Product).where(Product.id == product_id).values(real_views=Product.real_views + 1)
        )

    async def bulk_increment_purchases(self, items: List[Tuple[int, int]]) -> None:
        """Bump real_purchases for several (product_id, quantity) pairs at once
        (order fulfillment). Small N per order — one UPDATE each is fine."""
        for product_id, quantity in items:
            await self.increment_purchases(product_id, quantity)

    async def list_published_by_ids(self, ids: List[int]) -> List[Product]:
        if not ids:
            return []
        result = await self.db.execute(
            select(Product).where(Product.id.in_(ids), Product.status == ProductStatus.published)
        )
        return list(result.scalars().all())

    async def add_recently_viewed(self, user_id: int, product_id: int) -> None:
        from datetime import datetime, timezone
        result = await self.db.execute(
            select(RecentlyViewed).where(RecentlyViewed.user_id == user_id, RecentlyViewed.product_id == product_id)
        )
        rv = result.scalars().first()
        if rv:
            rv.viewed_at = datetime.now(timezone.utc)
        else:
            self.db.add(RecentlyViewed(user_id=user_id, product_id=product_id))


class CategoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self) -> List[Category]:
        result = await self.db.execute(select(Category))
        return list(result.scalars().all())

    async def get_by_id(self, category_id: int) -> Optional[Category]:
        result = await self.db.execute(select(Category).where(Category.id == category_id))
        return result.scalars().first()


class TagRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self) -> List[Tag]:
        result = await self.db.execute(select(Tag))
        return list(result.scalars().all())

    async def get_by_id(self, tag_id: int) -> Optional[Tag]:
        result = await self.db.execute(select(Tag).where(Tag.id == tag_id))
        return result.scalars().first()
