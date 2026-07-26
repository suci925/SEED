"""
Skill base definitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SkillMetadata:
    """Metadata loaded from a skill's SKILL.md frontmatter."""

    name: str
    description: str
    version: str = "1.0.0"
    keywords: list[str] = field(
        default_factory=list,
    )


@dataclass
class Skill:
    """
    A loaded skill ready for use.

    Contains the metadata and content of a skill
    directory that the Agent can reference.
    """

    metadata: SkillMetadata
    path: Path
    content: str = ""
    """Full SKILL.md content including body."""

    references: list[Path] = field(
        default_factory=list,
    )

    def matches(self, text: str) -> bool:
        """
        Check if this skill is relevant to a query.

        Matches against name, description keywords,
        and the skill name itself.
        """

        text_lower = text.lower()

        # Check skill name
        if self.metadata.name.lower() in text_lower:
            return True

        # Check keywords
        for kw in self.metadata.keywords:
            if kw.lower() in text_lower:
                return True

        return False
