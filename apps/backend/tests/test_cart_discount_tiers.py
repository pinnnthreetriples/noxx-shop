"""Discount tiers count the cart that is actually sold.

list_published_by_ids collapses duplicates and drops unknown ids, so counting the
raw client list let a cart of one product repeated 20 times claim the bulk tier
("20+ videos in this order") while paying for a single video.
"""
import pytest_asyncio
from sqlalchemy import delete

from app.modules.orders.service import OrderService
from app.modules.catalog.models import Product, ProductStatus
from app.modules.users.models import User

# The test db is shared across the whole session, so everything seeded here is
# torn down again: published products are global state other suites read.
_USER_ID = 9500
_ONE = 9500
_BULK = list(range(9501, 9521))


async def _seed(db, ids):
    for i in ids:
        db.add(Product(id=i, slug=f"tier-{i}", status=ProductStatus.published, price_stars=100))
    await db.commit()


@pytest_asyncio.fixture
async def user(db_session):
    u = User(id=_USER_ID, telegram_id=95000)
    db_session.add(u)
    await _seed(db_session, [_ONE])
    yield u
    await db_session.execute(delete(Product).where(Product.id.in_([_ONE, *_BULK])))
    await db_session.execute(delete(User).where(User.id == _USER_ID))
    await db_session.commit()


async def test_one_product_sent_twenty_times_is_priced_as_one(db_session, user):
    out = await OrderService(db_session).estimate_cart(user, [_ONE] * 20)
    # bulk is 15%, first-purchase is 10% — a single-video cart may only get 10%
    assert out.base_discount_percent == 10
    assert out.product_ids == [_ONE]


async def test_padding_with_unknown_ids_does_not_unlock_the_bulk_tier(db_session, user):
    padded = [_ONE] + list(range(10_000, 10_019))  # 19 ids that do not exist
    out = await OrderService(db_session).estimate_cart(user, padded)
    assert out.base_discount_percent == 10
    assert out.product_ids == [_ONE]


async def test_the_bulk_tier_still_applies_to_a_real_bulk_cart(db_session, user):
    await _seed(db_session, _BULK)
    out = await OrderService(db_session).estimate_cart(user, _BULK)
    assert out.base_discount_percent == 15
