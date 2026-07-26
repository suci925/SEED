"""
Experience Service.

Contains business logic related
to experience management and learning history.
"""

from __future__ import annotations


from app.core.types import (
    ExperienceID,
    IdentityID,
)

from app.domain.experience import Experience

from app.application.repositories.experience_repository import (
    ExperienceRepository,
)


class ExperienceService:
    """
    Application service for Experience.

    Responsible for coordinating
    experience operations.
    """


    def __init__(
        self,
        repository: ExperienceRepository,
    ) -> None:
        self._repository = repository


    async def create_experience(
        self,
        experience: Experience,
    ) -> Experience:
        """
        Create and persist experience.
        """

        await self._repository.save(
            experience
        )

        return experience


    async def get_experience(
        self,
        experience_id: ExperienceID,
    ) -> Experience | None:
        """
        Retrieve experience.
        """

        return await self._repository.get_by_id(
            experience_id
        )


    async def list_experiences(
        self,
        owner_id: IdentityID,
    ) -> list[Experience]:
        """
        List experiences owned by identity.
        """

        return await self._repository.list_by_owner(
            owner_id
        )


    async def search_experience(
        self,
        query: str,
    ) -> list[Experience]:
        """
        Search experiences.
        """

        return await self._repository.search(
            query
        )


    async def delete_experience(
        self,
        experience_id: ExperienceID,
    ) -> None:
        """
        Delete experience.
        """

        await self._repository.delete(
            experience_id
        )