"""Settings admin service - use-case logic."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.admin.models import AdminLog, Setting
from app.modules.admin_api.settings.repository import SettingsAdminRepository


class SettingsAdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SettingsAdminRepository(db)
    
    async def get(self) -> Optional[Setting]:
        return await self.repo.get()
    
    async def update(self, admin, payload: dict) -> Setting:
        setting = await self.repo.get_or_create()
        await self.repo.update(setting, {k: v for k, v in payload.items() if hasattr(setting, k) and k != "id"})
        self.db.add(AdminLog(admin_id=admin.id, action="update_settings", entity_type="settings", entity_id=setting.id))
        await self.db.commit()
        await self.db.refresh(setting)
        return setting