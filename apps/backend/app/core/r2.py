"""Cloudflare R2 (S3-compatible) upload helper.

When R2 is configured, admin media lands here and is served by Cloudflare's CDN
at settings.r2_public_base_url, so the app itself never streams media bytes.
boto3 is blocking, so callers run upload_fileobj() in a thread.
"""
from functools import lru_cache
from typing import BinaryIO

import boto3
from botocore.config import Config

from app.core.config import settings

# Match the media_server's headers: media is immutable (uuid-named), cache forever.
_CACHE_CONTROL = "public, max-age=31536000, immutable"


def r2_enabled() -> bool:
    return bool(
        settings.r2_bucket
        and settings.r2_endpoint_url
        and settings.r2_access_key_id
        and settings.r2_secret_access_key
    )


@lru_cache(maxsize=1)
def _get_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.r2_endpoint_url,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",  # R2 ignores region but boto3 requires one
        config=Config(signature_version="s3v4"),
    )


def upload_fileobj(fileobj: BinaryIO, key: str, content_type: str) -> str:
    """Upload a file-like object to R2 and return its public CDN URL."""
    _get_client().upload_fileobj(
        fileobj,
        settings.r2_bucket,
        key,
        ExtraArgs={"ContentType": content_type, "CacheControl": _CACHE_CONTROL},
    )
    return f"{settings.r2_public_base_url.rstrip('/')}/{key}"
