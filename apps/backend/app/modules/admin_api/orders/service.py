"""Order admin service - use-case logic."""
import json
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.admin.models import AdminLog
from app.modules.orders.models import Order
from app.modules.admin_api.orders.repository import OrderAdminRepository
from app.modules.admin_api.filters import AdminListFilters


class OrderAdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = OrderAdminRepository(db)
    
    async def list(self, status: Optional[str], sort_field: str, order: str, start: int, end: int) -> Dict[str, Any]:
        f = AdminListFilters(status=status, sort_field=sort_field, order=order, start=start, end=end)
        items, total = await self.repo.list_with_filters(f)
        return {"data": items, "total": total}
    
    async def get(self, id: int) -> Optional[Order]:
        return await self.repo.get_by_id(id)
    
    async def update(self, admin, id: int, payload: dict) -> Optional[Order]:
        order = await self.repo.get_by_id(id)
        if not order:
            return None
        fields = {k: v for k, v in payload.items() if hasattr(order, k) and k != "id"}
        # Flipping the status by hand skips the whole fulfillment path - no payment
        # row, no links delivered, no promo redeemed, no premium extended - so the
        # buyer gets nothing. Only the transition is refused: re-saving the form on
        # an order that is already paid must stay a no-op.
        if fields.get("status") == "paid" and order.status != "paid":
            raise ValueError("Order status 'paid' is set by an actual payment, not by hand")
        before = {k: getattr(order, k) for k, v in fields.items() if getattr(order, k) != v}
        await self.repo.update(order, fields)
        # An edited order status was unprovable before: log what actually changed.
        if before:
            self.db.add(AdminLog(
                admin_id=admin.id,
                action="update_order",
                entity_type="order",
                entity_id=order.id,
                before_data=json.dumps(before),
                after_data=json.dumps({k: fields[k] for k in before}),
            ))
        await self.db.commit()
        await self.db.refresh(order)
        return order
    
    async def resend_links(self, admin, id: int) -> Optional[Order]:
        order = await self.repo.get_by_id(id)
        if not order or order.status != "paid":
            return None
        await self.repo.resend_links(order, admin.id)
        await self.db.commit()
        return order