"""Admin authentication service."""
import jwt as pyjwt
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.modules.admin_api.auth.repository import AdminRepository
from app.modules.admin.models import Admin


class AdminAuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AdminRepository(db)

    async def login(self, email: str, password: str) -> Optional[str]:
        """Authenticate admin and return JWT token."""
        if email == settings.admin_default_email and password == settings.admin_default_password:
            admin = await self.repo.get_by_telegram_id(int(settings.admin_default_telegram_id or 0))
            if not admin:
                admin = await self.repo.create(
                    telegram_id=int(settings.admin_default_telegram_id or 0),
                    name="Owner",
                    role="owner",
                )
                await self.db.commit()
                await self.db.refresh(admin)
            token = pyjwt.encode(
                {"sub": str(admin.id), "exp": datetime.now(timezone.utc) + timedelta(days=7)},
                settings.admin_jwt_secret or settings.jwt_secret,
                algorithm="HS256",
            )
            return token
        return None

    async def me(self, admin: Admin) -> Admin:
        """Return current admin info."""
        return admin