from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class CategoryOut(BaseModel):
    id: int
    slug: str
    title: str
    model_config = ConfigDict(from_attributes=True)


class TagOut(BaseModel):
    id: int
    slug: str
    title: str
    model_config = ConfigDict(from_attributes=True)


class ProductListItem(BaseModel):
    id: int
    slug: str
    title: str
    category: Optional[CategoryOut] = None
    tags: List[TagOut] = []
    display_views: int
    display_purchases: int
    cover_url: Optional[str] = None
    is_premium: bool
    price_stars: int
    approx_usd: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)


class ProductDetail(BaseModel):
    id: int
    slug: str
    title: str
    description: Optional[str] = None
    category: Optional[CategoryOut] = None
    tags: List[TagOut] = []
    display_views: int
    display_purchases: int
    cover_url: Optional[str] = None
    preview_video_url: Optional[str] = None
    price_stars: int
    approx_usd: Optional[float] = None
    is_premium: bool
    model_config = ConfigDict(from_attributes=True)


class FavoriteToggleOut(BaseModel):
    is_favorite: bool


class RecentlyViewedOut(BaseModel):
    id: int
    product: ProductListItem
    viewed_at: str
    model_config = ConfigDict(from_attributes=True)
