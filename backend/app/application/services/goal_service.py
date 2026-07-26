"""
Goal Service.

Handles goal management
and objective tracking.
"""

from __future__ import annotations


from app.core.types import (
    GoalID,
    IdentityID,
)

from app.domain.goal import Goal

from app.application.repositories.goal_repository import (
    GoalRepository,
)


class GoalService:
    """
    Application service for Goal.

    Responsible for managing
    user objectives.
    """


    def __init__(
        self,
        repository: GoalRepository,
    ) -> None:
        self._repository = repository


    async def create_goal(
        self,
        goal: Goal,
    ) -> Goal:
        """
        Create and persist goal.
        """

        await self._repository.save(
            goal
        )

        return goal


    async def get_goal(
        self,
        goal_id: GoalID,
    ) -> Goal | None:
        """
        Retrieve goal.
        """

        return await self._repository.get_by_id(
            goal_id
        )


    async def list_goals(
        self,
        owner_id: IdentityID,
    ) -> list[Goal]:
        """
        List goals owned by identity.
        """

        return await self._repository.list_by_owner(
            owner_id
        )


    async def list_active_goals(
        self,
        owner_id: IdentityID,
    ) -> list[Goal]:
        """
        Retrieve active goals.

        Used by planning systems.
        """

        return await self._repository.list_active(
            owner_id
        )


    async def delete_goal(
        self,
        goal_id: GoalID,
    ) -> None:
        """
        Delete goal.
        """

        await self._repository.delete(
            goal_id
        )