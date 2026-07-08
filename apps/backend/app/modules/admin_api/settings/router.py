"""Settings router - thin API layer."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.auth import get_current_admin
from app.modules.admin.models import Admin
from app.modules.admin_api.settings.service import SettingsAdminService

router = APIRouter(tags=["admin-settings"])


@router.get("/settings")
async def get_settings(
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = SettingsAdminService(db)
    return await service.get()


@router.post("/settings/reset")
async def reset_all_data(
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = SettingsAdminService(db)
    return await service.reset_all(admin)


@router.put("/settings")
async def update_settings(
    payload: dict,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = SettingsAdminService(db)
    return await service.update(admin, payload)


# react-admin getOne/update address the singleton as /settings/{id}
@router.get("/settings/{setting_id}")
async def get_settings_by_id(
    setting_id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await get_settings(admin, db)


@router.put("/settings/{setting_id}")
async def update_settings_by_id(
    setting_id: int,
    payload: dict,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await update_settings(payload, admin, db)