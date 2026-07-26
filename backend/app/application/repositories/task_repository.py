"""
Task Repository Interface.

Defines abstraction for task persistence.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.types import (
    GoalID,
    IdentityID,
    TaskID,
)

from app.domain.task import Task


class TaskRepository(ABC):
    """
    Abstract repository for Task.

    Provides persistence abstraction
    for executable tasks.
    """


    @abstractmethod
    async def save(
        self,
        task: Task,
    ) -> None:
        """
        Save task entity.
        """

        raise NotImplementedError


    @abstractmethod
    async def get_by_id(
        self,
        task_id: TaskID,
    ) -> Task | None:
        """
        Retrieve task by id.
        """

        raise NotImplementedError


    @abstractmethod
    async def list_by_goal(
        self,
        goal_id: GoalID,
    ) -> list[Task]:
        """
        List tasks belonging
        to a goal.
        """

        raise NotImplementedError


    @abstractmethod
    async def list_by_owner(
        self,
        owner_id: IdentityID,
    ) -> list[Task]:
        """
        List tasks belonging
        to an identity.
        """

        raise NotImplementedError


    @abstractmethod
    async def list_pending(
        self,
        owner_id: IdentityID,
    ) -> list[Task]:
        """
        List pending tasks.

        Used by planning and execution systems.
        """

        raise NotImplementedError


    @abstractmethod
    async def delete(
        self,
        task_id: TaskID,
    ) -> None:
        """
        Delete task entity.
        """

        raise NotImplementedError