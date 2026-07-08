"""Settings admin service - use-case logic."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings as config
from app.modules.admin.models import AdminLog, Setting
from app.modules.admin_api.settings.repository import SettingsAdminRepository


class SettingsAdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SettingsAdminRepository(db)

    @staticmethod
    def _with_rate(setting: Setting) -> Setting:
        # expose the built-in fallback rate (a constant, not a DB column) so the
        # admin form can preview USD prices even in "standard" mode
        setting.star_usd_rate = config.star_usd_rate
        return setting

    async def get(self) -> Setting:
        # self-healing singleton: a lost row (fresh DB, partial restore) must
        # not 404-loop the admin settings page — recreate it with defaults
        setting = await self.repo.get_or_create()
        await self.db.commit()
        await self.db.refresh(setting)
        return self._with_rate(setting)

    async def update(self, admin, payload: dict) -> Setting:
        setting = await self.repo.get_or_create()
        await self.repo.update(setting, {k: v for k, v in payload.items() if hasattr(setting, k) and k != "id"})
        self.db.add(AdminLog(admin_id=admin.id, action="update_settings", entity_type="settings", entity_id=setting.id))
        await self.db.commit()
        await self.db.refresh(setting)
        return self._with_rate(setting)