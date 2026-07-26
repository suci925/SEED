"""
Obsidian ↔ Seed Synchronisation Service.

Bidirectional sync between an Obsidian vault
and Seed's internal Knowledge / Memory stores.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.core.types import IdentityID

from app.domain.knowledge import (
    Knowledge,
    KnowledgeType,
)

from app.domain.memory import Memory

from app.application.repositories.knowledge_repository import (
    KnowledgeRepository,
)

from app.application.repositories.memory_repository import (
    MemoryRepository,
)

from app.infrastructure.obsidian.vault import (
    ObsidianVault,
    ObsidianNote,
)


class SyncService:
    """
    Coordinates import and export between
    Obsidian vault and Seed storage.
    """

    def __init__(
        self,
        vault: ObsidianVault,
        knowledge_repo: KnowledgeRepository,
        memory_repo: MemoryRepository,
    ) -> None:
        self._vault = vault
        self._knowledge_repo = knowledge_repo
        self._memory_repo = memory_repo

    # --------------------------------------------------
    # Import: Obsidian → Seed Knowledge
    # --------------------------------------------------

    async def import_all_notes(
        self,
        *,
        owner_id: IdentityID | None = None,
    ) -> int:
        """
        Import all Obsidian notes into Seed's Knowledge base.

        Returns the number of notes imported.
        """

        count = 0

        for note in self._vault.notes:
            exists = await self._find_existing_knowledge(
                note.name,
            )

            if exists is not None:
                continue

            knowledge = self._note_to_knowledge(
                note,
                owner_id=owner_id,
            )

            await self._knowledge_repo.save(knowledge)

            count += 1

        return count

    async def import_note(
        self,
        note_name: str,
        *,
        owner_id: IdentityID | None = None,
    ) -> Knowledge | None:
        """
        Import a single note by name.

        Returns None if the note does not exist
        or was already imported.
        """

        note = self._vault.get_note(note_name)

        if note is None:
            return None

        exists = await self._find_existing_knowledge(
            note.name,
        )

        if exists is not None:
            return exists

        knowledge = self._note_to_knowledge(
            note,
            owner_id=owner_id,
        )

        await self._knowledge_repo.save(knowledge)

        return knowledge

    def _note_to_knowledge(
        self,
        note: ObsidianNote,
        *,
        owner_id: IdentityID | None = None,
    ) -> Knowledge:
        """Convert an Obsidian note to a Knowledge entity."""

        return Knowledge(
            title=note.name,
            content=note.content,
            knowledge_type=KnowledgeType.NOTE,
            source="obsidian",
            metadata={
                "vault_path": str(self._vault.path),
                "note_path": note.path,
                "tags": note.tags,
            },
        )

    async def _find_existing_knowledge(
        self,
        note_name: str,
    ) -> Knowledge | None:
        """Check if a note was already imported by title."""

        results = await self._knowledge_repo.search(
            note_name,
        )

        for k in results:
            if k.title == note_name and k.source == "obsidian":
                return k

        return None

    # --------------------------------------------------
    # Export: Seed Memory → Obsidian
    # --------------------------------------------------

    async def export_memory_to_note(
        self,
        memory: Memory,
        *,
        vault_subdir: str | None = None,
    ) -> Path:
        """
        Write a Seed Memory into the Obsidian vault
        as a markdown note.
        """

        # Build frontmatter
        now = datetime.now(timezone.utc).isoformat()

        frontmatter_lines = [
            "---",
            f"id: {memory.id}",
            f"source: seed-memory",
            f"memory_type: {memory.memory_type.value}",
            f"importance: {memory.importance}",
            f"created_at: {now}",
        ]

        if memory.metadata and "tags" in memory.metadata:
            tags_list = memory.metadata.get("tags", [])
            if tags_list:
                tags_yaml = ", ".join(tags_list)
                frontmatter_lines.append(
                    f"tags: [{tags_yaml}]",
                )

        frontmatter_lines.append("---")
        frontmatter_lines.append("")
        frontmatter_lines.append(memory.content)
        frontmatter_lines.append("")

        content = "\n".join(frontmatter_lines)

        # Build file path
        note_name = self._safe_filename(memory.content)

        if vault_subdir:
            rel_dir = vault_subdir.strip("/\\")
            note_path = (
                self._vault.path / rel_dir / f"{note_name}.md"
            )
        else:
            note_path = (
                self._vault.path / "seed" / f"{note_name}.md"
            )

        note_path.parent.mkdir(parents=True, exist_ok=True)

        note_path.write_text(
            content,
            encoding="utf-8",
        )

        return note_path

    @staticmethod
    def _safe_filename(text: str, max_len: int = 40) -> str:
        """
        Generate a safe filename from text content.

        Uses the first meaningful segment of text.
        """

        # Take first line or first N chars
        first_line = text.split("\n")[0].strip()

        # Remove characters invalid on Windows
        invalid_chars = '<>:"/\\|?*'

        safe = "".join(
            "_" if c in invalid_chars else c
            for c in first_line
        )

        # Truncate
        if len(safe) > max_len:
            safe = safe[:max_len].rstrip("_")

        return safe or "untitled"

    # --------------------------------------------------
    # Bulk: Export all important memories
    # --------------------------------------------------

    async def export_important_memories(
        self,
        owner_id: IdentityID,
        *,
        min_importance: float = 0.7,
    ) -> int:
        """
        Export all high-importance memories
        to the Obsidian vault.

        Returns the number of notes written.
        """

        memories = await self._memory_repo.list_by_owner(
            owner_id,
        )

        count = 0

        for memory in memories:
            if memory.importance < min_importance:
                continue

            await self.export_memory_to_note(memory)

            count += 1

        return count
