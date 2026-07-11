import logging
from aiogram import Router, F
from aiogram.types import Message
from ..http_client import api_client
from ..bot_instance import bot
from ..delivery import deliver_videos, build_webapp_keyboard

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payment = message.successful_payment
    try:
        result = await api_client.successful_payment(
            invoice_payload=payment.invoice_payload,
            telegram_payment_charge_id=payment.telegram_payment_charge_id,
            provider_payment_charge_id=payment.provider_payment_charge_id,
            total_amount=payment.total_amount,
        )
    except Exception as e:
        logger.exception("successful_payment internal API error: %s", e)
        await message.answer("Payment processed but server error. Contact support.")
        return
    if not result.get("ok"):
        await message.answer("Payment processed but order not found.")
        return
    user_telegram_id = result.get("user_telegram_id")
    message_text = result.get("message_text") or f"Order #{result.get('order_id')} received."
    if user_telegram_id:
        # Send message to user; "My purchases" keyboard on the last chunk,
        # same as the crypto delivery worker.
        kb = build_webapp_keyboard(result.get("button"))
        chunks = [message_text[i:i + 4000] for i in range(0, len(message_text), 4000)]
        try:
            for i, chunk in enumerate(chunks):
                await bot.send_message(user_telegram_id, chunk,
                                       reply_markup=kb if i == len(chunks) - 1 else None)
        except Exception as e:
            logger.warning("send delivery message failed: %s", e)
        await deliver_videos(user_telegram_id, result.get("channel_id"), result.get("videos") or [])
    await message.answer("Payment successful! ✅")
