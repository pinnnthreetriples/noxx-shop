"""Favorites / recently-viewed schemas (DTO)."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.modules.catalog.schemas import ProductListItem


class FavoriteToggleOut(BaseModel):
    """Result of adding or removing a product from the user's favorites."""
    is_favorite: bool


class FavoriteOut(BaseModel):
    """A favorite record with the associated product snapshot."""
    id: int
    user_id: int
    product_id: int
    product: Optional[ProductListItem] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RecentlyViewedOut(BaseModel):
    """A recently-viewed product with the snapshot at view time."""
    id: int
    product: ProductListItem
    viewed_at: datetime
    model_config = ConfigDict(from_attributes=True)
