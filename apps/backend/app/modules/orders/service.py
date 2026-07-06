"""
Order use-case service.

Owns ALL business logic for orders, payments, fulfillment, and discounts.
Routers must be thin: parse request → call service → return response.
"""
from __future__ import annotations

import logging
import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.modules.orders.models import (
    Order,
    OrderItem,
    OrderStatus,
    PaymentStatus,
)
from app.modules.orders.repository import (
    OrderRepository,
    OrderItemRepository,
    PaymentRepository,
    LinkDeliveryLogRepository,
    BotMessageMapRepository,
)
from app.modules.catalog.repository import ProductRepository
from app.modules.users.repository import UserRepository
from app.modules.promos.repository import PromoCodeRepository, PromoRedemptionRepository
from app.modules.orders.schemas import (
    CartEstimateOut,
    CheckoutOut,
    CoinOut,
    OrderItemOut,
    OrderOut,
    PaymentStateOut,
)

logger = logging.getLogger(__name__)


class OrderService:
    """Use-case service for orders and payments."""

    # Premium subscription plans. Prepaid periods, no auto-renewal.
    # Durations are fixed; prices in Stars come from admin Settings
    # (sub_price_*_stars), these are the fallbacks. Mirrored in the miniapp.
    SUB_DAYS = {"week": 7, "month": 30, "year": 365}
    SUB_PRICE_DEFAULTS = {"week": 99, "month": 299, "year": 2499}

    def __init__(self, db: AsyncSession):
        self.db = db
        self.product_repo = ProductRepository(db)
        self.order_repo = OrderRepository(db)
        self.item_repo = OrderItemRepository(db)
        self.payment_repo = PaymentRepository(db)
        self.delivery_log_repo = LinkDeliveryLogRepository(db)
        self.bot_message_repo = BotMessageMapRepository(db)
        self.user_repo = UserRepository(db)
        self.promo_repo = PromoCodeRepository(db)
        self.redemption_repo = PromoRedemptionRepository(db)

    # ----- Discount calculation (business rule) -----

    async def calculate_discounts(
        self,
        user,
        product_ids: List[int],
        promo_code: Optional[str] = None,
        cart_total_stars: int = 0,
    ) -> Dict[str, int]:
        """
        Business rule: ONE automatic discount (the best of those the user qualifies
        for — they never stack), then the promo code on top, capped by max_discount_percent.
        All tiers/percents/cap are admin-configurable (Settings), defaults:
          30% — loyalty: 20+ videos bought lifetime (paid orders)
          15% — big cart: 20+ videos in this order
          10% — first purchase (no paid video purchases yet)
        """
        s = await self._settings_row()
        purchased = await self.item_repo.count_paid_items_for_user(user.id)
        eligible = [0]
        if purchased >= (s.discount_loyalty_min_items if s else 20):
            eligible.append(s.discount_loyalty_percent if s else 30)
        if len(product_ids) >= (s.discount_bulk_min_items if s else 20):
            eligible.append(s.discount_bulk_percent if s else 15)
        if purchased == 0:
            eligible.append(s.discount_first_purchase_percent if s else 10)
        base_discount = max(eligible)
        promo_discount = 0

        if promo_code:
            promo_pct = await self._lookup_promo_discount(promo_code, user, cart_total_stars)
            if promo_pct is not None:
                promo_discount = promo_pct

        # Cap: admin setting wins, env value is the fallback (same pattern as _star_rate).
        cap = (s.max_discount_percent if s else None) or settings.max_discount_percent
        final = min(base_discount + promo_discount, cap)
        return {
            "base_discount_percent": base_discount,
            "promo_discount_percent": promo_discount,
            "final_discount_percent": final,
        }

    async def _lookup_promo_discount(
        self,
        promo_code: str,
        user,
        cart_total_stars: int = 0,
    ) -> Optional[int]:
        promo = await self.promo_repo.get_by_code(promo_code)
        if not promo or not promo.active:
            return None
        now = datetime.now(timezone.utc)
        if promo.starts_at and promo.starts_at > now:
            return None
        if promo.expires_at and promo.expires_at < now:
            return None
        if promo.usage_limit is not None and promo.used_count >= promo.usage_limit:
            return None
        # One redemption per user (paid orders only; pending checkouts don't count).
        if await self.redemption_repo.exists(promo.id, user.id):
            return None
        if promo.first_purchase_only:
            if await self.item_repo.count_paid_items_for_user(user.id) > 0:
                return None
        if promo.min_cart_total is not None and cart_total_stars < promo.min_cart_total:
            return None
        if promo.discount_type == "percentage":
            return int(promo.discount_value)
        return None

    # ----- Cart estimate -----

    async def estimate_cart(
        self,
        user,
        product_ids: List[int],
        promo_code: Optional[str] = None,
    ) -> CartEstimateOut:
        if not product_ids:
            return CartEstimateOut(
                product_ids=[],
                total_stars=0,
                base_discount_percent=0,
                promo_discount_percent=0,
                final_discount_percent=0,
                to_pay_stars=0,
                approx_usd=None,
                promo_code=None,
            )
        products = await self.product_repo.list_published_by_ids(product_ids)
        total = sum(p.price_stars for p in products)
        dinfo = await self.calculate_discounts(user, product_ids, promo_code, total)
        to_pay = int(total * (100 - dinfo["final_discount_percent"]) / 100)
        return CartEstimateOut(
            product_ids=product_ids,
            total_stars=total,
            base_discount_percent=dinfo["base_discount_percent"],
            promo_discount_percent=dinfo["promo_discount_percent"],
            final_discount_percent=dinfo["final_discount_percent"],
            to_pay_stars=to_pay,
            approx_usd=None,
            promo_code=promo_code,
        )

    # ----- Checkout -----

    async def create_checkout(
        self,
        user,
        product_ids: List[int],
        promo_code: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> CheckoutOut:
        products = await self.product_repo.list_published_by_ids(product_ids)
        if not products:
            raise ValueError("No valid products")
        # money guard: a mispriced (0-Star) product must block checkout,
        # not silently sell for the 1-Star invoice minimum
        if any((p.price_stars or 0) <= 0 for p in products):
            raise ValueError("A product in the cart has no price set — contact support")

        total = sum(p.price_stars for p in products)
        dinfo = await self.calculate_discounts(user, product_ids, promo_code, total)
        to_pay = max(int(total * (100 - dinfo["final_discount_percent"]) / 100), 1)

        promo_code_id: Optional[int] = None
        if promo_code and dinfo["promo_discount_percent"] > 0:
            promo = await self.promo_repo.get_by_code(promo_code)
            if promo:
                promo_code_id = promo.id

        order = await self.order_repo.create(
            user_id=user.id,
            total_stars=total,
            base_discount_percent=dinfo["base_discount_percent"],
            promo_discount_percent=dinfo["promo_discount_percent"],
            final_discount_percent=dinfo["final_discount_percent"],
            paid_stars=to_pay,
            promo_code_id=promo_code_id,
        )
        for p in products:
            await self.order_repo.add_item(order.id, p.id, 1, p.price_stars)

        await self.db.commit()
        await self.db.refresh(order)

        return await self._invoice_for_order(order.id, to_pay, provider)

    async def create_subscription_checkout(
        self,
        user,
        plan: str,
        provider: Optional[str] = None,
    ) -> CheckoutOut:
        """Premium subscription purchase: an itemless order whose fulfillment
        extends user.premium_until instead of delivering links."""
        if plan not in self.SUB_DAYS:
            raise ValueError("Unknown plan")
        s = await self._settings_row()
        stars = (getattr(s, f"sub_price_{plan}_stars", None) if s else None) or self.SUB_PRICE_DEFAULTS[plan]
        if stars <= 0:
            raise ValueError("Subscription price is not configured")
        order = await self.order_repo.create(
            user_id=user.id,
            total_stars=stars,
            base_discount_percent=0,
            promo_discount_percent=0,
            final_discount_percent=0,
            paid_stars=stars,
            promo_code_id=None,
        )
        order.subscription_plan = plan
        await self.db.commit()
        await self.db.refresh(order)
        return await self._invoice_for_order(order.id, stars, provider)

    async def _invoice_for_order(self, order_id: int, to_pay: int, provider: Optional[str]) -> CheckoutOut:
        # Honor the client's payment-method choice; default (None) prefers
        # OrbChain crypto checkout when configured, else Telegram Stars.
        if settings.orbchain_api_key and provider != "telegram":
            invoice_url = await self._create_orbchain_invoice(order_id, to_pay)
            if invoice_url:
                return CheckoutOut(
                    order_id=order_id,
                    invoice_url=invoice_url,
                    provider="orbchain",
                    amount_usd=await self._amount_usd(to_pay),
                )

        invoice_url = await self._create_telegram_invoice(order_id, to_pay)
        if not invoice_url:
            invoice_url = f"https://t.me/{settings.bot_username}?start=invoice_{order_id}"
        return CheckoutOut(order_id=order_id, invoice_url=invoice_url, provider="telegram")

    async def _settings_row(self):
        """The singleton admin Settings row (None if the table is empty)."""
        from app.modules.admin.models import Setting
        return (await self.db.execute(select(Setting).limit(1))).scalars().first()

    async def _star_rate(self) -> float:
        """Effective Stars→USD rate: admin setting "manual" wins, "auto" = built-in rate."""
        from app.modules.admin.models import Setting
        row = await self.db.execute(
            select(Setting.stars_to_usd_mode, Setting.manual_stars_to_usd_rate).limit(1)
        )
        s = row.first()
        if s and s.stars_to_usd_mode == "manual" and s.manual_stars_to_usd_rate:
            return float(s.manual_stars_to_usd_rate)
        return settings.star_usd_rate

    async def _amount_usd(self, stars: int) -> float:
        """USD charged for a Stars total (OrbChain has a $0.50 invoice floor)."""
        return max(round(stars * await self._star_rate(), 2), 0.5)

    async def _create_orbchain_invoice(self, order_id: int, amount_stars: int) -> str:
        from app.modules.payments_orbchain.client import create_invoice, OrbChainError
        amount_usd = await self._amount_usd(amount_stars)
        return_url = f"{settings.telegram_webapp_url.rstrip('/')}/purchases" if settings.telegram_webapp_url else ""
        try:
            data = await create_invoice(
                amount_usd=amount_usd,
                order_id=str(order_id),
                description=f"Order #{order_id}",
                return_url=return_url,
            )
            track_id = data.get("track_id")
            if track_id:
                await self.order_repo.update_fields(order_id, {"orbchain_track_id": track_id})
                await self.db.commit()
            return data.get("payment_url", "")
        except OrbChainError as e:
            logger.warning("OrbChain invoice error: %s", e)
            return ""

    async def check_orbchain_payment(self, user, order_id: int) -> Dict[str, Any]:
        """Poll OrbChain for this order's status and fulfill it once Paid.
        Uses merchant_api_key only (no webhook secret needed). Idempotent."""
        from app.modules.payments_orbchain.client import get_payment, OrbChainError
        order = await self.order_repo.get_by_id_for_user(order_id, user.id)
        if not order:
            return {"paid": False, "status": "not_found"}
        if order.status.value == "paid":
            return {"paid": True, "status": "paid"}
        if not order.orbchain_track_id:
            return {"paid": False, "status": order.status.value}
        try:
            data = await get_payment(order.orbchain_track_id)
        except OrbChainError as e:
            logger.warning("OrbChain status error: %s", e)
            return {"paid": False, "status": "unavailable"}
        remote = (data.get("status") or "").lower()
        if remote == "paid":
            await self.fulfill(
                invoice_payload=str(order_id),
                telegram_payment_charge_id=f"orb:{order.orbchain_track_id}",
                provider_payment_charge_id=order.orbchain_track_id,
                total_amount=0,
            )
            return {"paid": True, "status": "paid"}
        return {"paid": False, "status": remote or order.status.value}

    async def get_orbchain_payment(self, user, order_id: int) -> Optional[PaymentStateOut]:
        """Current in-app payment state for an order: coin list + (if a coin was
        already picked) the deposit address, exact amount, QR and expiry.
        Fulfills opportunistically if OrbChain already shows it as paid."""
        from app.modules.payments_orbchain.client import get_payment, qr_data_uri, OrbChainError
        from app.modules.payments_orbchain.coins import ORBCHAIN_COINS
        order = await self.order_repo.get_by_id_for_user(order_id, user.id)
        if not order:
            return None
        coins = [CoinOut(**c) for c in ORBCHAIN_COINS]
        base = dict(order_id=order_id, amount_usd=await self._amount_usd(order.paid_stars), coins=coins)
        if order.status.value == "paid":
            return PaymentStateOut(status="paid", paid=True, **base)
        if not order.orbchain_track_id:
            return PaymentStateOut(status="pending", paid=False, **base)
        try:
            data = await get_payment(order.orbchain_track_id)
        except OrbChainError:
            return PaymentStateOut(status="pending", paid=False, **base)
        remote = (data.get("status") or "").lower()
        if remote == "paid":
            await self.fulfill(
                invoice_payload=str(order_id),
                telegram_payment_charge_id=f"orb:{order.orbchain_track_id}",
                provider_payment_charge_id=order.orbchain_track_id,
                total_amount=0,
            )
            return PaymentStateOut(status="paid", paid=True, **base)
        addr = data.get("address")
        return PaymentStateOut(
            status="pending", paid=False,
            pay_currency=data.get("pay_currency"),
            pay_amount=data.get("pay_amount"),
            address=addr,
            qr=qr_data_uri(addr) if addr else None,
            expires_at=data.get("expires_at"),
            **base,
        )

    async def select_orbchain_coin(self, user, order_id: int, coin: str) -> PaymentStateOut:
        """Pick a coin: OrbChain assigns a deposit address, we return it inline."""
        from app.modules.payments_orbchain.client import select_coin, qr_data_uri, OrbChainError
        from app.modules.payments_orbchain.coins import VALID_COIN_CODES
        if coin not in VALID_COIN_CODES:
            raise ValueError("Unsupported coin")
        order = await self.order_repo.get_by_id_for_user(order_id, user.id)
        if not order:
            raise ValueError("Order not found")
        if not order.orbchain_track_id:
            raise ValueError("No crypto invoice for this order")
        try:
            data = await select_coin(order.orbchain_track_id, coin)
        except OrbChainError as e:
            logger.warning("OrbChain select coin error: %s", e)
            raise ValueError("Could not reserve a deposit address, please try again") from e
        addr = data.get("address")
        remote = (data.get("status") or "").lower()
        return PaymentStateOut(
            order_id=order_id,
            status="paid" if remote == "paid" else "pending",
            paid=remote == "paid",
            amount_usd=await self._amount_usd(order.paid_stars),
            pay_currency=data.get("pay_currency") or coin,
            pay_amount=data.get("pay_amount"),
            address=addr,
            qr=qr_data_uri(addr) if addr else None,
            expires_at=data.get("expires_at"),
            coins=[],  # picker already loaded on the client
        )

    async def _create_telegram_invoice(self, order_id: int, amount_stars: int) -> str:
        if not settings.bot_token:
            return ""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"https://api.telegram.org/bot{settings.bot_token}/createInvoiceLink",
                    json={
                        "title": f"Order #{order_id}",
                        "description": "Video content purchase",
                        "payload": str(order_id),
                        "provider_token": "",
                        "currency": "XTR",
                        "prices": [{"label": "Stars", "amount": amount_stars}],
                    },
                    timeout=15.0,
                )
                data = resp.json()
                if data.get("ok"):
                    return data["result"]
        except Exception as e:
            logger.warning("createInvoiceLink exception: %s", e)
        return ""

    # ----- User-facing queries -----

    async def list_user_orders(
        self,
        user,
        limit: int = 20,
        offset: int = 0,
    ) -> List[OrderOut]:
        from app.modules.catalog.service import resolve_language
        lang = resolve_language(user)
        orders = await self.order_repo.list_for_user(user.id, limit=limit, offset=offset)
        return [self._to_order_out(o, lang) for o in orders]

    async def get_user_order(self, user, order_id: int) -> Optional[OrderOut]:
        from app.modules.catalog.service import resolve_language
        lang = resolve_language(user)
        o = await self.order_repo.get_by_id_for_user(order_id, user.id)
        if not o:
            return None
        return self._to_order_out(o, lang)

    def _to_order_out(self, o: Order, lang: str) -> OrderOut:
        from app.modules.catalog.service import _product_title
        items_out: List[OrderItemOut] = []
        for item in o.items:
            p = item.product
            items_out.append(
                OrderItemOut(
                    id=item.id,
                    product_id=p.id if p else item.product_id,
                    title=_product_title(p, lang) if p else "",
                    quantity=item.quantity,
                    price_stars=item.price_stars,
                    google_drive_link=p.google_drive_link if (p and o.status.value == "paid") else None,
                )
            )
        return OrderOut(
            id=o.id,
            status=o.status.value,
            total_stars=o.total_stars,
            base_discount_percent=o.base_discount_percent,
            promo_discount_percent=o.promo_discount_percent,
            final_discount_percent=o.final_discount_percent,
            paid_stars=o.paid_stars,
            approx_usd=float(o.approx_usd) if o.approx_usd else None,
            subscription_plan=o.subscription_plan,
            created_at=o.created_at,
            items=items_out,
        )

    # ----- Webhook payment (existing public endpoint) -----

    async def webhook_payment(self, telegram_charge_id: Optional[str], provider_charge_id: Optional[str]) -> Dict[str, Any]:
        if not telegram_charge_id and not provider_charge_id:
            raise ValueError("Missing charge id")
        payment = await self.payment_repo.find_by_charge_id(telegram_charge_id, provider_charge_id)
        if payment:
            await self.payment_repo.mark_paid(payment.id)
            await self.db.commit()
            return {"ok": True, "order_id": payment.order_id}
        return {"ok": False, "detail": "Payment not found"}

    # ----- Admin actions -----

    async def resend_links(self, order_id: int) -> Dict[str, Any]:
        order = await self.order_repo.get_paid_by_id(order_id)
        if not order:
            return {"resent": False, "reason": "Paid order not found"}
        await self.delivery_log_repo.bulk_create_for_order(order, delivery_method="resend")
        await self.db.commit()
        return {"resent": True}

    async def update_order_fields(self, order_id: int, fields: Dict[str, Any]) -> Optional[Order]:
        order = await self.order_repo.update_fields(order_id, fields)
        if order:
            await self.db.commit()
        return order

    # ----- Internal API: pre-checkout validation -----

    async def pre_checkout_validate(
        self,
        invoice_payload: str,
        total_amount: int,
    ) -> Dict[str, Any]:
        """Validate that an order is still pending and matches the amount."""
        try:
            order_id = int(invoice_payload)
        except (ValueError, TypeError):
            return {"ok": False, "error_message": "Invalid order id"}
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            return {"ok": False, "error_message": "Order not found", "order_id": None}
        if order.status.value != "pending":
            return {"ok": False, "error_message": "Order is not pending", "order_id": order_id}
        if order.paid_stars != total_amount:
            return {"ok": False, "error_message": "Order amount mismatch", "order_id": order_id}
        return {"ok": True, "order_id": order_id, "error_message": None}

    # ----- Internal API: payment fulfillment (moved from bot) -----

    async def fulfill(
        self,
        invoice_payload: str,
        telegram_payment_charge_id: str,
        provider_payment_charge_id: str,
        total_amount: int,
    ) -> Dict[str, Any]:
        """
        Fulfill an order after successful payment.
        Idempotent: a duplicate webhook with the same telegram_payment_charge_id
        returns the existing payment without re-running side effects.
        1. Mark order paid.
        2. Create payment record.
        3. Increment product stats.
        4. Create link delivery logs.
        5. Return user_telegram_id + message_text for the bot to deliver.
        """
        try:
            order_id = int(invoice_payload)
        except (ValueError, TypeError):
            return {"ok": False, "error": "Invalid invoice_payload"}

        # Idempotency: if this charge was already processed, return existing result.
        if telegram_payment_charge_id:
            existing = await self.payment_repo.find_by_telegram_charge_id(telegram_payment_charge_id)
            if existing:
                return await self._build_delivery_result(existing.order_id)

        order = await self.order_repo.get_by_id(order_id)
        if not order:
            return {"ok": False, "error": "Order not found"}

        # 1. status pending -> paid
        await self.order_repo.set_status_paid(order_id)
        # 2. payment record
        await self.payment_repo.create(
            order_id=order_id,
            telegram_payment_charge_id=telegram_payment_charge_id,
            provider_payment_charge_id=provider_payment_charge_id,
            status=PaymentStatus.paid.value,
            stars_amount=total_amount,
        )
        # Promo bookkeeping on payment, not checkout: abandoned carts must not burn usage.
        if order.promo_code_id and not await self.redemption_repo.exists(order.promo_code_id, order.user_id):
            await self.promo_repo.increment_used_count(order.promo_code_id)
            await self.redemption_repo.create(order.promo_code_id, order.user_id, order.id)
        if order.subscription_plan:
            # 3./4. Subscription order: extend premium access instead of delivering links.
            days = self.SUB_DAYS.get(order.subscription_plan, 30)
            buyer = await self.user_repo.get_by_id(order.user_id)
            if buyer:
                now = datetime.now(timezone.utc)
                base = buyer.premium_until if buyer.premium_until and buyer.premium_until > now else now
                buyer.premium_until = base + timedelta(days=days)
        else:
            # 3. Increment product purchases (single bulk UPDATE; no N+1)
            await self.product_repo.bulk_increment_purchases(
                [(item.product_id, item.quantity) for item in order.items]
            )
            # 4. Link delivery logs (bulk insert)
            await self.delivery_log_repo.bulk_create_for_order(order, delivery_method="bot")

        await self.db.commit()

        # Stars payments are delivered by the bot from this method's return value;
        # crypto payments have no bot update, so the queue delivers the message.
        if telegram_payment_charge_id and telegram_payment_charge_id.startswith("orb:"):
            await self._enqueue_delivery(order_id)

        return await self._build_delivery_result(order_id)

    async def _enqueue_delivery(self, order_id: int) -> None:
        """Queue the delivery message for the bot. Used when there is no Telegram
        payment update to reply to: crypto payments and premium claims."""
        result = await self._build_delivery_result(order_id)
        if not result.get("ok"):
            return
        try:
            import redis.asyncio as redis_async
            r = redis_async.from_url(settings.redis_url, decode_responses=True)
            try:
                await r.lpush("deliveries:queue", json.dumps({
                    "user_telegram_id": result["user_telegram_id"],
                    "message_text": result["message_text"],
                }))
            finally:
                await r.aclose()
        except Exception as e:
            logger.warning("delivery enqueue failed for order %s: %s", order_id, e)

    async def claim_with_premium(self, user, product_id: int) -> Dict[str, Any]:
        """Premium perk: an active subscriber gets any premium video at no cost.
        Creates a paid 0-star order so the video lands in My purchases and the
        bot delivers the link, same as a regular purchase."""
        now = datetime.now(timezone.utc)
        if not (user.premium_until and user.premium_until > now):
            raise ValueError("No active Premium subscription")
        products = await self.product_repo.list_published_by_ids([product_id])
        product = products[0] if products else None
        if not product or not product.is_premium:
            raise ValueError("Not a premium video")
        # Idempotent: already owned -> return the existing order.
        existing = await self.db.execute(
            select(OrderItem.order_id)
            .join(Order, OrderItem.order_id == Order.id)
            .where(Order.user_id == user.id, Order.status == OrderStatus.paid,
                   OrderItem.product_id == product_id)
            .limit(1)
        )
        owned = existing.scalar()
        if owned:
            return {"ok": True, "order_id": owned}
        order = await self.order_repo.create(
            user_id=user.id, total_stars=product.price_stars,
            base_discount_percent=100, promo_discount_percent=0,
            final_discount_percent=100, paid_stars=0, promo_code_id=None,
        )
        await self.order_repo.add_item(order.id, product.id, 1, product.price_stars)
        await self.order_repo.set_status_paid(order.id)
        await self.product_repo.bulk_increment_purchases([(product.id, 1)])
        order = await self.order_repo.get_by_id(order.id)  # reload with items eager
        await self.delivery_log_repo.bulk_create_for_order(order, delivery_method="premium")
        await self.db.commit()
        await self._enqueue_delivery(order.id)
        return {"ok": True, "order_id": order.id}

    async def _build_delivery_result(self, order_id: int) -> Dict[str, Any]:
        """Compose the user_telegram_id + message_text for a paid order."""
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            return {"ok": False, "error": "Order not found"}
        items = await self.item_repo.list_items_with_products(order_id)
        user = await self.user_repo.get_by_id(order.user_id)
        if not user or not user.telegram_id:
            return {"ok": False, "error": "User not found"}

        if order.subscription_plan:
            until = user.premium_until.strftime("%b %d, %Y") if user.premium_until else ""
            message_text = f"Premium activated! Your subscription is active until {until}."
        else:
            lines = [f"Thanks for your purchase!\n\nOrder #{order_id}\n"]
            for idx, (_, product, translation) in enumerate(items, 1):
                title = translation.title if translation else (product.slug if product else "Item")
                link = (product.google_drive_link if product else "") or "Link unavailable"
                lines.append(f"{idx}. {title} — {link}")
            message_text = "\n".join(lines)

        return {
            "ok": True,
            "order_id": order_id,
            "user_telegram_id": user.telegram_id,
            "message_text": message_text,
        }



