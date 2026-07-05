"""Notifications router - thin API layer."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.auth import get_current_admin
from app.modules.admin.models import Admin
from app.modules.admin_api.notifications.service import NotificationAdminService

router = APIRouter(tags=["admin-notifications"])


@router.get("/notifications")
async def list_notifications(
    _sort: str = "id",
    _order: str = "ASC",
    _start: int = 0,
    _end: int = 25,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationAdminService(db)
    return await service.list(sort_field=_sort, order=_order, start=_start, end=_end)


@router.get("/notifications/{id}")
async def get_notification(
    id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationAdminService(db)
    notif = await service.get(id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notif


@router.post("/notifications")
async def create_notification(
    payload: dict,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationAdminService(db)
    return await service.create(admin, payload)


@router.delete("/notifications/{id}")
async def delete_notification(
    id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationAdminService(db)
    notif = await service.delete(admin, id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"deleted": True}