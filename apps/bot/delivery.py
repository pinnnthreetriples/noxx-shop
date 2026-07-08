"""Native video delivery: copy purchased videos from the private channel to the
buyer. copyMessage references files already on Telegram, so it bypasses the Bot
API 50 MB upload limit (videos can be up to 2 GB) and hides the source channel.
protect_content stops the buyer forwarding or saving the file."""
import asyncio
import logging

from .bot_instance import bot

logger = logging.getLogger(__name__)


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
