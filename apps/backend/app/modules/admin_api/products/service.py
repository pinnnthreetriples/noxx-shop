"""Product admin service - use-case logic."""
from typing import Optional, Dict, Any
from sqlalchemy import inspect as sa_inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.admin.models import AdminLog
from app.modules.catalog.models import Product, ProductTag, ProductTranslation
from app.modules.admin_api.products.repository import ProductAdminRepository
from app.modules.admin_api.filters import LANGUAGE_CODES, AdminListFilters


class ProductAdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ProductAdminRepository(db)
    
    async def list(self, q: Optional[str], status: Optional[str], sort_field: str, order: str, start: int, end: int) -> Dict[str, Any]:
        f = AdminListFilters(q=q, status=status, sort_field=sort_field, order=order, start=start, end=end)
        items, total = await self.repo.list_with_filters(f)
        return {"data": items, "total": total}
    
    async def get(self, id: int) -> Optional[Dict[str, Any]]:
        product = await self.repo.get_by_id(id)
        if not product:
            return None
        return await self._serialize(product)

    async def _serialize(self, product: Product) -> Dict[str, Any]:
        """Flatten the ORM row + translations (title_<lang>) + tag_ids for the
        react-admin edit form — otherwise translations are invisible when editing."""
        data = {c.key: getattr(product, c.key) for c in sa_inspect(product).mapper.column_attrs}
        trs = await self.db.execute(
            select(ProductTranslation).where(ProductTranslation.product_id == product.id)
        )
        for tr in trs.scalars():
            data[f"title_{tr.language_code}"] = tr.title
            data[f"description_{tr.language_code}"] = tr.description
        tag_rows = await self.db.execute(
            select(ProductTag.tag_id).where(ProductTag.product_id == product.id)
        )
        data["tag_ids"] = [r[0] for r in tag_rows]
        return data
    
    async def create(self, admin, payload: dict) -> Product:
        product = await self.repo.create(
            slug=payload.get("slug", ""),
            status=payload.get("status", "draft"),
            price_stars=payload.get("price_stars", 0),
            usd_price_mode=payload.get("usd_price_mode", "auto"),
            usd_price_manual=payload.get("usd_price_manual"),
            category_id=payload.get("category_id"),
            cover_url=payload.get("cover_url"),
            preview_video_url=payload.get("preview_video_url"),
            google_drive_link=payload.get("google_drive_link"),
            google_drive_file_id=payload.get("google_drive_file_id"),
            trend_score=payload.get("trend_score", 0),
            is_premium=payload.get("is_premium", False),
            available_for_subscription=payload.get("available_for_subscription", False),
        )
        for lang in LANGUAGE_CODES:
            title = payload.get(f"title_{lang}")
            if title:
                await self.repo.upsert_translation(product.id, lang, title, payload.get(f"description_{lang}"))
        for tid in payload.get("tag_ids", []):
            await self.repo.add_tag(product.id, tid)
        self.db.add(AdminLog(admin_id=admin.id, action="create_product", entity_type="product", entity_id=product.id))
        await self.db.commit()
        await self.db.refresh(product)
        return await self._serialize(product)
    
    async def update(self, admin, id: int, payload: dict) -> Optional[Product]:
        product = await self.repo.get_by_id(id)
        if not product:
            return None
        await self.repo.update(product, {k: v for k, v in payload.items() if not k.startswith(("title_", "description_")) and hasattr(product, k) and k != "id"})
        for lang in LANGUAGE_CODES:
            title = payload.get(f"title_{lang}")
            if title:
                await self.repo.upsert_translation(id, lang, title, payload.get(f"description_{lang}"))
        if "tag_ids" in payload:
            await self.repo.clear_tags(id)
            for tid in payload["tag_ids"]:
                await self.repo.add_tag(id, tid)
        self.db.add(AdminLog(admin_id=admin.id, action="update_product", entity_type="product", entity_id=product.id))
        await self.db.commit()
        await self.db.refresh(product)
        return await self._serialize(product)
    
    async def soft_delete(self, admin, id: int) -> Optional[Product]:
        product = await self.repo.get_by_id(id)
        if not product:
            return None
        await self.repo.soft_delete(product)
        self.db.add(AdminLog(admin_id=admin.id, action="soft_delete_product", entity_type="product", entity_id=product.id))
        await self.db.commit()
        return product