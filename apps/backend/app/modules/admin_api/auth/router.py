"""Admin auth router: login, me and 2FA endpoints."""
import hashlib
import json
import secrets

import pyotp
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.ratelimit import client_ip, too_many_attempts
from app.core.totp_crypto import encrypt_secret, decrypt_secret
from app.auth import get_current_admin
from app.modules.admin.models import Admin
from app.modules.admin_api.auth.service import AdminAuthService, check_otp
from app.modules.admin_api.auth.schemas import LoginResponse, AdminMeResponse

router = APIRouter(prefix="/auth", tags=["admin-auth"])


class TwoFACode(BaseModel):
    code: str


@router.post("/login", response_model=LoginResponse)
async def admin_login(request: Request, db: AsyncSession = Depends(get_db)):
    # Covers password and otp attempts alike: the counter is per-IP for the endpoint.
    if await too_many_attempts(f"admin-login:{client_ip(request)}", limit=10, window_seconds=300):
        raise HTTPException(status_code=429, detail="Too many login attempts, try again later")
    body = await request.json()
    email = body.get("email")
    password = body.get("password")
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")

    service = AdminAuthService(db)
    token = await service.login(email, password, otp=body.get("otp"))
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": token}


@router.get("/me", response_model=AdminMeResponse)
async def admin_me(admin: Admin = Depends(get_current_admin)):
    service = AdminAuthService(None)  # db not needed for me
    return await service.me(admin)


@router.get("/2fa/status")
async def twofa_status(admin: Admin = Depends(get_current_admin)):
    return {"enabled": bool(admin.totp_enabled), "required": settings.admin_2fa_required}


@router.post("/2fa/setup")
async def twofa_setup(
    admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
):
    secret = pyotp.random_base32()
    admin.totp_pending_secret = encrypt_secret(secret)
    await db.commit()
    label = settings.admin_default_email or admin.name or str(admin.telegram_id)
    # otpauth_uri is built from the raw secret: that's what the user scans.
    uri = pyotp.TOTP(secret).provisioning_uri(name=label, issuer_name="NoxX Admin")
    return {"secret": secret, "otpauth_uri": uri}


@router.post("/2fa/enable")
async def twofa_enable(
    body: TwoFACode,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    if not admin.totp_pending_secret:
        raise HTTPException(status_code=400, detail="Run /auth/2fa/setup first")
    pending = decrypt_secret(admin.totp_pending_secret)
    if not pyotp.TOTP(pending).verify(body.code.strip(), valid_window=1):
        raise HTTPException(status_code=401, detail={"code": "totp_invalid"})
    backup_codes = [secrets.token_hex(8) for _ in range(10)]
    admin.totp_secret = admin.totp_pending_secret
    admin.totp_pending_secret = None
    admin.totp_enabled = True
    admin.backup_codes = json.dumps(
        [hashlib.sha256(c.encode()).hexdigest() for c in backup_codes]
    )
    # token_version deliberately NOT bumped: the session that just enabled 2FA
    # keeps working. Revocation happens on disable.
    await db.commit()
    # Plaintext codes are returned exactly once; only sha256 hashes are stored.
    return {"backup_codes": backup_codes}


@router.post("/2fa/disable", status_code=204)
async def twofa_disable(
    body: TwoFACode,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    if not admin.totp_enabled:
        raise HTTPException(status_code=400, detail="2FA is not enabled")
    if not check_otp(admin, body.code):  # TOTP or a one-time backup code
        raise HTTPException(status_code=401, detail={"code": "totp_invalid"})
    admin.totp_secret = None
    admin.totp_pending_secret = None
    admin.totp_enabled = False
    admin.backup_codes = None
    admin.token_version = (admin.token_version or 0) + 1  # revoke all outstanding tokens
    await db.commit()
