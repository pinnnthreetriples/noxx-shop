"""One-off: move existing product media from the local volume into Cloudflare R2.

Finds Product.cover_url / preview_video_url values that are still relative paths
(served by the old media-server), uploads each file from MEDIA_ROOT to R2, and
rewrites the DB value to the public CDN URL. Absolute URLs and missing files are
skipped, so it is safe to re-run.

Run inside the backend container (needs the media_data volume + R2 env):
    docker compose exec backend python -m scripts.migrate_media_to_r2
"""
import asyncio
import mimetypes
import os

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core import r2
from app.core.config import settings
from app.modules.catalog.models import Product

MEDIA_ROOT = os.environ.get("MEDIA_ROOT", "/app/media")

engine = create_async_engine(settings.database_url, future=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def _migrate_value(value: str | None) -> str | None:
    """Upload the file behind a relative media path to R2; return its CDN URL.

    Returns None when there is nothing to do (empty, already absolute, or the
    file is not on disk) so the caller leaves the DB value untouched.
    """
    if not value or value.startswith(("http://", "https://")):
        return None
    key = value.lstrip("/")
    src = os.path.join(MEDIA_ROOT, key)
    if not os.path.isfile(src):
        print(f"  ! skip (file not found): {key}")
        return None
    content_type = mimetypes.guess_type(key)[0] or "application/octet-stream"
    with open(src, "rb") as f:
        url = r2.upload_fileobj(f, key, content_type)
    print(f"  -> {key}  =>  {url}")
    return url


async def main() -> None:
    if not r2.r2_enabled():
        raise SystemExit("R2 is not configured (set R2_* env vars). Aborting.")
    migrated = 0
    async with async_session() as session:
        result = await session.execute(
            select(Product).where(
                or_(Product.cover_url.isnot(None), Product.preview_video_url.isnot(None))
            )
        )
        for product in result.scalars().all():
            print(f"product #{product.id} ({product.slug})")
            new_cover = _migrate_value(product.cover_url)
            if new_cover:
                product.cover_url = new_cover
                migrated += 1
            new_preview = _migrate_value(product.preview_video_url)
            if new_preview:
                product.preview_video_url = new_preview
                migrated += 1
        await session.commit()
    print(f"Done. Migrated {migrated} file(s) to R2.")


if __name__ == "__main__":
    asyncio.run(main())
