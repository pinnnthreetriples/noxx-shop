from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.auth import get_current_user
from app.modules.support.schemas import SupportTicketIn, SupportTicketOut, SupportTicketDetail, SupportMessageIn, SupportMessageOut
from app.models import SupportTicket, SupportMessage

router = APIRouter(prefix="")


@router.post("/support/tickets", response_model=SupportTicketOut)
async def create_support_ticket(body: SupportTicketIn, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user.is_blocked:
        raise HTTPException(status_code=403, detail="User is blocked")
    ticket = SupportTicket(user_id=user.id, topic=body.topic, status="open")
    db.add(ticket)
    await db.flush()
    msg = SupportMessage(ticket_id=ticket.id, sender_type="user", sender_id=user.id, text=body.message)
    db.add(msg)
    await db.commit()
    await db.refresh(ticket)
    return SupportTicketOut(id=ticket.id, topic=ticket.topic.value, status=ticket.status.value, created_at=ticket.created_at)


@router.get("/support/tickets", response_model=List[SupportTicketDetail])
async def list_support_tickets(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SupportTicket)
        .options(selectinload(SupportTicket.messages))  # eager-load: async lazy access to .messages 500s (MissingGreenlet)
        .where(SupportTicket.user_id == user.id)
        .order_by(desc(SupportTicket.created_at))
    )
    tickets = result.scalars().all()
    out = []
    for t in tickets:
        msgs = [
            SupportMessageOut(
                id=m.id, sender_type=m.sender_type, text=m.text,
                file_url=m.file_url, file_type=m.file_type, created_at=m.created_at,
            )
            for m in t.messages
        ]
        out.append(SupportTicketDetail(
            id=t.id, topic=t.topic.value, status=t.status.value,
            created_at=t.created_at, messages=msgs,
        ))
    return out


@router.post("/support/tickets/{ticket_id}/messages", response_model=SupportMessageOut)
async def add_support_message(ticket_id: int, body: SupportMessageIn, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id, SupportTicket.user_id == user.id))
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if user.is_blocked:
        raise HTTPException(status_code=403, detail="User is blocked")
    msg = SupportMessage(
        ticket_id=ticket_id, sender_type="user", sender_id=user.id,
        text=body.text, file_url=body.file_url, file_type=body.file_type,
    )
    db.add(msg)
    ticket.status = "open"
    await db.commit()
    await db.refresh(msg)
    return SupportMessageOut(
        id=msg.id, sender_type=msg.sender_type, text=msg.text,
        file_url=msg.file_url, file_type=msg.file_type, created_at=msg.created_at,
    )
