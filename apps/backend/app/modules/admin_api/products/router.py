"""Products router - thin API layer."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.auth import get_current_admin
from app.modules.admin.models import Admin
from app.modules.admin_api.products.service import ProductAdminService

router = APIRouter(tags=["admin-products"])


@router.get("/products")
async def list_products(
    q: Optional[str] = None,
    status: Optional[str] = None,
    category_id: Optional[int] = None,
    _sort: str = "id",
    _order: str = "ASC",
    _start: int = 0,
    _end: int = 25,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = ProductAdminService(db)
    return await service.list(q=q, status=status, category_id=category_id, sort_field=_sort, order=_order, start=_start, end=_end)


@router.get("/products/{id}")
async def get_product(
    id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = ProductAdminService(db)
    product = await service.get(id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/products")
async def create_product(
    payload: dict,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = ProductAdminService(db)
    try:
        return await service.create(admin, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.put("/products/{id}")
async def update_product(
    id: int,
    payload: dict,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = ProductAdminService(db)
    try:
        product = await service.update(admin, id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.delete("/products/{id}")
async def delete_product(
    id: int,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    service = ProductAdminService(db)
    product = await service.soft_delete(admin, id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"deleted": True}