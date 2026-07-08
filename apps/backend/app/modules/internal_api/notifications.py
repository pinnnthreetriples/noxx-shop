import json
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import settings
from sqlalchemy import select
from app.modules.internal_api.schemas import (
    NotificationSendResultRequest, NotificationSendResultResponse,
    PopNotificationResponse,
    NotificationRecipientsResponse, NotificationRecipientItem,
)
import redis.asyncio as redis_async
from app.modules.notifications.service import NotificationService
from app.modules.notifications.repository import NotificationRepository
from app.modules.catalog.models import Product, ProductTranslation
from app.modules.users.repository import UserRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["internal-notifications"])


@router.post("/send-result", response_model=NotificationSendResultResponse)
async def notification_send_result(payload: NotificationSendResultRequest, db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    user = await user_repo.get_by_telegram_id(payload.user_telegram_id)
    if not user:
        return NotificationSendResultResponse(ok=False)
    service = NotificationService(db)
    if payload.status == "sent":
        await service.mark_sent(payload.notification_id, user.id)
    else:
        await service.mark_failed(payload.notification_id, user.id, payload.error or "unknown")
    return NotificationSendResultResponse(ok=True)


@router.post("/pop", response_model=PopNotificationResponse)
async def pop_notification():
    """Bot pops a notification job from Redis queue. Returns empty=True if queue is empty."""
    try:
        r = redis_async.from_url(settings.redis_url, decode_responses=True)
        try:
            data = await r.rpop("notifications:queue")
        finally:
            await r.aclose()
    except Exception as e:
        logger.warning("redis pop failed: %s", e)
        return PopNotificationResponse(empty=True)
    
    if not data:
        return PopNotificationResponse(empty=True)
    
    try:
        payload = json.loads(data)
    except Exception:
        return PopNotificationResponse(empty=True)
    
    notification_id = payload.get("notification_id")
    if not notification_id:
        return PopNotificationResponse(empty=True)
    
    return PopNotificationResponse(
        empty=False,
        notification_id=notification_id,
        title=payload.get("title"),
        body=payload.get("body"),
        product_id=payload.get("product_id"),
        webapp_url=settings.telegram_webapp_url,
    )


@router.get("/{notification_id}/recipients", response_model=NotificationRecipientsResponse)
async def notification_recipients(notification_id: int, db: AsyncSession = Depends(get_db)):
    users = await UserRepository(db).list_for_notifications()
    recipients = [
        NotificationRecipientItem(telegram_id=u.telegram_id, lang=u.selected_language or "en")
        for u in users
    ]
    # For a product broadcast, hand the bot the slug (deep link) and the
    # per-language titles so it can localize the message; the bot falls back
    # to the "en" title and then the notification title when one is missing.
    product_slug = None
    titles: dict[str, str] = {}
    notif = await NotificationRepository(db).get_by_id(notification_id)
    if notif and notif.product_id:
        product = (
            await db.execute(select(Product.slug).where(Product.id == notif.product_id))
        ).scalars().first()
        product_slug = product
        rows = await db.execute(
            select(ProductTranslation.language_code, ProductTranslation.title)
            .where(ProductTranslation.product_id == notif.product_id)
        )
        titles = {code: title for code, title in rows.all()}
    return NotificationRecipientsResponse(
        recipients=recipients, product_slug=product_slug, titles=titles
    )