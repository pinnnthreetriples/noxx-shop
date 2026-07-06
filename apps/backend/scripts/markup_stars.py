"""One-shot: mark up every product's Stars price to bake in Telegram's
withdrawal commission, so the buyer covers it and the owner nets the target.

Default factor 1.54 = 0.02 / 0.013 (buyer in-app rate / creator withdrawal rate):
a product that showed "$10" (500 Stars) becomes 770 Stars, the buyer pays those
Stars, and after commission the owner receives ~$10.

Not idempotent — running twice marks up twice. Run once:
    python -m scripts.markup_stars           # factor 1.54
    python -m scripts.markup_stars 1.6       # custom factor
"""
import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.modules.catalog.models import Product

engine = create_async_engine(settings.database_url, future=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def bumped(stars: int, factor: float) -> int:
    """New Stars price after markup; 0 stays 0, a positive price never drops below 1."""
    return max(int(round(stars * factor)), 1) if stars > 0 else stars


async def main(factor: float) -> None:
    async with async_session() as db:
        products = (await db.execute(select(Product))).scalars().all()
        for p in products:
            old = p.price_stars
            p.price_stars = bumped(old, factor)
            # keep a manual USD price in step so the storefront $ stays consistent
            if p.usd_price_manual:
                p.usd_price_manual = round(float(p.usd_price_manual) * factor, 2)
            print(f"#{p.id} {p.slug}: {old} -> {p.price_stars} Stars")
        await db.commit()
        print(f"done: {len(products)} products x{factor}")


if __name__ == "__main__":
    arg_factor = float(sys.argv[1]) if len(sys.argv) > 1 else 1.54
    asyncio.run(main(arg_factor))
