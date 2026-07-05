"""User repository - SQL operations only."""
from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.users.models import User
from app.modules.admin_api.filters import AdminListFilters, apply_sort, count_total, search_ilike, apply_updates


class UserAdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list_with_filters(self, f: AdminListFilters) -> Tuple[List[User], int]:
        stmt = select(User)
        if f.q:
            stmt = stmt.where(search_ilike([User.username, User.first_name], f.q))
        if f.status:
            if f.status == "blocked":
                stmt = stmt.where(User.is_blocked.is_(True))
            elif f.status == "active":
                stmt = stmt.where(User.is_blocked.is_(False))
        total = await count_total(self.db, stmt)
        stmt = apply_sort(stmt, User, f.sort_field, f.desc_order)
        stmt = stmt.offset(f.offset).limit(f.limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total
    
    async def get_by_id(self, id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == id))
        return result.scalars().first()
    
    async def update(self, user: User, fields: dict) -> User:
        apply_updates(user, fields)
        return user