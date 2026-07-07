"""Pricing rules: Stars is the charged currency; USD-only input must derive Stars,
and a published product can never cost 0 Stars."""
import pytest
from app.modules.admin_api.products.service import ProductAdminService


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


def test_storefront_usd_ignores_stale_manual_in_auto_mode():
    """Auto mode: the $ hint must come from stars x rate (client-side), not a
    leftover manual value that could contradict the charged stars price."""
    from app.modules.catalog.models import Product
    from app.modules.catalog.service import _approx_usd
    off = (False, 35)  # commission disabled -> no gross-up in these display checks
    auto = Product(price_stars=500, usd_price_mode="auto", usd_price_manual=7)
    assert _approx_usd(auto, off) is None
    manual = Product(price_stars=500, usd_price_mode="manual", usd_price_manual=10)
    assert _approx_usd(manual, off) == 10.0
