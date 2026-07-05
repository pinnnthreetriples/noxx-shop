import json
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import settings
from app.modules.internal_api.schemas import (
    NotificationSendResultRequest, NotificationSendResultResponse,
    PopNotificationResponse,
    NotificationRecipientsResponse,
)
import redis.asyncio as redis_async
from app.modules.notifications.service import NotificationService
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
    user_repo = UserRepository(db)
    users = await user_repo.list_for_notifications()
    return NotificationRecipientsResponse(user_telegram_ids=[u.telegram_id for u in users])