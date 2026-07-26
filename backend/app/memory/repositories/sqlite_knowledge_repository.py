"""
SQLite implementation of the Knowledge repository.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import KnowledgeID

from app.domain.knowledge import (
    Knowledge,
    KnowledgeType,
)

from app.memory.repositories.interfaces.knowledge_repository import (
    KnowledgeRepository,
)

from app.infrastructure.database.models import KnowledgeModel


class SQLiteKnowledgeRepository(KnowledgeRepository):
    """
    SQLite-backed Knowledge repository.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    @staticmethod
    def _to_domain(model: KnowledgeModel) -> Knowledge:
        """Convert ORM model → domain entity."""
        return Knowledge(
            id=KnowledgeID(model.id),
            title=model.title,
            content=model.content,
            knowledge_type=KnowledgeType(
                model.knowledge_type,
            ),
            source=model.source or "manual",
            created_at=model.created_at,
        )

    @staticmethod
    def _to_model(knowledge: Knowledge) -> KnowledgeModel:
        """Convert domain entity → ORM model."""
        return KnowledgeModel(
            id=str(knowledge.id),
            title=knowledge.title,
            content=knowledge.content,
            knowledge_type=knowledge.knowledge_type.value,
            source=knowledge.source,
            created_at=knowledge.created_at,
        )

    # --------------------------------------------------
    # Interface
    # --------------------------------------------------

    async def save(self, knowledge: Knowledge) -> None:
        """Persist a knowledge entity."""

        model = self._to_model(knowledge)

        await self._session.merge(model)

        await self._session.commit()

    async def get_by_id(
        self,
        knowledge_id: KnowledgeID,
    ) -> Knowledge | None:
        """Retrieve knowledge by ID."""

        model = await self._session.get(
            KnowledgeModel,
            str(knowledge_id),
        )

        if model is None:
            return None

        return self._to_domain(model)

    async def delete(
        self,
        knowledge_id: KnowledgeID,
    ) -> None:
        """Delete knowledge by ID."""

        model = await self._session.get(
            KnowledgeModel,
            str(knowledge_id),
        )

        if model is not None:
            await self._session.delete(model)

            await self._session.commit()

    async def list_all(self) -> list[Knowledge]:
        """Return all knowledge entities."""

        stmt = (
            select(KnowledgeModel)
            .order_by(KnowledgeModel.created_at.desc())
        )

        result = await self._session.execute(stmt)

        models = result.scalars().all()

        return [self._to_domain(m) for m in models]

    async def search(
        self,
        query: str,
    ) -> list[Knowledge]:
        """Search knowledge by title or content."""

        like_pattern = f"%{query}%"

        stmt = (
            select(KnowledgeModel)
            .where(
                KnowledgeModel.title.ilike(like_pattern)
                | KnowledgeModel.content.ilike(like_pattern),
            )
            .order_by(KnowledgeModel.created_at.desc())
        )

        result = await self._session.execute(stmt)

        models = result.scalars().all()

        return [self._to_domain(m) for m in models]
