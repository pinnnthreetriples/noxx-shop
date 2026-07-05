"""Tag repository - SQL operations only."""
from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.catalog.models import Tag, TagTranslation
from app.modules.admin_api.filters import AdminListFilters, apply_sort, count_total, search_ilike, apply_updates


class TagAdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list_with_filters(self, f: AdminListFilters) -> Tuple[List[Tag], int]:
        stmt = select(Tag)
        if f.q:
            stmt = stmt.where(search_ilike([Tag.slug], f.q))
        total = await count_total(self.db, stmt)
        stmt = apply_sort(stmt, Tag, f.sort_field, f.desc_order)
        stmt = stmt.offset(f.offset).limit(f.limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total
    
    async def get_by_id(self, id: int) -> Optional[Tag]:
        result = await self.db.execute(select(Tag).where(Tag.id == id))
        return result.scalars().first()
    
    async def create(self, **fields) -> Tag:
        tag = Tag(**fields)
        self.db.add(tag)
        await self.db.flush()
        return tag
    
    async def update(self, tag: Tag, fields: dict) -> Tag:
        apply_updates(tag, fields)
        return tag
    
    async def delete(self, tag: Tag):
        await self.db.delete(tag)
    
    # Translation helpers
    async def upsert_translation(self, tag_id: int, language: str, title: str):
        result = await self.db.execute(
            select(TagTranslation).where(
                TagTranslation.tag_id == tag_id,
                TagTranslation.language_code == language,
            )
        )
        tr = result.scalars().first()
        if tr:
            tr.title = title
        else:
            self.db.add(TagTranslation(
                tag_id=tag_id,
                language_code=language,
                title=title,
            ))