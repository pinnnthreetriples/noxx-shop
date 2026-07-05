"""Internal setup endpoint: receive the OrbChain webhook secret and store it in
the DB settings row. Called once from the merchant dashboard browser so the
secret never transits any third party's logs or the operator's clipboard."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.admin.models import Setting

router = APIRouter(prefix="/orbchain", tags=["internal-orbchain"])


class WebhookSecretIn(BaseModel):
    secret: str


@router.post("/webhook-secret")
async def set_webhook_secret(body: WebhookSecretIn, db: AsyncSession = Depends(get_db)):
    row = await db.execute(select(Setting).limit(1))
    setting = row.scalar_one_or_none()
    if not setting:
        setting = Setting()
        db.add(setting)
    setting.orbchain_webhook_secret = body.secret.strip()
    await db.commit()
    return {"ok": True, "configured": bool(setting.orbchain_webhook_secret)}
