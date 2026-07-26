"""
SQLite implementation of the Experience repository.
"""

from __future__ import annotations

import json

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

from app.memory.repositories.interfaces.experience_repository import (
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

        # Map stored values safely
        try:
            outcome = ExperienceOutcome(model.result)
        except ValueError:
            outcome = ExperienceOutcome.SUCCESS

        try:
            exp_type = ExperienceType(
                model.experience_type
            )
        except (ValueError, AttributeError):
            exp_type = ExperienceType.INTERACTION

        # Parse JSON fields safely
        def _parse_json(val: str | None, default: Any = None) -> Any:
            if not val:
                return default
            try:
                return json.loads(val)
            except (json.JSONDecodeError, TypeError):
                return default

        return Experience(
            id=ExperienceID(model.id),
            owner_id=IdentityID(model.owner_id),
            action=model.action,
            outcome=outcome,
            experience_type=exp_type,
            lesson=model.lesson,
            created_at=model.created_at,
            updated_at=getattr(model, "updated_at", None),
            context=_parse_json(
                getattr(model, "context_json", None), {}
            ),
            actions=_parse_json(
                getattr(model, "actions_json", None), []
            ),
            failures=_parse_json(
                getattr(model, "failures_json", None), []
            ),
            solution=getattr(model, "solution", "") or "",
            confidence=getattr(model, "confidence", 0.0) or 0.0,
        )

    @staticmethod
    def _to_model(experience: Experience) -> ExperienceModel:
        """Convert domain entity → ORM model."""
        return ExperienceModel(
            id=str(experience.id),
            owner_id=str(experience.owner_id),
            action=experience.action,
            result=experience.outcome.value,
            experience_type=experience.experience_type.value,
            lesson=experience.lesson,
            created_at=experience.created_at,
            updated_at=experience.updated_at,
            context_json=json.dumps(
                experience.context, ensure_ascii=False
            ),
            actions_json=json.dumps(
                experience.actions, ensure_ascii=False
            ),
            failures_json=json.dumps(
                experience.failures, ensure_ascii=False
            ),
            solution=experience.solution or "",
            confidence=experience.confidence or 0.0,
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
