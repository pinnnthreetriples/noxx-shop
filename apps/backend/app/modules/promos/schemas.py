from typing import List, Optional
from pydantic import BaseModel


class PromoValidateIn(BaseModel):
    code: str
    product_ids: List[int]


class PromoValidateOut(BaseModel):
    valid: bool
    discount_type: Optional[str] = None
    discount_value: Optional[int] = None
    message: Optional[str] = None
