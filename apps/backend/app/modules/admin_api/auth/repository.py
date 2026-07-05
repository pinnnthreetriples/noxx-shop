"""Admin repository - re-export from admin module."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.admin.models import Admin


class AdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[Admin]:
        result = await self.db.execute(select(Admin).where(Admin.telegram_id == telegram_id))
        return result.scalars().first()

    async def get_by_id(self, admin_id: int) -> Optional[Admin]:
        result = await self.db.execute(select(Admin).where(Admin.id == admin_id, Admin.active.is_(True)))
        return result.scalars().first()

    async def create(self, telegram_id: int, name: str, role: str = "owner") -> Admin:
        admin = Admin(telegram_id=telegram_id, name=name, role=role, active=True)
        self.db.add(admin)
        await self.db.flush()
        return admin