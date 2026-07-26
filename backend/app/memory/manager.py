"""
Memory Manager.

Coordinates the decision to save information,
writes to both Obsidian (markdown notes) and
SQLite (structured Memory entities).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.core.types import IdentityID

from app.domain.memory import (
    Memory,
    MemoryType,
)

from app.memory.repositories.interfaces.memory_repository import (
    MemoryRepository,
)

from app.memory.classifier import (
    Classifier,
    ClassificationResult,
    MemoryCategory,
)

from app.perception.context.vault import (
    ObsidianVault,
)

from app.cognition.world_model.graph import (
    KnowledgeGraph,
)

from app.cognition.world_model.relationship import (
    RelationType,
)


class MemoryManager:
    """
    Decides what to remember and where to store it.

    Flow:
      1. Classifier decides if content is worth saving
      2. If yes → write structured note to Obsidian
      3. Always → save condensed entry to SQLite Memory table
    """

    # Category → Obsidian subdirectory mapping
    _CATEGORY_DIRS = {
        MemoryCategory.PREFERENCE: "Preferences",
        MemoryCategory.KNOWLEDGE: "Knowledge",
        MemoryCategory.EXPERIENCE: "Experience",
        MemoryCategory.TASK_RESULT: "Tasks",
    }

    # Category → MemoryType mapping
    _CATEGORY_MEMORY_TYPES = {
        MemoryCategory.PREFERENCE: MemoryType.PREFERENCE,
        MemoryCategory.KNOWLEDGE: MemoryType.FACT,
        MemoryCategory.EXPERIENCE: MemoryType.EXPERIENCE,
        MemoryCategory.TASK_RESULT: MemoryType.CONTEXT,
    }

    def __init__(
        self,
        vault: ObsidianVault | None,
        memory_repo: MemoryRepository,
    ) -> None:
        self._vault = vault
        self._memory_repo = memory_repo
        self._classifier = Classifier()

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    async def process_exchange(
        self,
        user_message: str,
        assistant_reply: str,
        *,
        owner_id: IdentityID,
    ) -> MemoryManagerResult:
        """
        Process a user ↔ assistant exchange.

        Decides whether to remember it, then persists
        accordingly.

        Returns a result describing what was saved.
        """

        # 1. Classify
        classification = self._classifier.classify(
            user_message,
            assistant_reply,
        )

        # 2. If not worth saving, still log to SQLite
        #    but don't write to Obsidian
        memory = self._build_memory(
            user_message=user_message,
            assistant_reply=assistant_reply,
            classification=classification,
            owner_id=owner_id,
        )

        await self._memory_repo.save(memory)

        # 3. If worth saving, write to Obsidian
        obsidian_path: Path | None = None

        if self._should_save_to_obsidian(classification):

            if self._vault is not None:

                obsidian_path = (
                    self._write_obsidian_note(
                        user_message=user_message,
                        assistant_reply=assistant_reply,
                        classification=classification,
                    )
                )

        return MemoryManagerResult(
            category=classification.category,
            saved_to_obsidian=obsidian_path is not None,
            obsidian_path=obsidian_path,
            memory_id=memory.id,
            importance=classification.importance,
            reason=classification.reason,
        )

    # --------------------------------------------------
    # Memory building
    # --------------------------------------------------

    def _build_memory(
        self,
        *,
        user_message: str,
        assistant_reply: str,
        classification: ClassificationResult,
        owner_id: IdentityID,
    ) -> Memory:
        """Build a Memory entity from the exchange."""

        memory_type = self._CATEGORY_MEMORY_TYPES.get(
            classification.category,
            MemoryType.CONTEXT,
        )

        # Build meaningful content
        if classification.category == MemoryCategory.PREFERENCE:
            content = user_message
        else:
            content = (
                f"Q: {user_message}\n"
                f"A: {assistant_reply}"
            )

        return Memory(
            owner_id=owner_id,
            content=content,
            memory_type=memory_type,
            importance=classification.importance,
            source="agent",
            metadata={
                "category": classification.category.value,
                "reason": classification.reason,
                "tags": classification.suggested_tags,
            },
        )

    # --------------------------------------------------
    # Obsidian note writing
    # --------------------------------------------------

    def _should_save_to_obsidian(
        self,
        classification: ClassificationResult,
    ) -> bool:
        """Only save high-importance items to Obsidian."""

        return (
            classification.category != MemoryCategory.SKIP
            and classification.importance >= 0.6
        )

    def _write_obsidian_note(
        self,
        *,
        user_message: str,
        assistant_reply: str,
        classification: ClassificationResult,
    ) -> Path:
        """Write a markdown note to the Obsidian vault."""

        subdir = self._CATEGORY_DIRS.get(
            classification.category,
            "Knowledge",
        )

        # Build frontmatter
        now = datetime.now(timezone.utc).isoformat()

        tags_yaml = ", ".join(
            classification.suggested_tags
        ) if classification.suggested_tags else "seed"

        frontmatter = (
            "---\n"
            f"title: {classification.suggested_title or 'Untitled'}\n"
            f"source: seed-agent\n"
            f"category: {classification.category.value}\n"
            f"importance: {classification.importance}\n"
            f"created: {now}\n"
            f"tags: [{tags_yaml}]\n"
            "---\n\n"
        )

        # Build body
        if classification.category == MemoryCategory.PREFERENCE:
            body = (
                f"## 偏好记录\n\n"
                f"{user_message}\n\n"
            )
        else:
            body = (
                f"## 对话记录\n\n"
                f"**用户**: {user_message}\n\n"
                f"**回答**: {assistant_reply}\n\n"
            )

        # Ensure directory exists
        note_dir = self._vault.path / subdir
        note_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        safe_name = self._safe_filename(
            classification.suggested_title
            or user_message,
        )
        note_path = note_dir / f"{safe_name}.md"

        note_path.write_text(
            frontmatter + body,
            encoding="utf-8",
        )

        # Add to knowledge graph
        self._add_to_graph(
            note_path=note_path,
            classification=classification,
            content=frontmatter + body,
        )

        return note_path

    # --------------------------------------------------
    # Knowledge Graph Integration
    # --------------------------------------------------

    def _add_to_graph(
        self,
        *,
        note_path: Path,
        classification: ClassificationResult,
        content: str,
    ) -> None:
        """
        Add a note to the knowledge graph with
        embedding and relationships.
        """

        graph = self._vault.graph

        # Use relative path from vault root
        rel_path = str(
            note_path.relative_to(self._vault.path)
        )

        node_id = f"{classification.category.value}:{note_path.stem}"

        # Add node with embedding
        graph.add_node(
            node_id=node_id,
            path=rel_path,
            content=content,
            node_type=classification.category.value,
        )

        # Create edges with all existing nodes
        for existing_id, existing_node in list(
            graph._nodes.items()
        ):
            if existing_id == node_id:
                continue

            graph.add_edge(
                source=node_id,
                target=existing_id,
                rel_type=RelationType.RELATED,
            )

        # Update weights for the new node
        graph.update_weights(node_id)

        graph.save()

    @staticmethod
    def _safe_filename(text: str, max_len: int = 40) -> str:
        """Generate a safe filename from text."""

        # Take first meaningful segment
        first_line = text.split("\n")[0].strip()

        # Remove invalid Windows characters
        invalid_chars = '<>:"/\\|?*'

        safe = "".join(
            "_" if c in invalid_chars else c
            for c in first_line
        )

        if len(safe) > max_len:
            safe = safe[:max_len].rstrip("_")

        return safe or "untitled"


from dataclasses import dataclass
from pathlib import Path

from app.memory.classifier import (
    MemoryCategory,
)


@dataclass
class MemoryManagerResult:
    """Result of processing an exchange through Memory Manager."""

    category: MemoryCategory = MemoryCategory.SKIP
    saved_to_obsidian: bool = False
    obsidian_path: Path | None = None
    memory_id: object = None
    importance: float = 0.0
    reason: str = ""
