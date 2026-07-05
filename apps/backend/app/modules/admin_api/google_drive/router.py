"""Admin Google Drive router (stub - integration placeholder).

The Google Drive OAuth integration lives in services. This router exposes only
the minimal endpoints needed for the admin panel to verify the connection.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.modules.admin.models import GoogleDriveToken

router = APIRouter()


@router.get("/google-drive/status")
async def google_drive_status(db: AsyncSession = Depends(get_db)):
    """Report whether any admin has a valid Google Drive token."""
    row = (await db.execute(select(GoogleDriveToken).order_by(GoogleDriveToken.id.desc()))).scalars().first()
    if not row:
        return {"connected": False, "admin_id": None}
    return {"connected": True, "admin_id": row.admin_id, "expires_at": row.expires_at.isoformat() if row.expires_at else None}
