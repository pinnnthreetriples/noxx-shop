"""Category repository - SQL operations only."""
from typing import List, Optional, Tuple
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.catalog.models import Category, CategoryTranslation, Product
from app.modules.admin_api.filters import AdminListFilters, apply_sort, count_total, search_ilike, apply_updates


class CategoryAdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list_with_filters(self, f: AdminListFilters) -> Tuple[List[Category], int]:
        stmt = select(Category)
        if f.q:
            # search matches translated titles too, not just the latin slug
            stmt = (
                stmt.outerjoin(CategoryTranslation, CategoryTranslation.category_id == Category.id)
                .where(search_ilike([Category.slug, CategoryTranslation.title], f.q))
                .distinct()
            )
        total = await count_total(self.db, stmt)
        stmt = apply_sort(stmt, Category, f.sort_field, f.desc_order)
        stmt = stmt.offset(f.offset).limit(f.limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total
    
    async def get_by_id(self, id: int) -> Optional[Category]:
        result = await self.db.execute(select(Category).where(Category.id == id))
        return result.scalars().first()
    
    async def create(self, **fields) -> Category:
        category = Category(**fields)
        self.db.add(category)
        await self.db.flush()
        return category
    
    async def update(self, category: Category, fields: dict) -> Category:
        apply_updates(category, fields)
        return category
    
    async def hard_delete(self, category: Category):
        # A category is just a shelf, not order history: really remove it.
        # Detach its products (category_id is nullable), drop translations, then the row.
        await self.db.execute(
            update(Product).where(Product.category_id == category.id).values(category_id=None)
        )
        await self.db.execute(delete(CategoryTranslation).where(CategoryTranslation.category_id == category.id))
        await self.db.execute(delete(Category).where(Category.id == category.id))
    
    # Translation helpers
    async def upsert_translation(self, category_id: int, language: str, title: str):
        result = await self.db.execute(
            select(CategoryTranslation).where(
                CategoryTranslation.category_id == category_id,
                CategoryTranslation.language_code == language,
            )
        )
        tr = result.scalars().first()
        if tr:
            tr.title = title
        else:
            self.db.add(CategoryTranslation(
                category_id=category_id,
                language_code=language,
                title=title,
            ))