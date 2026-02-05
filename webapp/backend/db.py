import os
from contextlib import asynccontextmanager
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./webapp.db")

# For SQLite, need check_same_thread False; handled by aiosqlite.
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


# FastAPI dependency helper
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# Legacy helper (unused now, kept for compatibility)
@asynccontextmanager
async def get_session():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    from . import models  # noqa: F401 ensure models imported

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
