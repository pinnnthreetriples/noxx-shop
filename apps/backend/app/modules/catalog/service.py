from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, or_
from sqlalchemy.orm import selectinload
from app.models import Product, ProductTranslation, ProductTag, Category, Tag
from app.modules.catalog.schemas import ProductListItem, ProductDetail, CategoryOut, TagOut
from app.core.exceptions import NotFoundException

# Eager-load every relationship the serializers touch (translations, category, tags)
# so response building never triggers a lazy load outside the async greenlet.
_EAGER = (
    selectinload(Product.translations),
    selectinload(Product.category).selectinload(Category.translations),
    selectinload(Product.tags).selectinload(ProductTag.tag).selectinload(Tag.translations),
)

SUPPORTED_LANGUAGES = {"en", "ru", "es", "de", "el", "ro", "bg", "mo", "sr", "tr"}


def resolve_language(user) -> str:
    lang = user.selected_language or user.language_code or "en"
    return lang if lang in SUPPORTED_LANGUAGES else "en"


def _product_title(product: Product, lang: str) -> str:
    trans = next((t for t in product.translations if t.language_code == lang), None)
    if not trans:
        trans = next((t for t in product.translations if t.language_code == "en"), None)
    return trans.title if trans else product.slug


def _product_desc(product: Product, lang: str) -> Optional[str]:
    trans = next((t for t in product.translations if t.language_code == lang), None)
    if not trans:
        trans = next((t for t in product.translations if t.language_code == "en"), None)
    return trans.description if trans else None


def _category_out(product: Product, lang: str) -> Optional[CategoryOut]:
    if not product.category:
        return None
    c = product.category
    ctrans = next((t for t in c.translations if t.language_code == lang), None)
    if not ctrans:
        ctrans = next((t for t in c.translations if t.language_code == "en"), None)
    return CategoryOut(id=c.id, slug=c.slug, title=ctrans.title if ctrans else c.slug)


def _tags_out(product: Product, lang: str) -> List[TagOut]:
    out = []
    for pt in product.tags:
        ttrans = next((t for t in pt.tag.translations if t.language_code == lang), None)
        if not ttrans:
            ttrans = next((t for t in pt.tag.translations if t.language_code == "en"), None)
        out.append(TagOut(id=pt.tag.id, slug=pt.tag.slug, title=ttrans.title if ttrans else pt.tag.slug))
    return out


def _to_list_item(product: Product, lang: str) -> ProductListItem:
    return ProductListItem(
        id=product.id, slug=product.slug, title=_product_title(product, lang),
        category=_category_out(product, lang), tags=_tags_out(product, lang),
        display_views=product.display_views, display_purchases=product.display_purchases,
        cover_url=product.cover_url, is_premium=product.is_premium,
        price_stars=product.price_stars,
        approx_usd=float(product.usd_price_manual) if product.usd_price_manual else None,
    )


def _to_detail(product: Product, lang: str) -> ProductDetail:
    return ProductDetail(
        id=product.id, slug=product.slug, title=_product_title(product, lang),
        description=_product_desc(product, lang),
        category=_category_out(product, lang), tags=_tags_out(product, lang),
        display_views=product.display_views, display_purchases=product.display_purchases,
        cover_url=product.cover_url, preview_video_url=product.preview_video_url,
        price_stars=product.price_stars,
        approx_usd=float(product.usd_price_manual) if product.usd_price_manual else None,
        is_premium=product.is_premium,
    )


async def list_products(
    db: AsyncSession,
    user,
    category_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    search: Optional[str] = None,
    sort: str = "trend_score",
    limit: int = 20,
    offset: int = 0,
    premium_only: bool = False,
) -> List[ProductListItem]:
    lang = resolve_language(user)
    stmt = (
        select(Product)
        .options(*_EAGER)
        .where(Product.status == "published")
        .order_by(desc(getattr(Product, sort, Product.trend_score)))
        .limit(limit)
        .offset(offset)
    )
    if category_id:
        stmt = stmt.where(Product.category_id == category_id)
    if premium_only:
        stmt = stmt.where(Product.is_premium.is_(True))
    if tag_id:
        stmt = stmt.join(ProductTag).where(ProductTag.tag_id == tag_id)
    if search:
        like = f"%{search}%"
        sub = select(ProductTranslation.product_id).where(
            and_(
                ProductTranslation.language_code == lang,
                or_(ProductTranslation.title.ilike(like), ProductTranslation.description.ilike(like)),
            )
        ).scalar_subquery()
        stmt = stmt.where(Product.id.in_(sub))
    result = await db.execute(stmt)
    products = result.scalars().all()
    return [_to_list_item(p, lang) for p in products]


async def get_product_by_slug(db: AsyncSession, user, slug: str) -> ProductDetail:
    lang = resolve_language(user)
    result = await db.execute(
        select(Product).options(*_EAGER).where(Product.slug == slug, Product.status == "published")
    )
    product = result.scalars().first()
    if not product:
        raise NotFoundException("Product not found")
    return _to_detail(product, lang)
