from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update
from app.modules.support.models import SupportTicket, SupportMessage, TicketStatus, SupportTopic


class SupportTicketRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: int, topic: SupportTopic, initial_message: str) -> SupportTicket:
        ticket = SupportTicket(user_id=user_id, topic=topic)
        self.db.add(ticket)
        await self.db.flush()
        
        msg = SupportMessage(ticket_id=ticket.id, sender_type="user", sender_id=user_id, text=initial_message)
        self.db.add(msg)
        await self.db.flush()
        return ticket

    async def get_by_id(self, ticket_id: int) -> Optional[SupportTicket]:
        result = await self.db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
        return result.scalars().first()

    async def list_for_user(self, user_id: int, limit: int = 20, offset: int = 0) -> List[SupportTicket]:
        result = await self.db.execute(
            select(SupportTicket).where(SupportTicket.user_id == user_id).order_by(desc(SupportTicket.created_at)).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def list_with_status(
        self,
        status: Optional[TicketStatus] = None,
        sort: str = "created_at",
        order: str = "desc",
        start: int = 0,
        end: int = 50,
    ) -> Tuple[List[SupportTicket], int]:
        stmt = select(SupportTicket)
        if status:
            stmt = stmt.where(SupportTicket.status == status)
        
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0
        
        sort_col = getattr(SupportTicket, sort, SupportTicket.created_at)
        if order == "desc":
            stmt = stmt.order_by(desc(sort_col))
        else:
            stmt = stmt.order_by(sort_col)
        
        stmt = stmt.limit(end - start).offset(start)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def mark_answered(self, ticket_id: int) -> None:
        await self.db.execute(update(SupportTicket).where(SupportTicket.id == ticket_id).values(status=TicketStatus.answered))

    async def mark_admin_notified(self, ticket_id: int) -> None:
        await self.db.execute(update(SupportTicket).where(SupportTicket.id == ticket_id).values(admin_notified=True))

    async def list_unnotified(self, after_id: int, limit: int = 100) -> List[SupportTicket]:
        result = await self.db.execute(
            select(SupportTicket)
            .where(SupportTicket.admin_notified.is_(False), SupportTicket.id > after_id)
            .order_by(SupportTicket.id.asc())
            .limit(limit)
        )
        return list(result.scalars().all())


class SupportMessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        ticket_id: int,
        sender_type: str,
        sender_id: int,
        text: Optional[str] = None,
        file_url: Optional[str] = None,
        file_type: Optional[str] = None,
    ) -> SupportMessage:
        msg = SupportMessage(
            ticket_id=ticket_id,
            sender_type=sender_type,
            sender_id=sender_id,
            text=text,
            file_url=file_url,
            file_type=file_type,
        )
        self.db.add(msg)
        await self.db.flush()
        return msg

    async def list_for_ticket(self, ticket_id: int, limit: int = 50, offset: int = 0) -> List[SupportMessage]:
        result = await self.db.execute(
            select(SupportMessage)
            .where(SupportMessage.ticket_id == ticket_id)
            .order_by(SupportMessage.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
