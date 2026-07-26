"""
Task Service.

Handles task management
and execution preparation.
"""

from __future__ import annotations


from app.core.types import (
    TaskID,
    GoalID,
    IdentityID,
)

from app.domain.task import Task

from app.application.repositories.task_repository import (
    TaskRepository,
)


class TaskService:
    """
    Application service for Task.

    Responsible for task lifecycle
    management.
    """


    def __init__(
        self,
        repository: TaskRepository,
    ) -> None:
        self._repository = repository


    async def create_task(
        self,
        task: Task,
    ) -> Task:
        """
        Create and persist task.
        """

        await self._repository.save(
            task
        )

        return task


    async def get_task(
        self,
        task_id: TaskID,
    ) -> Task | None:
        """
        Retrieve task.
        """

        return await self._repository.get_by_id(
            task_id
        )


    async def list_tasks(
        self,
        goal_id: GoalID,
    ) -> list[Task]:
        """
        List tasks belonging to goal.
        """

        return await self._repository.list_by_goal(
            goal_id
        )


    async def list_pending_tasks(
        self,
        owner_id: IdentityID,
    ) -> list[Task]:
        """
        List pending tasks.

        Used by planner and executor.
        """

        return await self._repository.list_pending(
            owner_id
        )


    async def delete_task(
        self,
        task_id: TaskID,
    ) -> None:
        """
        Delete task.
        """

        await self._repository.delete(
            task_id
        )