"""
Memory Coordinator — 三层记忆协调器。

统一管理：
  - Episodic Memory（事件记忆）
  - Semantic Memory（知识记忆）
  - Procedural Memory（技能记忆）
"""

from __future__ import annotations

from app.core.types import IdentityID
from app.domain.memory import Memory, MemoryType

from app.memory.classifier import Classifier, ClassificationResult, MemoryCategory
from app.memory.repositories.interfaces.memory_repository import MemoryRepository

from app.perception.context.vault import ObsidianVault


class MemoryCoordinator:
    """
    Coordinates all three memory layers.

    For each input:
      1. Classifier decides which layer(s) to store in
      2. Routes to the appropriate storage
      3. Returns the result
    """

    def __init__(
        self,
        vault: ObsidianVault,
        memory_repo: MemoryRepository,
    ) -> None:
        self._vault = vault
        self._memory_repo = memory_repo
        self._classifier = Classifier()

    async def process_exchange(
        self,
        user_message: str,
        assistant_reply: str,
        *,
        owner_id: IdentityID,
    ) -> MemoryResult:
        """
        Process and store a conversation exchange.

        Routes to appropriate memory layer(s) based on content.
        """
        classification = self._classifier.classify(user_message, assistant_reply)

        # Always save to SQLite Memory table
        memory = self._build_memory(user_message, assistant_reply, classification, owner_id)
        await self._memory_repo.save(memory)

        # Route to appropriate layer
        episodic_saved = False
        if classification.category in (MemoryCategory.EXPERIENCE, MemoryCategory.TASK_RESULT):
            episodic_saved = True

        semantic_saved = False
        if classification.category == MemoryCategory.KNOWLEDGE:
            semantic_saved = True

        procedural_saved = False
        if classification.category == MemoryCategory.PREFERENCE:
            procedural_saved = True

        # Write to Obsidian if important enough
        obsidian_path = None
        if classification.category != MemoryCategory.SKIP and classification.importance >= 0.6:
            obsidian_path = self._write_obsidian_note(
                user_message, assistant_reply, classification
            )

        return MemoryResult(
            category=classification.category.value,
            importance=classification.importance,
            episodic_saved=episodic_saved,
            semantic_saved=semantic_saved,
            procedural_saved=procedural_saved,
            obsidian_path=str(obsidian_path) if obsidian_path else None,
        )

    def _build_memory(self, user_msg: str, assist_reply: str, cls: ClassificationResult, owner_id: IdentityID) -> Memory:
        content = user_msg if cls.category == MemoryCategory.PREFERENCE else f"Q: {user_msg}\nA: {assist_reply}"
        return Memory(
            owner_id=owner_id,
            content=content,
            memory_type=self._map_type(cls.category),
            importance=cls.importance,
            source="agent",
            metadata={"category": cls.category.value, "reason": cls.reason},
        )

    @staticmethod
    def _map_type(cat: MemoryCategory) -> MemoryType:
        return {
            MemoryCategory.PREFERENCE: MemoryType.PREFERENCE,
            MemoryCategory.KNOWLEDGE: MemoryType.FACT,
            MemoryCategory.EXPERIENCE: MemoryType.EXPERIENCE,
            MemoryCategory.TASK_RESULT: MemoryType.CONTEXT,
        }.get(cat, MemoryType.CONTEXT)

    def _write_obsidian_note(self, user_msg: str, assist_reply: str, cls: ClassificationResult):
        from datetime import datetime, timezone
        subdir = {"preference": "Preferences", "knowledge": "Knowledge", "experience": "Experience", "task_result": "Tasks"}.get(cls.category.value, "Knowledge")
        now = datetime.now(timezone.utc).isoformat()
        frontmatter = f"---\ntitle: {cls.reason or 'Note'}\nsource: seed-agent\ncategory: {cls.category.value}\nimportance: {cls.importance}\ncreated: {now}\ntags: [seed]\n---\n\n"
        body = f"## 对话记录\n\n**用户**: {user_msg}\n\n**回答**: {assist_reply}\n\n" if cls.category != MemoryCategory.PREFERENCE else f"## 偏好记录\n\n{user_msg}\n\n"
        note_dir = self._vault.path / subdir
        note_dir.mkdir(parents=True, exist_ok=True)
        safe = "".join(c if c not in '<>:"/\\|?*' else "_" for c in (cls.reason or "note")[:40]) or "note"
        path = note_dir / f"{safe}.md"
        path.write_text(frontmatter + body, encoding="utf-8")
        return path


from dataclasses import dataclass


@dataclass
class MemoryResult:
    category: str = "skip"
    importance: float = 0.0
    episodic_saved: bool = False
    semantic_saved: bool = False
    procedural_saved: bool = False
    obsidian_path: str | None = None
