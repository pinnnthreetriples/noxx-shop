from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class AdminCreate(BaseModel):
    telegram_id: int
    name: Optional[str] = None
    role: str = "admin"
    active: bool = True


class AdminUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    active: Optional[bool] = None


class AdminOut(BaseModel):
    id: int
    telegram_id: int
    name: Optional[str] = None
    role: str
    active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AdminListResponse(BaseModel):
    data: List[AdminOut]
    total: int