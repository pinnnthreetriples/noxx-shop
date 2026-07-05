from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.modules.admin.models import Admin, AdminLog, LinkDeliveryLog, GoogleDriveToken, BotMessageMap, AdminRole


class AdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, admin_id: int) -> Optional[Admin]:
        result = await self.db.execute(select(Admin).where(Admin.id == admin_id))
        return result.scalars().first()

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[Admin]:
        result = await self.db.execute(select(Admin).where(Admin.telegram_id == telegram_id))
        return result.scalars().first()

    async def create(
        self,
        telegram_id: int,
        name: Optional[str] = None,
        role: AdminRole = AdminRole.owner,
        active: bool = True,
    ) -> Admin:
        admin = Admin(telegram_id=telegram_id, name=name, role=role, active=active)
        self.db.add(admin)
        await self.db.flush()
        return admin

    async def update(self, admin_id: int, fields: dict) -> Optional[Admin]:
        result = await self.db.execute(select(Admin).where(Admin.id == admin_id))
        admin = result.scalars().first()
        if admin:
            for key, value in fields.items():
                setattr(admin, key, value)
            await self.db.flush()
        return admin

    async def list(
        self,
        sort: str = "created_at",
        order: str = "desc",
        start: int = 0,
        end: int = 50,
    ) -> Tuple[List[Admin], int]:
        stmt = select(Admin)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        sort_col = getattr(Admin, sort, Admin.created_at)
        if order == "desc":
            stmt = stmt.order_by(desc(sort_col))
        else:
            stmt = stmt.order_by(sort_col)

        stmt = stmt.limit(end - start).offset(start)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def deactivate(self, admin_id: int) -> Optional[Admin]:
        return await self.update(admin_id, {"active": False})

    async def list_active_telegram_ids(self) -> List[int]:
        result = await self.db.execute(select(Admin.telegram_id).where(Admin.active.is_(True)))
        return list(result.scalars().all())


class AdminLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(
        self,
        admin_id: int,
        action: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        before_data: Optional[str] = None,
        after_data: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> AdminLog:
        log = AdminLog(
            admin_id=admin_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_data=before_data,
            after_data=after_data,
            ip_address=ip_address,
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def list(
        self,
        sort: str = "created_at",
        order: str = "desc",
        start: int = 0,
        end: int = 50,
    ) -> Tuple[List[AdminLog], int]:
        stmt = select(AdminLog)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        sort_col = getattr(AdminLog, sort, AdminLog.created_at)
        if order == "desc":
            stmt = stmt.order_by(desc(sort_col))
        else:
            stmt = stmt.order_by(sort_col)

        stmt = stmt.limit(end - start).offset(start)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def get_by_id(self, log_id: int) -> Optional[AdminLog]:
        result = await self.db.execute(select(AdminLog).where(AdminLog.id == log_id))
        return result.scalars().first()


class LinkDeliveryLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: int,
        order_id: int,
        product_id: int,
        google_drive_link: str,
        delivery_method: str = "sent",
        status: str = "sent",
        error: Optional[str] = None,
    ) -> LinkDeliveryLog:
        log = LinkDeliveryLog(
            user_id=user_id,
            order_id=order_id,
            product_id=product_id,
            google_drive_link=google_drive_link,
            delivery_method=delivery_method,
            status=status,
            error=error,
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def bulk_create_for_order(
        self,
        order,
        delivery_method: str = "resend",
    ) -> List[LinkDeliveryLog]:
        logs = []
        for item in order.items:
            product = item.product
            if product and product.google_drive_link:
                log = LinkDeliveryLog(
                    user_id=order.user_id,
                    order_id=order.id,
                    product_id=product.id,
                    google_drive_link=product.google_drive_link,
                    delivery_method=delivery_method,
                    status="sent",
                )
                self.db.add(log)
                logs.append(log)
        await self.db.flush()
        return logs

    async def list(
        self,
        sort: str = "sent_at",
        order: str = "desc",
        start: int = 0,
        end: int = 50,
    ) -> Tuple[List[LinkDeliveryLog], int]:
        stmt = select(LinkDeliveryLog)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        sort_col = getattr(LinkDeliveryLog, sort, LinkDeliveryLog.sent_at)
        if order == "desc":
            stmt = stmt.order_by(desc(sort_col))
        else:
            stmt = stmt.order_by(sort_col)

        stmt = stmt.limit(end - start).offset(start)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def get_by_id(self, log_id: int) -> Optional[LinkDeliveryLog]:
        result = await self.db.execute(select(LinkDeliveryLog).where(LinkDeliveryLog.id == log_id))
        return result.scalars().first()


class GoogleDriveTokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        admin_id: int,
        access_token: str,
        refresh_token: Optional[str],
        expires_at: Optional[datetime],
    ) -> GoogleDriveToken:
        token = GoogleDriveToken(
            admin_id=admin_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )
        self.db.add(token)
        await self.db.flush()
        return token

    async def get_valid_for_admin(self, admin_id: int) -> Optional[GoogleDriveToken]:
        result = await self.db.execute(
            select(GoogleDriveToken)
            .where(
                GoogleDriveToken.admin_id == admin_id,
                GoogleDriveToken.expires_at > datetime.now(timezone.utc),
            )
            .order_by(desc(GoogleDriveToken.created_at))
        )
        return result.scalars().first()


class BotMessageMapRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, admin_message_id: int, chat_id: int, ticket_id: int) -> BotMessageMap:
        mapping = BotMessageMap(admin_message_id=admin_message_id, chat_id=chat_id, ticket_id=ticket_id)
        self.db.add(mapping)
        await self.db.flush()
        return mapping

    async def get_ticket_id_by_admin_message(self, admin_message_id: int) -> Optional[int]:
        result = await self.db.execute(
            select(BotMessageMap.ticket_id).where(BotMessageMap.admin_message_id == admin_message_id)
        )
        return result.scalars().first()

    async def table_check_or_create(self) -> None:
        pass