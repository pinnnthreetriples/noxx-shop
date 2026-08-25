"""Bot delivery queue (crypto payments, premium claims) + the reliable-queue
transport shared with the notification queue.

A job is never handed to the bot with a plain RPOP. It is moved to a per-queue
`:processing` list with LMOVE (atomic) and recorded in a `:inflight` hash, and
it only leaves processing once the bot acknowledges the send. Anything that
dies in between — the bot, this process, the network — is picked up by the
reclaim pass that runs on the next pop. Delivery is therefore at-least-once:
a buyer may see the same message twice, but never zero times.
"""
import json
import logging
import time
import uuid
from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(tags=["internal-bot-delivery"])

DELIVERY_QUEUE = "deliveries:queue"
NOTIFICATION_QUEUE = "notifications:queue"

# queue -> (visibility timeout in seconds, max attempts before dead-letter).
_LIMITS = {
    # A delivery is a handful of send_message calls; anything still in flight
    # after two minutes is a dead worker, not a slow one.
    DELIVERY_QUEUE: (120, 5),
    # A broadcast walks every user at ~0.3 s each, so an hour in flight is
    # legitimate. Attempts are capped at 2 because every replay re-messages
    # the users that already received it.
    NOTIFICATION_QUEUE: (3600, 2),
}
# Keep the most recent poisoned jobs for inspection instead of growing forever.
DEAD_LETTER_KEEP = 200


class JobAck(BaseModel):
    job_id: str
    error: Optional[str] = None
    # Retrying cannot help (user blocked the bot, payload unsendable): skip the
    # remaining attempts and dead-letter straight away.
    permanent: bool = False


def get_redis():
    from app.core.redis_client import redis_client
    return redis_client


def _keys(queue: str) -> tuple[str, str, str]:
    return f"{queue}:processing", f"{queue}:inflight", f"{queue}:dead"


async def _retire(r, queue: str, job_id: Optional[str], raw: str,
                  error: Optional[str], permanent: bool = False) -> None:
    """Take a job out of processing and either requeue it or dead-letter it."""
    proc, inflight, dead = _keys(queue)
    _, max_attempts = _LIMITS[queue]
    await r.lrem(proc, 1, raw)
    if job_id:
        await r.hdel(inflight, job_id)
    try:
        payload = json.loads(raw)
    except Exception:
        logger.error("dropping unparsable job from %s: %r", queue, raw[:200])
        return
    attempts = int(payload.get("_attempts") or 0) + 1
    payload["_attempts"] = attempts
    if permanent or attempts >= max_attempts:
        payload["_error"] = error
        await r.lpush(dead, json.dumps(payload))
        await r.ltrim(dead, 0, DEAD_LETTER_KEEP - 1)
        logger.error("job dead-lettered from %s after %s attempt(s): %s",
                     queue, attempts, error)
        return
    # Requeue at the producer end, so a job that keeps failing waits behind
    # everything else instead of blocking the head of the queue.
    await r.lpush(queue, json.dumps(payload))
    logger.warning("job requeued to %s (attempt %s): %s", queue, attempts, error)


async def reclaim_stale(r, queue: str) -> None:
    """Return jobs abandoned by a dead worker to the queue."""
    proc, inflight, _ = _keys(queue)
    if not await r.llen(proc):
        return
    visibility, _ = _LIMITS[queue]
    entries = await r.lrange(proc, 0, -1)
    meta_by_raw: dict[str, tuple[str, float]] = {}
    for job_id, meta_raw in (await r.hgetall(inflight)).items():
        try:
            meta = json.loads(meta_raw)
        except Exception:
            # Unreadable in-flight row: its job keeps its place in processing
            # and is reclaimed as an orphan below.
            logger.warning("unreadable in-flight row %s on %s", job_id, queue)
            continue
        meta_by_raw[meta.get("raw")] = (job_id, float(meta.get("popped_at") or 0))
    now = time.time()
    for raw in entries:
        job_id, popped_at = meta_by_raw.get(raw, (None, 0.0))
        if job_id is None:
            # Crashed between the LMOVE and the in-flight write: the bot never
            # received this job, so requeueing it is safe and necessary.
            await _retire(r, queue, None, raw, "orphaned")
        elif now - popped_at > visibility:
            await _retire(r, queue, job_id, raw, "visibility timeout")
    # In-flight rows whose job already left processing (crash between the LREM
    # and the HDEL of an ack) would otherwise leak forever.
    live = set(entries)
    leaked = [jid for raw, (jid, _) in meta_by_raw.items() if raw not in live]
    if leaked:
        await r.hdel(inflight, *leaked)


