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
