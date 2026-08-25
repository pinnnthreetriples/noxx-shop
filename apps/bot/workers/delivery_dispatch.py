import asyncio
import logging

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from ..http_client import api_client
from ..bot_instance import bot
from ..delivery import deliver_videos, build_webapp_keyboard

logger = logging.getLogger(__name__)

# Telegram hard-caps a text message at 4096 chars and a delivery message grows
# ~120 chars per video, so a large order must be split. Same split as the Stars
# path in handlers/successful_payment.py.
CHUNK_SIZE = 4000


async def _ack(job_id):
    """Confirm delivery; without it the backend replays the job."""
    if not job_id:
        return
    try:
        await api_client.client.post("/internal/bot/deliveries/ack", json={"job_id": job_id})
    except Exception as e:
        # Job stays in processing and is replayed after the visibility timeout:
        # the buyer may get the message twice, which beats losing it.
        logger.warning("delivery ack failed for job %s: %s", job_id, e)


async def _nack(job_id, error, permanent=False):
    if not job_id:
        return
    try:
        await api_client.client.post(
            "/internal/bot/deliveries/nack",
            json={"job_id": job_id, "error": str(error)[:500], "permanent": permanent},
        )
    except Exception as e:
        logger.warning("delivery nack failed for job %s: %s", job_id, e)


async def delivery_dispatcher():
    """Send queued per-user delivery messages (crypto payments, premium claims)."""
    while True:
        job_id = None
        try:
            try:
                payload = await api_client.pop_delivery()
            except Exception as e:
                logger.warning("pop delivery http error: %s", e)
                await asyncio.sleep(5)
                continue
            if not payload or payload.get("empty"):
                await asyncio.sleep(3)
                continue
            job_id = payload.get("job_id")
            user_telegram_id = payload.get("user_telegram_id")
            message_text = payload.get("message_text")
            if not user_telegram_id or not message_text:
                await _nack(job_id, "empty delivery payload", permanent=True)
                continue
            kb = build_webapp_keyboard(payload.get("button"))
            chunks = [message_text[i:i + CHUNK_SIZE]
                      for i in range(0, len(message_text), CHUNK_SIZE)]
            try:
                for i, chunk in enumerate(chunks):
                    await bot.send_message(user_telegram_id, chunk,
                                           reply_markup=kb if i == len(chunks) - 1 else None)
            except (TelegramForbiddenError, TelegramBadRequest) as e:
                # Bot blocked / message unsendable — replaying it forever would
                # just clog the queue, so retire it to the dead-letter list.
                logger.error("delivery undeliverable to %s: %s", user_telegram_id, e)
                await _nack(job_id, e, permanent=True)
                continue
            except Exception as e:
                logger.warning("delivery send failed for %s: %s", user_telegram_id, e)
                await _nack(job_id, e)
                continue
            # deliver_videos swallows its own per-video errors.
            await deliver_videos(user_telegram_id, payload.get("channel_id"),
                                 payload.get("videos") or [])
            await _ack(job_id)
        except Exception as e:
            logger.exception("delivery dispatcher fatal: %s", e)
            await _nack(job_id, e)
            await asyncio.sleep(10)
