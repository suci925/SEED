"""
Database connection management.

Provides SQLAlchemy async engine
and session factory.
"""

from __future__ import annotations


from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


from app.core.config import settings


engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
)


AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)