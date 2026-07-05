from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.internal_api.schemas import (
    AdminReplyRequest, AdminReplyResponse,
    UnnotifiedTicketsResponse, TicketNotification,
    ActiveAdminIdsResponse,
    AdminMessageMapRequest, AdminMessageMapResponse,
    MarkTicketNotifiedResponse,
)
from app.modules.support.service import SupportService
from app.modules.admin.repository import AdminRepository
from app.modules.orders.repository import BotMessageMapRepository

router = APIRouter(prefix="/support", tags=["internal-support"])


@router.post("/admin-reply", response_model=AdminReplyResponse)
async def admin_reply(payload: AdminReplyRequest, db: AsyncSession = Depends(get_db)):
    service = SupportService(db)
    result = await service.admin_reply_by_telegram(
        admin_telegram_id=payload.admin_telegram_id,
        reply_to_message_id=payload.reply_to_message_id,
        text=payload.text,
        file_url=payload.file_url,
        file_type=payload.file_type,
    )
    return AdminReplyResponse(**result)


@router.get("/tickets/unnotified", response_model=UnnotifiedTicketsResponse)
async def unnotified_tickets(after_id: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    service = SupportService(db)
    tickets = await service.get_unnotified_tickets(after_id=after_id, limit=limit)
    return UnnotifiedTicketsResponse(tickets=[
        TicketNotification(
            ticket_id=t["ticket_id"],
            user_telegram_id=t["user_telegram_id"],
            topic=t["topic"],
            created_at=t["created_at"],
        )
        for t in tickets
    ])


@router.post("/tickets/{ticket_id}/mark-notified", response_model=MarkTicketNotifiedResponse)
async def mark_ticket_notified(ticket_id: int, db: AsyncSession = Depends(get_db)):
    service = SupportService(db)
    ok = await service.mark_admin_notified(ticket_id)
    return MarkTicketNotifiedResponse(ok=ok)


@router.get("/admins/active", response_model=ActiveAdminIdsResponse)
async def active_admins(db: AsyncSession = Depends(get_db)):
    repo = AdminRepository(db)
    return ActiveAdminIdsResponse(admin_telegram_ids=await repo.list_active_telegram_ids())


@router.post("/bot/admin-message-map", response_model=AdminMessageMapResponse)
async def admin_message_map(payload: AdminMessageMapRequest, db: AsyncSession = Depends(get_db)):
    repo = BotMessageMapRepository(db)
    await repo.create(
        admin_message_id=payload.admin_message_id,
        chat_id=payload.chat_id,
        ticket_id=payload.ticket_id,
    )
    return AdminMessageMapResponse(ok=True)