"""
Shared filters for admin_api subdomains: pagination, sort, search.
"""
from dataclasses import dataclass
from typing import Optional
from sqlalchemy import select, func, desc, asc, or_
from sqlalchemy.sql import Select


@dataclass
class AdminListFilters:
    """Pagination + sort params for react-admin data provider."""
    q: Optional[str] = None
    status: Optional[str] = None
    sort_field: str = "id"
    order: str = "ASC"
    start: int = 0
    end: int = 25
    
    @property
    def desc_order(self) -> bool:
        return self.order.upper() == "DESC"
    
    @property
    def limit(self) -> int:
        return max(1, self.end - self.start)
    
    @property
    def offset(self) -> int:
        return max(0, self.start)


def apply_sort(stmt: Select, model, field: str, desc_order: bool) -> Select:
    col = getattr(model, field, model.id)
    return stmt.order_by(desc(col) if desc_order else asc(col))


async def count_total(db, stmt: Select) -> int:
    return await db.scalar(select(func.count()).select_from(stmt.subquery()))


def search_ilike(fields: list, q: str):
    """Build OR ILIKE across multiple fields."""
    like = f"%{q}%"
    return or_(*[f.ilike(like) for f in fields])


LANGUAGE_CODES = ["en", "ru", "es", "de", "el", "ro", "bg", "mo", "sr", "tr"]


def apply_updates(obj, fields: dict) -> None:
    """Set editable scalar fields on an ORM object.

    Skips `id`. DateTime columns are set only when the value is already a real
    datetime (or None): react-admin echoes the whole record back on save, with
    timestamps as ISO strings that asyncpg rejects — a service that wants a
    datetime editable must parse the string first (see users service).
    """
    from datetime import datetime
    from sqlalchemy import DateTime, inspect as sa_inspect

    cols = {a.key: a.columns[0] for a in sa_inspect(obj).mapper.column_attrs}
    for k, v in fields.items():
        if k == "id" or k not in cols:
            continue
        if isinstance(cols[k].type, DateTime) and not (v is None or isinstance(v, datetime)):
            continue
        setattr(obj, k, v)