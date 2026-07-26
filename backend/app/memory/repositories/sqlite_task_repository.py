"""
SQLite implementation of the Task repository.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import GoalID, IdentityID, TaskID
from app.domain.task import Task, TaskStatus
from app.memory.repositories.interfaces.task_repository import TaskRepository
from app.infrastructure.database.models import TaskModel


class SQLiteTaskRepository(TaskRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_domain(model: TaskModel) -> Task:
        task = Task(
            id=TaskID(model.id),
            owner_id=IdentityID(model.owner_id),
            goal_id=GoalID(model.goal_id),
            title=model.title,
            description=model.description,
        )
        task.status = TaskStatus(model.status)
        task.priority = model.priority
        task.created_at = model.created_at
        task.updated_at = model.updated_at
        return task

    @staticmethod
    def _to_model(task: Task) -> TaskModel:
        return TaskModel(
            id=str(task.id),
            owner_id=str(task.owner_id),
            goal_id=str(task.goal_id),
            title=task.title,
            description=task.description,
            status=task.status.value,
            priority=task.priority,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    async def save(self, task: Task) -> None:
        await self._session.merge(self._to_model(task))
        await self._session.commit()

    async def get_by_id(self, task_id: TaskID) -> Task | None:
        model = await self._session.get(TaskModel, str(task_id))
        return self._to_domain(model) if model else None

    async def list_by_goal(self, goal_id: GoalID) -> list[Task]:
        stmt = select(TaskModel).where(TaskModel.goal_id == str(goal_id)).order_by(TaskModel.priority.desc())
        return [self._to_domain(m) for m in (await self._session.execute(stmt)).scalars().all()]

    async def list_by_owner(self, owner_id: IdentityID) -> list[Task]:
        stmt = select(TaskModel).where(TaskModel.owner_id == str(owner_id)).order_by(TaskModel.created_at.desc())
        return [self._to_domain(m) for m in (await self._session.execute(stmt)).scalars().all()]

    async def list_pending(self, owner_id: IdentityID) -> list[Task]:
        stmt = select(TaskModel).where(
            TaskModel.owner_id == str(owner_id),
            TaskModel.status == "pending",
        ).order_by(TaskModel.priority.desc())
        return [self._to_domain(m) for m in (await self._session.execute(stmt)).scalars().all()]

    async def delete(self, task_id: TaskID) -> None:
        model = await self._session.get(TaskModel, str(task_id))
        if model:
            await self._session.delete(model)
            await self._session.commit()
