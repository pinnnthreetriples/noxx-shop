"""Minimal Redis fixed-window rate limiter for brute-force-sensitive endpoints."""
import logging

from fastapi import Request

from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)


def client_ip(request: Request) -> str:
    """Best-effort real client IP. Behind the Cloudflare tunnel, request.client
    is always 127.0.0.1, so trust CF's header first, then a forwarded hop."""
    return (
        request.headers.get("cf-connecting-ip")
        or (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )


async def too_many_attempts(key: str, limit: int, window_seconds: int) -> bool:
    """Count one hit against `key`; return True once it exceeds `limit` within
    `window_seconds`. Fails open (False) if Redis is unreachable so an outage
    can't lock legitimate users out."""
    try:
        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, window_seconds)
        return count > limit
    except Exception as e:
        logger.warning("rate-limit check skipped (redis error): %s", e)
        return False
