from datetime import datetime, time, timezone
from pydantic import BaseModel, BeforeValidator, ConfigDict
from typing import Annotated, Optional, List, Literal


# The only type checkout understands: OrderService._lookup_promo_discount returns
# a discount for "percentage" and None for anything else, so a typo like
# "percent" or "fixed" used to create a promo code that silently never discounted
# anything. Widening this list means teaching checkout the new type first.
DiscountType = Literal["percentage"]


def _bound(value: object, *, end_of_day: bool) -> object:
    """Normalize a promo window bound to an aware UTC datetime.

    The admin form (react-admin DateInput) posts a bare "YYYY-MM-DD" while the
    columns are timestamptz. Read as midnight, "expires 2026-09-01" died at the
    *start* of 1 September, so the last day of the promo never worked. A bare
    date is therefore anchored to the last microsecond of that day when it ends
    the window and to the first when it opens it. Anything naive is stamped UTC:
    the checks compare against datetime.now(timezone.utc).
    """
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        value = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if "T" not in text and " " not in text:  # date only, no clock time
            value = datetime.combine(value.date(), time.max if end_of_day else time.min)
    if isinstance(value, datetime) and value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value


StartsAt = Annotated[Optional[datetime], BeforeValidator(lambda v: _bound(v, end_of_day=False))]
ExpiresAt = Annotated[Optional[datetime], BeforeValidator(lambda v: _bound(v, end_of_day=True))]


class PromoCodeCreate(BaseModel):
    code: str
    discount_type: DiscountType = "percentage"
    discount_value: int = 0
    active: bool = True
    usage_limit: Optional[int] = None
    first_purchase_only: bool = False
    min_cart_total: Optional[int] = None
    starts_at: StartsAt = None
    expires_at: ExpiresAt = None


class PromoCodeUpdate(BaseModel):
    code: Optional[str] = None
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[int] = None
    active: Optional[bool] = None
    usage_limit: Optional[int] = None
    first_purchase_only: Optional[bool] = None
    min_cart_total: Optional[int] = None
    starts_at: StartsAt = None
    expires_at: ExpiresAt = None


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