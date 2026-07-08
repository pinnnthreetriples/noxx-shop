import os
import mimetypes
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

MEDIA_ROOT = os.environ.get("MEDIA_ROOT", "/app/media")

app = FastAPI(title="Media Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_file_path(path: str) -> str:
    full = os.path.abspath(os.path.join(MEDIA_ROOT, path))
    if not full.startswith(os.path.abspath(MEDIA_ROOT)):
        raise HTTPException(status_code=403, detail="Access denied")
    return full


@app.get("/{path:path}")
async def serve_media(path: str, request: Request):
    file_path = _get_file_path(path)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    file_size = os.path.getsize(file_path)
    content_type, _ = mimetypes.guess_type(file_path)
    content_type = content_type or "application/octet-stream"

    range_header = request.headers.get("range")
    if range_header:
        try:
            start_str, end_str = range_header.replace("bytes=", "").split("-")
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_size - 1
            if start > end or end >= file_size:
                raise ValueError("Invalid range")
        except Exception:
            raise HTTPException(status_code=416, detail="Invalid Range") from None

        with open(file_path, "rb") as f:
            f.seek(start)
            data = f.read(end - start + 1)

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(len(data)),
            "Content-Type": content_type,
            "Cache-Control": "public, max-age=31536000, immutable",
        }
        return Response(content=data, status_code=206, headers=headers)

    with open(file_path, "rb") as f:
        data = f.read()
    headers = {
        "Content-Length": str(file_size),
        "Content-Type": content_type,
        "Accept-Ranges": "bytes",
        "Cache-Control": "public, max-age=31536000, immutable",
    }
    return Response(content=data, status_code=200, headers=headers)
