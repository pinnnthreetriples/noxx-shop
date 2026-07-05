import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, Integer, String, Boolean, Text, ForeignKey, DateTime, Numeric, Enum, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.models_base import Base


class AdminRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    support = "support"
    content_manager = "content_manager"


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[AdminRole] = mapped_column(Enum(AdminRole), default=AdminRole.owner)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Setting(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bot_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    support_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    content_18_plus_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    default_language: Mapped[str] = mapped_column(String(10), default="en")
    stars_to_usd_mode: Mapped[str] = mapped_column(String(20), default="auto")
    manual_stars_to_usd_rate: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    max_discount_percent: Mapped[int] = mapped_column(Integer, default=50)
    terms_text_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refund_policy_text_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notifications_enabled_by_default: Mapped[bool] = mapped_column(Boolean, default=True)
    subscription_coming_soon_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    subscription_coming_soon_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Auto-discount tiers (the best single one applies, then promo on top)
    discount_first_purchase_percent: Mapped[int] = mapped_column(Integer, default=10)
    discount_bulk_percent: Mapped[int] = mapped_column(Integer, default=15)
    discount_bulk_min_items: Mapped[int] = mapped_column(Integer, default=20)
    discount_loyalty_percent: Mapped[int] = mapped_column(Integer, default=30)
    discount_loyalty_min_items: Mapped[int] = mapped_column(Integer, default=20)
    # Premium subscription prices in Stars (durations are fixed: 7/30/365 days)
    sub_price_week_stars: Mapped[int] = mapped_column(Integer, default=99)
    sub_price_month_stars: Mapped[int] = mapped_column(Integer, default=299)
    sub_price_year_stars: Mapped[int] = mapped_column(Integer, default=2499)
    # OrbChain webhook signing secret — pushed from the merchant dashboard, never exposed to the client.
    orbchain_webhook_secret: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AdminLog(Base):
    __tablename__ = "admin_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id"), index=True)
    action: Mapped[str] = mapped_column(String(50))
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    before_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    after_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LinkDeliveryLog(Base):
    __tablename__ = "link_delivery_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    google_drive_link: Mapped[str] = mapped_column(Text)
    delivery_method: Mapped[str] = mapped_column(String(50))
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[str] = mapped_column(String(20), default="sent")
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class GoogleDriveToken(Base):
    __tablename__ = "google_drive_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id"), index=True)
    access_token: Mapped[str] = mapped_column(Text)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class BotMessageMap(Base):
    __tablename__ = "bot_message_map"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_message_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    ticket_id: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
