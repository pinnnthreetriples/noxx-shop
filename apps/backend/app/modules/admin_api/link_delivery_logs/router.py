"""Admin link_delivery_logs router.

Exposes the list endpoint used by the admin panel to inspect link deliveries.
Implements the ra-data-simple-rest list contract: the route name matches the
react-admin resource ("link_delivery_logs"), honors _sort/_order/_start/_end,
and returns {"data": [...], "total": N} so the admin grid paginates and sorts.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, asc, desc
from app.core.database import get_db
from app.modules.admin.models import LinkDeliveryLog

router = APIRouter(tags=["admin-link-delivery-logs"])

# Whitelist of columns the admin grid is allowed to sort by.
_SORTABLE = {
    "id": LinkDeliveryLog.id,
    "user_id": LinkDeliveryLog.user_id,
    "order_id": LinkDeliveryLog.order_id,
    "product_id": LinkDeliveryLog.product_id,
    "delivery_method": LinkDeliveryLog.delivery_method,
    "status": LinkDeliveryLog.status,
    "sent_at": LinkDeliveryLog.sent_at,
}


def _serialize(r: LinkDeliveryLog) -> dict:
    return {
        "id": r.id,
        "user_id": r.user_id,
        "order_id": r.order_id,
        "product_id": r.product_id,
        "delivery_method": r.delivery_method,
        "status": r.status,
        "sent_at": r.sent_at.isoformat() if r.sent_at else None,
    }


@router.get("/link_delivery_logs")
async def list_link_delivery_logs(
    order_id: Optional[int] = None,
    user_id: Optional[int] = None,
    sort: str = Query("sent_at", alias="_sort"),
    order: str = Query("DESC", alias="_order"),
    start: int = Query(0, alias="_start"),
    end: int = Query(50, alias="_end"),
    db: AsyncSession = Depends(get_db),
):
    """Paginated + sortable list of link delivery log entries for the admin grid."""
    filters = []
    if order_id is not None:
        filters.append(LinkDeliveryLog.order_id == order_id)
    if user_id is not None:
        filters.append(LinkDeliveryLog.user_id == user_id)

    column = _SORTABLE.get(sort, LinkDeliveryLog.sent_at)
    direction = asc if str(order).upper() == "ASC" else desc

    count_stmt = select(func.count()).select_from(LinkDeliveryLog)
    list_stmt = select(LinkDeliveryLog).order_by(direction(column))
    for f in filters:
        count_stmt = count_stmt.where(f)
        list_stmt = list_stmt.where(f)

    limit = max(end - start, 0)
    list_stmt = list_stmt.offset(start).limit(limit)

    total = (await db.execute(count_stmt)).scalar_one()
    rows = (await db.execute(list_stmt)).scalars().all()
    return {"data": [_serialize(r) for r in rows], "total": total}
