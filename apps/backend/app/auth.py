import hmac
import hashlib
import json
import urllib.parse
import time
import jwt as pyjwt
from datetime import datetime, timezone
from typing import Optional
from fastapi import Request, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.core.database import get_db
from app.models import User, Admin

security = HTTPBearer(auto_error=False)


def _parse_init_data(init_data: str) -> dict:
    result = {}
    for pair in init_data.split("&"):
        if "=" in pair:
            key, value = pair.split("=", 1)
            result[urllib.parse.unquote(key)] = urllib.parse.unquote(value)
    return result


def _validate_init_data(init_data_raw: str) -> dict:
    parsed = _parse_init_data(init_data_raw)
    hash_value = parsed.pop("hash", None)
    if not hash_value:
        raise HTTPException(status_code=401, detail="Missing hash in initData")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_hash, hash_value):
        raise HTTPException(status_code=401, detail="Invalid initData signature")

    auth_date = int(parsed.get("auth_date", 0))
    if time.time() - auth_date > settings.initdata_max_age_seconds:
        raise HTTPException(status_code=401, detail="initData expired")

    return parsed


def _get_user_from_init_data(init_data: str) -> dict:
    parsed = _validate_init_data(init_data)
    user_json = parsed.get("user")
    if not user_json:
        raise HTTPException(status_code=401, detail="Missing user in initData")
    return json.loads(user_json)


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

    user_info = _get_user_from_init_data(token)
    telegram_id = user_info.get("id")
    if not telegram_id:
        raise HTTPException(status_code=401, detail="Invalid user data")

    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalars().first()
    if not user:
        user = User(
            telegram_id=telegram_id,
            username=user_info.get("username"),
            first_name=user_info.get("first_name"),
            last_name=user_info.get("last_name"),
            language_code=user_info.get("language_code"),
            selected_language=user_info.get("language_code"),
            started_bot_at=datetime.now(timezone.utc),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    if user.is_blocked:
        raise HTTPException(status_code=403, detail="User is blocked")

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
        payload = pyjwt.decode(token, settings.admin_jwt_secret or settings.jwt_secret, algorithms=["HS256"])
        admin_id = payload.get("sub")
        if not admin_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(select(Admin).where(Admin.id == int(admin_id), Admin.active.is_(True)))
    admin = result.scalars().first()
    if not admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return admin
