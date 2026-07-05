from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
