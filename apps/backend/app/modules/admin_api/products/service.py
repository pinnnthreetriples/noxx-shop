"""Product admin service - use-case logic."""
import re
from typing import Optional, Dict, Any
from sqlalchemy import inspect as sa_inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.admin.models import AdminLog
from app.modules.catalog.models import Product, ProductTag, ProductTranslation
from app.modules.notifications.models import Notification
from app.modules.notifications.service import NotificationService
from app.modules.admin_api.products.repository import ProductAdminRepository
from app.modules.admin_api.filters import LANGUAGE_CODES, AdminListFilters
from app.modules.orders.service import OrderService


def _status_str(product: Product) -> str:
    return getattr(product.status, "value", str(product.status))


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "").strip().lower()).strip("-")


def _normalize_tg_message_id(payload: dict) -> None:
    """Admins paste the channel message link ("Copy Message Link"), e.g.
    https://t.me/c/2312345678/45 — the trailing number is the message id the bot
    copies from. Accept a raw number too. Store the int (or None to clear)."""
    if "tg_message_id" not in payload:
        return
    raw = payload["tg_message_id"]
    if raw is None or raw == "" or isinstance(raw, int):
        payload["tg_message_id"] = raw or None
        return
    m = re.search(r"(\d+)\s*$", str(raw).split("?")[0].rstrip("/"))
    payload["tg_message_id"] = int(m.group(1)) if m else None


class ProductAdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ProductAdminRepository(db)
    
    async def list(self, q: Optional[str], status: Optional[str], category_id: Optional[int], sort_field: str, order: str, start: int, end: int) -> Dict[str, Any]:
        f = AdminListFilters(q=q, status=status, category_id=category_id, sort_field=sort_field, order=order, start=start, end=end)
        items, total = await self.repo.list_with_filters(f)
        return {"data": items, "total": total}
    
    async def get(self, id: int) -> Optional[Dict[str, Any]]:
        product = await self.repo.get_by_id(id)
        if not product:
            return None
        return await self._serialize(product)

    async def _serialize(self, product: Product) -> Dict[str, Any]:
        """Flatten the ORM row + translations (title_<lang>) + tag_ids for the
        react-admin edit form — otherwise translations are invisible when editing."""
        data = {c.key: getattr(product, c.key) for c in sa_inspect(product).mapper.column_attrs}
        trs = await self.db.execute(
            select(ProductTranslation).where(ProductTranslation.product_id == product.id)
        )
        for tr in trs.scalars():
            data[f"title_{tr.language_code}"] = tr.title
            data[f"description_{tr.language_code}"] = tr.description
        tag_rows = await self.db.execute(
            select(ProductTag.tag_id).where(ProductTag.product_id == product.id)
        )
        data["tag_ids"] = [r[0] for r in tag_rows]
        return data
    
    async def _apply_pricing_rules(self, payload: dict, current: Optional[Product] = None) -> None:
        """The shop charges Stars; USD is secondary. Stars are derived from the
        USD price when Stars is empty — or when the admin changed USD without
        touching Stars (bulk repricing in $ must not leave stale Stars). An
        explicitly edited Stars value always wins. A published product must
        never end up costing 0 Stars."""
        stars = payload.get("price_stars", current.price_stars if current else 0) or 0
        usd = payload.get("usd_price_manual", current.usd_price_manual if current else None)
        cur_stars = (current.price_stars if current else 0) or 0
        cur_usd = float(current.usd_price_manual) if current is not None and current.usd_price_manual else None
        usd_changed = "usd_price_manual" in payload and (float(usd) if usd else None) != cur_usd
        stars_untouched = "price_stars" not in payload or stars == cur_stars
        if usd and float(usd) > 0 and (stars <= 0 or (usd_changed and stars_untouched)):
            rate = await OrderService(self.db)._star_rate()
            stars = max(int(round(float(usd) / rate)), 1)
            payload["price_stars"] = stars
        if "status" in payload:
            status = str(payload["status"])
        elif current is not None:
            status = getattr(current.status, "value", str(current.status))
        else:
            status = "draft"
        if status == "published" and stars <= 0:
            raise ValueError("У опубликованного товара должна быть цена: заполните «Цена (Stars)» или «Цена (USD)»")

    async def _resolve_slug(self, payload: dict, current: Optional[Product]) -> str:
        """Guarantee a non-empty, unique slug (the column is UNIQUE, so a blank or
        duplicate slug raised a 500 IntegrityError). An explicit clash is reported
        back to the admin; an auto-derived one gets a numeric suffix instead."""
        explicit = bool((payload.get("slug") or "").strip())
        base = _slugify(payload.get("slug") or "")
        if not base:  # derive from any provided title (only latin survives slugify)
            for lang in LANGUAGE_CODES:
                base = _slugify(payload.get(f"title_{lang}") or "")
                if base:
                    break
        if not base:
            raise ValueError("Заполните поле «slug» латиницей — из названия его сформировать не удалось")
        exclude_id = current.id if current else None
        if not await self.repo.slug_taken(base, exclude_id):
            return base
        if explicit:
            raise ValueError(f"Товар со slug «{base}» уже существует — задайте другой")
        n = 2
        while await self.repo.slug_taken(f"{base}-{n}", exclude_id):
            n += 1
        return f"{base}-{n}"

    async def _notify_new_product(self, admin, product: Product) -> None:
        """Announce a newly published product to eligible users — once ever.
        De-duped without a migration: if a notification row already exists for
        this product_id we skip, so re-publishing or editing never re-notifies.
        The bot builds the localized user-facing text from the product title."""
        existing = await self.db.execute(
            select(Notification.id).where(Notification.product_id == product.id)
        )
        if existing.scalars().first() is not None:
            return
        await NotificationService(self.db).create_and_enqueue(
            admin, title="New product", body=None, product_id=product.id,
        )

    async def create(self, admin, payload: dict) -> Product:
        await self._apply_pricing_rules(payload)
        _normalize_tg_message_id(payload)
        payload["slug"] = await self._resolve_slug(payload, None)
        product = await self.repo.create(
            slug=payload["slug"],
            status=payload.get("status", "draft"),
            price_stars=payload.get("price_stars", 0),
            usd_price_mode=payload.get("usd_price_mode", "auto"),
            usd_price_manual=payload.get("usd_price_manual"),
            category_id=payload.get("category_id"),
            cover_url=payload.get("cover_url"),
            preview_video_url=payload.get("preview_video_url"),
            google_drive_link=payload.get("google_drive_link"),
            google_drive_file_id=payload.get("google_drive_file_id"),
            tg_message_id=payload.get("tg_message_id"),
            trend_score=payload.get("trend_score", 0),
            display_views=payload.get("display_views") or 0,
            display_purchases=payload.get("display_purchases") or 0,
            is_premium=payload.get("is_premium", False),
            available_for_subscription=payload.get("available_for_subscription", False),
        )
        for lang in LANGUAGE_CODES:
            title = payload.get(f"title_{lang}")
            if title:
                await self.repo.upsert_translation(product.id, lang, title, payload.get(f"description_{lang}"))
        for tid in dict.fromkeys(payload.get("tag_ids") or []):
            await self.repo.add_tag(product.id, tid)
        self.db.add(AdminLog(admin_id=admin.id, action="create_product", entity_type="product", entity_id=product.id))
        await self.db.commit()
        await self.db.refresh(product)
        if _status_str(product) == "published":
            await self._notify_new_product(admin, product)
        return await self._serialize(product)

    async def update(self, admin, id: int, payload: dict) -> Optional[Product]:
        product = await self.repo.get_by_id(id)
        if not product:
            return None
        old_status = _status_str(product)
        await self._apply_pricing_rules(payload, product)
        _normalize_tg_message_id(payload)
        if "slug" in payload:
            payload["slug"] = await self._resolve_slug(payload, product)
        await self.repo.update(product, {k: v for k, v in payload.items() if not k.startswith(("title_", "description_")) and hasattr(product, k) and k != "id"})
        for lang in LANGUAGE_CODES:
            title = payload.get(f"title_{lang}")
            if title:
                await self.repo.upsert_translation(id, lang, title, payload.get(f"description_{lang}"))
        if "tag_ids" in payload:
            await self.repo.clear_tags(id)
            for tid in dict.fromkeys(payload["tag_ids"]):
                await self.repo.add_tag(id, tid)
        self.db.add(AdminLog(admin_id=admin.id, action="update_product", entity_type="product", entity_id=product.id))
        await self.db.commit()
        await self.db.refresh(product)
        if old_status != "published" and _status_str(product) == "published":
            await self._notify_new_product(admin, product)
        return await self._serialize(product)
    
    async def soft_delete(self, admin, id: int) -> Optional[Product]:
        product = await self.repo.get_by_id(id)
        if not product:
            return None
        await self.repo.soft_delete(product)
        self.db.add(AdminLog(admin_id=admin.id, action="soft_delete_product", entity_type="product", entity_id=product.id))
        await self.db.commit()
        return product