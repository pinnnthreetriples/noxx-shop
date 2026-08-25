import asyncio
import logging
from ..config import TICKET_POLL_INTERVAL_SEC
from ..http_client import api_client
from ..bot_instance import bot

logger = logging.getLogger(__name__)

# A ticket that cannot reach a single admin is retried on the next polls, but
# not forever: otherwise one bad ticket blocks the cursor and every later
# ticket behind it. After this many polls it is skipped and stays unnotified in
# the admin panel (nothing is deleted), with a loud log line.
MAX_NOTIFY_ATTEMPTS = 5


def _ticket_text(t: dict) -> str:
    text = (
        f"New support ticket #{t['ticket_id']}\n"
        f"User ID: {t['user_telegram_id']}\n"
        f"Topic: {t.get('topic') or ''}\n"
        f"Created: {t.get('created_at')}"
    )
    user_message = (t.get("message") or "").strip()
    return f"{text}\n\n{user_message[:3000]}" if user_message else text


async def _notify_admins(t: dict, admin_ids: list) -> bool:
    """Send one ticket to every active admin. True once it is marked notified."""
    ticket_id = t["ticket_id"]
    text = _ticket_text(t)
    delivered = False
    for admin_tg_id in admin_ids:
        try:
            sent = await bot.send_message(admin_tg_id, text)
            delivered = True
            await api_client.record_admin_message_map(
                admin_message_id=sent.message_id,
                chat_id=sent.chat.id,
                ticket_id=ticket_id,
            )
        except Exception as e:
            logger.warning("notify admin %s failed: %s", admin_tg_id, e)
    # Only mark notified once at least one admin actually got it — marking
    # after a total failure loses the ticket for good.
    if not delivered:
        logger.error("ticket %s reached none of the %s active admin(s)",
                     ticket_id, len(admin_ids))
        return False
    try:
        await api_client.mark_ticket_notified(ticket_id)
        return True
    except Exception as e:
        # Not marked -> the ticket is re-polled and admins may get a duplicate.
        # Better than a silent loss, and this has to be visible in production
        # (was logger.debug).
        logger.error("mark_ticket_notified failed for ticket %s: %s", ticket_id, e)
        return False


async def periodic_ticket_checker():
    after_id = 0
    attempts: dict[int, int] = {}
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
            # The cursor may only advance past tickets that are actually done;
            # once one is left pending, everything after it must be re-polled.
            stalled = False
            for t in sorted(tickets, key=lambda x: x["ticket_id"]):
                ticket_id = t["ticket_id"]
                if not await _notify_admins(t, admin_ids):
                    tries = attempts[ticket_id] = attempts.get(ticket_id, 0) + 1
                    if tries < MAX_NOTIFY_ATTEMPTS:
                        stalled = True
                        continue
                    logger.error("giving up on ticket %s after %s attempts; it stays "
                                 "unnotified and is visible in the admin panel",
                                 ticket_id, tries)
                attempts.pop(ticket_id, None)
                if not stalled:
                    after_id = max(after_id, ticket_id)
        except Exception as e:
            logger.exception("ticket checker fatal: %s", e)
            await asyncio.sleep(30)
