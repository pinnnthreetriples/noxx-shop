import asyncio
import logging
from ..config import TICKET_POLL_INTERVAL_SEC
from ..http_client import api_client
from ..bot_instance import bot

logger = logging.getLogger(__name__)


async def periodic_ticket_checker():
    after_id = 0
    while True:
        try:
            await asyncio.sleep(TICKET_POLL_INTERVAL_SEC)
            try:
                result = await api_client.fetch_unnotified_tickets(after_id=after_id, limit=50)
            except Exception as e:
                logger.warning("ticket poll http error: %s", e)
                continue
            tickets = result.get("tickets", [])
            if not tickets:
                continue
            admin_ids = await api_client.get_active_admin_telegram_ids()
            for t in tickets:
                ticket_id = t["ticket_id"]
                user_telegram_id = t["user_telegram_id"]
                topic = t.get("topic") or ""
                created_at = t.get("created_at")
                text = (
                    f"New support ticket #{ticket_id}\n"
                    f"User ID: {user_telegram_id}\n"
                    f"Topic: {topic}\n"
                    f"Created: {created_at}"
                )
                for admin_tg_id in admin_ids:
                    try:
                        sent = await bot.send_message(admin_tg_id, text)
                        await api_client.record_admin_message_map(
                            admin_message_id=sent.message_id,
                            chat_id=sent.chat.id,
                            ticket_id=ticket_id,
                        )
                    except Exception as e:
                        logger.warning("notify admin %s failed: %s", admin_tg_id, e)
                # after successful dispatch mark ticket as notified
                try:
                    await api_client.mark_ticket_notified(ticket_id)
                except Exception:
                    logger.debug("mark_ticket_notified failed", exc_info=True)
                after_id = max(after_id, ticket_id)
        except Exception as e:
            logger.exception("ticket checker fatal: %s", e)
            await asyncio.sleep(30)
