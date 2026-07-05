from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from ..config import WEBAPP_URL

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Open Mini App", web_app=WebAppInfo(url=WEBAPP_URL))],
    ])
    await message.answer("Welcome! Open the Mini App to browse videos.", reply_markup=kb)


@router.message(Command("support"))
async def cmd_support(message: Message):
    await message.answer("Support is available through the Mini App. Go to Profile → Support to create a ticket.")


@router.message(Command("paysupport"))
async def cmd_paysupport(message: Message):
    await message.answer("For payment issues, please use Support in the Mini App and select topic 'Payment issue'.")


@router.message(Command("terms"))
async def cmd_terms(message: Message):
    text = (
        "<b>Terms & Refund Policy</b>\n\n"
        "Refunds are handled manually via support.\n"
        "Digital content is delivered after successful payment.\n"
        "Google Drive links are provided for purchased videos."
    )
    await message.answer(text)
