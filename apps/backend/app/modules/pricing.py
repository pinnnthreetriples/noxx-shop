"""Buyer-facing price gross-up for Telegram's withdrawal commission.

Telegram pays out Stars at ~35% below their in-app value. With the setting on,
the owner's stored price (their take-home) is grossed up so the buyer covers
that cut: buyer pays base / (1 - percent/100), the owner still nets `base`.
The stored price_stars stays the base — the gross-up is computed on every
buyer-facing read/charge, so toggling the setting off restores base prices.
"""
from typing import Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def gross_stars(base: int, enabled: bool, percent: int) -> int:
    """Buyer-facing Stars price for an owner base price."""
    if not enabled or base <= 0 or percent <= 0:
        return base
    return int(round(base / (1 - min(percent, 95) / 100)))


def gross_usd(base: float, enabled: bool, percent: int) -> float:
    """Buyer-facing USD hint, grossed the same way as Stars."""
    if not enabled or base <= 0 or percent <= 0:
        return base
    return round(base / (1 - min(percent, 95) / 100), 2)


async def load_commission(db: AsyncSession) -> Tuple[bool, int]:
    """(enabled, percent) from the singleton Setting row; safe default if absent."""
    from app.modules.admin.models import Setting
    row = (await db.execute(
        select(Setting.withdrawal_commission_enabled, Setting.withdrawal_commission_percent).limit(1)
    )).first()
    if not row:
        return (False, 35)
    return (bool(row[0]), int(row[1] or 0))
