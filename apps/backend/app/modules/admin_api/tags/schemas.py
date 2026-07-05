from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class TagTranslationIn(BaseModel):
    language_code: str
    title: str


class TagCreate(BaseModel):
    slug: str
    translations: List[TagTranslationIn] = []


class TagUpdate(BaseModel):
    slug: Optional[str] = None
    translations: List[TagTranslationIn] = []


class TagTranslationOut(BaseModel):
    id: int
    tag_id: int
    language_code: str
    title: str
    model_config = ConfigDict(from_attributes=True)


class TagOut(BaseModel):
    id: int
    slug: str
    created_at: datetime
    translations: List[TagTranslationOut] = []
    model_config = ConfigDict(from_attributes=True)


class TagListResponse(BaseModel):
    data: List[TagOut]
    total: int