from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class SupportTicketIn(BaseModel):
    topic: str
    message: str


class SupportTicketOut(BaseModel):
    id: int
    topic: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SupportMessageIn(BaseModel):
    text: Optional[str] = None
    file_url: Optional[str] = None
    file_type: Optional[str] = None


class SupportMessageOut(BaseModel):
    id: int
    sender_type: str
    text: Optional[str] = None
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SupportTicketDetail(BaseModel):
    id: int
    topic: str
    status: str
    created_at: datetime
    messages: List[SupportMessageOut]
    model_config = ConfigDict(from_attributes=True)
