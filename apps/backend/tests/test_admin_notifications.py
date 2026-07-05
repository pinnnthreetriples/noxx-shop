"""Tests that admin-created notifications enqueue the FULL payload to Redis.

Regression test for bug: admin_api/notifications/service.py was lpush-ing
only `{"notification_id": id}`, so the bot's notification dispatcher
received None for title/body and sent empty messages to users.

The fix is to include title, body, and product_id in the JSON payload
pushed to the `notifications:queue` Redis list.
"""
import json
import pytest


class FakeRedis:
    """Captures lpush calls for assertion without hitting a real Redis."""
    def __init__(self):
        self.pushed = []

    async def lpush(self, key, value):
        self.pushed.append((key, value))


@pytest.mark.asyncio
async def test_create_enqueue_includes_title_body_product_id(db_session, monkeypatch):
    """NotificationAdminService.create must push full payload {notification_id, title, body, product_id}."""
    from app.modules.admin_api.notifications.service import NotificationAdminService

    fake = FakeRedis()
    import app.core.redis_client as redis_module
    monkeypatch.setattr(redis_module, "redis_client", fake)

    service = NotificationAdminService(db_session)
    # service.create uses admin.id implicitly; stub a minimal admin object.
    admin = type("Admin", (), {"id": 1})()

    notif = await service.create(
        admin,
        {"title": "Summer sale", "body": "Use code SUMMER15", "product_id": 42},
    )

    assert len(fake.pushed) == 1, "redis_client.lpush must be called exactly once"
    key, value = fake.pushed[0]
    assert key == "notifications:queue"
    payload = json.loads(value)
    assert payload["notification_id"] == notif.id
    assert payload["title"] == "Summer sale"
    assert payload["body"] == "Use code SUMMER15"
    assert payload["product_id"] == 42


@pytest.mark.asyncio
async def test_create_enqueue_preserves_none_values(db_session, monkeypatch):
    """Body and product_id may be None — payload must include them explicitly as null."""
    from app.modules.admin_api.notifications.service import NotificationAdminService

    fake = FakeRedis()
    import app.core.redis_client as redis_module
    monkeypatch.setattr(redis_module, "redis_client", fake)

    service = NotificationAdminService(db_session)
    admin = type("Admin", (), {"id": 1})()

    notif = await service.create(
        admin,
        {"title": "Heads up", "body": None, "product_id": None},
    )

    payload = json.loads(fake.pushed[0][1])
    assert payload["notification_id"] == notif.id
    assert payload["title"] == "Heads up"
    assert "body" in payload and payload["body"] is None
    assert "product_id" in payload and payload["product_id"] is None
