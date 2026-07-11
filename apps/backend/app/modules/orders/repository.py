from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, desc, asc
from sqlalchemy.orm import selectinload
from app.modules.orders.models import Order, OrderItem, Payment, Cart, CartItem, OrderStatus
from app.modules.catalog.models import Product as CatalogProduct

# Eager-load everything _to_order_out touches (items -> product -> translations)
# so serialization never lazy-loads outside the async greenlet.
_ORDER_EAGER = (
    selectinload(Order.items)
    .selectinload(OrderItem.product)
    .selectinload(CatalogProduct.translations),
)


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_published_by_ids(self, ids: List[int]) -> List[CatalogProduct]:
        if not ids:
            return []
        from app.modules.catalog.models import ProductStatus
        result = await self.db.execute(
            select(CatalogProduct).where(CatalogProduct.id.in_(ids), CatalogProduct.status == ProductStatus.published)
        )
        return list(result.scalars().all())

    async def bulk_increment_purchases(self, items: list) -> None:
        """Increment real_purchases for many products in one UPDATE.

        items: iterable of (product_id, quantity).
        Uses a single CASE statement instead of N round-trips.
        """
        from sqlalchemy import case
        agg: dict[int, int] = {}
        for product_id, quantity in items:
            agg[int(product_id)] = agg.get(int(product_id), 0) + int(quantity)
        if not agg:
            return
        ids = list(agg.keys())
        cases = [
            (CatalogProduct.id == pid, CatalogProduct.real_purchases + qty)
            for pid, qty in agg.items()
        ]
        stmt = (
            update(CatalogProduct)
            .where(CatalogProduct.id.in_(ids))
            .values(real_purchases=case(*cases, value=CatalogProduct.id))
        )
        await self.db.execute(stmt)


