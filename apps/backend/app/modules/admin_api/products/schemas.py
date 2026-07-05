from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class ProductTranslationIn(BaseModel):
    language_code: str
    title: str
    description: Optional[str] = None


class ProductCreate(BaseModel):
    slug: str
    status: str = "draft"
    price_stars: int = 0
    usd_price_mode: str = "auto"
    usd_price_manual: Optional[float] = None
    category_id: Optional[int] = None
    cover_url: Optional[str] = None
    preview_video_url: Optional[str] = None
    google_drive_link: Optional[str] = None
    google_drive_file_id: Optional[str] = None
    trend_score: int = 0
    is_premium: bool = False
    available_for_subscription: bool = False
    translations: List[ProductTranslationIn] = []
    tag_ids: List[int] = []


class ProductUpdate(BaseModel):
    slug: Optional[str] = None
    status: Optional[str] = None
    price_stars: Optional[int] = None
    usd_price_mode: Optional[str] = None
    usd_price_manual: Optional[float] = None
    category_id: Optional[int] = None
    cover_url: Optional[str] = None
    preview_video_url: Optional[str] = None
    google_drive_link: Optional[str] = None
    google_drive_file_id: Optional[str] = None
    trend_score: Optional[int] = None
    is_premium: Optional[bool] = None
    available_for_subscription: Optional[bool] = None
    translations: List[ProductTranslationIn] = []
    tag_ids: List[int] = []


class ProductTranslationOut(BaseModel):
    id: int
    product_id: int
    language_code: str
    title: str
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ProductOut(BaseModel):
    id: int
    slug: str
    status: str
    price_stars: int
    usd_price_mode: str
    usd_price_manual: Optional[float] = None
    category_id: Optional[int] = None
    cover_url: Optional[str] = None
    preview_video_url: Optional[str] = None
    google_drive_link: Optional[str] = None
    google_drive_file_id: Optional[str] = None
    display_views: int
    real_views: int
    display_purchases: int
    real_purchases: int
    trend_score: int
    is_premium: bool
    available_for_subscription: bool
    created_at: datetime
    updated_at: datetime
    translations: List[ProductTranslationOut] = []
    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    data: List[ProductOut]
    total: int