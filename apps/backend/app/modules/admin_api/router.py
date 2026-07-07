"""admin_api aggregator: thin router that includes submodules."""
from fastapi import APIRouter, Depends
from app.auth import get_current_admin

from app.modules.admin_api.auth.router import router as auth_router
from app.modules.admin_api.products.router import router as products_router
from app.modules.admin_api.categories.router import router as categories_router
from app.modules.admin_api.tags.router import router as tags_router
from app.modules.admin_api.users.router import router as users_router
from app.modules.admin_api.orders.router import router as orders_router
from app.modules.admin_api.promo_codes.router import router as promo_codes_router
from app.modules.admin_api.support_tickets.router import router as support_tickets_router
from app.modules.admin_api.notifications.router import router as notifications_router
from app.modules.admin_api.admins.router import router as admins_router
from app.modules.admin_api.settings.router import router as settings_router
from app.modules.admin_api.admin_logs.router import router as admin_logs_router
from app.modules.admin_api.link_delivery_logs.router import router as link_delivery_logs_router
from app.modules.admin_api.import_.router import router as import_router
from app.modules.admin_api.analytics.router import router as analytics_router
from app.modules.admin_api.google_drive.router import router as google_drive_router
from app.modules.admin_api.uploads.router import router as uploads_router
from app.modules.admin_api.translate.router import router as translate_router


# auth_router подключается БЕЗ admin-dep (login не требует авторизации)
# все остальные — С admin-dep
admin_protected = APIRouter(prefix="/admin", dependencies=[Depends(get_current_admin)])
admin_protected.include_router(products_router)
admin_protected.include_router(categories_router)
admin_protected.include_router(tags_router)
admin_protected.include_router(users_router)
admin_protected.include_router(orders_router)
admin_protected.include_router(promo_codes_router)
admin_protected.include_router(support_tickets_router)
admin_protected.include_router(notifications_router)
admin_protected.include_router(admins_router)
admin_protected.include_router(settings_router)
admin_protected.include_router(admin_logs_router)
admin_protected.include_router(link_delivery_logs_router)
admin_protected.include_router(import_router)
admin_protected.include_router(analytics_router)
admin_protected.include_router(google_drive_router)
admin_protected.include_router(uploads_router)
admin_protected.include_router(translate_router)


# Top-level router (без prefix) — auth роутер подключается отдельно в main.py
# Для обратной совместимости — здесь тоже подключим:
admin_root = APIRouter()
admin_root.include_router(auth_router)  # /auth/login, /me
admin_root.include_router(admin_protected)


# Экспортируемый router — содержит /auth/login, /me, /products, /categories, etc.
router = admin_root