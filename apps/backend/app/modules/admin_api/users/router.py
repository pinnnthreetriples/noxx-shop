"""Users router - thin API layer."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.auth import get_current_admin
from app.modules.admin.models import Admin
from app.modules.admin_api.users.service import UserAdminService

router = APIRouter(tags=["admin-users"])


@router.get("/users")
async def list_users(
    q: Optional[str] = None,
    status: Optional[str] = None,
    _sort: str = "id",
    _order: str = "ASC",
    _start: int = 0,
    _end: int = 25,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = UserAdminService(db)
    return await service.list(q=q, status=status, sort_field=_sort, order=_order, start=_start, end=_end)


@router.get("/users/{id}")
async def get_user(
    id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = UserAdminService(db)
    user = await service.get(id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/users/{id}")
async def update_user(
    id: int,
    payload: dict,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = UserAdminService(db)
    user = await service.update(admin, id, payload)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users/{id}/block")
async def block_user(
    id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = UserAdminService(db)
    user = await service.block(admin, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"blocked": True}


@router.post("/users/{id}/unblock")
async def unblock_user(
    id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = UserAdminService(db)
    user = await service.unblock(admin, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"unblocked": True}