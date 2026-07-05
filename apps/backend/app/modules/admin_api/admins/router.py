"""Admins router - thin API layer."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.auth import get_current_admin
from app.modules.admin.models import Admin
from app.modules.admin_api.admins.service import AdminAdminService

router = APIRouter(tags=["admin-admins"])


@router.get("/admins")
async def list_admins(
    _sort: str = "id",
    _order: str = "ASC",
    _start: int = 0,
    _end: int = 25,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminAdminService(db)
    return await service.list(sort_field=_sort, order=_order, start=_start, end=_end)


@router.get("/admins/{id}")
async def get_admin(
    id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminAdminService(db)
    a = await service.get(id)
    if not a:
        raise HTTPException(status_code=404, detail="Admin not found")
    return a


@router.post("/admins")
async def create_admin(
    payload: dict,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminAdminService(db)
    return await service.create(admin, payload)


@router.put("/admins/{id}")
async def update_admin(
    id: int,
    payload: dict,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminAdminService(db)
    a = await service.update(admin, id, payload)
    if not a:
        raise HTTPException(status_code=404, detail="Admin not found")
    return a


@router.delete("/admins/{id}")
async def delete_admin(
    id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminAdminService(db)
    a = await service.deactivate(admin, id)
    if not a:
        raise HTTPException(status_code=404, detail="Admin not found")
    return {"deleted": True}