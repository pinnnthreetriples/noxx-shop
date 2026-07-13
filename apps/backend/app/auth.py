from datetime import datetime, timezone
from typing import Optional
from fastapi import Request, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_user_from_init_data, decode_admin_token
from app.models import User, Admin
from app.modules.catalog.service import SUPPORTED_LANGUAGES
from app.modules.users.repository import UserRepository

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = None
    if credentials and credentials.scheme == "Bearer":
        token = credentials.credentials
    if not token:
        token = request.headers.get("x-telegram-init-data")
    if not token:
        raise HTTPException(status_code=401, detail="Missing Telegram initData")

    try:
        user_info = get_user_from_init_data(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e) or "Invalid Telegram initData") from None
    telegram_id = user_info.get("id")
    if not telegram_id:
        raise HTTPException(status_code=401, detail="Invalid user data")

    user = await UserRepository(db).get_or_create_by_telegram_id(
        telegram_id,
        dict(
            username=user_info.get("username"),
            first_name=user_info.get("first_name"),
            last_name=user_info.get("last_name"),
            language_code=user_info.get("language_code"),
            selected_language=user_info.get("language_code"),
            started_bot_at=datetime.now(timezone.utc),
        ),
    )

    if user.is_blocked:
        raise HTTPException(status_code=403, detail="User is blocked")

    hdr = request.headers.get("x-lang")
    if hdr in SUPPORTED_LANGUAGES and hdr != user.selected_language:
        user.selected_language = hdr

    user.last_seen_at = datetime.now(timezone.utc)
    await db.commit()
    return user


async def get_current_admin(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Admin:
    token = None
    if credentials and credentials.scheme == "Bearer":
        token = credentials.credentials
    if not token:
        token = request.headers.get("x-admin-token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing admin token")
    try:
        payload = decode_admin_token(token)
        admin_id = payload.get("sub")
        if not admin_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token") from None
    result = await db.execute(select(Admin).where(Admin.id == int(admin_id), Admin.active.is_(True)))
    admin = result.scalars().first()
    if not admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    # Pre-"ver" tokens count as version 0 and stay valid until the version is bumped.
    if payload.get("ver", 0) != (admin.token_version or 0):
        raise HTTPException(status_code=401, detail="Token revoked")
    if (
        settings.admin_2fa_required
        and not admin.totp_enabled
        and not request.url.path.startswith("/auth/2fa")
    ):
        raise HTTPException(status_code=403, detail={"code": "totp_setup_required"})
    return admin
