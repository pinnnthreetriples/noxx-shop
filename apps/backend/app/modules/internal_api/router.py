from fastapi import APIRouter, Depends
from app.modules.internal_api.deps import verify_internal_secret
from app.modules.internal_api.telegram import router as telegram_router
from app.modules.internal_api.support import router as support_router
from app.modules.internal_api.notifications import router as notifications_router
from app.modules.internal_api.bot_delivery import router as bot_delivery_router

router = APIRouter(prefix="/internal", dependencies=[Depends(verify_internal_secret)])
router.include_router(telegram_router)
router.include_router(support_router)
router.include_router(notifications_router)
router.include_router(bot_delivery_router)