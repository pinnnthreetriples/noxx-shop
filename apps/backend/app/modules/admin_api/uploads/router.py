"""Admin media upload: covers (images) and short preview videos.

When R2 is configured, files go to Cloudflare R2 and the DB stores the public
CDN URL (served from r2_public_base_url). Otherwise they land in MEDIA_ROOT (the
shared media_data volume) served by the media-server container — the dev/test
fallback. Either way the DB stores a value the miniapp can use directly.
"""
import asyncio
import mimetypes
import os
import uuid

from fastapi import APIRouter, HTTPException, UploadFile

from app.core import r2
from app.core.config import settings

router = APIRouter(tags=["admin-uploads"])

MEDIA_ROOT = os.environ.get("MEDIA_ROOT", "/app/media")
ALLOWED_EXT = {
    ".jpg", ".jpeg", ".png", ".webp", ".gif",  # covers
    ".mp4", ".webm", ".mov",  # preview videos
}
MAX_BYTES = 200 * 1024 * 1024  # ponytail: flat 200MB limit, tune per-type if ever needed


@router.post("/upload")
async def upload_media(file: UploadFile):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail=f"File type {ext or '?'} not allowed")
    if file.size and file.size > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 200MB)")

    key = f"uploads/{uuid.uuid4().hex}{ext}"
    content_type = mimetypes.guess_type(key)[0] or "application/octet-stream"

    if r2.r2_enabled():
        await file.seek(0)
        url = await asyncio.to_thread(r2.upload_fileobj, file.file, key, content_type)
        return {"path": key, "url": url}

    # Local-disk fallback (dev/tests). Enforce the size cap while streaming.
    dest = os.path.join(MEDIA_ROOT, key)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    written = 0
    with open(dest, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            written += len(chunk)
            if written > MAX_BYTES:
                out.close()
                os.remove(dest)
                raise HTTPException(status_code=413, detail="File too large (max 200MB)")
            out.write(chunk)
    base = settings.media_public_url.rstrip("/")
    return {"path": key, "url": f"{base}/{key}" if base else f"/{key}"}
