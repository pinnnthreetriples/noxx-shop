from typing import Optional
from dataclasses import dataclass
from app.modules.admin_api.filters import Page


@dataclass
class ProductFilters:
    q: Optional[str] = None
    status: Optional[str] = None
    sort_field: str = "id"
    order: str = "ASC"
    start: int = 0
    end: int = 25

    def to_page(self) -> Page:
        return Page(
            sort_field=self.sort_field,
            order=self.order,
            start=self.start,
            end=self.end,
        )
