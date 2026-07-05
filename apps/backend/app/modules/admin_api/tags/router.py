"""Tags router - thin API layer."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.auth import get_current_admin
from app.modules.admin.models import Admin
from app.modules.admin_api.tags.service import TagAdminService

router = APIRouter(tags=["admin-tags"])


@router.get("/tags")
async def list_tags(
    q: Optional[str] = None,
    _sort: str = "id",
    _order: str = "ASC",
    _start: int = 0,
    _end: int = 25,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = TagAdminService(db)
    return await service.list(q=q, sort_field=_sort, order=_order, start=_start, end=_end)


@router.get("/tags/{id}")
async def get_tag(
    id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = TagAdminService(db)
    tag = await service.get(id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@router.post("/tags")
async def create_tag(
    payload: dict,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = TagAdminService(db)
    return await service.create(admin, payload)


@router.put("/tags/{id}")
async def update_tag(
    id: int,
    payload: dict,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = TagAdminService(db)
    tag = await service.update(admin, id, payload)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@router.delete("/tags/{id}")
async def delete_tag(
    id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = TagAdminService(db)
    tag = await service.delete(admin, id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"deleted": True}