"""
Seed Goal Domain Entity.

Goal represents a long-term objective
that Seed attempts to achieve.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from app.core.types import (
    GoalID,
    IdentityID,
)


class GoalStatus(str, Enum):
    """
    Goal lifecycle status.
    """

    ACTIVE = "active"

    COMPLETED = "completed"

    PAUSED = "paused"

    CANCELLED = "cancelled"


@dataclass
class Goal:
    """
    Represents a long-term objective.

    Goals provide direction for Seed's planning
    and task execution systems.
    """

    owner_id: IdentityID

    title: str

    description: str


    id: GoalID = field(
        default_factory=lambda: GoalID(uuid4())
    )


    status: GoalStatus = (
        GoalStatus.ACTIVE
    )


    priority: float = 0.5


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


    def update_priority(
        self,
        priority: float,
    ) -> None:
        """
        Update goal priority.

        Priority range:
        0.0 - 1.0
        """

        if not 0 <= priority <= 1:
            raise ValueError(
                "Priority must be between 0 and 1."
            )

        self.priority = priority

        self._touch()


    def complete(self) -> None:
        """
        Mark goal as completed.
        """

        self.status = (
            GoalStatus.COMPLETED
        )

        self._touch()


    def pause(self) -> None:
        """
        Pause current goal.
        """

        self.status = (
            GoalStatus.PAUSED
        )

        self._touch()


    def cancel(self) -> None:
        """
        Cancel goal.
        """

        self.status = (
            GoalStatus.CANCELLED
        )

        self._touch()


    def _touch(self) -> None:
        """
        Update modification timestamp.
        """

        self.updated_at = datetime.now(
            timezone.utc
        )