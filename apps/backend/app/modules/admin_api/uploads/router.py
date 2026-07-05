"""Admin media upload: covers (images) and short preview videos.

Files land in MEDIA_ROOT (the shared media_data volume) and are served by the
media-server container. The DB stores the relative path; the miniapp prefixes
it with its media base URL.
"""
import os
import uuid

from fastapi import APIRouter, HTTPException, UploadFile

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
    name = f"uploads/{uuid.uuid4().hex}{ext}"
    dest = os.path.join(MEDIA_ROOT, name)
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
    return {"path": name, "url": f"{base}/{name}" if base else f"/{name}"}
