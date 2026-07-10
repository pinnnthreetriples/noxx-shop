"""Admin authentication service."""
import hashlib
import hmac
import json
from typing import Optional

import pyotp
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_password, create_admin_token
from app.core.totp_crypto import decrypt_secret
from app.modules.admin_api.auth.repository import AdminRepository
from app.modules.admin.models import Admin


def check_otp(admin: Admin, code: str) -> bool:
    """Accept a current TOTP code or a one-time backup code. A matched backup
    code is removed from admin.backup_codes — the caller must commit."""
    code = (code or "").strip()
    if admin.totp_secret and pyotp.TOTP(decrypt_secret(admin.totp_secret)).verify(code, valid_window=1):
        return True
    digest = hashlib.sha256(code.encode()).hexdigest()
    hashes = json.loads(admin.backup_codes or "[]")
    for h in hashes:
        if hmac.compare_digest(h, digest):
            hashes.remove(h)
            admin.backup_codes = json.dumps(hashes)
            return True
    return False


class AdminAuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AdminRepository(db)

    async def login(self, email: str, password: str, otp: Optional[str] = None) -> Optional[str]:
        """Authenticate admin and return JWT token."""
        if not hmac.compare_digest(email, settings.admin_default_email):
            return None
        if settings.admin_default_password_hash:
            if not verify_password(password, settings.admin_default_password_hash):
                return None
        elif settings.admin_default_password:
            if not hmac.compare_digest(password, settings.admin_default_password):
                return None
        else:
            return None
        admin = await self.repo.get_by_telegram_id(int(settings.admin_default_telegram_id or 0))
        if not admin:
            admin = await self.repo.create(
                telegram_id=int(settings.admin_default_telegram_id or 0),
                name="Owner",
                role="owner",
            )
            await self.db.commit()
            await self.db.refresh(admin)
        if admin.totp_enabled:
            if not otp:
                raise HTTPException(status_code=401, detail={"code": "totp_required"})
            if not check_otp(admin, otp):
                raise HTTPException(status_code=401, detail={"code": "totp_invalid"})
            await self.db.commit()  # persist a consumed backup code
        return create_admin_token(
            admin.id, hours=settings.admin_jwt_ttl_hours, version=admin.token_version or 0
        )

    async def me(self, admin: Admin) -> Admin:
        """Return current admin info."""
        return admin