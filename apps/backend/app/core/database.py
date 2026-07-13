from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

# pool_pre_ping: revalidate pooled connections so a DB restart/idle drop doesn't
# surface as InterfaceError("connection is closed") on the next request.
# pool_recycle: proactively retire connections older than 30 min, before Postgres
# / a proxy silently closes a long-idle one out from under the pool.
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    future=True,
    pool_pre_ping=True,
    pool_recycle=1800,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
