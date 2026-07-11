"""Premium-expiry reminders: /internal/bot/premium-reminders/pop selects who is
due, localizes the message, and marks each user so a period is reminded once.
Also covers the admin-service fix: naive premium_until strings parse as UTC.
"""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.core.config import settings
from app.modules.admin_api.users.repository import UserAdminRepository
from app.modules.admin_api.users.service import UserAdminService
from app.modules.internal_api.premium_reminders import pop_premium_reminders
from app.modules.users.models import User


def _user(telegram_id: int, **kw) -> User:
    defaults = dict(
        first_name="Sub",
        selected_language="en",
        is_blocked=False,
        started_bot_at=datetime.now(timezone.utc),
    )
    return User(telegram_id=telegram_id, **{**defaults, **kw})


async def test_pop_returns_due_user_and_marks_sent(db_session, monkeypatch):
    monkeypatch.setattr(settings, "telegram_webapp_url", "https://app.example.com")
    now = datetime.now(timezone.utc)
    due = _user(88010001, selected_language="ru", premium_until=now + timedelta(days=2))
    far = _user(88010002, premium_until=now + timedelta(days=10))   # outside window
    expired = _user(88010003, premium_until=now - timedelta(days=1))
    no_premium = _user(88010004)
    db_session.add_all([due, far, expired, no_premium])
    await db_session.commit()

    out = await pop_premium_reminders(db=db_session)

    assert [r["user_telegram_id"] for r in out["reminders"]] == [88010001]
    r = out["reminders"][0]
    assert due.premium_until.strftime("%d.%m.%Y") in r["message_text"]
    assert "Продлите" in r["message_text"]  # localized by selected_language
    assert r["button"] == {"text": "Продлить", "url": "https://app.example.com/subscription"}
    assert due.premium_reminder_sent_at is not None  # marked, committed by the endpoint


async def test_pop_reminds_once_per_period(db_session, monkeypatch):
    monkeypatch.setattr(settings, "telegram_webapp_url", "https://app.example.com")
    now = datetime.now(timezone.utc)
    u = _user(88010011, premium_until=now + timedelta(days=1))
    db_session.add(u)
    await db_session.commit()

    first = await pop_premium_reminders(db=db_session)
    second = await pop_premium_reminders(db=db_session)

    assert [r["user_telegram_id"] for r in first["reminders"]] == [88010011]
    assert second == {"reminders": []}


async def test_pop_reminds_again_in_new_period(db_session, monkeypatch):
    monkeypatch.setattr(settings, "telegram_webapp_url", "https://app.example.com")
    now = datetime.now(timezone.utc)
    # Reminder went out last period; the user renewed since (premium_until moved).
    u = _user(
        88010021,
        premium_until=now + timedelta(days=2),
        premium_reminder_sent_at=now - timedelta(days=40),
    )
    db_session.add(u)
    await db_session.commit()

    out = await pop_premium_reminders(db=db_session)

    assert [r["user_telegram_id"] for r in out["reminders"]] == [88010021]


async def test_pop_excludes_blocked_and_users_without_bot_chat(db_session, monkeypatch):
    monkeypatch.setattr(settings, "telegram_webapp_url", "https://app.example.com")
    now = datetime.now(timezone.utc)
    blocked = _user(88010031, premium_until=now + timedelta(days=1), is_blocked=True)
    no_chat = _user(88010032, premium_until=now + timedelta(days=1), started_bot_at=None)
    db_session.add_all([blocked, no_chat])
    await db_session.commit()

    out = await pop_premium_reminders(db=db_session)

    assert out == {"reminders": []}


async def test_admin_update_parses_premium_until_as_utc(db_session, monkeypatch):
    user = _user(88010041)
    db_session.add(user)
    await db_session.commit()

    seen: list[dict] = []

    async def capture(self, user, fields):
        seen.append(fields)
        return user

    monkeypatch.setattr(UserAdminRepository, "update", capture)
    svc = UserAdminService(db_session)
    admin = SimpleNamespace(id=1)

    await svc.update(admin, user.id, {"premium_until": "2026-08-01T12:00"})   # naive (DateTimeInput)
    await svc.update(admin, user.id, {"premium_until": "2026-08-01T14:00:00Z"})
    await svc.update(admin, user.id, {"premium_until": ""})

    assert seen[0]["premium_until"] == datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
    assert seen[1]["premium_until"] == datetime(2026, 8, 1, 14, 0, tzinfo=timezone.utc)
    assert seen[2]["premium_until"] is None
