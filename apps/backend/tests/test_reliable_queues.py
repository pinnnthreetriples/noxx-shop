"""Delivery / broadcast queues must survive a failed send.

Before: both queues used a bare RPOP — the job was destroyed the moment the bot
asked for it, so any failure between the pop and send_message (bot restart,
network, Telegram 4xx, backend restart mid-broadcast) lost a paid delivery or a
whole broadcast forever.

Now: LMOVE into a `:processing` list + an `:inflight` hash, removed only on ack.
These tests pin the properties that matter: nothing disappears without an ack,
a replay eventually gives up instead of looping forever, and an admin-created
notification is committed before it is announced to the bot.
"""
import json
import time

import pytest

from app.modules.internal_api.bot_delivery import (
    DELIVERY_QUEUE,
    NOTIFICATION_QUEUE,
    JobAck,
    _LIMITS,
    ack_delivery,
    ack_job,
    nack_job,
    pop_delivery,
    reliable_pop,
)


class FakeRedis:
    """Enough of the redis list/hash API for the reliable-queue helpers."""

    def __init__(self):
        self.lists: dict[str, list[str]] = {}
        self.hashes: dict[str, dict[str, str]] = {}

    async def lpush(self, key, *values):
        self.lists.setdefault(key, [])[0:0] = list(reversed(values))
        return len(self.lists[key])

    async def llen(self, key):
        return len(self.lists.get(key, []))

    async def lrange(self, key, start, end):
        items = self.lists.get(key, [])
        return items[start:] if end == -1 else items[start:end + 1]

    async def ltrim(self, key, start, end):
        items = self.lists.get(key, [])
        self.lists[key] = items[start:] if end == -1 else items[start:end + 1]

    async def lrem(self, key, count, value):
        items = self.lists.get(key, [])
        if value not in items:
            return 0
        items.remove(value)
        return 1

    async def lmove(self, src, dst, src_side="LEFT", dst_side="RIGHT"):
        items = self.lists.get(src, [])
        if not items:
            return None
        value = items.pop() if src_side.upper() == "RIGHT" else items.pop(0)
        target = self.lists.setdefault(dst, [])
        if dst_side.upper() == "LEFT":
            target.insert(0, value)
        else:
            target.append(value)
        return value

    async def hset(self, key, field, value):
        self.hashes.setdefault(key, {})[field] = value

    async def hget(self, key, field):
        return self.hashes.get(key, {}).get(field)

    async def hgetall(self, key):
        return dict(self.hashes.get(key, {}))

    async def hdel(self, key, *fields):
        h = self.hashes.get(key, {})
        for f in fields:
            h.pop(f, None)


def _keys(queue):
    return f"{queue}:processing", f"{queue}:inflight", f"{queue}:dead"


def _use(monkeypatch, fake):
    """All queue helpers resolve the client through app.core.redis_client."""
    import app.core.redis_client as redis_module
    monkeypatch.setattr(redis_module, "redis_client", fake)
    return fake


def _expire_inflight(fake, queue):
    """Pretend every in-flight job was popped long ago (worker died)."""
    _, inflight, _ = _keys(queue)
    for job_id, meta_raw in fake.hashes.get(inflight, {}).items():
        meta = json.loads(meta_raw)
        meta["popped_at"] = time.time() - 10_000
        fake.hashes[inflight][job_id] = json.dumps(meta)


@pytest.mark.asyncio
async def test_pop_keeps_the_job_until_it_is_acked():
    fake = FakeRedis()
    await fake.lpush(DELIVERY_QUEUE, json.dumps({"user_telegram_id": 1, "message_text": "hi"}))

    payload, job_id = await reliable_pop(fake, DELIVERY_QUEUE)
    proc, inflight, _ = _keys(DELIVERY_QUEUE)

    assert payload["message_text"] == "hi"
    assert job_id
    assert fake.lists[DELIVERY_QUEUE] == []          # off the queue...
    assert len(fake.lists[proc]) == 1                # ...but not gone
    assert list(fake.hashes[inflight]) == [job_id]


