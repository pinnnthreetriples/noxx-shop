"""Rate limiting on sensitive authenticated endpoints.

Verifies the shared limiter's security-relevant behaviour (trips once a user
exceeds the window, fails open on a Redis outage) and that a sensitive endpoint
is actually wired to it and answers 429 before doing any work — all without a
real Redis or a valid heavy request body.
"""
import types

import pytest_asyncio
from httpx import AsyncClient, ASGITransport

import app.core.ratelimit as ratelimit
from app.main import app
from app.auth import get_current_user


class _FakeRedis:
    """Stand-in for redis: incr returns an ever-increasing count so the
    (limit+1)th call trips too_many_attempts; expire is a no-op."""

    def __init__(self, start=0):
        self.count = start

    async def incr(self, key):
        self.count += 1
        return self.count

    async def expire(self, key, seconds):
        return True


@pytest_asyncio.fixture
async def client():
    app.dependency_overrides[get_current_user] = lambda: types.SimpleNamespace(
        id=1, is_blocked=False, selected_language="en"
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(get_current_user, None)


async def test_too_many_attempts_trips_after_limit(monkeypatch):
    """The real limiter returns False up to the limit, True once exceeded."""
    monkeypatch.setattr(ratelimit, "redis_client", _FakeRedis())
    results = [
        await ratelimit.too_many_attempts("k", limit=3, window_seconds=60)
        for _ in range(5)
    ]
    assert results == [False, False, False, True, True]


async def test_too_many_attempts_fails_open_on_redis_error(monkeypatch):
    """A Redis outage must not lock legitimate users out (fails open)."""

    class _Broken:
        async def incr(self, key):
            raise RuntimeError("redis down")

    monkeypatch.setattr(ratelimit, "redis_client", _Broken())
    assert await ratelimit.too_many_attempts("k", limit=1, window_seconds=60) is False


async def test_support_ticket_returns_429_when_over_limit(client, monkeypatch):
    """POST /support/tickets answers 429 (before any DB work) once the
    per-user counter is over the limit."""
    monkeypatch.setattr(ratelimit, "redis_client", _FakeRedis(start=1000))
    resp = await client.post("/support/tickets", json={"topic": "Other", "message": "hi"})
    assert resp.status_code == 429, resp.text
    assert resp.json()["detail"] == "Too many requests, slow down"
