"""Settings repository - SQL operations only."""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.admin_api.filters import apply_updates
from app.modules.admin.models import Setting


class SettingsAdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get(self) -> Optional[Setting]:
        result = await self.db.execute(select(Setting))
        return result.scalars().first()
    
    async def get_or_create(self) -> Setting:
        setting = await self.get()
        if not setting:
            setting = Setting()
            self.db.add(setting)
            await self.db.flush()
        return setting
    
    async def update(self, setting: Setting, fields: dict) -> Setting:
        apply_updates(setting, fields)
        return setting