@pytest.mark.asyncio
async def test_send_failure_puts_the_delivery_back():
    """The bot got the job and failed to send: nack must requeue it verbatim."""
    fake = FakeRedis()
    await fake.lpush(DELIVERY_QUEUE, json.dumps({"user_telegram_id": 7, "message_text": "order"}))
    _, job_id = await reliable_pop(fake, DELIVERY_QUEUE)

    assert await nack_job(fake, DELIVERY_QUEUE, job_id, "telegram 500") is True

    proc, inflight, _ = _keys(DELIVERY_QUEUE)
    assert fake.lists[proc] == []
    assert fake.hashes[inflight] == {}
    again, _ = await reliable_pop(fake, DELIVERY_QUEUE)
    assert again["message_text"] == "order"
    assert again["_attempts"] == 1


@pytest.mark.asyncio
async def test_worker_death_between_pop_and_send_replays_the_job():
    """No ack, no nack — the process just died. The next pop reclaims it."""
    fake = FakeRedis()
    await fake.lpush(DELIVERY_QUEUE, json.dumps({"user_telegram_id": 3, "message_text": "paid"}))
    first, _ = await reliable_pop(fake, DELIVERY_QUEUE)
    assert first["message_text"] == "paid"

    _expire_inflight(fake, DELIVERY_QUEUE)

    second, job_id = await reliable_pop(fake, DELIVERY_QUEUE)
    assert second["message_text"] == "paid"
    assert second["_attempts"] == 1
    assert job_id


@pytest.mark.asyncio
async def test_crash_before_the_inflight_write_is_reclaimed():
    """Entry sitting in processing with no in-flight record: the bot never saw it."""
    fake = FakeRedis()
    proc, _, _ = _keys(DELIVERY_QUEUE)
    await fake.lpush(proc, json.dumps({"user_telegram_id": 5, "message_text": "orphan"}))

    payload, _ = await reliable_pop(fake, DELIVERY_QUEUE)
    assert payload["message_text"] == "orphan"


@pytest.mark.asyncio
async def test_ack_is_the_only_thing_that_destroys_a_job():
    fake = FakeRedis()
    await fake.lpush(DELIVERY_QUEUE, json.dumps({"user_telegram_id": 2, "message_text": "done"}))
    _, job_id = await reliable_pop(fake, DELIVERY_QUEUE)

    assert await ack_job(fake, DELIVERY_QUEUE, job_id) is True

    proc, inflight, dead = _keys(DELIVERY_QUEUE)
    assert fake.lists[proc] == []
    assert fake.hashes[inflight] == {}
    assert fake.lists.get(dead, []) == []
    _expire_inflight(fake, DELIVERY_QUEUE)
    assert await reliable_pop(fake, DELIVERY_QUEUE) == (None, None)
    # A duplicate ack (bot retried the HTTP call) is a no-op, not a crash.
    assert await ack_job(fake, DELIVERY_QUEUE, job_id) is False


@pytest.mark.asyncio
async def test_a_poison_job_is_dead_lettered_instead_of_looping_forever():
    fake = FakeRedis()
    _, max_attempts = _LIMITS[DELIVERY_QUEUE]
    await fake.lpush(DELIVERY_QUEUE, json.dumps({"user_telegram_id": 4, "message_text": "poison"}))

    for _ in range(max_attempts):
        payload, job_id = await reliable_pop(fake, DELIVERY_QUEUE)
        assert payload is not None
        await nack_job(fake, DELIVERY_QUEUE, job_id, "boom")

    proc, inflight, dead = _keys(DELIVERY_QUEUE)
    assert await reliable_pop(fake, DELIVERY_QUEUE) == (None, None)
    assert fake.lists[proc] == []
    assert fake.hashes[inflight] == {}
    buried = json.loads(fake.lists[dead][0])
    assert buried["message_text"] == "poison"
    assert buried["_attempts"] == max_attempts
    assert buried["_error"] == "boom"


