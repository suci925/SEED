"""
Seed Identity Domain Entity.

The Identity entity represents the primary subject
that Seed serves and learns from.
"""

from __future__ import annotations

import sys
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

# Ensure the project root is on sys.path
# so app.core.types can be imported when
# running this file directly.
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from app.core.types import IdentityID


@dataclass
class Identity:
    """
    Represents a Seed identity.

    An identity is the central entity that owns
    memories, knowledge, experiences, and preferences.
    """

    name: str

    id: IdentityID = field(
        default_factory=lambda: IdentityID(uuid4())
    )

    preferences: dict[str, Any] = field(
        default_factory=dict
    )

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

    def update_preferences(
        self,
        preferences: dict[str, Any],
    ) -> None:
        """
        Update identity preferences.

        Args:
            preferences:
                New preference values.
        """

        self.preferences.update(
            preferences
        )

        self._touch()

    def update_metadata(
        self,
        metadata: dict[str, Any],
    ) -> None:
        """
        Update identity metadata.
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