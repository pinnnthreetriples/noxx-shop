"""Regression tests for the security-hardening pass:
- config refuses placeholder secrets outside development
- admin-login rate limiter (fail-open, trips after the limit)
- real client IP extraction behind the Cloudflare tunnel
- the unauthenticated /webhook/payment route is gone
"""
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

import app.core.ratelimit as rl
from app.core.config import Settings
from app.core.ratelimit import client_ip
from app.main import app

_PLACEHOLDERS = dict(
    jwt_secret="change-me",
    admin_jwt_secret="admin-change-me",
    internal_api_secret="change-me-internal-secret",
)
_REAL = dict(
    jwt_secret="a" * 32,
    admin_jwt_secret="b" * 32,
    internal_api_secret="c" * 32,
)


def test_placeholder_secrets_rejected_in_prod():
    with pytest.raises(ValidationError):
        Settings(app_env="production", **_PLACEHOLDERS)


def test_placeholder_secrets_allowed_in_dev():
    Settings(app_env="development", **_PLACEHOLDERS)  # no raise


def test_real_secrets_pass_in_prod():
    Settings(app_env="production", **_REAL)  # no raise


def _req(headers, host="127.0.0.1"):
    return SimpleNamespace(headers=headers, client=SimpleNamespace(host=host))


def test_client_ip_prefers_cf_header():
    assert client_ip(_req({"cf-connecting-ip": "9.9.9.9", "x-forwarded-for": "1.1.1.1"})) == "9.9.9.9"


def test_client_ip_uses_first_forwarded_hop():
    assert client_ip(_req({"x-forwarded-for": "1.2.3.4, 5.6.7.8"})) == "1.2.3.4"


def test_client_ip_falls_back_to_socket():
    assert client_ip(_req({}, host="10.0.0.1")) == "10.0.0.1"


async def test_rate_limiter_fails_open_when_redis_down(monkeypatch):
    class Boom:
        async def incr(self, *a):
            raise RuntimeError("redis down")

        async def expire(self, *a):
            raise RuntimeError("redis down")

    monkeypatch.setattr(rl, "redis_client", Boom())
    assert await rl.too_many_attempts("k", limit=1, window_seconds=60) is False


async def test_rate_limiter_trips_after_limit(monkeypatch):
    class FakeRedis:
        def __init__(self):
            self.n = 0

        async def incr(self, key):
            self.n += 1
            return self.n

        async def expire(self, key, ttl):
            pass

    monkeypatch.setattr(rl, "redis_client", FakeRedis())
    assert await rl.too_many_attempts("k", limit=2, window_seconds=60) is False
    assert await rl.too_many_attempts("k", limit=2, window_seconds=60) is False
    assert await rl.too_many_attempts("k", limit=2, window_seconds=60) is True


def test_public_payment_webhook_route_removed():
    paths = {getattr(r, "path", None) for r in app.routes}
    assert "/webhook/payment" not in paths
    # the authenticated crypto path and the signed OrbChain webhook remain
    assert "/orders/{order_id}/check-payment" in paths
    assert "/webhook/orbchain" in paths
