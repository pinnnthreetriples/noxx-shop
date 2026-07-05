"""Admin analytics router (stub - basic counters).

Returns minimal aggregate stats used by the admin dashboard. Full analytics
(outliers, cohorts, retention) can be added later without changing the route.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.modules.orders.models import Order, OrderStatus
from app.modules.users.models import User
from app.modules.catalog.models import Product
from app.modules.support.models import SupportTicket

router = APIRouter()


@router.get("/analytics/summary")
async def analytics_summary(db: AsyncSession = Depends(get_db)):
    """Return top-level counters for the admin dashboard."""
    paid_orders = (await db.execute(
        select(func.count(Order.id)).where(Order.status == OrderStatus.paid)
    )).scalar() or 0
    total_revenue = (await db.execute(
        select(func.coalesce(func.sum(Order.paid_stars), 0)).where(Order.status == OrderStatus.paid)
    )).scalar() or 0
    users_count = (await db.execute(select(func.count(User.id)))).scalar() or 0
    products_count = (await db.execute(select(func.count(Product.id)))).scalar() or 0
    open_tickets = (await db.execute(select(func.count(SupportTicket.id)))).scalar() or 0
    return {
        "paid_orders": int(paid_orders),
        "total_revenue_stars": int(total_revenue),
        "users": int(users_count),
        "products": int(products_count),
        "open_support_tickets": int(open_tickets),
    }
