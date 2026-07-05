from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class SupportTicketOut(BaseModel):
    id: int
    user_id: int
    topic: str  # FIXED: was `subject`, but SupportTicket model field is `topic`
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SupportTicketUpdate(BaseModel):
    status: Optional[str] = None
    assigned_admin_id: Optional[int] = None


class SupportTicketListResponse(BaseModel):
    data: List[SupportTicketOut]
    total: int