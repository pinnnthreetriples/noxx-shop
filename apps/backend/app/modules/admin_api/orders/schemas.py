from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

from app.modules.orders.models import OrderStatus


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    price_stars: int
    model_config = ConfigDict(from_attributes=True)


class OrderOut(BaseModel):
    id: int
    user_id: int
    status: str
    total_stars: int
    paid_stars: Optional[int] = None
    promo_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemOut] = []
    model_config = ConfigDict(from_attributes=True)


class OrderUpdate(BaseModel):
    # Typed as the enum, not str: an unknown status used to reach the DB and blow
    # up on bind as a 500, where pydantic rejects it as a 422 up front.
    status: Optional[OrderStatus] = None


class OrderListResponse(BaseModel):
    data: List[OrderOut]
    total: int