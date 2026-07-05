"""SupportTickets router - thin API layer."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.auth import get_current_admin
from app.modules.admin.models import Admin
from app.modules.admin_api.support_tickets.service import SupportTicketAdminService

router = APIRouter(tags=["admin-support_tickets"])


@router.get("/support_tickets")
async def list_support_tickets(
    status: Optional[str] = None,
    _sort: str = "id",
    _order: str = "ASC",
    _start: int = 0,
    _end: int = 25,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = SupportTicketAdminService(db)
    return await service.list(status=status, sort_field=_sort, order=_order, start=_start, end=_end)


@router.get("/support_tickets/{id}")
async def get_support_ticket(
    id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = SupportTicketAdminService(db)
    ticket = await service.get(id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Support ticket not found")
    return ticket


@router.put("/support_tickets/{id}")
async def update_support_ticket(
    id: int,
    payload: dict,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = SupportTicketAdminService(db)
    ticket = await service.update(admin, id, payload)
    if not ticket:
        raise HTTPException(status_code=404, detail="Support ticket not found")
    return ticket