from fastapi import Header, HTTPException, status
from app.core.config import settings


async def verify_internal_secret(x_internal_secret: str = Header(...)) -> None:
    if not settings.internal_api_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Internal API not configured (set INTERNAL_API_SECRET)",
        )
    if x_internal_secret != settings.internal_api_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid internal secret",
        )