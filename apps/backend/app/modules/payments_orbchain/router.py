"""OrbChain webhook receiver. Public endpoint (no auth dep) — authenticity is
proven by the HMAC-SHA512 signature, verified before we trust anything."""
import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.modules.admin.models import Setting
from app.modules.orders.service import OrderService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="")


async def _webhook_secret(db: AsyncSession) -> str:
    # DB value (pushed from the merchant dashboard) wins; env is the fallback.
    row = await db.execute(select(Setting.orbchain_webhook_secret).limit(1))
    secret = row.scalar_one_or_none()
    return secret or settings.orbchain_webhook_secret or ""


def _verify(raw: bytes, signature: str, secret: str) -> bool:
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode(), raw, hashlib.sha512).hexdigest()
    return hmac.compare_digest(expected, signature.strip())


@router.post("/webhook/orbchain")
async def orbchain_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    raw = await request.body()
    # OrbChain signs with X-Signature (hex HMAC-SHA512); accept an HMAC header too.
    signature = request.headers.get("x-signature") or request.headers.get("hmac") or ""

    secret = await _webhook_secret(db)
    if not _verify(raw, signature, secret):
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
        result = await OrderService(db).fulfill(
            invoice_payload=str(order_id),
            telegram_payment_charge_id=f"orb:{track_id}",
            provider_payment_charge_id=track_id,
            total_amount=0,
        )
        logger.info("OrbChain paid order_id=%s track=%s ok=%s", order_id, track_id, result.get("ok"))
    return {"ok": True}
