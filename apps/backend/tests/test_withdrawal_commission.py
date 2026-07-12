"""Withdrawal-commission gross-up: buyer covers Telegram's ~35% cut while the
owner's stored base price stays untouched, and toggling it off restores base."""
from types import SimpleNamespace

from app.modules.admin.models import Setting
from app.modules.catalog.models import Product, ProductTranslation
from app.modules.catalog.service import get_product_by_slug
from app.modules.orders.service import OrderService
from app.modules.pricing import gross_stars, gross_usd

USER = SimpleNamespace(id=1, selected_language="en", language_code="en")


def test_gross_helpers():
    assert gross_stars(500, True, 35) == 769   # 500 / 0.65
    assert gross_stars(500, False, 35) == 500  # off -> base
    assert gross_stars(0, True, 35) == 0        # free stays free
    assert gross_stars(500, True, 0) == 500     # 0% -> base
    assert gross_usd(10.0, True, 35) == 15.38
    assert gross_usd(10.0, False, 35) == 10.0


async def _set_commission(db, enabled: bool, percent: int = 35) -> None:
    """Upsert the singleton Setting (the shared test DB persists across tests)."""
    s = await db.get(Setting, 1)
    if not s:
        s = Setting(id=1)
        db.add(s)
    s.withdrawal_commission_enabled = enabled
    s.withdrawal_commission_percent = percent
    await db.commit()


async def _add_product(db, pid: int, slug: str, price: int = 500) -> None:
    db.add(Product(id=pid, slug=slug, status="published", price_stars=price, usd_price_mode="auto"))
    db.add(ProductTranslation(product_id=pid, language_code="en", title=slug))
    await db.commit()


async def test_catalog_shows_grossed_price(db_session):
    await _set_commission(db_session, True, 35)
    await _add_product(db_session, 810, "vid810")
    detail = await get_product_by_slug(db_session, USER, "vid810")
    assert detail.price_stars == 769                               # buyer sees grossed
    assert (await db_session.get(Product, 810)).price_stars == 500  # DB base untouched


async def test_checkout_charges_grossed(db_session):
    await _set_commission(db_session, True, 35)
    await _add_product(db_session, 811, "vid811")
    est = await OrderService(db_session).estimate_cart(USER, [811])
    assert est.total_stars == 769


async def test_negative_discount_cap_never_overcharges(db_session):
    """A mis-set (negative) max_discount_percent must clamp to 0% — the buyer
    must never pay MORE than the listed total."""
    await _set_commission(db_session, False)
    s = await db_session.get(Setting, 1)
    old_cap = s.max_discount_percent
    s.max_discount_percent = -10
    await db_session.commit()
    try:
        await _add_product(db_session, 813, "vid813")
        est = await OrderService(db_session).estimate_cart(USER, [813])
        assert est.to_pay_stars == est.total_stars
    finally:
        s.max_discount_percent = old_cap
        await db_session.commit()


async def test_subscription_checkout_charges_grossed(db_session):
    from app.modules.orders.models import Order
    await _set_commission(db_session, True, 35)
    s = await db_session.get(Setting, 1)
    # pin the rate so the USD→Stars derivation is deterministic: $1.98 → 99 base
    s.stars_to_usd_mode = "manual"
    s.manual_stars_to_usd_rate = 0.02
    s.sub_price_month_usd = 1.98
    await db_session.commit()
    out = await OrderService(db_session).create_subscription_checkout(USER, "month")
    order = await db_session.get(Order, out.order_id)
    assert order.paid_stars == 152  # 99 / 0.65, buyer covers the commission


async def test_toggle_off_restores_base(db_session):
    await _set_commission(db_session, False)
    await _add_product(db_session, 812, "vid812")
    detail = await get_product_by_slug(db_session, USER, "vid812")
    assert detail.price_stars == 500
