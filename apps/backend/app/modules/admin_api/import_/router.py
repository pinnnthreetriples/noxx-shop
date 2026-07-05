"""Admin import_ router (stub - bulk import placeholder).

This module's name ends with an underscore because `import` is a Python keyword.
The router is a placeholder; real bulk import endpoints will be added later.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/import/status")
async def import_status():
    """Return import job status (placeholder)."""
    return {"running": False, "last_run": None, "items_processed": 0}
