"""Notifications module schemas (DTO)."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class NotificationOut(BaseModel):
    """Public notification payload."""
    id: int
    title: str
    body: Optional[str] = None
    product_id: Optional[int] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class NotificationCreate(BaseModel):
    """Admin payload to create a notification (queued for delivery)."""
    title: str = Field(..., max_length=255)
    body: Optional[str] = None
    product_id: Optional[int] = None


class NotificationRecipientOut(BaseModel):
    """Per-recipient delivery record."""
    id: int
    notification_id: int
    user_id: int
    status: str
    sent_at: Optional[datetime] = None
    error: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
