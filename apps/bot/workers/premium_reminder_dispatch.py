import asyncio
import logging
from ..http_client import api_client
from ..bot_instance import bot
from ..delivery import build_webapp_keyboard

logger = logging.getLogger(__name__)

# Reminders are day-granular (3-day window, one per period) — hourly is plenty.
IDLE_SLEEP = 3600


async def premium_reminder_dispatcher():
    """Send "Premium expires soon" reminders. The backend owns who is due and
    the localized text/button; this loop only delivers."""
    while True:
        try:
            try:
                payload = await api_client.pop_premium_reminders()
            except Exception as e:
                logger.warning("pop premium reminders http error: %s", e)
                await asyncio.sleep(IDLE_SLEEP)
                continue
            reminders = payload.get("reminders") or []
            if not reminders:
                await asyncio.sleep(IDLE_SLEEP)
                continue
            for r in reminders:
                user_telegram_id = r.get("user_telegram_id")
                message_text = r.get("message_text")
                if not user_telegram_id or not message_text:
                    continue
                try:
                    await bot.send_message(
                        user_telegram_id, message_text,
                        reply_markup=build_webapp_keyboard(r.get("button")),
                    )
                except Exception as e:
                    logger.warning("premium reminder send failed for %s: %s", user_telegram_id, e)
                await asyncio.sleep(0.5)  # stay under Telegram's rate limit
            # Full batch may mean more are due — loop pops again immediately.
        except Exception as e:
            logger.exception("premium reminder dispatcher fatal: %s", e)
            await asyncio.sleep(IDLE_SLEEP)
