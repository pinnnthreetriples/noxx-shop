"""OrbChain webhook receiver. Public endpoint (no auth dep) — authenticity is
proven by the HMAC-SHA512 signature, verified before we trust anything."""
import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.modules.orders.service import OrderService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="")


def _verify(raw: bytes, signature: str, secret: str) -> bool:
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode(), raw, hashlib.sha512).hexdigest()
    return hmac.compare_digest(expected, signature.strip())


def _credited_usd(event: dict) -> float:
    """USD actually credited for a payment. OrbChain's webhook leaves the top-level
    `amount` null and reports the real value per settled transaction; sum the
    CREDITED ones."""
    return sum(
        float(t.get("amount_usd") or 0)
        for t in (event.get("transactions") or [])
        if str(t.get("status", "")).upper() == "CREDITED"
    )


@router.post("/webhook/orbchain")
async def orbchain_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    raw = await request.body()
    # OrbChain signs v2 webhooks with the `HMAC` header (hex HMAC-SHA512 over the
    # raw body, keyed by webhook_secret); accept x-signature too for safety.
    signature = request.headers.get("hmac") or request.headers.get("x-signature") or ""

    # Env is the single source of truth for the webhook secret (like the API key).
    if not _verify(raw, signature, settings.orbchain_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        event = json.loads(raw)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON") from None

    etype = event.get("type")
    status = (event.get("status") or "").lower()
    order_id = event.get("order_id")
    track_id = event.get("track_id") or ""

    # Only act on a confirmed payment tied to one of our orders.
    if etype == "payment" and status == "paid" and order_id:
        credited = _credited_usd(event)
        result = await OrderService(db).fulfill(
            invoice_payload=str(order_id),
            telegram_payment_charge_id=f"orb:{track_id}",
            provider_payment_charge_id=track_id,
            total_amount=0,
            paid_usd=credited or None,
        )
        logger.info("OrbChain paid order_id=%s track=%s ok=%s", order_id, track_id, result.get("ok"))
    return {"ok": True}
