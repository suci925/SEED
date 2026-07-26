"""
Seed Conversation Domain Entity.

Conversation represents an interaction session
between an Identity and Seed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from app.core.types import (
    ConversationID,
    IdentityID,
)


class ConversationStatus(str, Enum):
    """
    Conversation lifecycle status.
    """

    ACTIVE = "active"

    COMPLETED = "completed"

    ARCHIVED = "archived"


@dataclass
class Conversation:
    """
    Represents a conversation session.

    A conversation records interactions between
    an Identity and Seed.
    """

    owner_id: IdentityID

    title: str


    id: ConversationID = field(
        default_factory=lambda: ConversationID(uuid4())
    )


    messages: list[dict[str, Any]] = field(
        default_factory=list
    )


    status: ConversationStatus = (
        ConversationStatus.ACTIVE
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


    def add_message(
        self,
        role: str,
        content: str,
    ) -> None:
        """
        Add a message into conversation.

        Args:
            role:
                user / assistant / system

            content:
                Message content.
        """

        self.messages.append(
            {
                "role": role,
                "content": content,
            }
        )

        self._touch()


    def complete(self) -> None:
        """
        Mark conversation as completed.
        """

        self.status = (
            ConversationStatus.COMPLETED
        )

        self._touch()


    def archive(self) -> None:
        """
        Archive conversation.
        """

        self.status = (
            ConversationStatus.ARCHIVED
        )

        self._touch()


    def _touch(self) -> None:
        """
        Update modification timestamp.
        """

        self.updated_at = datetime.now(
            timezone.utc
        )