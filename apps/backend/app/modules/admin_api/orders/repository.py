"""Order repository - SQL operations only."""
from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.orders.models import Order, OrderItem
from app.modules.admin_api.filters import AdminListFilters, apply_sort, count_total, apply_updates

# resend_links walks order.items -> item.product, so they must be eager-loaded.
_ITEMS_EAGER = (selectinload(Order.items).selectinload(OrderItem.product),)


class OrderAdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list_with_filters(self, f: AdminListFilters) -> Tuple[List[Order], int]:
        stmt = select(Order)
        if f.status:
            stmt = stmt.where(Order.status == f.status)
        total = await count_total(self.db, stmt)
        stmt = apply_sort(stmt, Order, f.sort_field, f.desc_order)
        stmt = stmt.offset(f.offset).limit(f.limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total
    
    async def get_by_id(self, id: int) -> Optional[Order]:
        result = await self.db.execute(select(Order).options(*_ITEMS_EAGER).where(Order.id == id))
        return result.scalars().first()
    
    async def update(self, order: Order, fields: dict) -> Order:
        apply_updates(order, fields)
        return order
    
    async def resend_links(self, order: Order, admin_id: int):
        """Create LinkDeliveryLog entries for resending links."""
        from app.modules.admin.models import LinkDeliveryLog
        for item in order.items:
            log = LinkDeliveryLog(
                user_id=order.user_id,
                order_id=order.id,
                product_id=item.product_id,
                google_drive_link=item.product.google_drive_link or "",
                delivery_method="resend",
            )
            self.db.add(log)
        from app.modules.admin.models import AdminLog
        self.db.add(AdminLog(admin_id=admin_id, action="resend_links", entity_type="order", entity_id=order.id))