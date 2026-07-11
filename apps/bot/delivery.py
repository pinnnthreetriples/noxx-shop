"""Native video delivery: copy purchased videos from the private channel to the
buyer. copyMessage references files already on Telegram, so it bypasses the Bot
API 50 MB upload limit (videos can be up to 2 GB) and hides the source channel.
protect_content stops the buyer forwarding or saving the file."""
import asyncio
import logging

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from .bot_instance import bot
from .i18n import green_btn

logger = logging.getLogger(__name__)


def build_webapp_keyboard(button):
    """Inline web-app button from a `{text, url}` payload. Requires an https url
    (Telegram rejects non-https WebApp buttons), so a misconfigured WEBAPP_URL
    degrades to a plain-text message instead of a failed send."""
    url = button.get("url") if isinstance(button, dict) else None
    if not url or not url.startswith("https://"):
        return None
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=green_btn(button.get("text") or "Open"),
                              web_app=WebAppInfo(url=url))],
    ])


async def deliver_videos(user_telegram_id: int, channel_id, videos: list) -> None:
    if not channel_id or not videos:
        return
    try:
        from_chat_id = int(channel_id)
    except (TypeError, ValueError):
        logger.warning("invalid delivery channel_id: %r", channel_id)
        return
    for message_id in videos:
        try:
            await bot.copy_message(
                chat_id=user_telegram_id,
                from_chat_id=from_chat_id,
                message_id=int(message_id),
                protect_content=True,
            )
        except Exception as e:
            logger.warning("video delivery failed for %s (msg %s): %s", user_telegram_id, message_id, e)
        await asyncio.sleep(0.5)  # stay under Telegram's per-chat rate limit
