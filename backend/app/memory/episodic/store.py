"""
Episode Store — 事件存储层。

将 Episode 持久化到 SQLite 的 experiences 表，
以及 Obsidian 的 episodic 笔记。
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.core.types import IdentityID
from app.domain.experience import Experience, ExperienceOutcome, ExperienceType
from app.memory.repositories.interfaces.experience_repository import ExperienceRepository
from app.memory.episodic.episode import Episode


class EpisodeStore:
    """
    Stores and retrieves episodic memories.

    Each episode is stored in two places:
    1. SQLite experiences table (structured)
    2. Obsidian/Episodic/ directory (narrative markdown)
    """

    def __init__(
        self,
        experience_repo: ExperienceRepository,
        vault_path: str | Path | None = None,
    ) -> None:
        self._repo = experience_repo
        self._vault_path = Path(vault_path) if vault_path else None

    # --------------------------------------------------
    # Save
    # --------------------------------------------------

    async def save(
        self,
        episode: Episode,
        *,
        owner_id: IdentityID | None = None,
    ) -> None:
        """Save an episode to both SQLite and Obsidian."""

        # 1. Save to SQLite
        exp = Experience(
            id=IdentityID(episode.id),
            owner_id=owner_id or IdentityID("system"),
            action=episode.trigger,
            outcome=ExperienceOutcome(episode.outcome),
            experience_type=ExperienceType.TASK,
            lesson=episode.lesson or None,
            created_at=episode.timestamp,
            updated_at=episode.timestamp,
        )
        await self._repo.save(exp)

        # 2. Save to Obsidian (if vault configured)
        if self._vault_path:
            self._write_note(episode)

    def _write_note(self, episode: Episode) -> Path | None:
        """Write episode as Obsidian markdown."""

        epi_dir = self._vault_path / "Episodic"
        epi_dir.mkdir(parents=True, exist_ok=True)

        date_str = episode.timestamp.strftime("%Y-%m-%d")
        safe = "".join(
            c if c.isalnum() or c in " _-" else "_"
            for c in episode.summary[:40]
        ).strip() or "episode"

        lines = [
            "---",
            f"title: {episode.summary}",
            "type: episodic",
            f"outcome: {episode.outcome}",
            f"importance: {episode.importance}",
            f"date: {date_str}",
            f"tags: [{', '.join(episode.tags)}]",
            "---",
            "",
            f"# {episode.summary}",
            "",
        ]

        if episode.context:
            lines += ["## 上下文", "", episode.context, ""]
        if episode.actions:
            lines += ["## 行动", ""]
            lines += [f"- {a}" for a in episode.actions]
            lines += [""]
        if episode.lesson:
            lines += ["## 教训", "", f"> {episode.lesson}", ""]

        note_path = epi_dir / f"{date_str}-{safe}.md"
        note_path.write_text("\n".join(lines), encoding="utf-8")
        return note_path

    # --------------------------------------------------
    # Recall
    # --------------------------------------------------

    async def recall(
        self,
        *,
        owner_id: IdentityID | None = None,
        limit: int = 20,
    ) -> list[Episode]:
        """Recall recent episodes."""

        if owner_id is None:
            return []

        experiences = await self._repo.list_by_owner(owner_id)

        episodes: list[Episode] = []
        for exp in experiences[:limit]:
            episodes.append(
                Episode(
                    id=str(exp.id),
                    trigger=exp.action,
                    summary=exp.action[:80],
                    outcome=exp.outcome.value,
                    lesson=exp.lesson or "",
                    timestamp=exp.created_at,
                    tags=[],
                    importance=0.5,
                )
            )
        return episodes
