from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.auth import get_current_user
from app.modules.users.schemas import ProfileOut, ProfileUpdateLanguage, ProfileUpdateNotifications, ProfileConfirmAge
from app.models import User
from datetime import datetime, timezone

router = APIRouter(prefix="")


@router.get("/profile", response_model=ProfileOut)
async def get_profile(user: User = Depends(get_current_user)):
    return ProfileOut(
        telegram_id=user.telegram_id, username=user.username,
        first_name=user.first_name, last_name=user.last_name,
        language_code=user.language_code, selected_language=user.selected_language,
        notifications_enabled=user.notifications_enabled, age_confirmed=user.age_confirmed,
        is_blocked=user.is_blocked,
        is_premium=bool(user.premium_until and user.premium_until > datetime.now(timezone.utc)),
        premium_until=user.premium_until,
    )


@router.post("/profile/language")
async def update_language(body: ProfileUpdateLanguage, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user.selected_language = body.language
    await db.commit()
    return {"language": user.selected_language}


@router.post("/profile/notifications")
async def update_notifications(body: ProfileUpdateNotifications, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user.notifications_enabled = body.enabled
    await db.commit()
    return {"notifications_enabled": user.notifications_enabled}


@router.post("/profile/confirm-age")
async def confirm_age(body: ProfileConfirmAge, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user.age_confirmed = body.confirmed
    user.age_confirmed_at = datetime.now(timezone.utc)
    await db.commit()
    return {"age_confirmed": user.age_confirmed}


@router.post("/auth/telegram")
async def auth_telegram(user: User = Depends(get_current_user)):
    return {"user_id": user.id, "telegram_id": user.telegram_id}
