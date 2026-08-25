import logging
from typing import Optional
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
from app.modules.internal_api.bot_delivery import (
    NOTIFICATION_QUEUE, JobAck, ack_job, get_redis, nack_job, reliable_pop,
)
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


class PopNotificationJob(PopNotificationResponse):
    """Pop response + the handle the bot needs to ack/nack the broadcast."""
    job_id: Optional[str] = None


@router.post("/pop", response_model=PopNotificationJob)
async def pop_notification():
    """Bot pops a notification job from the Redis queue. The job stays in the
    processing list until the bot acks it, so a backend/bot failure between the
    pop and the last recipient replays the broadcast instead of losing it."""
    try:
        payload, job_id = await reliable_pop(get_redis(), NOTIFICATION_QUEUE)
    except Exception as e:
        logger.warning("redis pop failed: %s", e)
        return PopNotificationJob(empty=True)

    if payload is None:
        return PopNotificationJob(empty=True)

    notification_id = payload.get("notification_id")
    if not notification_id:
        # Nothing identifies this broadcast, so no retry can rescue it.
        await nack_job(get_redis(), NOTIFICATION_QUEUE, job_id,
                       "missing notification_id", permanent=True)
        return PopNotificationJob(empty=True)

    return PopNotificationJob(
        empty=False,
        job_id=job_id,
        notification_id=notification_id,
        title=payload.get("title"),
        body=payload.get("body"),
        product_id=payload.get("product_id"),
        webapp_url=settings.telegram_webapp_url,
    )


@router.post("/ack")
async def ack_notification(payload: JobAck):
    """Broadcast finished — drop the job for good."""
    try:
        return {"ok": await ack_job(get_redis(), NOTIFICATION_QUEUE, payload.job_id)}
    except Exception as e:
        logger.error("notification ack failed for job %s: %s", payload.job_id, e)
        return {"ok": False}


@router.post("/nack")
async def nack_notification(payload: JobAck):
    """Broadcast failed — requeue it, or dead-letter it once attempts run out."""
    try:
        return {"ok": await nack_job(get_redis(), NOTIFICATION_QUEUE, payload.job_id,
                                     payload.error, payload.permanent)}
    except Exception as e:
        logger.error("notification nack failed for job %s: %s", payload.job_id, e)
        return {"ok": False}


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