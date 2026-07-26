"""
Memory Service.

Contains business logic related
to user memory management.
"""

from __future__ import annotations


from app.core.types import (
    MemoryID,
)

from app.domain.memory import Memory

from app.application.repositories.memory_repository import (
    MemoryRepository,
)


class MemoryService:
    """
    Application service for Memory.

    Coordinates domain logic and persistence.
    """


    def __init__(
        self,
        repository: MemoryRepository,
    ) -> None:
        self._repository = repository


    async def create_memory(
        self,
        memory: Memory,
    ) -> Memory:
        """
        Create and persist a memory.
        """

        await self._repository.save(
            memory
        )

        return memory


    async def get_memory(
        self,
        memory_id: MemoryID,
    ) -> Memory | None:
        """
        Retrieve memory.
        """

        return await self._repository.get_by_id(
            memory_id
        )


    async def delete_memory(
        self,
        memory_id: MemoryID,
    ) -> None:
        """
        Delete memory.
        """

        await self._repository.delete(
            memory_id
        )


    async def search_memory(
        self,
        owner_id,
        query: str,
    ) -> list[Memory]:
        """
        Search memories.
        """

        return await self._repository.search(
            owner_id,
            query,
        )