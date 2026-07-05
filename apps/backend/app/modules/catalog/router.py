from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.auth import get_current_user
from app.modules.catalog import service
from app.modules.catalog.schemas import ProductListItem, ProductDetail
from app.modules.favorites.service import FavoriteService
from app.models import User

router = APIRouter(prefix="")


@router.get("/products", response_model=List[ProductListItem])
async def list_products(
    category_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    search: Optional[str] = None,
    sort: str = "trend_score",
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    premium_only: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_products(
        db, user, category_id=category_id, tag_id=tag_id, search=search,
        sort=sort, limit=limit, offset=offset, premium_only=premium_only,
    )


@router.get("/products/{slug}", response_model=ProductDetail)
async def get_product(slug: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await service.get_product_by_slug(db, user, slug)


@router.post("/products/{product_id}/view")
async def record_view(product_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    fav_service = FavoriteService(db)
    await fav_service.record_view(user, product_id)
    return {"ok": True}
