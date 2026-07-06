"""Product repository - SQL operations only."""
from typing import List, Optional, Tuple
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.catalog.models import Product, ProductStatus, ProductTranslation, ProductTag
from app.modules.admin_api.filters import AdminListFilters, apply_sort, count_total, search_ilike, apply_updates


class ProductAdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list_with_filters(self, f: AdminListFilters) -> Tuple[List[Product], int]:
        stmt = select(Product)
        if f.q:
            stmt = stmt.where(search_ilike([Product.slug, Product.google_drive_link], f.q))
        if f.status:
            stmt = stmt.where(Product.status == f.status)
        else:
            # soft-deleted products are hidden unless explicitly filtered for
            stmt = stmt.where(Product.status != ProductStatus.deleted)
        total = await count_total(self.db, stmt)
        stmt = apply_sort(stmt, Product, f.sort_field, f.desc_order)
        stmt = stmt.offset(f.offset).limit(f.limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total
    
    async def get_by_id(self, id: int) -> Optional[Product]:
        result = await self.db.execute(select(Product).where(Product.id == id))
        return result.scalars().first()
    
    async def create(self, **fields) -> Product:
        product = Product(**fields)
        self.db.add(product)
        await self.db.flush()
        return product
    
    async def update(self, product: Product, fields: dict) -> Product:
        apply_updates(product, fields)
        return product
    
    async def soft_delete(self, product: Product):
        product.status = "deleted"
    
    # Translation helpers
    async def upsert_translation(self, product_id: int, language: str, title: str, description: Optional[str]):
        result = await self.db.execute(
            select(ProductTranslation).where(
                ProductTranslation.product_id == product_id,
                ProductTranslation.language_code == language,
            )
        )
        tr = result.scalars().first()
        if tr:
            tr.title = title
            tr.description = description
        else:
            self.db.add(ProductTranslation(
                product_id=product_id,
                language_code=language,
                title=title,
                description=description,
            ))
    
    async def clear_tags(self, product_id: int):
        await self.db.execute(delete(ProductTag).where(ProductTag.product_id == product_id))
    
    async def add_tag(self, product_id: int, tag_id: int):
        self.db.add(ProductTag(product_id=product_id, tag_id=tag_id))