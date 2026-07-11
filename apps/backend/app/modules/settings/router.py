from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings as config
from app.core.database import get_db
from app.modules.admin.schemas import SettingsOut
from app.modules.admin.schemas import LanguageOut
from app.modules.pricing import effective_star_rate, gross_stars
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
    out = SettingsOut.model_validate(setting)
    out.star_usd_rate = effective_star_rate(
        setting.stars_to_usd_mode, setting.manual_stars_to_usd_rate, config.star_usd_rate
    )
    if setting.withdrawal_commission_enabled:
        # buyer-facing subscription prices carry the same commission gross-up as products
        pct = setting.withdrawal_commission_percent
        out.sub_price_week_stars = gross_stars(out.sub_price_week_stars, True, pct)
        out.sub_price_month_stars = gross_stars(out.sub_price_month_stars, True, pct)
        out.sub_price_year_stars = gross_stars(out.sub_price_year_stars, True, pct)
    return out


@router.get("/languages", response_model=List[LanguageOut])
async def get_languages():
    return [LanguageOut(code=k, name=v) for k, v in LANGUAGE_NAMES.items()]
