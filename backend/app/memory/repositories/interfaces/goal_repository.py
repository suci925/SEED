"""
Goal Repository Interface.

Defines abstraction for goal persistence.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.types import (
    GoalID,
    IdentityID,
)

from app.domain.goal import Goal


class GoalRepository(ABC):
    """
    Abstract repository for Goal.

    Provides persistence abstraction
    for Seed objectives.
    """


    @abstractmethod
    async def save(
        self,
        goal: Goal,
    ) -> None:
        """
        Save goal entity.
        """

        raise NotImplementedError


    @abstractmethod
    async def get_by_id(
        self,
        goal_id: GoalID,
    ) -> Goal | None:
        """
        Retrieve goal by id.
        """

        raise NotImplementedError


    @abstractmethod
    async def list_by_owner(
        self,
        owner_id: IdentityID,
    ) -> list[Goal]:
        """
        List goals belonging
        to an identity.
        """

        raise NotImplementedError


    @abstractmethod
    async def list_active(
        self,
        owner_id: IdentityID,
    ) -> list[Goal]:
        """
        List active goals.

        Used by planning systems.
        """

        raise NotImplementedError


    @abstractmethod
    async def delete(
        self,
        goal_id: GoalID,
    ) -> None:
        """
        Delete goal entity.
        """

        raise NotImplementedError