from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

from app.modules.admin.models import AdminRole


# Whitelists for POST/PUT /admin/admins. Deliberately absent: totp_enabled,
# totp_secret, totp_pending_secret, backup_codes and token_version — the second
# factor is owned by /auth/2fa/*, which demands an OTP and revokes tokens.
class AdminCreate(BaseModel):
    telegram_id: int
    name: Optional[str] = None
    # Typed as the enum, not str: an unknown role used to reach the DB and blow
    # up on bind as a 500, where pydantic rejects it as a 422 up front.
    role: AdminRole = AdminRole.admin
    active: bool = True


# telegram_id is missing on purpose: it is the identity the bot trusts to answer
# support tickets, so re-pointing an existing admin row at another account would
# be a silent handover. Create a new admin instead.
class AdminUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[AdminRole] = None
    active: Optional[bool] = None


# Wired as the response_model of every /admin/admins route: the raw ORM row used
# to be serialized field-for-field, handing totp_secret (plaintext unless
# ADMIN_TOTP_ENC_KEY is set), totp_pending_secret and backup_codes to any admin
# that could list admins.
class AdminOut(BaseModel):
    id: int
    telegram_id: int
    name: Optional[str] = None
    role: AdminRole
    active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AdminListResponse(BaseModel):
    data: List[AdminOut]
    total: int