"""User admin service - use-case logic."""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.admin.models import AdminLog
from app.modules.users.models import User
from app.modules.admin_api.users.repository import UserAdminRepository
from app.modules.admin_api.filters import AdminListFilters


class UserAdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserAdminRepository(db)
    
    async def list(self, q: Optional[str], status: Optional[str], sort_field: str, order: str, start: int, end: int) -> Dict[str, Any]:
        f = AdminListFilters(q=q, status=status, sort_field=sort_field, order=order, start=start, end=end)
        items, total = await self.repo.list_with_filters(f)
        return {"data": items, "total": total}
    
    async def get(self, id: int) -> Optional[User]:
        return await self.repo.get_by_id(id)
    
    async def update(self, admin, id: int, payload: dict) -> Optional[User]:
        user = await self.repo.get_by_id(id)
        if not user:
            return None
        old_blocked = user.is_blocked
        # react-admin sends datetimes as ISO strings; the DateTime column needs a real datetime
        if isinstance(payload.get("premium_until"), str):
            from datetime import datetime, timezone
            v = payload["premium_until"].strip()
            dt = datetime.fromisoformat(v.replace("Z", "+00:00")) if v else None
            # DateTimeInput sends naive local ISO (no Z/offset) — treat it as UTC;
            # a naive value breaks the tz-aware column and premium_until > now checks.
            if dt is not None and dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            payload["premium_until"] = dt
        await self.repo.update(user, {k: v for k, v in payload.items() if hasattr(user, k) and k != "id"})
        # Log block/unblock actions
        if "is_blocked" in payload and payload["is_blocked"] != old_blocked:
            action = "block_user" if payload["is_blocked"] else "unblock_user"
            self.db.add(AdminLog(admin_id=admin.id, action=action, entity_type="user", entity_id=user.id))
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def block(self, admin, id: int) -> Optional[User]:
        user = await self.repo.get_by_id(id)
        if not user:
            return None
        user.is_blocked = True
        self.db.add(AdminLog(admin_id=admin.id, action="block_user", entity_type="user", entity_id=user.id))
        await self.db.commit()
        return user
    
    async def unblock(self, admin, id: int) -> Optional[User]:
        user = await self.repo.get_by_id(id)
        if not user:
            return None
        user.is_blocked = False
        self.db.add(AdminLog(admin_id=admin.id, action="unblock_user", entity_type="user", entity_id=user.id))
        await self.db.commit()
        return user