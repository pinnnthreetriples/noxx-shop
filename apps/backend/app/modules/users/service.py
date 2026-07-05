"""User use-case service."""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import ProfileOut


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserRepository(db)

    async def get_profile(self, user) -> ProfileOut:
        return ProfileOut(
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code,
            selected_language=user.selected_language,
            notifications_enabled=user.notifications_enabled,
            age_confirmed=user.age_confirmed,
            is_blocked=user.is_blocked,
        )

    async def update_language(self, user, language: str):
        await self.repo.set_language(user.id, language)
        await self.db.commit()
        return {"language": language}

    async def update_notifications(self, user, enabled: bool):
        await self.repo.set_notifications_enabled(user.id, enabled)
        await self.db.commit()
        return {"notifications_enabled": enabled}

    async def confirm_age(self, user, confirmed: bool):
        if confirmed:
            await self.repo.set_age_confirmed(user.id)
            await self.db.commit()
        return {"age_confirmed": confirmed}

    async def get_or_create_from_init_data(self, telegram_id: int, defaults: dict):
        return await self.repo.upsert_by_telegram_id(telegram_id, defaults)

    async def list_admin(self, q=None, sort="id", order="DESC", start=0, end=25):
        return await self.repo.list_with_search(q=q, sort=sort, order=order, start=start, end=end)