"""
Database session utilities.
"""

from __future__ import annotations


from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import (
    AsyncSessionFactory,
)


async def get_session() -> AsyncGenerator[
    AsyncSession,
    None
]:
    """
    Provide database session.
    """

    async with AsyncSessionFactory() as session:
        yield session