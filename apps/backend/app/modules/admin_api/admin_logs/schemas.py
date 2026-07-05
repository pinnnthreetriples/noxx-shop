from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class AdminLogOut(BaseModel):
    id: int
    admin_id: int
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    before_data: Optional[str] = None
    after_data: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AdminLogListResponse(BaseModel):
    data: List[AdminLogOut]
    total: int