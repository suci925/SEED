"""
Memory Repository Interface.

Defines abstraction for memory persistence.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.types import (
    IdentityID,
    MemoryID,
)

from app.domain.memory import Memory


class MemoryRepository(ABC):
    """
    Abstract repository for Memory.

    This interface hides storage implementation
    from application services.
    """


    @abstractmethod
    async def save(
        self,
        memory: Memory,
    ) -> None:
        """
        Save a memory entity.
        """

        raise NotImplementedError


    @abstractmethod
    async def get_by_id(
        self,
        memory_id: MemoryID,
    ) -> Memory | None:
        """
        Retrieve memory by id.
        """

        raise NotImplementedError


    @abstractmethod
    async def delete(
        self,
        memory_id: MemoryID,
    ) -> None:
        """
        Delete memory.
        """

        raise NotImplementedError


    @abstractmethod
    async def list_by_owner(
        self,
        owner_id: IdentityID,
    ) -> list[Memory]:
        """
        List memories owned by identity.
        """

        raise NotImplementedError


    @abstractmethod
    async def search(
        self,
        owner_id: IdentityID,
        query: str,
    ) -> list[Memory]:
        """
        Search memories.
        """

        raise NotImplementedError