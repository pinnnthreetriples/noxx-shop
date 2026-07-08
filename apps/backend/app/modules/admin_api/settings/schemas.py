from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class SettingsUpdate(BaseModel):
    bot_name: Optional[str] = None
    support_enabled: Optional[bool] = None
    content_18_plus_enabled: Optional[bool] = None
    default_language: Optional[str] = None
    stars_to_usd_mode: Optional[str] = None
    manual_stars_to_usd_rate: Optional[float] = None
    max_discount_percent: Optional[int] = Field(None, ge=0, le=100)
    terms_text_en: Optional[str] = None
    refund_policy_text_en: Optional[str] = None
    notifications_enabled_by_default: Optional[bool] = None
    subscription_coming_soon_enabled: Optional[bool] = None
    subscription_coming_soon_text: Optional[str] = None
    discount_first_purchase_percent: Optional[int] = Field(None, ge=0, le=100)
    discount_bulk_percent: Optional[int] = Field(None, ge=0, le=100)
    discount_bulk_min_items: Optional[int] = Field(None, ge=1)
    discount_loyalty_percent: Optional[int] = Field(None, ge=0, le=100)
    discount_loyalty_min_items: Optional[int] = Field(None, ge=1)
    sub_price_week_stars: Optional[int] = Field(None, ge=1)
    sub_price_month_stars: Optional[int] = Field(None, ge=1)
    sub_price_year_stars: Optional[int] = Field(None, ge=1)


class SettingsOut(BaseModel):
    id: int
    bot_name: Optional[str] = None
    support_enabled: bool
    content_18_plus_enabled: bool
    default_language: str
    stars_to_usd_mode: str
    manual_stars_to_usd_rate: Optional[float] = None
    star_usd_rate: float
    max_discount_percent: int
    terms_text_en: Optional[str] = None
    refund_policy_text_en: Optional[str] = None
    notifications_enabled_by_default: bool
    subscription_coming_soon_enabled: bool
    subscription_coming_soon_text: Optional[str] = None
    discount_first_purchase_percent: int = 10
    discount_bulk_percent: int = 15
    discount_bulk_min_items: int = 20
    discount_loyalty_percent: int = 30
    discount_loyalty_min_items: int = 20
    sub_price_week_stars: int = 99
    sub_price_month_stars: int = 299
    sub_price_year_stars: int = 2499
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
