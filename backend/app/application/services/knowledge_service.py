"""
Knowledge Service.

Contains business logic related
to knowledge management.
"""

from __future__ import annotations


from app.core.types import KnowledgeID

from app.domain.knowledge import Knowledge

from app.application.repositories.knowledge_repository import (
    KnowledgeRepository,
)


class KnowledgeService:
    """
    Application service for Knowledge.

    Responsible for coordinating
    knowledge operations.
    """


    def __init__(
        self,
        repository: KnowledgeRepository,
    ) -> None:
        self._repository = repository


    async def create_knowledge(
        self,
        knowledge: Knowledge,
    ) -> Knowledge:
        """
        Create and persist knowledge.
        """

        await self._repository.save(
            knowledge
        )

        return knowledge


    async def get_knowledge(
        self,
        knowledge_id: KnowledgeID,
    ) -> Knowledge | None:
        """
        Retrieve knowledge.
        """

        return await self._repository.get_by_id(
            knowledge_id
        )


    async def search_knowledge(
        self,
        query: str,
    ) -> list[Knowledge]:
        """
        Search knowledge base.
        """

        return await self._repository.search(
            query
        )


    async def delete_knowledge(
        self,
        knowledge_id: KnowledgeID,
    ) -> None:
        """
        Delete knowledge.
        """

        await self._repository.delete(
            knowledge_id
        )