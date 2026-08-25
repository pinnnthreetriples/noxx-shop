"""Thin OrbChain REST client. Only what the shop needs: create a hosted invoice."""
import logging
import time
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class OrbChainError(Exception):
    pass


async def create_invoice(
    amount_usd: float,
    order_id: str,
    description: str,
    return_url: str,
    lifetime_minutes: int = 60,
) -> Dict[str, Any]:
    """Create a hosted invoice. Customer picks any accepted coin on OrbChain's page.

    Returns the `data` object: track_id, payment_url, status, expires_at, ...
    """
    if not settings.orbchain_api_key:
        raise OrbChainError("ORBCHAIN_API_KEY not configured")

    url = f"{settings.orbchain_api_base.rstrip('/')}/v1/payment/invoice"
    payload = {
        # OrbChain validates amount as a string.
        "amount": f"{round(amount_usd, 2):.2f}",
        "currency": "USD",
        "order_id": order_id,
        "description": description,
        "return_url": return_url,
        "lifetime": lifetime_minutes,
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "merchant_api_key": settings.orbchain_api_key,
                },
            )
    except httpx.HTTPError as e:
        raise OrbChainError(f"OrbChain unreachable: {type(e).__name__}") from e
    if resp.status_code != 200:
        logger.warning("OrbChain invoice failed %s: %s", resp.status_code, resp.text[:300])
        raise OrbChainError(f"OrbChain invoice failed: HTTP {resp.status_code}")
    body = resp.json()
    data: Optional[Dict[str, Any]] = body.get("data") if isinstance(body, dict) else None
    if not data or not data.get("payment_url"):
        raise OrbChainError("OrbChain invoice response missing payment_url")
    return data


async def get_payment(track_id: str) -> Dict[str, Any]:
    """Fetch current status of a hosted invoice. Auth: merchant_api_key only,
    so we can confirm payment by polling — no webhook secret required."""
    if not settings.orbchain_api_key:
        raise OrbChainError("ORBCHAIN_API_KEY not configured")
    url = f"{settings.orbchain_api_base.rstrip('/')}/v1/payment/{track_id}"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, headers={"merchant_api_key": settings.orbchain_api_key})
    except httpx.HTTPError as e:
        raise OrbChainError(f"OrbChain unreachable: {type(e).__name__}") from e
    if resp.status_code != 200:
        raise OrbChainError(f"OrbChain status failed: HTTP {resp.status_code}")
    body = resp.json()
    return (body.get("data") if isinstance(body, dict) else None) or {}


async def select_coin(track_id: str, pay_currency: str) -> Dict[str, Any]:
    """Assign a deposit address for a chosen coin, then read it back.

    OrbChain assigns the per-coin address server-side when the hosted pay page is
    hit with `?pay_currency=X`; the value then surfaces on the JSON status API.
    We drive that from the backend so the mini-app can show the address inline —
    no redirect to the hosted page. Returns the invoice `data` (address,
    pay_amount, pay_currency, expires_at, status, ...)."""
    base = settings.orbchain_api_base.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            # Trigger address derivation for this coin (HTML response is ignored).
            await client.get(
                f"{base}/pay/{track_id}",
                params={"pay_currency": pay_currency},
                headers={"User-Agent": "Mozilla/5.0"},
            )
    except httpx.HTTPError as e:
        raise OrbChainError(f"OrbChain unreachable: {type(e).__name__}") from e
    return await get_payment(track_id)


def credited_usd(payload: Dict[str, Any]) -> Optional[float]:
    """USD actually credited for a payment, or None when the payload says nothing
    about amounts.

    Zero is an answer ("nothing landed"), not missing data, so it is never
    collapsed into None — the caller must be able to tell "no money" from "no
    data". On the multi-transaction shape the top-level `amount` is null and the
    real value is per settled transaction, so the CREDITED ones are summed; the
    flat shape carries `amount_usd` instead. Works on both the signed webhook
    event and the status-API `data` object.
    """
    txs = payload.get("transactions")
    if isinstance(txs, list) and txs:
        return sum(
            float(t.get("amount_usd") or 0)
            for t in txs
            if str(t.get("status", "")).upper() == "CREDITED"
        )
    try:
        return float(payload["amount_usd"])
    except (KeyError, TypeError, ValueError):
        return None


def payment_window_open(payload: Dict[str, Any]) -> bool:
    """True only when `expires_at` proves the invoice can still be paid.

    Callers use this to hold a fulfillment back while a better-informed signal
    (the amount-carrying webhook) may still arrive, so anything we cannot read
    as seconds-since-epoch inside a sane horizon answers False: an odd unit or a
    missing field must never hold an order back forever.
    """
    try:
        expires = float(payload["expires_at"])
    except (KeyError, TypeError, ValueError):
        return False
    now = time.time()
    return now < expires < now + 86400


def qr_data_uri(text: str) -> str:
    """Small self-contained SVG QR as a data URI (segno, no external calls)."""
    try:
        import segno
        return segno.make(text, error="m").svg_data_uri(
            scale=1, border=2, dark="#101014", light="#ffffff"
        )
    except Exception as e:  # QR is a nice-to-have; never block the payment flow.
        logger.warning("QR generation failed: %s", e)
        return ""
