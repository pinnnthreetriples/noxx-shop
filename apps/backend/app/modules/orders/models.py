import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Integer, String, ForeignKey, DateTime, Numeric, Enum, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.models_base import Base
from app.modules.promos.models import PromoCode, PromoRedemption  # noqa: F401 - re-exported


class OrderStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"
    cancelled = "cancelled"
    refunded_manual = "refunded_manual"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    pre_checkout = "pre_checkout"
    paid = "paid"
    failed = "failed"




class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    promo_code_id: Mapped[Optional[int]] = mapped_column(ForeignKey("promo_codes.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="cart")
    items: Mapped[List["CartItem"]] = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")
    promo_code: Mapped[Optional["PromoCode"]] = relationship("PromoCode")


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    cart: Mapped["Cart"] = relationship("Cart", back_populates="items")
    product: Mapped["Product"] = relationship("Product")

    __table_args__ = (UniqueConstraint("cart_id", "product_id", name="uq_cart_item"),)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.pending)
    total_stars: Mapped[int] = mapped_column(Integer, default=0)
    base_discount_percent: Mapped[int] = mapped_column(Integer, default=0)
    promo_discount_percent: Mapped[int] = mapped_column(Integer, default=0)
    final_discount_percent: Mapped[int] = mapped_column(Integer, default=0)
    paid_stars: Mapped[int] = mapped_column(Integer, default=0)
    approx_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    promo_code_id: Mapped[Optional[int]] = mapped_column(ForeignKey("promo_codes.id"), nullable=True)
    # OrbChain hosted-invoice id, so we can poll payment status without a webhook.
    orbchain_track_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    # Set for premium-subscription orders ("week" | "month" | "year"); such
    # orders have no items — fulfillment extends user.premium_until instead.
    subscription_plan: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment: Mapped[Optional["Payment"]] = relationship("Payment", back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    price_stars: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="order_items")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True, index=True)
    telegram_payment_charge_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provider_payment_charge_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.pending)
    stars_amount: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    order: Mapped["Order"] = relationship("Order", back_populates="payment")
