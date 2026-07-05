from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class NotificationCreate(BaseModel):
    title: str
    body: Optional[str] = None
    product_id: Optional[int] = None


class NotificationOut(BaseModel):
    id: int
    title: str
    body: Optional[str] = None
    product_id: Optional[int] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    data: List[NotificationOut]
    total: int