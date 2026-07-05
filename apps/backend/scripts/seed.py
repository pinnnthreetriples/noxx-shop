"""Seed the database with initial data.

Run from the backend directory:
    python -m scripts.seed

Seeds:
  - Categories and category translations (new, popular, premium).
  - Tags and tag translations (promo, hd).
  - Default Settings row if missing.
  - Default owner Admin from env (ADMIN_DEFAULT_TELEGRAM_ID) if configured.

The `create_default_admin(session)` helper is extracted as a separately
importable function so unit tests can verify admin-creation without
spinning up the whole seed pipeline.
"""
import asyncio
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Fixed import path: settings lives in app.core.config (was app.config — broken).
from app.core.config import settings
from app.models import Admin, Base, Category, CategoryTranslation, Setting, Tag, TagTranslation

engine = create_async_engine(settings.database_url, future=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_default_admin(session: AsyncSession) -> Optional[Admin]:
    """Create the default owner admin from env vars if not already present.

    Returns the Admin row, or None if no telegram_id is configured.
    Idempotent: re-running on an existing admin does not create a duplicate.
    """
    admin_tg_id = settings.admin_default_telegram_id
    if not admin_tg_id:
        return None
    try:
        tid = int(admin_tg_id)
    except (TypeError, ValueError):
        return None

    result = await session.execute(select(Admin).where(Admin.telegram_id == tid))
    admin = result.scalars().first()
    if admin is None:
        admin = Admin(telegram_id=tid, name="Owner", role="owner", active=True)
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
    return admin


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # Seed categories
        cats = [
            ("new", {"en": "New", "ru": "Новые", "de": "Neu", "tr": "Yeni"}),
            ("popular", {"en": "Popular", "ru": "Популярные", "de": "Beliebt", "tr": "Popüler"}),
            ("premium", {"en": "Premium", "ru": "Премиум", "de": "Premium", "tr": "Premium"}),
        ]
        for slug, trans in cats:
            result = await db.execute(select(Category).where(Category.slug == slug))
            cat = result.scalars().first()
            if not cat:
                cat = Category(slug=slug)
                db.add(cat)
                await db.flush()
                for lang, title in trans.items():
                    db.add(CategoryTranslation(category_id=cat.id, language_code=lang, title=title))

        # Seed tags
        tags = [("promo", {"en": "Promo", "ru": "Акция"}), ("hd", {"en": "HD", "ru": "HD"})]
        for slug, trans in tags:
            result = await db.execute(select(Tag).where(Tag.slug == slug))
            tag = result.scalars().first()
            if not tag:
                tag = Tag(slug=slug)
                db.add(tag)
                await db.flush()
                for lang, title in trans.items():
                    db.add(TagTranslation(tag_id=tag.id, language_code=lang, title=title))

        # Seed settings
        result = await db.execute(select(Setting))
        setting = result.scalars().first()
        if not setting:
            db.add(Setting(
                bot_name="Video Shop",
                support_enabled=True,
                content_18_plus_enabled=False,
                default_language="en",
                stars_to_usd_mode="manual",
                manual_stars_to_usd_rate=0.02,
                max_discount_percent=50,
                terms_text_en="Terms and Refund Policy. Refunds are handled manually via support. Digital content is delivered after successful payment. Google Drive links are provided for purchased videos.",
                refund_policy_text_en="Refunds are handled manually via support.",
                notifications_enabled_by_default=True,
                subscription_coming_soon_enabled=True,
                subscription_coming_soon_text="Subscription coming soon. Access to all videos.",
            ))

        # Seed owner admin from env via the extracted helper.
        await create_default_admin(db)

        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())
