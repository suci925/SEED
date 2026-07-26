"""
Seed Experience Domain Entity.

Experience represents events, outcomes and lessons
that Seed can learn from over time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from app.core.types import (
    ExperienceID,
    IdentityID,
)


class ExperienceType(str, Enum):
    """
    Categories of experiences.
    """

    TASK = "task"

    INTERACTION = "interaction"

    ERROR = "error"

    IMPROVEMENT = "improvement"


class ExperienceOutcome(str, Enum):
    """
    Result of an experience.
    """

    SUCCESS = "success"

    FAILURE = "failure"

    PARTIAL = "partial"


@dataclass
class Experience:
    """
    Represents an experience accumulated by Seed.

    Experiences provide learning material
    for future reflection and improvement.
    """

    owner_id: IdentityID

    action: str

    outcome: ExperienceOutcome

    experience_type: ExperienceType


    id: ExperienceID = field(
        default_factory=lambda: ExperienceID(uuid4())
    )


    lesson: str | None = None


    metadata: dict[str, Any] = field(
        default_factory=dict
    )


    created_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )


    updated_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )


    def add_lesson(
        self,
        lesson: str,
    ) -> None:
        """
        Add a learned lesson from this experience.
        """

        self.lesson = lesson

        self._touch()


    def update_metadata(
        self,
        metadata: dict[str, Any],
    ) -> None:
        """
        Update experience metadata.
        """

        self.metadata.update(
            metadata
        )

        self._touch()


    def _touch(self) -> None:
        """
        Update modification timestamp.
        """

        self.updated_at = datetime.now(
            timezone.utc
        )