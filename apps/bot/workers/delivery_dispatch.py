import asyncio
import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from ..http_client import api_client
from ..bot_instance import bot

logger = logging.getLogger(__name__)


def _build_keyboard(button):
    """Inline web-app button from a `{text, url}` payload; None if absent/invalid."""
    if not isinstance(button, dict) or not button.get("url"):
        return None
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=button.get("text") or "Open",
                              web_app=WebAppInfo(url=button["url"]))],
    ])


async def delivery_dispatcher():
    """Send queued per-user delivery messages (crypto payments, premium claims)."""
    while True:
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
            user_telegram_id = payload.get("user_telegram_id")
            message_text = payload.get("message_text")
            if not user_telegram_id or not message_text:
                continue
            kb = _build_keyboard(payload.get("button"))
            try:
                await bot.send_message(user_telegram_id, message_text, reply_markup=kb)
            except Exception as e:
                logger.warning("delivery send failed for %s: %s", user_telegram_id, e)
        except Exception as e:
            logger.exception("delivery dispatcher fatal: %s", e)
            await asyncio.sleep(10)
