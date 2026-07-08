"""Regression: creating products must not 500 on the UNIQUE slug constraint.

`Product.slug` is UNIQUE, but create() inserted the raw (possibly blank) slug,
so a second product saved with an empty slug — or a typed duplicate — raised an
IntegrityError (duplicate key). Blank slugs now derive from the title and get a
numeric suffix; an explicit clash is reported as a clean ValueError (HTTP 400).
"""
import pytest
from app.modules.admin_api.products.service import ProductAdminService

_ADMIN = type("Admin", (), {"id": 1})()


@pytest.mark.asyncio
async def test_blank_slug_derives_and_suffixes_instead_of_colliding(db_session):
    svc = ProductAdminService(db_session)
    p1 = await svc.create(_ADMIN, {"title_en": "First Movie", "price_stars": 10, "status": "draft"})
    p2 = await svc.create(_ADMIN, {"title_en": "First Movie", "price_stars": 10, "status": "draft"})
    assert p1["slug"] == "first-movie"
    assert p2["slug"] == "first-movie-2"


@pytest.mark.asyncio
async def test_duplicate_explicit_slug_raises_valueerror(db_session):
    svc = ProductAdminService(db_session)
    await svc.create(_ADMIN, {"slug": "unique-one", "title_en": "A", "price_stars": 5, "status": "draft"})
    with pytest.raises(ValueError):
        await svc.create(_ADMIN, {"slug": "unique-one", "title_en": "B", "price_stars": 5, "status": "draft"})
