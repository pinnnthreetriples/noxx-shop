from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.modules.users.models import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def get_by_id_for_update(self, user_id: int) -> Optional[User]:
        """SELECT ... FOR UPDATE: serializes concurrent premium_until writes for
        one user. populate_existing so a session that already loaded this user
        (the Stars/polling paths do) sees the row as re-read under the lock,
        not the stale identity-map copy."""
        result = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return result.scalars().first()

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalars().first()

    async def create(self, **fields) -> User:
        user = User(**fields)
        self.db.add(user)
        await self.db.flush()
        return user

    async def upsert_by_telegram_id(self, telegram_id: int, defaults: dict) -> User:
        result = await self.db.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalars().first()
        if user:
            for key, value in defaults.items():
                setattr(user, key, value)
        else:
            user = User(telegram_id=telegram_id, **defaults)
            self.db.add(user)
        await self.db.flush()
        return user

    async def update(self, user_id: int, fields: dict) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if user:
            for key, value in fields.items():
                setattr(user, key, value)
            await self.db.flush()
        return user

    async def list_with_search(
        self,
        q: Optional[str] = None,
        sort: str = "created_at",
        order: str = "desc",
        start: int = 0,
        end: int = 50,
    ) -> Tuple[List[User], int]:
        stmt = select(User)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                or_(
                    User.username.ilike(like),
                    User.first_name.ilike(like),
                    User.last_name.ilike(like),
                    User.telegram_id.cast(str).ilike(like),
                )
            )
        
        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0
        
        # Apply sort
        sort_col = getattr(User, sort, User.created_at)
        if order == "desc":
            stmt = stmt.order_by(sort_col.desc())
        else:
            stmt = stmt.order_by(sort_col.asc())
        
        stmt = stmt.limit(end - start).offset(start)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def set_blocked(self, user_id: int, blocked: bool) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if user:
            user.is_blocked = blocked
            await self.db.flush()
        return user

    async def list_for_notifications(self) -> List[User]:
        # started_bot_at gates users who only ever used the mini-app and have no
        # private chat with the bot — sending there fails with 403/chat not found.
        result = await self.db.execute(
            select(User).where(
                User.is_blocked.is_(False),
                User.notifications_enabled.is_(True),
                User.started_bot_at.isnot(None),
            )
        )
        return list(result.scalars().all())

    async def set_notifications_enabled(self, user_id: int, enabled: bool) -> Optional[User]:
        return await self.update(user_id, {"notifications_enabled": enabled})

    async def set_language(self, user_id: int, language: str) -> Optional[User]:
        return await self.update(user_id, {"selected_language": language})

    async def set_age_confirmed(self, user_id: int) -> Optional[User]:
        from datetime import datetime, timezone
        return await self.update(user_id, {"age_confirmed": True, "age_confirmed_at": datetime.now(timezone.utc)})
