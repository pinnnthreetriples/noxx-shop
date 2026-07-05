"""AdminLogs router - thin API layer."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.auth import get_current_admin
from app.modules.admin.models import Admin
from app.modules.admin_api.admin_logs.service import AdminLogAdminService

router = APIRouter(tags=["admin-admin_logs"])


@router.get("/admin_logs")
async def list_admin_logs(
    _sort: str = "id",
    _order: str = "ASC",
    _start: int = 0,
    _end: int = 25,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminLogAdminService(db)
    return await service.list(sort_field=_sort, order=_order, start=_start, end=_end)


@router.get("/admin_logs/{id}")
async def get_admin_log(
    id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminLogAdminService(db)
    log = await service.get(id)
    if not log:
        raise HTTPException(status_code=404, detail="Admin log not found")
    return log