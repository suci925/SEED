"""
Reflection Engine.

Uses the LLM to analyze recent interactions
and extract patterns, insights, and areas for improvement.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.infrastructure.llm.base import LLMProvider


class Reflector:
    """
    Analyzes recent experiences and generates
    structured reflections for the Evolution Loop.
    """

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def reflect(
        self,
        recent_experiences: list[dict[str, Any]],
    ) -> Reflection:
        """
        Analyze recent experiences and generate a reflection.

        Args:
            recent_experiences: List of dicts with
                action, outcome, lesson, created_at.

        Returns:
            Reflection with patterns and insights.
        """

        if not recent_experiences:
            return Reflection(
                summary="No recent activity to reflect on.",
            )

        # Build a summary for the LLM
        summary_lines = []
        for i, exp in enumerate(
            recent_experiences[:15], 1
        ):
            action = exp.get("action", "")[:80]
            lesson = exp.get("lesson", "")
            line = f"{i}. {action}"
            if lesson:
                line += f" → {lesson[:80]}"
            summary_lines.append(line)

        experiences_text = "\n".join(summary_lines)

        prompt = (
            "你是一个个人智能体的反思引擎。\n\n"
            "分析以下最近的交互记录，找出模式、"
            "趋势和改进机会。\n\n"
            f"最近 {len(recent_experiences[:15])} 次交互：\n"
            f"{experiences_text}\n\n"
            "请用 JSON 格式返回分析结果：\n"
            "{\n"
            '  "patterns": ["发现的模式1", "模式2"],\n'
            '  "insights": ["洞察1", "洞察2"],\n'
            '  "improvements": ["改进1", "改进2"],\n'
            '  "summary": "总体总结（一句话）"\n'
            "}\n\n"
            "如果没有足够数据，patterns 返回空数组。"
        )

        try:
            reply = await self._llm.chat_async(
                prompt, max_tokens=600
            )

            import json

            start = reply.find("{")
            end = reply.rfind("}")

            if start >= 0 and end > start:
                data = json.loads(
                    reply[start : end + 1]
                )
                return Reflection(
                    patterns=data.get("patterns", []),
                    insights=data.get("insights", []),
                    improvements=data.get(
                        "improvements", []
                    ),
                    summary=data.get(
                        "summary",
                        "反思完成",
                    ),
                )
        except Exception:
            pass

        return Reflection(
            summary="Reflection completed.",
            patterns=[],
        )


from dataclasses import dataclass, field


@dataclass
class Reflection:
    """Structured output from the reflection process."""

    summary: str = ""
    patterns: list[str] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)
