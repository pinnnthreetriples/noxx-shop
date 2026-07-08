from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.internal_api.schemas import (
    PreCheckoutRequest, PreCheckoutResponse,
    SuccessfulPaymentRequest, SuccessfulPaymentResponse,
    AdminMessageMapRequest, AdminMessageMapResponse,
)
from app.modules.orders.service import OrderService
from app.modules.support.service import SupportService

router = APIRouter(prefix="/telegram", tags=["internal-telegram"])


@router.post("/pre-checkout", response_model=PreCheckoutResponse)
async def pre_checkout(payload: PreCheckoutRequest, db: AsyncSession = Depends(get_db)):
    """
    Bot pre-checkout handler. Backend validates the order and returns ok/error_message.
    """
    service = OrderService(db)
    result = await service.pre_checkout_validate(
        invoice_payload=payload.invoice_payload,
        total_amount=payload.total_amount,
    )
    return PreCheckoutResponse(
        ok=result.get("ok", False),
        order_id=result.get("order_id"),
        error_message=result.get("error_message"),
    )


@router.post("/successful-payment", response_model=SuccessfulPaymentResponse)
async def successful_payment(payload: SuccessfulPaymentRequest, db: AsyncSession = Depends(get_db)):
    """
    Bot successful-payment handler. Backend marks order as paid, creates payment,
    logs delivery, and returns user_telegram_id + message_text for delivery.
    """
    service = OrderService(db)
    result = await service.fulfill(
        invoice_payload=payload.invoice_payload,
        telegram_payment_charge_id=payload.telegram_payment_charge_id,
        provider_payment_charge_id=payload.provider_payment_charge_id,
        total_amount=payload.total_amount,
    )
    return SuccessfulPaymentResponse(
        ok=result.get("ok", False),
        order_id=result.get("order_id"),
        user_telegram_id=result.get("user_telegram_id"),
        message_text=result.get("message_text"),
        channel_id=result.get("channel_id"),
        videos=result.get("videos") or [],
        error=result.get("error"),
    )


@router.post("/admin-message-map", response_model=AdminMessageMapResponse)
async def admin_message_map(payload: AdminMessageMapRequest, db: AsyncSession = Depends(get_db)):
    service = SupportService(db)
    await service.record_admin_message_map(
        payload.admin_message_id,
        payload.chat_id,
        payload.ticket_id,
    )
    return AdminMessageMapResponse(ok=True)