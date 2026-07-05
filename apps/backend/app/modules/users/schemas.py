from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProfileOut(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    selected_language: Optional[str] = None
    notifications_enabled: bool
    age_confirmed: bool
    is_blocked: bool
    is_premium: bool = False
    premium_until: Optional[datetime] = None


class ProfileUpdateLanguage(BaseModel):
    language: str


class ProfileUpdateNotifications(BaseModel):
    enabled: bool


class ProfileConfirmAge(BaseModel):
    confirmed: bool = True
