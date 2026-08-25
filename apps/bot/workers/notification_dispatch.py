import asyncio
import logging
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from ..config import WEBAPP_URL
from ..http_client import api_client
from ..bot_instance import bot
from ..i18n import t, btn

logger = logging.getLogger(__name__)


def _build_message(lang, titles, product_slug, fallback_title, fallback_body, webapp_url):
    """Localized text + inline button. For a product broadcast the button deep
    links to the product card; a manual broadcast keeps the legacy base-url button."""
    if product_slug:
        title = titles.get(lang) or titles.get("en") or fallback_title
        text = t(lang, "new_product").format(title=title)
        url = f"{webapp_url.rstrip('/')}/product/{product_slug}"
    else:
        text = fallback_title + (f"\n{fallback_body}" if fallback_body else "")
        url = webapp_url
    kb = None
    if url.startswith("https://"):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=btn("🎬", t(lang, "view")), web_app=WebAppInfo(url=url))],
        ])
    return text, kb


async def _send(telegram_id, text, kb):
    """Send once, retrying after a Telegram rate-limit; report sent/failed."""
    try:
        await bot.send_message(telegram_id, text, reply_markup=kb)
        return "sent", None
    except TelegramRetryAfter as e:
        await asyncio.sleep(e.retry_after)
        try:
            await bot.send_message(telegram_id, text, reply_markup=kb)
            return "sent", None
        except Exception as e2:
            logger.warning("send retry failed for %s: %s", telegram_id, e2)
            return "failed", str(e2)
    except TelegramForbiddenError:
        logger.info("user %s blocked the bot", telegram_id)
        return "failed", "forbidden"
    except Exception as e:
        logger.warning("send notification failed for %s: %s", telegram_id, e)
        return "failed", str(e)


async def _ack(job_id):
    """Confirm the broadcast; without it the backend replays the whole job."""
    if not job_id:
        return
    try:
        await api_client.client.post("/internal/notifications/ack", json={"job_id": job_id})
    except Exception as e:
        logger.warning("notification ack failed for job %s: %s", job_id, e)


async def _nack(job_id, error, permanent=False):
    if not job_id:
        return
    try:
        await api_client.client.post(
            "/internal/notifications/nack",
            json={"job_id": job_id, "error": str(error)[:500], "permanent": permanent},
        )
    except Exception as e:
        logger.warning("notification nack failed for job %s: %s", job_id, e)


async def notification_dispatcher():
    while True:
        job_id = None
        try:
            try:
                payload = await api_client.pop_notification()
            except Exception as e:
                logger.warning("pop notification http error: %s", e)
                await asyncio.sleep(5)
                continue
            if not payload or payload.get("empty"):
                await asyncio.sleep(5)
                continue
            job_id = payload.get("job_id")
            notification_id = payload["notification_id"]
            fallback_title = payload.get("title") or ""
            fallback_body = payload.get("body") or ""
            webapp_url = payload.get("webapp_url") or WEBAPP_URL
            try:
                data = await api_client.get_notification_recipients(notification_id)
            except Exception as e:
                # Backend restarting / timing out: put the broadcast back.
                logger.warning("get recipients failed: %s", e)
                await _nack(job_id, f"recipients: {e}")
                continue
            product_slug = data.get("product_slug")
            titles = data.get("titles") or {}
            try:
                for r in data.get("recipients", []):
                    telegram_id = r["telegram_id"]
                    lang = r.get("lang") or "en"
                    text, kb = _build_message(
                        lang, titles, product_slug, fallback_title, fallback_body, webapp_url,
                    )
                    status, error = await _send(telegram_id, text, kb)
                    try:
                        await api_client.notification_send_result(
                            notification_id=notification_id,
                            user_telegram_id=telegram_id,
                            status=status,
                            error=error,
                        )
                    except Exception:
                        logger.warning("failed to report delivery status for %s", telegram_id,
                                       exc_info=True)
                    await asyncio.sleep(0.3)
            except Exception as e:
                logger.exception("broadcast %s interrupted: %s", notification_id, e)
                await _nack(job_id, e)
                continue
            # Per-recipient failures are already recorded one by one, so the job
            # is done even when some sends failed; replaying it would re-message
            # everyone who did receive it.
            await _ack(job_id)
        except Exception as e:
            logger.exception("notification dispatcher fatal: %s", e)
            await _nack(job_id, e)
            await asyncio.sleep(10)
