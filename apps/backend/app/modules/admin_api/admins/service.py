"""Admin admin service - use-case logic."""
from typing import Optional, Dict, Any
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.admin.models import Admin, AdminRole
from app.modules.admin_api.admins.repository import AdminAdminRepository
from app.modules.admin_api.filters import AdminListFilters


class AdminAdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AdminAdminRepository(db)
    
    async def list(self, sort_field: str, order: str, start: int, end: int) -> Dict[str, Any]:
        f = AdminListFilters(sort_field=sort_field, order=order, start=start, end=end)
        items, total = await self.repo.list_with_filters(f)
        return {"data": items, "total": total}
    
    async def get(self, id: int) -> Optional[Admin]:
        return await self.repo.get_by_id(id)
    
    async def create(self, admin, payload: dict) -> Admin:
        try:
            a = await self.repo.create(
                telegram_id=payload.get("telegram_id", 0),
                name=payload.get("name"),
                role=payload.get("role", "admin"),
                active=payload.get("active", True),
            )
            await self.db.commit()
        except IntegrityError:
            # admins.telegram_id is unique and is the only unique column on
            # the table, so a duplicate is the only thing that lands here. The
            # repo flushes inside create(), and without the rollback that failed
            # flush leaves the session poisoned: the 500 then cascades onto
            # every later statement on the same request-scoped session.
            await self.db.rollback()
            raise HTTPException(
                status_code=409, detail="An admin with this telegram_id already exists"
            ) from None
        await self.db.refresh(a)
        return a
    
    async def _refuse_if_last_owner(self, a: Admin, new_role, new_active: bool) -> None:
        """Refuse any edit that would leave the shop with no active owner.

        Managing admins is owner-only, so losing the last active owner locks
        the roster permanently: nothing in the app can hand out the role again,
        and the /auth/login auto-create only fires when no row matches
        ADMIN_DEFAULT_TELEGRAM_ID, which is not the case once the row exists.
        The check is stated as "an active owner must remain" rather than "you
        may not edit yourself" because the self-edit rule misses two owners
        deactivating each other in turn, and needlessly blocks a lone owner
        from stepping down once a replacement exists.
        """
        if a.role != AdminRole.owner or not a.active:
            return  # not an active owner - this edit can't cost us one
        if new_role == AdminRole.owner and new_active:
            return  # still an active owner afterwards
        if await self.repo.count_other_active_owners(a.id) == 0:
            raise HTTPException(
                status_code=409, detail="Cannot remove the last active owner"
            )
    
    async def update(self, admin, id: int, payload: dict) -> Optional[Admin]:
        a = await self.repo.get_by_id(id)
        if not a:
            return None
        await self._refuse_if_last_owner(
            a, payload.get("role", a.role), payload.get("active", a.active)
        )
        await self.repo.update(a, {k: v for k, v in payload.items() if hasattr(a, k) and k != "id"})
        await self.db.commit()
        await self.db.refresh(a)
        return a
    
    async def deactivate(self, admin, id: int) -> Optional[Admin]:
        a = await self.repo.get_by_id(id)
        if not a:
            return None
        await self._refuse_if_last_owner(a, a.role, False)
        a.active = False
        await self.db.commit()
        return a