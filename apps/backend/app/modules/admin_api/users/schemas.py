from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class UserOut(BaseModel):
    id: int
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    selected_language: Optional[str] = None
    is_blocked: bool
    balance_stars: int
    subscription_expires_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    selected_language: Optional[str] = None
    is_blocked: Optional[bool] = None
    balance_stars: Optional[int] = None


class UserListResponse(BaseModel):
    data: List[UserOut]
    total: int