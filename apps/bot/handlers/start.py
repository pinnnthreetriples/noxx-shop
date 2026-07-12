from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from ..config import WEBAPP_URL
from ..i18n import t, norm_lang, btn

router = Router()


def _lang(message: Message) -> str:
    return norm_lang(message.from_user.language_code if message.from_user else None)


def _app_kb(lang: str, label_key: str, emoji: str, path: str = "") -> InlineKeyboardMarkup | None:
    """One web-app button into the mini app (optionally a deep path).
    Telegram rejects non-https WebApp buttons, so degrade to no button."""
    if not WEBAPP_URL.startswith("https://"):
        return None
    url = f"{WEBAPP_URL.rstrip('/')}{path}" if path else WEBAPP_URL
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn(emoji, t(lang, label_key)), web_app=WebAppInfo(url=url))],
    ])


@router.message(CommandStart())
async def cmd_start(message: Message):
    lang = _lang(message)
    await message.answer(t(lang, "welcome"), reply_markup=_app_kb(lang, "open_app", "🛍️"))


@router.message(Command("support"))
async def cmd_support(message: Message):
    lang = _lang(message)
    await message.answer(t(lang, "support_cmd"), reply_markup=_app_kb(lang, "open_support", "💬", "/support"))


@router.message(Command("paysupport"))
async def cmd_paysupport(message: Message):
    lang = _lang(message)
    await message.answer(t(lang, "paysupport_cmd"), reply_markup=_app_kb(lang, "open_support", "💳", "/support"))


@router.message(Command("terms"))
async def cmd_terms(message: Message):
    # The full localized terms/refund text lives in the mini app (/terms),
    # editable from the admin — the bot only points there.
    lang = _lang(message)
    await message.answer(t(lang, "terms_cmd"), reply_markup=_app_kb(lang, "open_terms", "📄", "/terms"))
