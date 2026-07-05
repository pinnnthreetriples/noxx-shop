"""Orders router - thin API layer."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.auth import get_current_admin
from app.modules.admin.models import Admin
from app.modules.admin_api.orders.service import OrderAdminService

router = APIRouter(tags=["admin-orders"])


@router.get("/orders")
async def list_orders(
    status: Optional[str] = None,
    _sort: str = "id",
    _order: str = "ASC",
    _start: int = 0,
    _end: int = 25,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = OrderAdminService(db)
    return await service.list(status=status, sort_field=_sort, order=_order, start=_start, end=_end)


@router.get("/orders/{id}")
async def get_order(
    id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = OrderAdminService(db)
    order = await service.get(id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.put("/orders/{id}")
async def update_order(
    id: int,
    payload: dict,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = OrderAdminService(db)
    order = await service.update(admin, id, payload)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/orders/{order_id}/resend-links")
async def resend_order_links(
    order_id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = OrderAdminService(db)
    order = await service.resend_links(admin, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Paid order not found")
    return {"resent": True}