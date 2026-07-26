"""
SQLite implementation of the Memory repository.
"""

from __future__ import annotations

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import IdentityID, MemoryID

from app.domain.memory import Memory

from app.application.repositories.memory_repository import (
    MemoryRepository,
)

from app.infrastructure.database.models import MemoryModel


class SQLiteMemoryRepository(MemoryRepository):
    """
    SQLite-backed Memory repository.

    Translates between domain Memory entities
    and SQLAlchemy MemoryModel rows.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    @staticmethod
    def _to_domain(model: MemoryModel) -> Memory:
        """Convert ORM model → domain entity."""
        from app.domain.memory import MemoryType

        return Memory(
            id=MemoryID(model.id),
            owner_id=IdentityID(model.owner_id),
            content=model.content,
            memory_type=MemoryType(model.memory_type),
            importance=model.importance,
            source=model.source,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(memory: Memory) -> MemoryModel:
        """Convert domain entity → ORM model."""
        return MemoryModel(
            id=str(memory.id),
            owner_id=str(memory.owner_id),
            content=memory.content,
            memory_type=memory.memory_type.value,
            importance=memory.importance,
            source=memory.source,
            created_at=memory.created_at,
            updated_at=memory.updated_at,
        )

    # --------------------------------------------------
    # Interface
    # --------------------------------------------------

    async def save(self, memory: Memory) -> None:
        """
        Persist a memory entity.

        Uses merge to handle both insert and update
        in a single call.
        """

        model = self._to_model(memory)

        await self._session.merge(model)

        await self._session.commit()

    async def get_by_id(
        self,
        memory_id: MemoryID,
    ) -> Memory | None:
        """
        Retrieve a memory by its ID.
        """

        model = await self._session.get(
            MemoryModel,
            str(memory_id),
        )

        if model is None:
            return None

        return self._to_domain(model)

    async def delete(
        self,
        memory_id: MemoryID,
    ) -> None:
        """
        Delete a memory by its ID.
        """

        model = await self._session.get(
            MemoryModel,
            str(memory_id),
        )

        if model is not None:
            await self._session.delete(model)

            await self._session.commit()

    async def list_by_owner(
        self,
        owner_id: IdentityID,
    ) -> list[Memory]:
        """
        List all memories belonging to an identity.
        """

        stmt = (
            select(MemoryModel)
            .where(MemoryModel.owner_id == str(owner_id))
            .order_by(MemoryModel.created_at.desc())
        )

        result = await self._session.execute(stmt)

        models = result.scalars().all()

        return [
            self._to_domain(m) for m in models
        ]

    async def search(
        self,
        owner_id: IdentityID,
        query: str,
    ) -> list[Memory]:
        """
        Search memories by content text.
        """

        like_pattern = f"%{query}%"

        stmt = (
            select(MemoryModel)
            .where(
                MemoryModel.owner_id == str(owner_id),
                MemoryModel.content.ilike(like_pattern),
            )
            .order_by(MemoryModel.created_at.desc())
        )

        result = await self._session.execute(stmt)

        models = result.scalars().all()

        return [
            self._to_domain(m) for m in models
        ]
