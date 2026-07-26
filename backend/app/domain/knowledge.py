"""
Seed Knowledge Domain Entity.

Knowledge represents information resources
that Seed can understand, retrieve and use.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from app.core.types import KnowledgeID


class KnowledgeType(str, Enum):
    """
    Types of knowledge resources.
    """

    DOCUMENT = "document"

    NOTE = "note"

    ARTICLE = "article"

    CODE = "code"

    OTHER = "other"


@dataclass
class Knowledge:
    """
    Represents a knowledge resource.

    Knowledge is external or internal information
    that Seed can retrieve and reason with.
    """

    title: str

    content: str

    knowledge_type: KnowledgeType

    id: KnowledgeID = field(
        default_factory=lambda: KnowledgeID(uuid4())
    )

    source: str = "manual"

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


    def update_content(
        self,
        content: str,
    ) -> None:
        """
        Update knowledge content.
        """

        self.content = content

        self._touch()


    def update_metadata(
        self,
        metadata: dict[str, Any],
    ) -> None:
        """
        Update knowledge metadata.
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