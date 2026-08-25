"""Admins router - thin API layer."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.auth import get_current_admin
from app.modules.admin.models import Admin
from app.modules.admin_api.admins.schemas import AdminCreate, AdminListResponse, AdminOut, AdminUpdate
from app.modules.admin_api.admins.service import AdminAdminService

router = APIRouter(tags=["admin-admins"])


@router.get("/admins", response_model=AdminListResponse)
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


@router.get("/admins/{id}", response_model=AdminOut)
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


@router.post("/admins", response_model=AdminOut)
async def create_admin(
    payload: AdminCreate,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminAdminService(db)
    return await service.create(admin, payload.model_dump())


@router.put("/admins/{id}", response_model=AdminOut)
async def update_admin(
    id: int,
    payload: AdminUpdate,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminAdminService(db)
    # react-admin PUTs the whole record back; AdminUpdate drops everything but
    # name/role/active, so the 2FA columns and token_version can't be rewritten
    # through the admin form - disabling 2FA stays an OTP-gated /auth/2fa call.
    a = await service.update(admin, id, payload.model_dump(exclude_unset=True, exclude_none=True))
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