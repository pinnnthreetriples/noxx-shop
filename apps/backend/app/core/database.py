from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

# pool_pre_ping: revalidate pooled connections so a DB restart/idle drop doesn't
# surface as InterfaceError("connection is closed") on the next request.
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    future=True,
    pool_pre_ping=True,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
