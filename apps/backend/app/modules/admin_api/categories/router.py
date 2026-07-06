"""Categories router - thin API layer."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.auth import get_current_admin
from app.modules.admin.models import Admin
from app.modules.admin_api.categories.service import CategoryAdminService

router = APIRouter(tags=["admin-categories"])


@router.get("/categories")
async def list_categories(
    q: Optional[str] = None,
    _sort: str = "id",
    _order: str = "ASC",
    _start: int = 0,
    _end: int = 25,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = CategoryAdminService(db)
    return await service.list(q=q, sort_field=_sort, order=_order, start=_start, end=_end)


@router.get("/categories/{id}")
async def get_category(
    id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = CategoryAdminService(db)
    cat = await service.get(id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


@router.post("/categories")
async def create_category(
    payload: dict,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = CategoryAdminService(db)
    return await service.create(admin, payload)


@router.put("/categories/{id}")
async def update_category(
    id: int,
    payload: dict,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = CategoryAdminService(db)
    cat = await service.update(admin, id, payload)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


@router.delete("/categories/{id}")
async def delete_category(
    id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = CategoryAdminService(db)
    deleted = await service.delete(admin, id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"id": id}