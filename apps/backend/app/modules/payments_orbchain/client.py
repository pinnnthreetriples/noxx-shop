"""Thin OrbChain REST client. Only what the shop needs: create a hosted invoice."""
import logging
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
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "merchant_api_key": settings.orbchain_api_key,
            },
        )
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
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(url, headers={"merchant_api_key": settings.orbchain_api_key})
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
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        # Trigger address derivation for this coin (HTML response is ignored).
        await client.get(
            f"{base}/pay/{track_id}",
            params={"pay_currency": pay_currency},
            headers={"User-Agent": "Mozilla/5.0"},
        )
    return await get_payment(track_id)


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
