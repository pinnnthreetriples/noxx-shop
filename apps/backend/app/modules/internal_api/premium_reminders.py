"""Premium-expiry reminders: the bot polls this endpoint and just sends what it
gets — the backend owns who is due, the localized text and the button."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.modules.users.models import User

router = APIRouter(tags=["internal-premium-reminders"])

# Remind once per paid period, this many days before premium_until.
REMINDER_DAYS = 3
BATCH_LIMIT = 50

# Same language set as _MY_PURCHASES in orders/service.py (mo = Moldovan, same
# wording as Romanian). {date} is premium_until as dd.mm.yyyy.
_REMINDER_TEXT = {
    "en": "⏳ <b>Premium expires on {date}</b>.\nRenew to keep your access.",
    "ru": "⏳ <b>Premium заканчивается {date}</b>.\nПродлите, чтобы не потерять доступ.",
    "de": "⏳ <b>Premium läuft am {date} ab</b>.\nVerlängern Sie, um den Zugang zu behalten.",
    "el": "⏳ <b>Το Premium λήγει στις {date}</b>.\nΑνανεώστε για να κρατήσετε την πρόσβαση.",
    "ro": "⏳ <b>Premium expiră pe {date}</b>.\nPrelungește ca să nu pierzi accesul.",
    "mo": "⏳ <b>Premium expiră pe {date}</b>.\nPrelungește ca să nu pierzi accesul.",
    "bg": "⏳ <b>Premium изтича на {date}</b>.\nПодновете, за да запазите достъпа.",
    "sr": "⏳ <b>Premium истиче {date}</b>.\nПродужите да не изгубите приступ.",
    "tr": "⏳ <b>Premium {date} tarihinde sona eriyor</b>.\nErişimi kaybetmemek için uzatın.",
}
_RENEW = {
    "en": "Renew", "ru": "Продлить", "de": "Verlängern",
    "el": "Ανανέωση", "ro": "Prelungește", "mo": "Prelungește",
    "bg": "Поднови", "sr": "Продужи", "tr": "Uzat",
}


def _needs_reminder(user: User) -> bool:
    """Not yet reminded for the CURRENT period. A sent_at older than the start
    of the reminder window belongs to a previous period (user renewed since)."""
    sent = user.premium_reminder_sent_at
    if user.premium_until is None:
        return False
    return sent is None or sent < user.premium_until - timedelta(days=REMINDER_DAYS)


@router.post("/bot/premium-reminders/pop")
async def pop_premium_reminders(db: AsyncSession = Depends(get_db)):
    """Bot pops a batch of "Premium expires soon" reminder messages."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(User)
        .where(
            User.is_blocked.is_(False),
            # No private chat with the bot -> send would 403.
            User.started_bot_at.isnot(None),
            User.premium_until.isnot(None),
            User.premium_until > now,
            User.premium_until <= now + timedelta(days=REMINDER_DAYS),
        )
        # Never-reminded first, so already-reminded rows can't starve the batch.
        .order_by(User.premium_reminder_sent_at.asc().nullsfirst(), User.premium_until.asc())
        .limit(BATCH_LIMIT)
    )
    # Per-period dedup compares two DB columns; interval arithmetic in SQL isn't
    # portable to the sqlite test DB, so filter the (small) window batch in Python.
    due = [u for u in result.scalars().all() if _needs_reminder(u)]
    if not due:
        return {"reminders": []}

    webapp = settings.telegram_webapp_url.rstrip("/")
    reminders = []
    for u in due:
        premium_until = u.premium_until
        if premium_until is None:
            continue
        lang = (u.selected_language or u.language_code or "en").lower()
        text = _REMINDER_TEXT.get(lang) or _REMINDER_TEXT.get(lang[:2], _REMINDER_TEXT["en"])
        label = _RENEW.get(lang) or _RENEW.get(lang[:2], _RENEW["en"])
        reminders.append({
            "user_telegram_id": u.telegram_id,
            "message_text": text.format(date=premium_until.strftime("%d.%m.%Y")),
            "button": {"text": label, "url": f"{webapp}/subscription"} if webapp else None,
        })
        u.premium_reminder_sent_at = now
    # ponytail: mark-then-send — commit BEFORE handing the batch to the bot, so a
    # bot crash loses a reminder instead of re-sending it forever. It's a nudge,
    # not a receipt; the cheap failure mode is the silent one.
    await db.commit()
    return {"reminders": reminders}
