import asyncio
import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from ..config import WEBAPP_URL
from ..http_client import api_client
from ..bot_instance import bot

logger = logging.getLogger(__name__)


async def notification_dispatcher():
    while True:
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
            notification_id = payload["notification_id"]
            title = payload.get("title") or ""
            body = payload.get("body") or ""
            webapp_url = payload.get("webapp_url") or WEBAPP_URL
            text = title + (f"\n{body}" if body else "")
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Open preview", web_app=WebAppInfo(url=webapp_url))],
            ])
            # list of recipients from internal API
            try:
                recipients = await api_client.get_notification_recipients(notification_id)
            except Exception as e:
                logger.warning("get recipients failed: %s", e)
                continue
            for user_telegram_id in recipients:
                try:
                    await bot.send_message(user_telegram_id, text, reply_markup=kb)
                    await api_client.notification_send_result(
                        notification_id=notification_id,
                        user_telegram_id=user_telegram_id,
                        status="sent",
                    )
                    await asyncio.sleep(0.3)
                except Exception as e:
                    logger.warning("send notification failed for %s: %s", user_telegram_id, e)
                    try:
                        await api_client.notification_send_result(
                            notification_id=notification_id,
                            user_telegram_id=user_telegram_id,
                            status="failed",
                            error=str(e),
                        )
                    except Exception:
                        pass
        except Exception as e:
            logger.exception("notification dispatcher fatal: %s", e)
            await asyncio.sleep(10)