@pytest.mark.asyncio
async def test_permanent_failure_skips_the_remaining_attempts():
    """User blocked the bot: retrying can never work, so bury it at once."""
    fake = FakeRedis()
    await fake.lpush(DELIVERY_QUEUE, json.dumps({"user_telegram_id": 6, "message_text": "blocked"}))
    _, job_id = await reliable_pop(fake, DELIVERY_QUEUE)

    await nack_job(fake, DELIVERY_QUEUE, job_id, "forbidden", permanent=True)

    _, _, dead = _keys(DELIVERY_QUEUE)
    assert fake.lists[DELIVERY_QUEUE] == []
    assert json.loads(fake.lists[dead][0])["_error"] == "forbidden"


@pytest.mark.asyncio
async def test_delivery_endpoints_round_trip(monkeypatch):
    fake = _use(monkeypatch, FakeRedis())
    await fake.lpush(DELIVERY_QUEUE, json.dumps({
        "user_telegram_id": 11, "message_text": "hello", "videos": [1, 2],
    }))

    popped = await pop_delivery()
    assert popped["empty"] is False
    assert popped["user_telegram_id"] == 11
    assert popped["videos"] == [1, 2]
    assert popped["job_id"]

    proc, _, _ = _keys(DELIVERY_QUEUE)
    assert len(fake.lists[proc]) == 1
    assert (await ack_delivery(JobAck(job_id=popped["job_id"])))["ok"] is True
    assert fake.lists[proc] == []
    assert (await pop_delivery())["empty"] is True


@pytest.mark.asyncio
async def test_broadcast_survives_a_recipients_lookup_failure(monkeypatch):
    """The exact loss in production: pop succeeded, the recipients call failed."""
    from app.modules.internal_api.notifications import (
        ack_notification, nack_notification, pop_notification,
    )

    fake = _use(monkeypatch, FakeRedis())
    await fake.lpush(NOTIFICATION_QUEUE, json.dumps({
        "notification_id": 4242, "title": "Sale", "body": "50% off", "product_id": None,
    }))

    job = await pop_notification()
    assert job.empty is False
    assert job.notification_id == 4242
    assert job.job_id

    # Backend restarting -> bot nacks -> the broadcast is still queued.
    assert (await nack_notification(JobAck(job_id=job.job_id, error="500")))["ok"] is True
    retry = await pop_notification()
    assert retry.notification_id == 4242
    assert retry.title == "Sale"

    assert (await ack_notification(JobAck(job_id=retry.job_id)))["ok"] is True
    assert (await pop_notification()).empty is True


@pytest.mark.asyncio
async def test_admin_notification_is_committed_before_it_is_queued(db_session, monkeypatch):
    """The bot fetches recipients as soon as it sees the job; pushing before the
    commit let it read the notification back as missing (generic-text fallback)."""
    from app.modules.admin_api.notifications.service import NotificationAdminService
    import app.core.redis_client as redis_module

    events: list[str] = []

    class RecordingRedis:
        async def lpush(self, key, value):
            events.append(f"push:{key}")

    monkeypatch.setattr(redis_module, "redis_client", RecordingRedis())

    real_commit = db_session.commit

    async def spy_commit():
        events.append("commit")
        await real_commit()

    monkeypatch.setattr(db_session, "commit", spy_commit)

    service = NotificationAdminService(db_session)
    notif = await service.create(
        type("Admin", (), {"id": 1})(),
        {"title": "Order matters", "body": None, "product_id": None},
    )
    try:
        assert events == ["commit", f"push:{NOTIFICATION_QUEUE}"]
    finally:
        # Session-scoped DB: leave no rows behind.
        monkeypatch.undo()
        await db_session.delete(notif)
        await db_session.commit()
