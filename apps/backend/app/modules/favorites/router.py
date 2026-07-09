from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.exc import IntegrityError
from app.core.database import get_db
from app.auth import get_current_user
from app.modules.catalog.schemas import ProductListItem, FavoriteToggleOut
from app.models import Favorite, Product
from app.modules.catalog.service import _EAGER, _to_list_item, resolve_language

router = APIRouter(prefix="")


@router.get("/favorites", response_model=List[ProductListItem])
async def list_favorites(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    lang = resolve_language(user)
    result = await db.execute(
        select(Product)
        .options(*_EAGER)
        .join(Favorite)
        .where(Favorite.user_id == user.id, Product.status == "published")
        .order_by(desc(Favorite.created_at))
    )
    products = result.scalars().all()
    return [_to_list_item(p, lang) for p in products]


@router.post("/favorites/{product_id}", response_model=FavoriteToggleOut)
async def add_favorite(product_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Favorite).where(Favorite.user_id == user.id, Favorite.product_id == product_id))
    fav = result.scalars().first()
    if not fav:
        db.add(Favorite(user_id=user.id, product_id=product_id))
        try:
            await db.commit()
        except IntegrityError:
            # Concurrent double-tap already inserted it — that's fine, it's favorited.
            await db.rollback()
    return FavoriteToggleOut(is_favorite=True)


@router.delete("/favorites/{product_id}", response_model=FavoriteToggleOut)
async def remove_favorite(product_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Favorite).where(Favorite.user_id == user.id, Favorite.product_id == product_id))
    fav = result.scalars().first()
    if fav:
        await db.delete(fav)
        await db.commit()
    return FavoriteToggleOut(is_favorite=False)
