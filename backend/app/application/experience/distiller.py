"""
Experience Distiller.

After completing a task or substantive conversation,
analyzes what happened and extracts reusable lessons,
methods, and pitfalls into structured Obsidian notes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.infrastructure.llm.base import (
    LLMProvider,
)

from app.infrastructure.obsidian.vault import (
    ObsidianVault,
)


class ExperienceDistiller:
    """
    Distills experiences from completed work.

    Uses the LLM to analyze what was done,
    extract lessons, and write structured
    notes to Obsidian for future reference.
    """

    def __init__(
        self,
        llm: LLMProvider,
        vault: ObsidianVault,
    ) -> None:
        self._llm = llm
        self._vault = vault

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    async def distill(
        self,
        *,
        user_message: str,
        assistant_reply: str,
        topic: str = "",
    ) -> DistillationResult:
        """
        Analyze a conversation exchange and optionally
        write an experience note.

        Only creates notes for substantive exchanges
        that contain actionable lessons.
        """

        # Only distill if the exchange has substance
        if not self._is_worth_distilling(
            user_message,
            assistant_reply,
        ):
            return DistillationResult(
                distilled=False,
                reason="Exchange too brief",
            )

        # Use LLM to extract the lesson
        lesson = await self._extract_lesson(
            user_message,
            assistant_reply,
        )

        # If LLM extraction fails, create a basic note
        if lesson is None:
            lesson = {
                "title": topic or "经验记录",
                "summary": assistant_reply[:100],
                "method": assistant_reply[:200],
                "pitfall": "",
                "tags": [],
            }

        # Write to Obsidian
        note_path = self._write_experience_note(
            lesson=lesson,
            topic=topic or lesson.get("title", ""),
        )

        return DistillationResult(
            distilled=True,
            title=lesson.get("title", ""),
            note_path=note_path,
            tags=lesson.get("tags", []),
        )

    # --------------------------------------------------
    # Heuristics
    # --------------------------------------------------

    @staticmethod
    def _is_worth_distilling(
        user_message: str,
        assistant_reply: str,
    ) -> bool:
        """
        Quick check: is this exchange worth analyzing?
        """

        combined = f"{user_message} {assistant_reply}"

        # Must be long enough
        if len(combined) < 30:
            return False

        # Must contain actionable content
        action_signals = [
            "解决", "修复", "配置", "安装", "部署",
            "写", "创建", "实现", "调试", "优化",
            "修复", "配置", "部署",
            "fix", "solve", "install", "deploy",
            "build", "create", "implement",
            "error", "bug", "issue", "problem",
            "脚本", "代码", "程序", "函数",
            "script", "code", "function",
        ]

        return any(
            s in combined.lower()
            for s in action_signals
        )

    # --------------------------------------------------
    # LLM-based lesson extraction
    # --------------------------------------------------

    async def _extract_lesson(
        self,
        user_message: str,
        assistant_reply: str,
    ) -> dict[str, Any] | None:
        """
        Use the LLM to extract a structured lesson
        from a conversation exchange.
        """

        prompt = (
            "分析以下对话，提取可复用的经验。\n\n"
            "对话：\n"
            f"用户: {user_message}\n"
            f"助手: {assistant_reply}\n\n"
            "如果这段对话包含有价值的技术经验、"
            "解决问题的方法、或值得记录的教训，\n"
            "请用 JSON 格式返回：\n"
            "{\n"
            '  "title": "简短的标题",\n'
            '  "summary": "一句话总结",\n'
            '  "method": "具体方法或步骤",\n'
            '  "pitfall": "踩了什么坑（如果没有则留空）",\n'
            '  "tags": ["标签1", "标签2"]\n'
            "}\n\n"
            "如果不值得记录，只返回：null"
        )

        try:
            reply = await self._llm.chat_async(
                prompt,
                max_tokens=512,
            )

            import json

            # Try to find JSON in the response
            start = reply.find("{")
            end = reply.rfind("}")

            if start >= 0 and end > start:
                data = json.loads(
                    reply[start : end + 1]
                )
                return data

            # Check for null response
            if "null" in reply.strip().lower():
                return None

            return None

        except Exception:
            return None

    # --------------------------------------------------
    # Note writing
    # --------------------------------------------------

    def _write_experience_note(
        self,
        *,
        lesson: dict[str, Any],
        topic: str,
    ) -> Path:
        """Write a structured experience note to Obsidian."""

        now = datetime.now(timezone.utc).isoformat()

        title = lesson.get("title", topic) or "经验记录"
        summary = lesson.get("summary", "")
        method = lesson.get("method", "")
        pitfall = lesson.get("pitfall", "")
        tags = lesson.get("tags", [])

        if not tags:
            tags = ["seed", "experience"]

        tags_yaml = ", ".join(tags)

        # Build note content
        lines = [
            "---",
            f"title: {title}",
            "type: experience",
            f"source: seed-distiller",
            f"created: {now}",
            f"tags: [{tags_yaml}]",
            "---",
            "",
            f"# {title}",
            "",
        ]

        if summary:
            lines.extend(["> " + summary, ""])

        if method:
            lines.extend([
                "## 方法",
                "",
                method,
                "",
            ])

        if pitfall:
            lines.extend([
                "## 踩坑记录",
                "",
                pitfall,
                "",
            ])

        # Ensure directory exists
        note_dir = self._vault.path / "Experience"
        note_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename with date
        date_str = datetime.now(timezone.utc).strftime(
            "%Y-%m-%d"
        )
        safe_name = self._safe_filename(title)
        note_path = note_dir / f"{date_str}-{safe_name}.md"

        note_path.write_text(
            "\n".join(lines),
            encoding="utf-8",
        )

        return note_path

    @staticmethod
    def _safe_filename(text: str, max_len: int = 40) -> str:
        """Generate a safe filename from text."""

        invalid_chars = '<>:"/\\|?*'
        safe = "".join(
            "_" if c in invalid_chars else c
            for c in text.strip()
        )

        if len(safe) > max_len:
            safe = safe[:max_len].rstrip("_")

        return safe or "experience"


from dataclasses import dataclass
from pathlib import Path


@dataclass
class DistillationResult:
    """Result of distilling an experience."""

    distilled: bool = False
    title: str = ""
    note_path: Path | None = None
    tags: list[str] | None = None
    reason: str = ""
