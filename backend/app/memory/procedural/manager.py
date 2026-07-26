"""
Skill Manager.

Loads skills from disk, matches them to user
queries, and provides their content to the Agent.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.memory.procedural.base import (
    Skill,
    SkillMetadata,
)


# Maximum depth for dependency resolution
_MAX_CHAIN_DEPTH = 5


class SkillManager:
    """
    Manages skill loading, matching, and retrieval.

    Skills are stored as directories under a root
    path (default: backend/skills/). Each skill
    has a SKILL.md file with YAML frontmatter.
    """

    def __init__(
        self,
        skills_path: str | Path | None = None,
    ) -> None:
        self._skills_path = Path(
            skills_path or self._default_path(),
        )
        self._skills: list[Skill] = []
        self._loaded = False

    # --------------------------------------------------
    # Loading
    # --------------------------------------------------

    def load_all(self) -> list[Skill]:
        """Scan the skills directory and load all skills."""

        self._skills = []
        skills_dir = self._skills_path

        if not skills_dir.is_dir():
            return self._skills

        for item in sorted(skills_dir.iterdir()):
            if not item.is_dir():
                continue

            skill_file = item / "SKILL.md"

            if not skill_file.exists():
                continue

            skill = self._load_single(skill_file)

            if skill is not None:
                self._skills.append(skill)

        self._loaded = True

        return self._skills

    def _load_single(
        self,
        skill_file: Path,
    ) -> Skill | None:
        """Load a single skill from its SKILL.md file."""

        try:
            content = skill_file.read_text(
                encoding="utf-8",
            )
        except Exception:
            return None

        # Parse YAML frontmatter
        metadata = self._parse_frontmatter(content)

        if metadata is None:
            return None

        # Strip frontmatter from content
        body = self._strip_frontmatter(content)

        # Find reference files
        ref_dir = skill_file.parent / "references"
        references: list[Path] = []

        if ref_dir.is_dir():
            references = sorted(ref_dir.iterdir())[:10]

        return Skill(
            metadata=metadata,
            path=skill_file.parent,
            content=body,
            references=references,
        )

    # --------------------------------------------------
    # Matching
    # --------------------------------------------------

    def find_matching(
        self,
        query: str,
    ) -> list[Skill]:
        """
        Find skills relevant to a user query.
        """

        if not self._loaded:
            self.load_all()

        return [
            s for s in self._skills if s.matches(query)
        ]

    def get_by_name(
        self,
        name: str,
    ) -> Skill | None:
        """Get a skill by its name."""

        for s in self.skills:
            if s.metadata.name == name:
                return s

        return None

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def skills(self) -> list[Skill]:
        """All loaded skills."""

        if not self._loaded:
            self.load_all()

        return self._skills

    @property
    def skills_path(self) -> Path:
        """Path to the skills directory."""
        return self._skills_path

    # --------------------------------------------------
    # Frontmatter parsing
    # --------------------------------------------------

    @staticmethod
    def _parse_frontmatter(
        content: str,
    ) -> SkillMetadata | None:
        """
        Parse YAML frontmatter from SKILL.md content.
        Expects content between --- markers.
        """

        if not content.startswith("---"):
            return None

        # Find closing ---
        end = content.find("---", 3)

        if end < 0:
            return None

        yaml_text = content[3:end].strip()

        try:
            data = yaml.safe_load(yaml_text)
        except Exception:
            return None

        if not isinstance(data, dict):
            return None

        return SkillMetadata(
            name=data.get("name", "unknown"),
            description=data.get("description", ""),
            version=str(
                data.get("version", "1.0.0")
            ),
            keywords=data.get("keywords", []),
        )

    @staticmethod
    def _strip_frontmatter(content: str) -> str:
        """Remove YAML frontmatter, return the body only."""

        if not content.startswith("---"):
            return content

        end = content.find("---", 3)

        if end < 0:
            return content

        return content[end + 3 :].strip()

    @staticmethod
    def _default_path() -> Path:
        """Default skills directory path."""

        import os

        project_root = Path(__file__).resolve().parents[4]
        backend_skills = project_root / "backend" / "skills"
        if backend_skills.is_dir():
            return backend_skills
        candidate = project_root / "skills"
        if candidate.is_dir():
            return candidate
        return backend_skills

    # --------------------------------------------------
    # Skill Composition
    # --------------------------------------------------

    def resolve_chain(self, skill_name: str, *, _depth: int = 0) -> list[Skill]:
        """Resolve a skill and all its dependencies in order."""
        if _depth > _MAX_CHAIN_DEPTH:
            return []
        skill = self.get_by_name(skill_name)
        if skill is None:
            return []
        result: list[Skill] = []
        seen: set[str] = set()
        for dep_name in skill.metadata.depends_on:
            if dep_name in seen:
                continue
            seen.add(dep_name)
            for s in self.resolve_chain(dep_name, _depth=_depth + 1):
                if s.metadata.name not in seen:
                    result.append(s)
                    seen.add(s.metadata.name)
        if skill.metadata.name not in seen:
            result.append(skill)
        return result

    def compose(self, skill_names: list[str]) -> str:
        """Combine multiple skills into a single context block."""
        seen: set[str] = set()
        sections: list[str] = []
        for name in skill_names:
            for skill in self.resolve_chain(name):
                if skill.metadata.name in seen:
                    continue
                seen.add(skill.metadata.name)
                sections.append(f"### {skill.metadata.name}\n{skill.content[:500]}")
        if not sections:
            return ""
        return "## 组合技能\n\n" + "\n\n---\n\n".join(sections)
