"""Category admin service - use-case logic."""
from typing import Optional, Dict, Any
from sqlalchemy import inspect as sa_inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.catalog.models import Category, CategoryTranslation
from app.modules.admin_api.categories.repository import CategoryAdminRepository
from app.modules.admin_api.filters import LANGUAGE_CODES, AdminListFilters


class CategoryAdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CategoryAdminRepository(db)
    
    async def list(self, q: Optional[str], sort_field: str, order: str, start: int, end: int) -> Dict[str, Any]:
        f = AdminListFilters(q=q, sort_field=sort_field, order=order, start=start, end=end)
        items, total = await self.repo.list_with_filters(f)
        return {"data": items, "total": total}
    
    async def get(self, id: int) -> Optional[Dict[str, Any]]:
        cat = await self.repo.get_by_id(id)
        if not cat:
            return None
        return await self._serialize(cat)

    async def _serialize(self, cat: Category) -> Dict[str, Any]:
        """Flatten row + title_<lang> so the edit form shows existing translations."""
        data = {c.key: getattr(cat, c.key) for c in sa_inspect(cat).mapper.column_attrs}
        trs = await self.db.execute(
            select(CategoryTranslation).where(CategoryTranslation.category_id == cat.id)
        )
        for tr in trs.scalars():
            data[f"title_{tr.language_code}"] = tr.title
        return data
    
    async def create(self, admin, payload: dict) -> Category:
        cat = await self.repo.create(
            slug=payload.get("slug", ""),
            status=payload.get("status", "published"),
        )
        for lang in LANGUAGE_CODES:
            title = payload.get(f"title_{lang}")
            if title:
                await self.repo.upsert_translation(cat.id, lang, title)
        await self.db.commit()
        await self.db.refresh(cat)
        return await self._serialize(cat)
    
    async def update(self, admin, id: int, payload: dict) -> Optional[Category]:
        cat = await self.repo.get_by_id(id)
        if not cat:
            return None
        await self.repo.update(cat, {k: v for k, v in payload.items() if not k.startswith("title_") and hasattr(cat, k) and k != "id"})
        for lang in LANGUAGE_CODES:
            title = payload.get(f"title_{lang}")
            if title:
                await self.repo.upsert_translation(id, lang, title)
        await self.db.commit()
        await self.db.refresh(cat)
        return await self._serialize(cat)
    
    async def soft_delete(self, admin, id: int) -> Optional[Category]:
        cat = await self.repo.get_by_id(id)
        if not cat:
            return None
        await self.repo.soft_delete(cat)
        await self.db.commit()
        return cat