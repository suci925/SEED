"""
Knowledge Repository Interface.

Defines abstraction for knowledge persistence.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.types import KnowledgeID

from app.domain.knowledge import Knowledge


class KnowledgeRepository(ABC):
    """
    Abstract repository for Knowledge.

    Storage implementations can be replaced
    without affecting application logic.
    """


    @abstractmethod
    async def save(
        self,
        knowledge: Knowledge,
    ) -> None:
        """
        Save knowledge entity.
        """

        raise NotImplementedError


    @abstractmethod
    async def get_by_id(
        self,
        knowledge_id: KnowledgeID,
    ) -> Knowledge | None:
        """
        Retrieve knowledge by id.
        """

        raise NotImplementedError


    @abstractmethod
    async def delete(
        self,
        knowledge_id: KnowledgeID,
    ) -> None:
        """
        Delete knowledge.
        """

        raise NotImplementedError


    @abstractmethod
    async def list_all(
        self,
    ) -> list[Knowledge]:
        """
        Return all knowledge entities.
        """

        raise NotImplementedError


    @abstractmethod
    async def search(
        self,
        query: str,
    ) -> list[Knowledge]:
        """
        Search knowledge.

        Later this can be implemented
        with vector similarity search.
        """

        raise NotImplementedError