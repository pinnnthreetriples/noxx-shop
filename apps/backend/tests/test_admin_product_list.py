"""Admin product list hides soft-deleted products unless explicitly filtered."""
from app.modules.admin_api.filters import AdminListFilters
from app.modules.admin_api.products.repository import ProductAdminRepository
from app.modules.catalog.models import Product


async def test_deleted_products_hidden_by_default(db_session):
    db_session.add_all([
        Product(slug="list-live", status="published"),
        Product(slug="list-gone", status="deleted"),
    ])
    await db_session.flush()
    repo = ProductAdminRepository(db_session)

    items, _ = await repo.list_with_filters(AdminListFilters(end=100))
    slugs = [p.slug for p in items]
    assert "list-live" in slugs
    assert "list-gone" not in slugs

    deleted, _ = await repo.list_with_filters(AdminListFilters(status="deleted", end=100))
    assert "list-gone" in [p.slug for p in deleted]
