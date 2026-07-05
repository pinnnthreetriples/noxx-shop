from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.admin.models import Setting


class SettingsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self) -> Optional[Setting]:
        result = await self.db.execute(select(Setting).order_by(Setting.id))
        return result.scalars().first()

    async def get_or_create(self) -> Setting:
        result = await self.db.execute(select(Setting).order_by(Setting.id))
        setting = result.scalars().first()
        if not setting:
            setting = Setting()
            self.db.add(setting)
            await self.db.flush()
        return setting

    async def update(self, fields: dict) -> Optional[Setting]:
        setting = await self.get_or_create()
        for key, value in fields.items():
            if hasattr(setting, key):
                setattr(setting, key, value)
        await self.db.flush()
        return setting