async def reliable_pop(r, queue: str) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    """Move the next job into processing and record it in flight.
    Returns (payload, job_id), or (None, None) when there is nothing to do."""
    await reclaim_stale(r, queue)
    proc, inflight, _ = _keys(queue)
    raw = await r.lmove(queue, proc, "RIGHT", "LEFT")
    if not raw:
        return None, None
    job_id = uuid.uuid4().hex
    await r.hset(inflight, job_id, json.dumps({"raw": raw, "popped_at": time.time()}))
    try:
        payload = json.loads(raw)
    except Exception:
        await _retire(r, queue, job_id, raw, "unparsable payload", permanent=True)
        return None, None
    return payload, job_id


async def ack_job(r, queue: str, job_id: str) -> bool:
    """Confirm the job was delivered — the only path that destroys it."""
    proc, inflight, _ = _keys(queue)
    meta_raw = await r.hget(inflight, job_id)
    if meta_raw is None:
        return False
    await r.lrem(proc, 1, json.loads(meta_raw)["raw"])
    await r.hdel(inflight, job_id)
    return True


async def nack_job(r, queue: str, job_id: str, error: Optional[str],
                   permanent: bool = False) -> bool:
    """Report a failed delivery: requeue the job, or dead-letter it once it has
    burned through its attempts (or is known to be undeliverable)."""
    _, inflight, _ = _keys(queue)
    meta_raw = await r.hget(inflight, job_id)
    if meta_raw is None:
        return False
    await _retire(r, queue, job_id, json.loads(meta_raw)["raw"], error, permanent)
    return True


@router.get("/bot/health")
async def bot_health():
    return {"ok": True}


@router.post("/bot/deliveries/pop")
async def pop_delivery():
    """Bot pops one delivery message (crypto payments / premium claims).
    The job stays in processing until the bot acks it."""
    try:
        payload, job_id = await reliable_pop(get_redis(), DELIVERY_QUEUE)
    except Exception as e:
        logger.warning("redis deliveries pop failed: %s", e)
        return {"empty": True}
    if payload is None:
        return {"empty": True}
    return {"empty": False,
            "job_id": job_id,
            "user_telegram_id": payload.get("user_telegram_id"),
            "message_text": payload.get("message_text"),
            "button": payload.get("button"),
            "channel_id": payload.get("channel_id"),
            "videos": payload.get("videos") or []}


@router.post("/bot/deliveries/ack")
async def ack_delivery(payload: JobAck):
    try:
        return {"ok": await ack_job(get_redis(), DELIVERY_QUEUE, payload.job_id)}
    except Exception as e:
        # The job stays in processing and is reclaimed after the visibility
        # timeout, i.e. the buyer may get the message twice. Never lost.
        logger.error("delivery ack failed for job %s: %s", payload.job_id, e)
        return {"ok": False}


@router.post("/bot/deliveries/nack")
async def nack_delivery(payload: JobAck):
    try:
        return {"ok": await nack_job(get_redis(), DELIVERY_QUEUE, payload.job_id,
                                     payload.error, payload.permanent)}
    except Exception as e:
        logger.error("delivery nack failed for job %s: %s", payload.job_id, e)
        return {"ok": False}
