import hmac
import hashlib
import json
import urllib.parse
import time
from datetime import datetime, timezone, timedelta

import jwt as pyjwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _parse_init_data(init_data: str) -> dict:
    result = {}
    for pair in init_data.split("&"):
        if "=" in pair:
            key, value = pair.split("=", 1)
            result[urllib.parse.unquote(key)] = urllib.parse.unquote(value)
    return result


def validate_init_data(init_data_raw: str) -> dict:
    parsed = _parse_init_data(init_data_raw)
    hash_value = parsed.pop("hash", None)
    if not hash_value:
        raise ValueError("Missing hash in initData")
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_hash, hash_value):
        raise ValueError("Invalid initData signature")
    auth_date = int(parsed.get("auth_date", 0))
    if time.time() - auth_date > settings.initdata_max_age_seconds:
        raise ValueError("initData expired")
    return parsed


def get_user_from_init_data(init_data: str) -> dict:
    parsed = validate_init_data(init_data)
    user_json = parsed.get("user")
    if not user_json:
        raise ValueError("Missing user in initData")
    return json.loads(user_json)


def create_admin_token(admin_id: int, hours: int = 12) -> str:
    return pyjwt.encode(
        {"sub": str(admin_id), "exp": datetime.now(timezone.utc) + timedelta(hours=hours)},
        settings.admin_jwt_secret or settings.jwt_secret,
        algorithm="HS256",
    )


def decode_admin_token(token: str) -> dict:
    return pyjwt.decode(token, settings.admin_jwt_secret or settings.jwt_secret, algorithms=["HS256"])


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)
