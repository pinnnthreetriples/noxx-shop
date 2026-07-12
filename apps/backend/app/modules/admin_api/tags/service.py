"""Tag admin service - use-case logic."""
from typing import Optional, Dict, Any
from sqlalchemy import inspect as sa_inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.catalog.models import Tag, TagTranslation
from app.modules.admin_api.tags.repository import TagAdminRepository
from app.modules.admin_api.filters import LANGUAGE_CODES, AdminListFilters


class TagAdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TagAdminRepository(db)
    
    async def list(self, q: Optional[str], sort_field: str, order: str, start: int, end: int) -> Dict[str, Any]:
        f = AdminListFilters(q=q, sort_field=sort_field, order=order, start=start, end=end)
        items, total = await self.repo.list_with_filters(f)
        return {"data": items, "total": total}
    
    async def get(self, id: int) -> Optional[Dict[str, Any]]:
        tag = await self.repo.get_by_id(id)
        if not tag:
            return None
        return await self._serialize(tag)

    async def _serialize(self, tag: Tag) -> Dict[str, Any]:
        """Flatten row + title_<lang> so the edit form shows existing translations."""
        data = {c.key: getattr(tag, c.key) for c in sa_inspect(tag).mapper.column_attrs}
        trs = await self.db.execute(
            select(TagTranslation).where(TagTranslation.tag_id == tag.id)
        )
        for tr in trs.scalars():
            data[f"title_{tr.language_code}"] = tr.title
        return data
    
    async def create(self, admin, payload: dict) -> dict:
        tag = await self.repo.create(slug=payload.get("slug", ""))
        for lang in LANGUAGE_CODES:
            title = payload.get(f"title_{lang}")
            if title:
                await self.repo.upsert_translation(tag.id, lang, title)
        await self.db.commit()
        await self.db.refresh(tag)
        return await self._serialize(tag)
    
    async def update(self, admin, id: int, payload: dict) -> Optional[dict]:
        tag = await self.repo.get_by_id(id)
        if not tag:
            return None
        await self.repo.update(tag, {k: v for k, v in payload.items() if not k.startswith("title_") and hasattr(tag, k) and k != "id"})
        for lang in LANGUAGE_CODES:
            title = payload.get(f"title_{lang}")
            if title:
                await self.repo.upsert_translation(id, lang, title)
        await self.db.commit()
        await self.db.refresh(tag)
        return await self._serialize(tag)
    
    async def delete(self, admin, id: int) -> Optional[Tag]:
        tag = await self.repo.get_by_id(id)
        if not tag:
            return None
        await self.repo.delete(tag)
        await self.db.commit()
        return tag