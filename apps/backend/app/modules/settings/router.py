from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.modules.admin.schemas import SettingsOut
from app.modules.admin.schemas import LanguageOut
from app.models import Setting

router = APIRouter(prefix="")

LANGUAGE_NAMES = {
    "en": "English", "ru": "Russian", "de": "German", "el": "Greek",
    "ro": "Romanian", "bg": "Bulgarian", "mo": "Moldavian",
    "sr": "Serbian", "tr": "Turkish",
}


@router.get("/settings", response_model=SettingsOut)
async def get_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Setting).order_by(Setting.id))
    setting = result.scalars().first()
    if not setting:
        # self-healing singleton: recreate defaults instead of 404 — a lost
        # row (fresh DB, partial restore) must not degrade the whole app
        setting = Setting()
        db.add(setting)
        await db.commit()
        await db.refresh(setting)
    return setting


@router.get("/languages", response_model=List[LanguageOut])
async def get_languages():
    return [LanguageOut(code=k, name=v) for k, v in LANGUAGE_NAMES.items()]


@router.get("/health")
async def health():
    return {"status": "ok"}
