from pydantic import BaseModel, ConfigDict
from typing import Optional


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str


class AdminMeResponse(BaseModel):
    id: int
    telegram_id: int
    name: Optional[str] = None
    role: str
    model_config = ConfigDict(from_attributes=True)