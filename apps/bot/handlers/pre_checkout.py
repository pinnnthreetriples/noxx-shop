import logging
from aiogram import Router
from aiogram.types import PreCheckoutQuery
from ..http_client import api_client
from ..bot_instance import bot

logger = logging.getLogger(__name__)

router = Router()


@router.pre_checkout_query()
async def process_pre_checkout(query: PreCheckoutQuery):
    try:
        result = await api_client.pre_checkout(
            invoice_payload=query.invoice_payload,
            total_amount=query.total_amount,
        )
        ok = bool(result.get("ok"))
        error = result.get("error_message") or "Order invalid"
    except Exception as e:
        logger.warning("pre_checkout internal API error: %s", e)
        ok = False
        error = "Internal error"
    await bot.answer_pre_checkout_query(query.id, ok=ok, error_message=None if ok else error)
