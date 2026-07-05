from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class CategoryTranslationIn(BaseModel):
    language_code: str
    title: str


class CategoryCreate(BaseModel):
    slug: str
    status: str = "published"
    translations: List[CategoryTranslationIn] = []


class CategoryUpdate(BaseModel):
    slug: Optional[str] = None
    status: Optional[str] = None
    translations: List[CategoryTranslationIn] = []


class CategoryTranslationOut(BaseModel):
    id: int
    category_id: int
    language_code: str
    title: str
    model_config = ConfigDict(from_attributes=True)


class CategoryOut(BaseModel):
    id: int
    slug: str
    status: str
    created_at: datetime
    updated_at: datetime
    translations: List[CategoryTranslationOut] = []
    model_config = ConfigDict(from_attributes=True)


class CategoryListResponse(BaseModel):
    data: List[CategoryOut]
    total: int