class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: int,
        total_stars: int,
        base_discount_percent: int,
        promo_discount_percent: int,
        final_discount_percent: int,
        paid_stars: int,
        promo_code_id: Optional[int] = None,
    ) -> Order:
        order = Order(
            user_id=user_id,
            total_stars=total_stars,
            base_discount_percent=base_discount_percent,
            promo_discount_percent=promo_discount_percent,
            final_discount_percent=final_discount_percent,
            paid_stars=paid_stars,
            promo_code_id=promo_code_id,
        )
        self.db.add(order)
        await self.db.flush()
        return order

    async def add_item(self, order_id: int, product_id: int, quantity: int, price_stars: int) -> OrderItem:
        item = OrderItem(order_id=order_id, product_id=product_id, quantity=quantity, price_stars=price_stars)
        self.db.add(item)
        await self.db.flush()
        return item

    async def get_by_id(self, order_id: int) -> Optional[Order]:
        # Eager-load items/product: fulfill() and delivery iterate order.items,
        # which would otherwise lazy-load outside the async greenlet.
        result = await self.db.execute(
            select(Order).options(*_ORDER_EAGER).where(Order.id == order_id)
        )
        return result.scalars().first()

    async def get_by_id_for_user(self, order_id: int, user_id: int) -> Optional[Order]:
        result = await self.db.execute(
            select(Order).options(*_ORDER_EAGER).where(Order.id == order_id, Order.user_id == user_id)
        )
        return result.scalars().first()

    async def list_for_user(self, user_id: int, limit: int = 20, offset: int = 0) -> List[Order]:
        result = await self.db.execute(
            select(Order).options(*_ORDER_EAGER).where(Order.user_id == user_id).order_by(Order.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def set_status_paid(self, order_id: int) -> bool:
        """Flip pending → paid. False means the order wasn't pending (already
        paid or cancelled) — the caller must not run fulfillment side effects."""
        result = await self.db.execute(
            update(Order)
            .where(Order.id == order_id, Order.status == OrderStatus.pending)
            .values(status="paid")
        )
        return bool(result.rowcount)

    async def find_pending_subscription(self, user_id: int, plan: str) -> Optional[Order]:
        """Newest unpaid subscription order for this plan (checkout re-use)."""
        result = await self.db.execute(
            select(Order)
            .where(
                Order.user_id == user_id,
                Order.status == OrderStatus.pending,
                Order.subscription_plan == plan,
            )
            .order_by(Order.created_at.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def get_paid_by_id(self, order_id: int) -> Optional[Order]:
        result = await self.db.execute(
            select(Order).options(*_ORDER_EAGER).where(Order.id == order_id, Order.status == OrderStatus.paid)
        )
        return result.scalars().first()

    async def list_with_filters_admin(
        self,
        status: Optional[OrderStatus] = None,
        sort: str = "created_at",
        order: str = "desc",
        start: int = 0,
        end: int = 50,
    ) -> Tuple[List[Order], int]:
        stmt = select(Order)
        if status:
            stmt = stmt.where(Order.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        sort_col = getattr(Order, sort, Order.created_at)
        if order == "desc":
            stmt = stmt.order_by(desc(sort_col))
        else:
            stmt = stmt.order_by(asc(sort_col))

        stmt = stmt.limit(end - start).offset(start)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def update_fields(self, order_id: int, fields: dict) -> Optional[Order]:
        result = await self.db.execute(select(Order).where(Order.id == order_id))
        order = result.scalars().first()
        if order:
            for key, value in fields.items():
                setattr(order, key, value)
            await self.db.flush()
        return order


class OrderItemRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def count_paid_items_for_user(self, user_id: int) -> int:
        """Lifetime videos bought: sum of item quantities across the user's paid
        orders. Free premium claims (paid_stars=0) are not purchases."""
        result = await self.db.execute(
            select(func.coalesce(func.sum(OrderItem.quantity), 0))
            .join(Order, OrderItem.order_id == Order.id)
            .where(Order.user_id == user_id, Order.status == OrderStatus.paid, Order.paid_stars > 0)
        )
        return int(result.scalar() or 0)

    async def list_items_with_products(self, order_id: int):
        from app.modules.catalog.models import ProductTranslation
        result = await self.db.execute(
            select(OrderItem, CatalogProduct, ProductTranslation)
            .join(CatalogProduct, OrderItem.product_id == CatalogProduct.id)
            .outerjoin(ProductTranslation, (ProductTranslation.product_id == CatalogProduct.id) & (ProductTranslation.language_code == "en"))
            .where(OrderItem.order_id == order_id)
        )
        return result.all()


class PaymentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        order_id: int,
        telegram_payment_charge_id: Optional[str],
        provider_payment_charge_id: Optional[str],
        status: str,
        stars_amount: int,
    ) -> Payment:
        payment = Payment(
            order_id=order_id,
            telegram_payment_charge_id=telegram_payment_charge_id,
            provider_payment_charge_id=provider_payment_charge_id,
            status=status,
            stars_amount=stars_amount,
        )
        self.db.add(payment)
        await self.db.flush()
        return payment

    async def find_by_telegram_charge_id(self, telegram_charge_id: str) -> Optional[Payment]:
        """Idempotency lookup: return existing Payment for this Telegram charge id, if any."""
        result = await self.db.execute(
            select(Payment).where(Payment.telegram_payment_charge_id == telegram_charge_id)
        )
        return result.scalars().first()


class LinkDeliveryLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: int,
        order_id: int,
        product_id: int,
        google_drive_link: str,
        delivery_method: str = "sent",
        status: str = "sent",
        error: Optional[str] = None,
    ):
        from app.modules.admin.models import LinkDeliveryLog
        log = LinkDeliveryLog(
            user_id=user_id,
            order_id=order_id,
            product_id=product_id,
            google_drive_link=google_drive_link,
            delivery_method=delivery_method,
            status=status,
            error=error,
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def bulk_create_for_order(self, order: Order, delivery_method: str = "resend") -> List:
        from app.modules.admin.models import LinkDeliveryLog
        logs = []
        for item in order.items:
            product = item.product
            if product and product.google_drive_link:
                log = LinkDeliveryLog(
                    user_id=order.user_id,
                    order_id=order.id,
                    product_id=product.id,
                    google_drive_link=product.google_drive_link,
                    delivery_method=delivery_method,
                    status="sent",
                )
                self.db.add(log)
                logs.append(log)
        await self.db.flush()
        return logs


class BotMessageMapRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, admin_message_id: int, chat_id: int, ticket_id: int):
        from app.modules.admin.models import BotMessageMap
        mapping = BotMessageMap(admin_message_id=admin_message_id, chat_id=chat_id, ticket_id=ticket_id)
        self.db.add(mapping)
        await self.db.flush()
        return mapping

    async def get_ticket_id_by_admin_message(self, admin_message_id: int) -> Optional[int]:
        from app.modules.admin.models import BotMessageMap
        result = await self.db.execute(
            select(BotMessageMap.ticket_id).where(BotMessageMap.admin_message_id == admin_message_id)
        )
        return result.scalars().first()

    async def table_check_or_create(self) -> None:
        # This is a no-op for SQLAlchemy models - tables are created via Alembic
        pass


class CartRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: int) -> Optional[Cart]:
        result = await self.db.execute(select(Cart).where(Cart.user_id == user_id))
        return result.scalars().first()

    async def create(self, user_id: int) -> Cart:
        cart = Cart(user_id=user_id)
        self.db.add(cart)
        await self.db.flush()
        return cart

    async def upsert_item(self, cart_id: int, product_id: int, quantity: int) -> CartItem:
        result = await self.db.execute(
            select(CartItem).where(CartItem.cart_id == cart_id, CartItem.product_id == product_id)
        )
        item = result.scalars().first()
        if item:
            item.quantity = quantity
        else:
            item = CartItem(cart_id=cart_id, product_id=product_id, quantity=quantity)
            self.db.add(item)
        await self.db.flush()
        return item

    async def remove_item(self, cart_id: int, product_id: int) -> None:
        result = await self.db.execute(
            select(CartItem).where(CartItem.cart_id == cart_id, CartItem.product_id == product_id)
        )
        item = result.scalars().first()
        if item:
            await self.db.delete(item)

    async def clear(self, cart_id: int) -> None:
        result = await self.db.execute(select(CartItem).where(CartItem.cart_id == cart_id))
        items = result.scalars().all()
        for item in items:
            await self.db.delete(item)

    async def set_promo_code(self, cart_id: int, promo_code_id: Optional[int]) -> None:
        await self.db.execute(update(Cart).where(Cart.id == cart_id).values(promo_code_id=promo_code_id))
