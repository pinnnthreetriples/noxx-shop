from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class PromoCodeCreate(BaseModel):
    code: str
    discount_type: str = "percentage"
    discount_value: int = 0
    active: bool = True
    usage_limit: Optional[int] = None
    first_purchase_only: bool = False
    min_cart_total: Optional[int] = None
    starts_at: Optional[str] = None
    expires_at: Optional[str] = None


class PromoCodeUpdate(BaseModel):
    code: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[int] = None
    active: Optional[bool] = None
    usage_limit: Optional[int] = None
    first_purchase_only: Optional[bool] = None
    min_cart_total: Optional[int] = None
    starts_at: Optional[str] = None
    expires_at: Optional[str] = None


class PromoCodeOut(BaseModel):
    id: int
    code: str
    discount_type: str
    discount_value: int
    active: bool
    usage_limit: Optional[int] = None
    used_count: int
    first_purchase_only: bool
    min_cart_total: Optional[int] = None
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PromoCodeListResponse(BaseModel):
    data: List[PromoCodeOut]
    total: int