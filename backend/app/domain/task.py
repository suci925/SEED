"""
Seed Task Domain Entity.

Task represents an actionable unit
derived from a goal.
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
    TaskID,
)


class TaskStatus(str, Enum):
    """
    Task lifecycle status.
    """

    PENDING = "pending"

    RUNNING = "running"

    COMPLETED = "completed"

    FAILED = "failed"

    CANCELLED = "cancelled"


@dataclass
class Task:
    """
    Represents an executable task.

    Tasks are concrete actions derived from goals.
    """

    owner_id: IdentityID

    goal_id: GoalID

    title: str

    description: str


    id: TaskID = field(
        default_factory=lambda: TaskID(uuid4())
    )


    status: TaskStatus = (
        TaskStatus.PENDING
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


    def start(self) -> None:
        """
        Mark task as running.
        """

        self.status = (
            TaskStatus.RUNNING
        )

        self._touch()


    def complete(self) -> None:
        """
        Mark task as completed.
        """

        self.status = (
            TaskStatus.COMPLETED
        )

        self._touch()


    def fail(self) -> None:
        """
        Mark task as failed.
        """

        self.status = (
            TaskStatus.FAILED
        )

        self._touch()


    def cancel(self) -> None:
        """
        Cancel task.
        """

        self.status = (
            TaskStatus.CANCELLED
        )

        self._touch()


    def update_priority(
        self,
        priority: float,
    ) -> None:
        """
        Update task priority.
        """

        if not 0 <= priority <= 1:
            raise ValueError(
                "Priority must be between 0 and 1."
            )

        self.priority = priority

        self._touch()


    def _touch(self) -> None:
        """
        Update modification timestamp.
        """

        self.updated_at = datetime.now(
            timezone.utc
        )