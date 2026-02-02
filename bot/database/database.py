"""Database connection and session management."""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from bot.core.config import settings

# Create async engine
engine: AsyncEngine = create_async_engine(
    settings.db.database_url,
    echo=settings.bot.DEBUG,
    pool_size=10,
    max_overflow=20,
)

# Create session factory
sessionmaker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with sessionmaker() as session:
        yield session
