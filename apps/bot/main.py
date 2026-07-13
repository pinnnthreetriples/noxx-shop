import asyncio
import contextlib
import logging
import sentry_sdk
from aiogram import Dispatcher
from aiogram.exceptions import TelegramNetworkError, TelegramServerError

from .config import SENTRY_DSN, APP_ENV
from .bot_instance import bot

# Errors-only; the logging integration reports the logger.exception calls below.
# Drop shutdown task-cancellation and transient api.telegram.org connectivity
# blips — neither is an actionable defect, they just spam Sentry. TelegramServerError
# is Telegram answering 5xx (Bad Gateway); it's their outage, not our bug. (Kept
# inside the `if` so the imports below stay E402-clean.)
if SENTRY_DSN:
    _TRANSIENT_TG = (asyncio.CancelledError, TelegramNetworkError, TelegramServerError)

    def _before_send(event, hint):
        exc = hint.get("exc_info")
        if exc and isinstance(exc[1], _TRANSIENT_TG):
            return None
        # aiogram's polling loop logs "Failed to fetch updates - TelegramNetworkError: ..."
        # without exc_info, so the isinstance check above never sees it.
        record = hint.get("log_record")
        if record and record.name == "aiogram.dispatcher" and any(
            name in record.getMessage() for name in ("TelegramNetworkError", "TelegramServerError")
        ):
            return None
        return event
    sentry_sdk.init(dsn=SENTRY_DSN, environment=APP_ENV, send_default_pii=False, before_send=_before_send)
from .http_client import api_client
from .handlers import start as handlers_start
from .handlers import pre_checkout, successful_payment, admin_reply
from .workers import ticket_notifications, notification_dispatch, delivery_dispatch, premium_reminder_dispatch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp = Dispatcher()

# Register handlers
dp.include_router(handlers_start.router)
dp.include_router(pre_checkout.router)
dp.include_router(successful_payment.router)
dp.include_router(admin_reply.router)

# Keep strong references to background tasks so the GC doesn't drop them.
_background_tasks: set[asyncio.Task] = set()


def _spawn(coro):
    """Create a background task and remember it; log exceptions instead of swallowing."""
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    task.add_done_callback(lambda t: not t.cancelled() and t.exception() and logger.exception("background task crashed: %r", t.exception()))
    return task


@dp.startup()
async def on_startup():
    await api_client.start()
    _spawn(ticket_notifications.periodic_ticket_checker())
    _spawn(notification_dispatch.notification_dispatcher())
    _spawn(delivery_dispatch.delivery_dispatcher())
    _spawn(premium_reminder_dispatch.premium_reminder_dispatcher())


@dp.shutdown()
async def on_shutdown():
    # Cancel background workers cleanly so they don't keep polling.
    for task in list(_background_tasks):
        task.cancel()
    for task in list(_background_tasks):
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await task
    _background_tasks.clear()
    await api_client.close()
    await bot.session.close()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
