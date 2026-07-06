"""Contract audit: every admin screen's list/getOne endpoint answers 200
with the react-admin shape ({data, total} for lists), so no section of the
admin panel can silently break again."""
import pytest
import pytest_asyncio
from types import SimpleNamespace
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.auth import get_current_admin
from app.modules.admin.models import Setting
from app.modules.catalog.models import Category, Product, Tag


@pytest_asyncio.fixture
async def client(db_session):
    app.dependency_overrides[get_current_admin] = lambda: SimpleNamespace(id=1)
    # singleton settings row + one product/category/tag for getOne checks
    if not await db_session.get(Setting, 1):
        db_session.add(Setting(id=1))
    if not await db_session.get(Category, 900):
        db_session.add(Category(id=900, slug="audit-cat"))
        db_session.add(Product(id=900, slug="audit-product", status="published", price_stars=100))
        db_session.add(Tag(id=900, slug="audit-tag"))
    await db_session.commit()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(get_current_admin, None)


LIST_ENDPOINTS = [
    "/admin/products",
    "/admin/categories",
    "/admin/tags",
    "/admin/users",
    "/admin/orders",
    "/admin/promo_codes",
    "/admin/support_tickets",
    "/admin/notifications",
    "/admin/admins",
    "/admin/admin_logs",
    "/admin/link_delivery_logs",
]


@pytest.mark.parametrize("path", LIST_ENDPOINTS)
async def test_list_endpoints_answer_react_admin_shape(client, path):
    resp = await client.get(path, params={"_sort": "id", "_order": "ASC", "_start": 0, "_end": 25})
    assert resp.status_code == 200, f"{path}: {resp.status_code} {resp.text[:200]}"
    body = resp.json()
    assert "data" in body and "total" in body, f"{path}: shape {list(body)}"


async def test_settings_singleton_and_by_id(client):
    for path in ("/admin/settings", "/admin/settings/1"):
        resp = await client.get(path)
        assert resp.status_code == 200, f"{path}: {resp.status_code} {resp.text[:200]}"
        assert resp.json()["id"] == 1


async def test_settings_update_roundtrip(client):
    resp = await client.put("/admin/settings/1", json={"max_discount_percent": 40})
    assert resp.status_code == 200, resp.text[:200]
    assert resp.json()["max_discount_percent"] == 40


async def test_product_get_one(client):
    resp = await client.get("/admin/products/900")
    assert resp.status_code == 200, resp.text[:200]
    assert resp.json()["slug"] == "audit-product"


async def test_category_get_one(client):
    resp = await client.get("/admin/categories/900")
    assert resp.status_code == 200, resp.text[:200]
    assert resp.json()["slug"] == "audit-cat"


async def test_settings_self_heal_when_row_missing(client, db_session):
    """Prod regression: the settings row vanished after a partial DB restore and
    every settings read 404-looped the admin page. Reads must recreate it."""
    from sqlalchemy import delete
    await db_session.execute(delete(Setting))
    await db_session.commit()

    admin_resp = await client.get("/admin/settings/1")
    assert admin_resp.status_code == 200, admin_resp.text[:200]

    await db_session.execute(delete(Setting))
    await db_session.commit()

    public_resp = await client.get("/settings")
    assert public_resp.status_code == 200, public_resp.text[:200]
