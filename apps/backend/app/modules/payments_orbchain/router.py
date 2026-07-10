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
    """USD actually credited for a payment. On the multi-transaction shape the
    top-level `amount` is null and the real value is per settled transaction, so
    sum the CREDITED ones; fall back to a top-level `amount_usd` when the event
    carries no transactions array."""
    txs = event.get("transactions") or []
    if txs:
        return sum(
            float(t.get("amount_usd") or 0)
            for t in txs
            if str(t.get("status", "")).upper() == "CREDITED"
        )
    return float(event.get("amount_usd") or 0)


def _is_paid(event: dict, event_type_header: str) -> bool:
    """Confirmed-payment signal. OrbChain's v2 envelope names the event
    `payment.paid` (in the body `event_type`/`type` and the `X-Event-Type`
    header); the older/simple shape sends `type == "payment"` + `status == "paid"`."""
    etype = str(event.get("event_type") or event.get("type") or event_type_header or "").lower()
    if etype == "payment.paid":
        return True
    return etype == "payment" and str(event.get("status") or "").lower() == "paid"


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

    # Signature already verified, so this body is trustworthy: log it once so the
    # exact live event shape (order_id, transaction fields) is observable without
    # a redeploy — deliberate, given webhooks are low-volume payment events.
    logger.info("OrbChain webhook: %s", raw.decode("utf-8", "replace"))

    order_id = event.get("order_id")
    if _is_paid(event, request.headers.get("x-event-type", "")) and order_id:
        credited = _credited_usd(event)
        track_id = event.get("track_id") or ""
        result = await OrderService(db).fulfill(
            invoice_payload=str(order_id),
            telegram_payment_charge_id=f"orb:{track_id}",
            provider_payment_charge_id=track_id,
            total_amount=0,
            paid_usd=credited or None,
        )
        logger.info("OrbChain paid order_id=%s track=%s ok=%s", order_id, track_id, result.get("ok"))
    return {"ok": True}
