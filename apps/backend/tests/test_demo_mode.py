"""Demo mode: the storefront hides every real product and serves one fake item.

The demo product is a normal row kept at status `hidden`, so every money path
(cart estimate, checkout, delivery) skips it like any other unpublished product
— that is what makes it unbuyable, and it's asserted here.
"""
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy import delete, func, select

from app.core.exceptions import NotFoundException
from app.modules.admin.models import Setting
from app.modules.catalog import service as catalog_service
from app.modules.catalog.models import Product, ProductStatus, ProductTranslation
from app.modules.catalog.repository import (
    DEMO_PRODUCT_SLUG,
    ProductRepository,
    ensure_demo_product,
)
from app.modules.users.models import User

REAL_SLUG = "demo-mode-real-product"


@pytest_asyncio.fixture
async def shop(db_session):
    """One published product plus the demo product, demo mode off. Cleans up
    after itself — the test DB is shared across the whole session."""
    setting = await db_session.get(Setting, 1)
    if not setting:
        setting = Setting(id=1)
        db_session.add(setting)
        await db_session.commit()
    was_enabled = setting.demo_mode_enabled
    setting.demo_mode_enabled = False

    real = Product(slug=REAL_SLUG, status=ProductStatus.published, price_stars=500)
    db_session.add(real)
    await db_session.flush()
    db_session.add(ProductTranslation(product_id=real.id, language_code="en", title="Real video"))
    demo = await ensure_demo_product(db_session)
    await db_session.commit()

    yield SimpleNamespace(
        setting=setting, real=real, demo=demo,
        user=User(language_code="en", selected_language=None),
    )

    # By slug, not by id: a test may have re-created the demo product.
    ids = (await db_session.execute(
        select(Product.id).where(Product.slug.in_([REAL_SLUG, DEMO_PRODUCT_SLUG]))
    )).scalars().all()
    await db_session.execute(delete(ProductTranslation).where(ProductTranslation.product_id.in_(ids)))
    await db_session.execute(delete(Product).where(Product.id.in_(ids)))
    setting.demo_mode_enabled = was_enabled
    await db_session.commit()


async def _enable_demo(db_session, shop):
    shop.setting.demo_mode_enabled = True
    await db_session.commit()


async def test_off_shows_real_and_hides_demo(db_session, shop):
    slugs = {p.slug for p in await catalog_service.list_products(db_session, shop.user, limit=100)}
    assert REAL_SLUG in slugs
    assert DEMO_PRODUCT_SLUG not in slugs

    assert (await catalog_service.get_product_by_slug(db_session, shop.user, REAL_SLUG)).slug == REAL_SLUG
    with pytest.raises(NotFoundException):
        await catalog_service.get_product_by_slug(db_session, shop.user, DEMO_PRODUCT_SLUG)


async def test_on_shows_only_the_demo_product(db_session, shop):
    await _enable_demo(db_session, shop)

    slugs = {p.slug for p in await catalog_service.list_products(db_session, shop.user, limit=100)}
    assert slugs == {DEMO_PRODUCT_SLUG}

    detail = await catalog_service.get_product_by_slug(db_session, shop.user, DEMO_PRODUCT_SLUG)
    assert detail.title == "Demo product"
    with pytest.raises(NotFoundException):
        await catalog_service.get_product_by_slug(db_session, shop.user, REAL_SLUG)


async def test_on_search_and_filters_cannot_surface_real_products(db_session, shop):
    """Search and the category/premium filters run through the same query, so a
    real product must stay hidden no matter how the storefront is queried."""
    await _enable_demo(db_session, shop)

    for kwargs in ({"search": "Real"}, {"category_id": 1}, {"premium_only": True}, {"sort": "id"}):
        found = await catalog_service.list_products(db_session, shop.user, limit=100, **kwargs)
        assert all(p.slug == DEMO_PRODUCT_SLUG for p in found), kwargs


async def test_demo_product_cannot_be_bought(db_session, shop):
    """The money guarantee: checkout resolves products through
    list_published_by_ids, and the demo product is never published."""
    await _enable_demo(db_session, shop)
    assert await ProductRepository(db_session).list_published_by_ids([shop.demo.id]) == []


async def test_ensure_demo_product_is_idempotent(db_session, shop):
    await ensure_demo_product(db_session)
    await db_session.commit()

    products = (await db_session.execute(
        select(func.count()).select_from(Product).where(Product.slug == DEMO_PRODUCT_SLUG)
    )).scalar()
    translations = (await db_session.execute(
        select(func.count()).select_from(ProductTranslation)
        .where(ProductTranslation.product_id == shop.demo.id)
    )).scalar()
    assert (products, translations) == (1, 2)


async def test_switching_demo_mode_on_creates_the_product(db_session, shop):
    """The wiring that matters: saving the admin toggle must leave a demo product
    behind on a shop that never had one."""
    from app.modules.admin.models import Admin, AdminLog
    from app.modules.admin_api.settings.service import SettingsAdminService

    await db_session.execute(delete(ProductTranslation).where(ProductTranslation.product_id == shop.demo.id))
    await db_session.execute(delete(Product).where(Product.id == shop.demo.id))
    admin = Admin(telegram_id=999000111, name="Toggle tester", role="owner", active=True)
    db_session.add(admin)
    await db_session.commit()
    try:
        await SettingsAdminService(db_session).update(admin, {"demo_mode_enabled": True})
        created = (await db_session.execute(
            select(Product).where(Product.slug == DEMO_PRODUCT_SLUG)
        )).scalars().first()
        assert created is not None
        assert created.status == ProductStatus.hidden
    finally:
        await db_session.execute(delete(AdminLog).where(AdminLog.admin_id == admin.id))
        await db_session.execute(delete(Admin).where(Admin.id == admin.id))
        await db_session.commit()


async def test_ensure_demo_product_revives_soft_deleted_row(db_session, shop):
    """Deleting the demo product from the admin is a soft delete; switching demo
    mode on again must bring it back instead of creating a duplicate."""
    shop.demo.status = ProductStatus.deleted
    await db_session.commit()

    revived = await ensure_demo_product(db_session)
    await db_session.commit()
    assert revived.id == shop.demo.id
    assert revived.status == ProductStatus.hidden
