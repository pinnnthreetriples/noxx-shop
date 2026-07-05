from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.auth import get_current_user
from app.modules.promos.schemas import PromoValidateIn, PromoValidateOut
from app.modules.orders.service import OrderService

router = APIRouter(prefix="")


@router.post("/promo/validate", response_model=PromoValidateOut)
async def validate_promo(body: PromoValidateIn, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    pct = await OrderService(db)._lookup_promo_discount(body.code, user)
    if pct is None:
        return PromoValidateOut(valid=False, message="Invalid or expired promo code")
    return PromoValidateOut(valid=True, discount_type="percentage", discount_value=pct)
