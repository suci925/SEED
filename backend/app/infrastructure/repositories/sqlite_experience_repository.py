"""
SQLite implementation of the Experience repository.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import (
    ExperienceID,
    IdentityID,
)

from app.domain.experience import (
    Experience,
    ExperienceOutcome,
    ExperienceType,
)

from app.application.repositories.experience_repository import (
    ExperienceRepository,
)

from app.infrastructure.database.models import ExperienceModel


class SQLiteExperienceRepository(ExperienceRepository):
    """
    SQLite-backed Experience repository.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    @staticmethod
    def _to_domain(model: ExperienceModel) -> Experience:
        """Convert ORM model → domain entity."""
        return Experience(
            id=ExperienceID(model.id),
            owner_id=IdentityID(model.owner_id),
            action=model.action,
            outcome=ExperienceOutcome.SUCCESS,
            experience_type=ExperienceType.INTERACTION,
            lesson=model.lesson,
            created_at=model.created_at,
        )

    @staticmethod
    def _to_model(experience: Experience) -> ExperienceModel:
        """Convert domain entity → ORM model."""
        return ExperienceModel(
            id=str(experience.id),
            owner_id=str(experience.owner_id),
            action=experience.action,
            result=experience.outcome.value,
            lesson=experience.lesson,
            created_at=experience.created_at,
        )

    # --------------------------------------------------
    # Interface
    # --------------------------------------------------

    async def save(
        self,
        experience: Experience,
    ) -> None:
        """Persist an experience entity."""

        model = self._to_model(experience)

        await self._session.merge(model)

        await self._session.commit()

    async def get_by_id(
        self,
        experience_id: ExperienceID,
    ) -> Experience | None:
        """Retrieve experience by ID."""

        model = await self._session.get(
            ExperienceModel,
            str(experience_id),
        )

        if model is None:
            return None

        return self._to_domain(model)

    async def list_by_owner(
        self,
        owner_id: IdentityID,
    ) -> list[Experience]:
        """List experiences belonging to an identity."""

        stmt = (
            select(ExperienceModel)
            .where(
                ExperienceModel.owner_id == str(owner_id),
            )
            .order_by(ExperienceModel.created_at.desc())
        )

        result = await self._session.execute(stmt)

        models = result.scalars().all()

        return [self._to_domain(m) for m in models]

    async def list_by_type(
        self,
        experience_type: str,
    ) -> list[Experience]:
        """Retrieve experiences by type."""

        stmt = (
            select(ExperienceModel)
            .where(
                ExperienceModel.result == experience_type,
            )
            .order_by(ExperienceModel.created_at.desc())
        )

        result = await self._session.execute(stmt)

        models = result.scalars().all()

        return [self._to_domain(m) for m in models]

    async def search(
        self,
        query: str,
    ) -> list[Experience]:
        """Search experiences."""

        like_pattern = f"%{query}%"

        stmt = (
            select(ExperienceModel)
            .where(
                ExperienceModel.action.ilike(like_pattern)
                | ExperienceModel.lesson.ilike(like_pattern),
            )
            .order_by(ExperienceModel.created_at.desc())
        )

        result = await self._session.execute(stmt)

        models = result.scalars().all()

        return [self._to_domain(m) for m in models]
