"""
Information Classifier.

Determines whether a piece of information is
worth remembering and what category it belongs to.
"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
import re


class MemoryCategory(str, Enum):
    """Categories of information worth remembering."""

    PREFERENCE = "preference"
    """User's personal preferences and tastes."""

    KNOWLEDGE = "knowledge"
    """Factual knowledge, concepts, solutions."""

    EXPERIENCE = "experience"
    """Lessons learned from completing tasks."""

    TASK_RESULT = "task_result"
    """Outcome of a completed task/project."""

    SKIP = "skip"
    """Not worth saving."""


@dataclass
class ClassificationResult:
    """Result of classifying a piece of information."""

    category: MemoryCategory = MemoryCategory.SKIP
    reason: str = ""
    suggested_tags: list[str] = field(
        default_factory=list,
    )
    importance: float = 0.5
    suggested_title: str = ""


# Known patterns that indicate something is worth saving
_PREFERENCE_PATTERNS = [
    r"我喜欢",
    r"我不喜欢",
    r"我更喜欢",
    r"我更倾向于",
    r"我习惯",
    r"我用的是",
    r"我推荐",
    r"我用",
    r"我选择",
    r"偏好",
    r"prefer",
    r"favorite",
]

_KNOWLEDGE_PATTERNS = [
    r"解决了",
    r"方法",
    r"步骤",
    r"原来",
    r"学会了",
    r"学到",
    r"理解为",
    r"意思是",
    r"是一种",
    r"是指",
    r"原理",
    r"概念",
    r"how to",
    r"solution",
    r"fix",
    r"tutorial",
]

_EXPERIENCE_PATTERNS = [
    r"踩坑",
    r"报错",
    r"错误",
    r"注意",
    r"教训",
    r"建议",
    r"经验",
    r"更好的做法",
    r"bug",
    r"error",
    r"lesson",
    r"tip",
]


class Classifier:
    """
    Classifies conversation content to decide
    whether it's worth remembering.

    Uses pattern matching for fast common cases.
    Falls back to LLM-based classification for
    ambiguous content.
    """

    MIN_CONTENT_LENGTH = 15
    """Messages shorter than this are never saved."""

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def classify(
        self,
        user_message: str,
        assistant_reply: str,
    ) -> ClassificationResult:
        """
        Classify a conversation exchange.

        Args:
            user_message: The user's input.
            assistant_reply: The agent's response.

        Returns:
            ClassificationResult with category and metadata.
        """

        combined = f"{user_message} {assistant_reply}"

        # Skip very short / trivial exchanges
        if len(combined.strip()) < self.MIN_CONTENT_LENGTH:
            return ClassificationResult(
                category=MemoryCategory.SKIP,
                reason="Content too short",
            )

        # Check for preference signals
        pref = self._match_patterns(
            combined, _PREFERENCE_PATTERNS
        )
        if pref:
            return ClassificationResult(
                category=MemoryCategory.PREFERENCE,
                reason=pref,
                importance=0.8,
                suggested_title=self._extract_pref_title(
                    user_message,
                ),
                suggested_tags=[],
            )

        # Check for knowledge signals
        know = self._match_patterns(
            combined, _KNOWLEDGE_PATTERNS
        )
        if know:
            return ClassificationResult(
                category=MemoryCategory.KNOWLEDGE,
                reason=know,
                importance=0.7,
                suggested_title=self._extract_knowledge_title(
                    user_message,
                ),
                suggested_tags=[],
            )

        # Check for experience signals
        exp = self._match_patterns(
            combined, _EXPERIENCE_PATTERNS
        )
        if exp:
            return ClassificationResult(
                category=MemoryCategory.EXPERIENCE,
                reason=exp,
                importance=0.75,
                suggested_tags=["经验"],
            )

        # Longer substantive exchanges are worth saving
        # as general knowledge
        if len(combined) > 100:
            return ClassificationResult(
                category=MemoryCategory.KNOWLEDGE,
                reason="Substantive exchange",
                importance=0.5,
            )

        return ClassificationResult(
            category=MemoryCategory.SKIP,
            reason="No save signal detected",
        )

    # --------------------------------------------------
    # Pattern matching
    # --------------------------------------------------

    @staticmethod
    def _match_patterns(
        text: str,
        patterns: list[str],
    ) -> str | None:
        """Return the first matched pattern, or None."""

        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return f"Matched: {pattern}"

        return None

    @staticmethod
    def _extract_pref_title(message: str) -> str:
        """Extract a title from preference statements."""

        # e.g. "我喜欢 React" → "编程偏好：React"
        for prefix in ["我喜欢", "我用的是", "我用", "我推荐"]:
            if prefix in message:
                rest = message.split(prefix, 1)[1].strip()
                rest = rest.split("。")[0].split("，")[0]
                if rest:
                    return f"偏好：{rest}"

        return f"偏好：{message[:30]}"

    @staticmethod
    def _extract_knowledge_title(message: str) -> str:
        """Extract a title from knowledge statements."""

        # Try to find "是/是一种" patterns
        for marker in ["什么是", "怎么", "如何", "什么是"]:
            if marker in message:
                topic = message.split(marker, 1)[1].strip()
                topic = topic.split("？")[0].split("?")[0]
                if topic:
                    return f"知识：{topic[:30]}"

        return f"知识：{message[:30]}"

    # --------------------------------------------------
    # Convenience
    # --------------------------------------------------

    @staticmethod
    def should_save(
        category: MemoryCategory,
    ) -> bool:
        """Quick check: should this category be persisted?"""

        return category != MemoryCategory.SKIP
