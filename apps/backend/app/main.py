from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sentry_sdk

from app.core.config import settings

# Errors-only; FastAPI/Starlette instrumentation auto-enables. No-op without a DSN.
if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.app_env, send_default_pii=False)
from app.core.database import engine
from app.models import Base
from app.modules.catalog.router import router as catalog_router
from app.modules.users.router import router as users_router
from app.modules.favorites.router import router as favorites_router
from app.modules.orders.router import router as orders_router
from app.modules.promos.router import router as promos_router
from app.modules.support.router import router as support_router
from app.modules.settings.router import router as settings_router
from app.modules.admin_api.router import router as admin_api_router
from app.modules.internal_api.router import router as internal_api_router
from app.modules.payments_orbchain.router import router as orbchain_router


async def _add_missing_columns(conn):
    """create_all builds new tables but never ALTERs existing ones, and this app
    has no live Alembic. Add columns shipped after the prod DB was created, so a
    new Setting field can't 500 the whole settings page. Postgres-only; sqlite
    test DBs are always fresh from create_all. Idempotent (ADD COLUMN IF NOT EXISTS)."""
    if conn.dialect.name != "postgresql":
        return
    await conn.exec_driver_sql(
        "ALTER TABLE settings ADD COLUMN IF NOT EXISTS "
        "withdrawal_commission_enabled BOOLEAN NOT NULL DEFAULT false"
    )
    await conn.exec_driver_sql(
        "ALTER TABLE settings ADD COLUMN IF NOT EXISTS "
        "withdrawal_commission_percent INTEGER NOT NULL DEFAULT 35"
    )
    for _lang in ("ru", "de", "el", "ro", "bg", "mo", "sr", "tr"):
        await conn.exec_driver_sql(
            f"ALTER TABLE settings ADD COLUMN IF NOT EXISTS terms_text_{_lang} TEXT"
        )
        await conn.exec_driver_sql(
            f"ALTER TABLE settings ADD COLUMN IF NOT EXISTS refund_policy_text_{_lang} TEXT"
        )
    # Native Telegram video delivery (falls back to google_drive_link when unset).
    await conn.exec_driver_sql(
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS tg_message_id BIGINT"
    )
    await conn.exec_driver_sql(
        "ALTER TABLE settings ADD COLUMN IF NOT EXISTS delivery_channel_id VARCHAR(64)"
    )
    # Admin 2FA + JWT revocation. Deliberately duplicated in alembic migration
    # 9f3d2c81a5e7: prod still runs with DB_AUTO_SCHEMA=1 (create_all adds new
    # tables but never new columns), so without this the deploy would 500.
    await conn.exec_driver_sql(
        "ALTER TABLE admins ADD COLUMN IF NOT EXISTS totp_enabled BOOLEAN NOT NULL DEFAULT false"
    )
    await conn.exec_driver_sql("ALTER TABLE admins ADD COLUMN IF NOT EXISTS totp_secret TEXT")
    await conn.exec_driver_sql(
        "ALTER TABLE admins ADD COLUMN IF NOT EXISTS totp_pending_secret TEXT"
    )
    await conn.exec_driver_sql("ALTER TABLE admins ADD COLUMN IF NOT EXISTS backup_codes TEXT")
    await conn.exec_driver_sql(
        "ALTER TABLE admins ADD COLUMN IF NOT EXISTS token_version INTEGER NOT NULL DEFAULT 0"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.db_auto_schema:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await _add_missing_columns(conn)
    yield
    await engine.dispose()


app = FastAPI(
    title="Telegram Video Shop API",
    version="1.0.0",
    lifespan=lifespan,
)

_cors_origins = [u for u in (settings.telegram_webapp_url, settings.admin_public_url) if u]
if settings.app_env == "development":
    # Local mini-app / admin dev servers run on these origins.
    _cors_origins += [
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:5174", "http://127.0.0.1:5174",
        "http://localhost:5175", "http://127.0.0.1:5175",
    ]

# Fail closed: never fall back to "*" (which with allow_credentials is unsafe and
# browser-rejected anyway). Empty means a misconfigured deploy should surface as a
# blocked cross-origin call, not silently allow everyone.
if not _cors_origins:
    import logging
    logging.getLogger(__name__).warning("CORS: no allowed origins configured (set telegram_webapp_url / admin_public_url)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def _security_headers(request, call_next):
    # Defense-in-depth on API responses. CSP / frame-ancestors are intentionally
    # NOT set here — they belong on the miniapp's HTML host (Cloudflare), and a
    # frame-ancestors:DENY here would break embedding in the Telegram webview.
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response


# Public routers
app.include_router(catalog_router)
app.include_router(users_router)
app.include_router(favorites_router)
app.include_router(orders_router)
app.include_router(orbchain_router)
app.include_router(promos_router)
app.include_router(support_router)
app.include_router(settings_router)

# Admin router
app.include_router(admin_api_router)

# Internal API router
app.include_router(internal_api_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
