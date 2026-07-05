"""Settings use-case service."""
from __future__ import annotations
from typing import List
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.settings.repository import SettingsRepository
from app.modules.admin.models import Setting, AdminLog
from app.modules.admin.schemas import SettingsOut, LanguageOut


LANGUAGE_NAMES = {
    "en": "English", "ru": "Russian", "de": "German", "el": "Greek",
    "ro": "Romanian", "bg": "Bulgarian", "mo": "Moldavian",
    "sr": "Serbian", "tr": "Turkish",
}


class SettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SettingsRepository(db)

    async def get_settings(self) -> Setting:
        s = await self.repo.get()
        if not s:
            raise HTTPException(status_code=404, detail="Settings not found")
        return s

    async def list_languages(self) -> List[LanguageOut]:
        return [LanguageOut(code=k, name=v) for k, v in LANGUAGE_NAMES.items()]

    async def update_settings(self, admin, payload: dict) -> Setting:
        s = await self.repo.get_or_create()
        await self.repo.update(payload)
        self.db.add(AdminLog(
            admin_id=admin.id,
            action="update_settings",
            entity_type="settings",
            entity_id=s.id,
        ))
        await self.db.commit()
        return s