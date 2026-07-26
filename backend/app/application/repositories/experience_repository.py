"""
Experience Repository Interface.

Defines abstraction for experience persistence.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.types import (
    ExperienceID,
    IdentityID,
)

from app.domain.experience import Experience


class ExperienceRepository(ABC):
    """
    Abstract repository for Experience.

    Provides persistence abstraction
    for Seed learning experiences.
    """


    @abstractmethod
    async def save(
        self,
        experience: Experience,
    ) -> None:
        """
        Save experience entity.
        """

        raise NotImplementedError


    @abstractmethod
    async def get_by_id(
        self,
        experience_id: ExperienceID,
    ) -> Experience | None:
        """
        Retrieve experience by id.
        """

        raise NotImplementedError


    @abstractmethod
    async def list_by_owner(
        self,
        owner_id: IdentityID,
    ) -> list[Experience]:
        """
        List experiences belonging
        to an identity.
        """

        raise NotImplementedError


    @abstractmethod
    async def list_by_type(
        self,
        experience_type: str,
    ) -> list[Experience]:
        """
        Retrieve experiences by type.
        """

        raise NotImplementedError


    @abstractmethod
    async def search(
        self,
        query: str,
    ) -> list[Experience]:
        """
        Search experiences.
        """

        raise NotImplementedError