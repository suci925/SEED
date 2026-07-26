"""
SQLite implementation of the Goal repository.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import GoalID, IdentityID
from app.domain.goal import Goal, GoalStatus
from app.memory.repositories.interfaces.goal_repository import GoalRepository
from app.infrastructure.database.models import GoalModel


class SQLiteGoalRepository(GoalRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_domain(model: GoalModel) -> Goal:
        goal = Goal(
            id=GoalID(model.id),
            owner_id=IdentityID(model.owner_id),
            title=model.title,
            description=model.description,
        )
        goal.status = GoalStatus(model.status)
        goal.priority = model.priority
        goal.created_at = model.created_at
        goal.updated_at = model.updated_at
        return goal

    @staticmethod
    def _to_model(goal: Goal) -> GoalModel:
        return GoalModel(
            id=str(goal.id),
            owner_id=str(goal.owner_id),
            title=goal.title,
            description=goal.description,
            status=goal.status.value,
            priority=goal.priority,
            created_at=goal.created_at,
            updated_at=goal.updated_at,
        )

    async def save(self, goal: Goal) -> None:
        await self._session.merge(self._to_model(goal))
        await self._session.commit()

    async def get_by_id(self, goal_id: GoalID) -> Goal | None:
        model = await self._session.get(GoalModel, str(goal_id))
        return self._to_domain(model) if model else None

    async def list_by_owner(self, owner_id: IdentityID) -> list[Goal]:
        stmt = select(GoalModel).where(GoalModel.owner_id == str(owner_id)).order_by(GoalModel.priority.desc())
        return [self._to_domain(m) for m in (await self._session.execute(stmt)).scalars().all()]

    async def list_active(self, owner_id: IdentityID) -> list[Goal]:
        stmt = select(GoalModel).where(
            GoalModel.owner_id == str(owner_id),
            GoalModel.status == "active",
        ).order_by(GoalModel.priority.desc())
        return [self._to_domain(m) for m in (await self._session.execute(stmt)).scalars().all()]

    async def delete(self, goal_id: GoalID) -> None:
        model = await self._session.get(GoalModel, str(goal_id))
        if model:
            await self._session.delete(model)
            await self._session.commit()
