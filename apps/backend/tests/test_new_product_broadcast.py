"""New-product broadcast: auto-enqueue on publish (de-duped) + recipients shape.

Uses the session-scoped in-memory sqlite DB (not rolled back between tests), so
every row uses a unique slug / telegram_id. Redis is faked because the notify
path lpushes to `notifications:queue`.
"""
from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select

from app.modules.notifications.models import Notification
from app.modules.users.models import User


class FakeRedis:
    def __init__(self):
        self.pushed = []

    async def lpush(self, key, value):
        self.pushed.append((key, value))


def _admin():
    return type("Admin", (), {"id": 1})()


async def _count_notifs(db, product_id):
    return await db.scalar(
        select(func.count()).select_from(Notification).where(Notification.product_id == product_id)
    )


@pytest.mark.asyncio
async def test_publish_enqueues_once_and_dedupes(db_session, monkeypatch):
    from app.modules.admin_api.products.service import ProductAdminService
    import app.modules.notifications.service as notif_service

    fake = FakeRedis()
    monkeypatch.setattr(notif_service, "redis_client", fake)

    service = ProductAdminService(db_session)
    admin = _admin()

    # Created as draft -> no notification.
    created = await service.create(admin, {"slug": "bc-draft", "status": "draft", "price_stars": 100})
    pid = created["id"]
    assert await _count_notifs(db_session, pid) == 0
    assert fake.pushed == []

    # draft -> published transition enqueues exactly one.
    await service.update(admin, pid, {"status": "published"})
    assert await _count_notifs(db_session, pid) == 1
    assert len(fake.pushed) == 1

    # Re-publishing / editing an already-published product does NOT re-notify.
    await service.update(admin, pid, {"status": "published"})
    await service.update(admin, pid, {"status": "published", "trend_score": 5})
    assert await _count_notifs(db_session, pid) == 1
    assert len(fake.pushed) == 1


@pytest.mark.asyncio
async def test_create_published_enqueues_once(db_session, monkeypatch):
    from app.modules.admin_api.products.service import ProductAdminService
    import app.modules.notifications.service as notif_service

    monkeypatch.setattr(notif_service, "redis_client", FakeRedis())
    service = ProductAdminService(db_session)

    created = await service.create(_admin(), {"slug": "bc-pub", "status": "published", "price_stars": 100})
    assert await _count_notifs(db_session, created["id"]) == 1


@pytest.mark.asyncio
async def test_recipients_endpoint_shape_and_eligibility(db_session, monkeypatch):
    from app.modules.admin_api.products.service import ProductAdminService
    from app.modules.internal_api.notifications import notification_recipients
    import app.modules.notifications.service as notif_service

    monkeypatch.setattr(notif_service, "redis_client", FakeRedis())

    service = ProductAdminService(db_session)
    created = await service.create(
        _admin(),
        {
            "slug": "bc-recipients",
            "status": "published",
            "price_stars": 100,
            "title_en": "Cool Vid",
            "title_ru": "Крутое видео",
        },
    )
    pid = created["id"]
    notif = (
        await db_session.execute(select(Notification).where(Notification.product_id == pid))
    ).scalars().first()

    now = datetime.now(timezone.utc)
    eligible = User(telegram_id=9001, selected_language="ru", started_bot_at=now,
                    notifications_enabled=True, is_blocked=False)
    no_start = User(telegram_id=9002, notifications_enabled=True, started_bot_at=None)
    disabled = User(telegram_id=9003, notifications_enabled=False, started_bot_at=now)
    blocked = User(telegram_id=9004, notifications_enabled=True, started_bot_at=now, is_blocked=True)
    db_session.add_all([eligible, no_start, disabled, blocked])
    await db_session.commit()

    resp = await notification_recipients(notif.id, db_session)

    langs = {r.telegram_id: r.lang for r in resp.recipients}
    assert langs.get(9001) == "ru"
    assert 9002 not in langs  # started_bot_at IS NULL
    assert 9003 not in langs  # notifications_enabled False
    assert 9004 not in langs  # blocked
    assert resp.product_slug == "bc-recipients"
    assert resp.titles.get("en") == "Cool Vid"
    assert resp.titles.get("ru") == "Крутое видео"
