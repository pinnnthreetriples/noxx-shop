from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ImportResult(BaseModel):
    created: int
    updated: int
    skipped: int
    errors: List[str]


class AdminLogOut(BaseModel):
    id: int
    admin_id: int
    action: str
    entity_type: str
    entity_id: Optional[int]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SettingsOut(BaseModel):
    bot_name: Optional[str] = None
    support_enabled: bool
    content_18_plus_enabled: bool
    default_language: str
    stars_to_usd_mode: str
    manual_stars_to_usd_rate: Optional[float] = None
    max_discount_percent: int
    subscription_coming_soon_enabled: bool
    subscription_coming_soon_text: Optional[str] = None
    terms_text_en: Optional[str] = None
    terms_text_ru: Optional[str] = None
    terms_text_de: Optional[str] = None
    terms_text_el: Optional[str] = None
    terms_text_ro: Optional[str] = None
    terms_text_bg: Optional[str] = None
    terms_text_mo: Optional[str] = None
    terms_text_sr: Optional[str] = None
    terms_text_tr: Optional[str] = None
    refund_policy_text_en: Optional[str] = None
    refund_policy_text_ru: Optional[str] = None
    refund_policy_text_de: Optional[str] = None
    refund_policy_text_el: Optional[str] = None
    refund_policy_text_ro: Optional[str] = None
    refund_policy_text_bg: Optional[str] = None
    refund_policy_text_mo: Optional[str] = None
    refund_policy_text_sr: Optional[str] = None
    refund_policy_text_tr: Optional[str] = None
    discount_first_purchase_percent: int = 10
    discount_bulk_percent: int = 15
    discount_bulk_min_items: int = 20
    discount_loyalty_percent: int = 30
    discount_loyalty_min_items: int = 20
    sub_price_week_stars: int = 99
    sub_price_month_stars: int = 299
    sub_price_year_stars: int = 2499
    model_config = ConfigDict(from_attributes=True)


class LanguageOut(BaseModel):
    code: str
    name: str
