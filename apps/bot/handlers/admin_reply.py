import logging
from aiogram import Router, F
from aiogram.types import Message
from ..http_client import api_client
from ..bot_instance import bot

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.reply_to_message)
async def handle_admin_reply(message: Message):
    if not message.reply_to_message:
        return
    file_url = None
    file_type = None
    text = message.text or message.caption or ""
    if message.photo:
        file_type = "photo"
        file_url = message.photo[-1].file_id
    elif message.document:
        file_type = "document"
        file_url = message.document.file_id
    try:
        result = await api_client.admin_reply(
            admin_telegram_id=message.from_user.id,
            reply_to_message_id=message.reply_to_message.message_id,
            text=text,
            file_url=file_url,
            file_type=file_type,
        )
    except Exception as e:
        logger.exception("admin_reply internal API error: %s", e)
        return
    if not result.get("ok"):
        await message.answer(f"Cannot forward: {result.get('error', 'unknown')}")
        return
    user_telegram_id = result.get("user_telegram_id")
    if not user_telegram_id:
        await message.answer("User not found.")
        return
    reply_text = result.get("text") or ""
    file_url_out = result.get("file_url")
    file_type_out = result.get("file_type")
    try:
        if file_type_out == "photo" and file_url_out:
            await bot.send_photo(user_telegram_id, file_url_out, caption=reply_text)
        elif file_type_out == "document" and file_url_out:
            await bot.send_document(user_telegram_id, file_url_out, caption=reply_text)
        else:
            await bot.send_message(user_telegram_id, reply_text)
        await message.answer("Ответ отправлен пользователю.")
    except Exception as e:
        logger.warning("send admin reply to user failed: %s", e)
        await message.answer("Не удалось отправить пользователю.")
