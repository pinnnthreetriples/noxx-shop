import json
import logging
from fastapi import APIRouter

from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["internal-bot-delivery"])


@router.get("/bot/health")
async def bot_health():
    return {"ok": True}


@router.post("/bot/deliveries/pop")
async def pop_delivery():
    """Bot pops one delivery message (crypto payments / premium claims) from Redis."""
    import redis.asyncio as redis_async
    try:
        r = redis_async.from_url(settings.redis_url, decode_responses=True)
        try:
            data = await r.rpop("deliveries:queue")
        finally:
            await r.aclose()
    except Exception as e:
        logger.warning("redis deliveries pop failed: %s", e)
        return {"empty": True}
    if not data:
        return {"empty": True}
    try:
        payload = json.loads(data)
    except Exception:
        return {"empty": True}
    return {"empty": False,
            "user_telegram_id": payload.get("user_telegram_id"),
            "message_text": payload.get("message_text"),
            "channel_id": payload.get("channel_id"),
            "videos": payload.get("videos") or []}
