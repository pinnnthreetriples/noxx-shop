import asyncio
import contextlib
import logging
from aiogram import Dispatcher

from .bot_instance import bot
from .http_client import api_client
from .handlers import start as handlers_start
from .handlers import pre_checkout, successful_payment, admin_reply
from .workers import ticket_notifications, notification_dispatch, delivery_dispatch

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
    task.add_done_callback(lambda t: t.exception() and logger.exception("background task crashed: %r", t.exception()))
    return task


@dp.startup()
async def on_startup():
    await api_client.start()
    _spawn(ticket_notifications.periodic_ticket_checker())
    _spawn(notification_dispatch.notification_dispatcher())
    _spawn(delivery_dispatch.delivery_dispatcher())


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
