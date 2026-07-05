"""Category repository - SQL operations only."""
from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.catalog.models import Category, CategoryTranslation
from app.modules.admin_api.filters import AdminListFilters, apply_sort, count_total, search_ilike, apply_updates


class CategoryAdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list_with_filters(self, f: AdminListFilters) -> Tuple[List[Category], int]:
        stmt = select(Category)
        if f.q:
            stmt = stmt.where(search_ilike([Category.slug], f.q))
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
    
    async def soft_delete(self, category: Category):
        category.status = "deleted"
    
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