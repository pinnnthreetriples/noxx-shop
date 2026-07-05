import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime, Text, Numeric, Enum, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.models_base import Base


class ProductStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    hidden = "hidden"
    deleted = "deleted"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    status: Mapped[ProductStatus] = mapped_column(Enum(ProductStatus), default=ProductStatus.published)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    translations: Mapped[List["CategoryTranslation"]] = relationship("CategoryTranslation", back_populates="category", cascade="all, delete-orphan")
    products: Mapped[List["Product"]] = relationship("Product", back_populates="category")


class CategoryTranslation(Base):
    __tablename__ = "category_translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    language_code: Mapped[str] = mapped_column(String(10))
    title: Mapped[str] = mapped_column(String(255))

    category: Mapped["Category"] = relationship("Category", back_populates="translations")

    __table_args__ = (UniqueConstraint("category_id", "language_code", name="uq_category_translation"),)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    translations: Mapped[List["TagTranslation"]] = relationship("TagTranslation", back_populates="tag", cascade="all, delete-orphan")
    products: Mapped[List["ProductTag"]] = relationship("ProductTag", back_populates="tag")


class TagTranslation(Base):
    __tablename__ = "tag_translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), index=True)
    language_code: Mapped[str] = mapped_column(String(10))
    title: Mapped[str] = mapped_column(String(255))

    tag: Mapped["Tag"] = relationship("Tag", back_populates="translations")

    __table_args__ = (UniqueConstraint("tag_id", "language_code", name="uq_tag_translation"),)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    status: Mapped[ProductStatus] = mapped_column(Enum(ProductStatus), default=ProductStatus.draft)
    price_stars: Mapped[int] = mapped_column(Integer, default=0)
    usd_price_mode: Mapped[str] = mapped_column(String(20), default="auto")
    usd_price_manual: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"), nullable=True, index=True)
    cover_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preview_video_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    google_drive_link: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    google_drive_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    display_views: Mapped[int] = mapped_column(Integer, default=0)
    real_views: Mapped[int] = mapped_column(Integer, default=0)
    display_purchases: Mapped[int] = mapped_column(Integer, default=0)
    real_purchases: Mapped[int] = mapped_column(Integer, default=0)
    trend_score: Mapped[int] = mapped_column(Integer, default=0)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    available_for_subscription: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="products")
    translations: Mapped[List["ProductTranslation"]] = relationship("ProductTranslation", back_populates="product", cascade="all, delete-orphan")
    tags: Mapped[List["ProductTag"]] = relationship("ProductTag", back_populates="product", cascade="all, delete-orphan")
    favorites: Mapped[List["Favorite"]] = relationship("Favorite", back_populates="product", cascade="all, delete-orphan")
    recently_viewed: Mapped[List["RecentlyViewed"]] = relationship("RecentlyViewed", back_populates="product")
    order_items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="product")


class ProductTranslation(Base):
    __tablename__ = "product_translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    language_code: Mapped[str] = mapped_column(String(10))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    product: Mapped["Product"] = relationship("Product", back_populates="translations")

    __table_args__ = (UniqueConstraint("product_id", "language_code", name="uq_product_translation"),)


class ProductTag(Base):
    __tablename__ = "product_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), index=True)

    product: Mapped["Product"] = relationship("Product", back_populates="tags")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="products")

    __table_args__ = (UniqueConstraint("product_id", "tag_id", name="uq_product_tag"),)
