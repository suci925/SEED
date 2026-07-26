"""
Seed Memory Domain Entity.

Memory represents information that Seed chooses
to retain for future reasoning and interaction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from app.core.types import (
    IdentityID,
    MemoryID,
)


class MemoryType(str, Enum):
    """
    Types of memories stored by Seed.
    """

    FACT = "fact"

    PREFERENCE = "preference"

    EXPERIENCE = "experience"

    CONTEXT = "context"


@dataclass
class Memory:
    """
    Represents a piece of retained information.

    Memory belongs to an Identity and may influence
    future decisions and responses.
    """

    owner_id: IdentityID

    content: str

    memory_type: MemoryType

    id: MemoryID = field(
        default_factory=lambda: MemoryID(uuid4())
    )

    importance: float = 0.5

    source: str = "conversation"

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


    def update_importance(
        self,
        value: float,
    ) -> None:
        """
        Update memory importance score.

        Importance must be between 0 and 1.
        """

        if not 0 <= value <= 1:
            raise ValueError(
                "Importance must be between 0 and 1."
            )

        self.importance = value

        self._touch()


    def update_metadata(
        self,
        metadata: dict[str, Any],
    ) -> None:
        """
        Update memory metadata.
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