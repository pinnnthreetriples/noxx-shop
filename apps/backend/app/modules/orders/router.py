"""
Thin orders router: request → service → response.
No SQL, no business logic, no direct external HTTP calls.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth import get_current_user
from app.modules.orders.schemas import (
    CartEstimateIn,
    CartEstimateOut,
    CheckoutIn,
    CheckoutOut,
    ClaimIn,
    OrderOut,
    PaymentStateOut,
    SelectCoinIn,
    SubscriptionCheckoutIn,
)
from app.modules.orders.service import OrderService


router = APIRouter(prefix="")


@router.post("/cart/estimate", response_model=CartEstimateOut)
async def cart_estimate(
    body: CartEstimateIn,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await OrderService(db).estimate_cart(
        user, body.product_ids, body.promo_code
    )


@router.post("/checkout/create", response_model=CheckoutOut)
async def checkout_create(
    body: CheckoutIn,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await OrderService(db).create_checkout(
            user, body.product_ids, body.promo_code, body.provider
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/subscription/checkout", response_model=CheckoutOut)
async def subscription_checkout(
    body: SubscriptionCheckoutIn,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await OrderService(db).create_subscription_checkout(user, body.plan, body.provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/subscription/claim")
async def subscription_claim(
    body: ClaimIn,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Premium perk: active subscriber gets a premium video for free."""
    try:
        return await OrderService(db).claim_with_premium(user, body.product_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/orders", response_model=List[OrderOut])
async def list_orders(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return await OrderService(db).list_user_orders(user, limit=limit, offset=offset)


@router.get("/orders/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    out = await OrderService(db).get_user_order(user, order_id)
    if not out:
        raise HTTPException(status_code=404, detail="Order not found")
    return out


@router.get("/orders/{order_id}/payment", response_model=PaymentStateOut)
async def get_payment_state(
    order_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """In-app crypto payment state: coin list + address/amount/QR once picked."""
    out = await OrderService(db).get_orbchain_payment(user, order_id)
    if not out:
        raise HTTPException(status_code=404, detail="Order not found")
    return out


@router.post("/orders/{order_id}/select-coin", response_model=PaymentStateOut)
async def select_coin(
    order_id: int,
    body: SelectCoinIn,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reserve a deposit address for the chosen coin and return it inline."""
    try:
        return await OrderService(db).select_orbchain_coin(user, order_id, body.coin)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/orders/{order_id}/check-payment")
async def check_payment(
    order_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Poll OrbChain and fulfill the order if it's been paid (crypto checkout)."""
    return await OrderService(db).check_orbchain_payment(user, order_id)


@router.post("/webhook/payment")
async def webhook_payment(body: dict, db: AsyncSession = Depends(get_db)):
    try:
        return await OrderService(db).webhook_payment(
            body.get("telegram_payment_charge_id"),
            body.get("provider_payment_charge_id"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
