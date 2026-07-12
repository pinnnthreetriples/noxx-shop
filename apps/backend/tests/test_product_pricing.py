"""Pricing rules: Stars is the charged currency; USD-only input must derive Stars,
and a published product can never cost 0 Stars."""
from decimal import Decimal

import pytest
from app.modules.admin_api.products.service import ProductAdminService
from app.modules.catalog.models import Product


@pytest.fixture
def service(db_session):
    return ProductAdminService(db_session)


async def test_usd_only_derives_stars(service):
    # default rate: 1 star = $0.02 -> $10 = 500 stars
    payload = {"status": "draft", "price_stars": 0, "usd_price_manual": 10}
    await service._apply_pricing_rules(payload)
    assert payload["price_stars"] == 500


async def test_published_without_any_price_rejected(service):
    with pytest.raises(ValueError):
        await service._apply_pricing_rules({"status": "published", "price_stars": 0})


async def test_explicit_stars_kept(service):
    payload = {"status": "published", "price_stars": 250, "usd_price_manual": 10}
    await service._apply_pricing_rules(payload)
    assert payload["price_stars"] == 250


async def test_usd_change_recomputes_stale_stars(service):
    """Bulk $ repricing: the admin types a new USD while the form echoes the old
    Stars — Stars must follow the new USD (regression: $8 left 200⭐ untouched)."""
    current = Product(price_stars=200, usd_price_manual=None, status="published")
    payload = {"status": "published", "price_stars": 200, "usd_price_manual": 8}
    await service._apply_pricing_rules(payload, current)
    assert payload["price_stars"] == 400  # $8 / 0.02


async def test_usd_unchanged_keeps_custom_stars(service):
    """Re-saving without touching USD must not clobber a hand-tuned Stars price
    (payload int 8 == stored Decimal 8.00)."""
    current = Product(price_stars=250, usd_price_manual=Decimal("8.00"), status="published")
    payload = {"status": "published", "price_stars": 250, "usd_price_manual": 8}
    await service._apply_pricing_rules(payload, current)
    assert payload["price_stars"] == 250


async def test_explicit_stars_beats_usd_change(service):
    """Both edited in one save -> the admin's explicit Stars wins."""
    current = Product(price_stars=200, usd_price_manual=Decimal("8.00"), status="published")
    payload = {"status": "published", "price_stars": 300, "usd_price_manual": 9}
    await service._apply_pricing_rules(payload, current)
    assert payload["price_stars"] == 300


async def test_partial_payload_usd_change_derives(service):
    """API-style partial update: only USD in the payload -> Stars recomputed."""
    current = Product(price_stars=200, usd_price_manual=Decimal("8.00"), status="published")
    payload = {"usd_price_manual": 9}
    await service._apply_pricing_rules(payload, current)
    assert payload["price_stars"] == 450


async def test_star_rate_ignores_nonpositive_manual(db_session):
    """A zero/negative manual rate must fall back to the built-in rate instead
    of corrupting every derived price."""
    from app.core.config import settings
    from app.modules.admin.models import Setting
    from app.modules.orders.service import OrderService
    s = await db_session.get(Setting, 1)
    if not s:
        s = Setting(id=1)
        db_session.add(s)
        await db_session.commit()  # apply column defaults before snapshotting
    old_mode, old_rate = s.stars_to_usd_mode, s.manual_stars_to_usd_rate
    s.stars_to_usd_mode, s.manual_stars_to_usd_rate = "manual", 0
    await db_session.commit()
    try:
        assert await OrderService(db_session)._star_rate() == settings.star_usd_rate
        s.manual_stars_to_usd_rate = 0.016
        await db_session.commit()
        assert await OrderService(db_session)._star_rate() == 0.016
    finally:  # shared test DB — leave the singleton as we found it
        s.stars_to_usd_mode, s.manual_stars_to_usd_rate = old_mode, old_rate
        await db_session.commit()


def test_effective_star_rate():
    from app.modules.pricing import effective_star_rate
    assert effective_star_rate("manual", 0.016, 0.02) == 0.016
    assert effective_star_rate("manual", 0, 0.02) == 0.02    # invalid manual -> fallback
    assert effective_star_rate("manual", -1, 0.02) == 0.02
    assert effective_star_rate("auto", 0.016, 0.02) == 0.02  # manual ignored in auto
    assert effective_star_rate(None, None, 0.02) == 0.02


def test_settings_pricing_bounds():
    """Server-side guard for money-critical settings (the admin UI limits are
    client-side only and bypassable via direct API calls)."""
    from app.modules.admin_api.settings.service import _validate_pricing_bounds
    _validate_pricing_bounds({"manual_stars_to_usd_rate": 0.02, "max_discount_percent": 40})
    _validate_pricing_bounds({})  # partial payloads stay valid
    for bad in (
        {"manual_stars_to_usd_rate": 0},
        {"manual_stars_to_usd_rate": -0.01},
        {"max_discount_percent": -10},
        {"withdrawal_commission_percent": 101},
        {"stars_to_usd_mode": "х-мode"},
        {"sub_price_month_usd": 0},
        {"discount_bulk_min_items": 0},
    ):
        with pytest.raises(ValueError):
            _validate_pricing_bounds(bad)


async def test_public_settings_exposes_effective_rate_not_commission(db_session):
    """The storefront derives ≈$ from star_usd_rate (effective, server-computed);
    commission internals must never leak — buyers only see grossed prices."""
    from httpx import ASGITransport, AsyncClient
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/settings")
    assert r.status_code == 200
    body = r.json()
    assert body["star_usd_rate"] > 0
    assert "withdrawal_commission_enabled" not in body
    assert "withdrawal_commission_percent" not in body


def test_storefront_usd_ignores_stale_manual_in_auto_mode():
    """Auto mode: the $ hint must come from stars x rate (client-side), not a
    leftover manual value that could contradict the charged stars price."""
    from app.modules.catalog.service import _approx_usd
    off = (False, 35)  # commission disabled -> no gross-up in these display checks
    auto = Product(price_stars=500, usd_price_mode="auto", usd_price_manual=7)
    assert _approx_usd(auto, off) is None
    manual = Product(price_stars=500, usd_price_mode="manual", usd_price_manual=10)
    assert _approx_usd(manual, off) == 10.0
