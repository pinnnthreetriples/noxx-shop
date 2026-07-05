"""Integration test fixtures for backend tests.

Provides an SQLite in-memory database, FastAPI dependency overrides for `get_db`,
and `sys.path` setup so tests can import `scripts.seed` and other top-level
backend packages.
"""
import sys
from pathlib import Path

# Ensure apps/backend (where `scripts/` lives) is on sys.path.
# pytest.ini has `pythonpath = .` but only when pytest is invoked from apps/backend.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.models_base import Base
from app.main import app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DB_URL, future=True, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


from app.core.database import get_db  # noqa: E402 - needs sys.path set up above

app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session
