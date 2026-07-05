"""PromoCodes router - thin API layer."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.auth import get_current_admin
from app.modules.admin.models import Admin
from app.modules.admin_api.promo_codes.service import PromoCodeAdminService

router = APIRouter(tags=["admin-promo_codes"])


@router.get("/promo_codes")
async def list_promo_codes(
    _sort: str = "id",
    _order: str = "ASC",
    _start: int = 0,
    _end: int = 25,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = PromoCodeAdminService(db)
    return await service.list(sort_field=_sort, order=_order, start=_start, end=_end)


@router.get("/promo_codes/{id}")
async def get_promo_code(
    id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = PromoCodeAdminService(db)
    pc = await service.get(id)
    if not pc:
        raise HTTPException(status_code=404, detail="Promo code not found")
    return pc


@router.post("/promo_codes")
async def create_promo_code(
    payload: dict,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = PromoCodeAdminService(db)
    return await service.create(admin, payload)


@router.put("/promo_codes/{id}")
async def update_promo_code(
    id: int,
    payload: dict,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = PromoCodeAdminService(db)
    pc = await service.update(admin, id, payload)
    if not pc:
        raise HTTPException(status_code=404, detail="Promo code not found")
    return pc


@router.delete("/promo_codes/{id}")
async def delete_promo_code(
    id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = PromoCodeAdminService(db)
    pc = await service.delete(admin, id)
    if not pc:
        raise HTTPException(status_code=404, detail="Promo code not found")
    return {"deleted": True}