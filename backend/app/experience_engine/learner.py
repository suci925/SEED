"""
Experience Learner — 从对话中提取经验卡片。

受 MemGovern / SWE-Agent 启发，每次对话后提取：
  - problem: 问题描述
  - context: 目标、环境
  - diagnosis: 根因分析
  - solution: 解决方案
  - verification: 如何验证已解决
  - confidence: 可信度
"""

from __future__ import annotations

import json
from typing import Any

from app.cognition.world_model.base import LLMProvider


class ExperienceLearner:
    """
    Uses LLM to extract structured experiences
    from natural conversation.
    """

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def extract(
        self,
        user_message: str,
        assistant_reply: str,
    ) -> ExperienceData | None:
        """
        Extract structured experience from a conversation turn.

        Returns None if the exchange doesn't contain
        a learnable experience.
        """

        if not self._is_worth_extracting(
            user_message, assistant_reply
        ):
            return None

        prompt = (
            "从以下对话中提取一张经验卡片。\n\n"
            f"用户: {user_message}\n"
            f"助手: {assistant_reply}\n\n"
            "如果包含问题解决过程，请用 JSON 返回：\n"
            "{\n"
            '  "problem": "问题描述",\n'
            '  "context": {"goal": "目标", "environment": "环境"},'
            '\n'
            '  "diagnosis": "根因分析",\n'
            '  "solution": "解决方案",\n'
            '  "verification": "如何验证已解决",\n'
            '  "confidence": 0.85\n'
            "}\n\n"
            "如果没有问题或解决方案，只返回 null。\n"
            "confidence 范围 0.0-1.0。"
        )

        try:
            reply = await self._llm.chat_async(
                prompt, max_tokens=800
            )
            start = reply.find("{")
            end = reply.rfind("}")
            if start >= 0 and end > start:
                data = json.loads(
                    reply[start : end + 1]
                )
                return ExperienceData(
                    context=data.get("context", {}),
                    actions=data.get("actions", []),
                    failures=data.get("failures", []),
                    solution=data.get("solution", ""),
                    confidence=min(
                        float(
                            data.get("confidence", 0.5)
                        ),
                        1.0,
                    ),
                )
        except Exception:
            pass

        return None

    @staticmethod
    def _is_worth_extracting(
        user_message: str,
        assistant_reply: str,
    ) -> bool:
        """Quick check if this exchange has learnable content."""
        combined = f"{user_message} {assistant_reply}"
        if len(combined) < 60:
            return False
        signals = [
            "部署", "配置", "安装", "修复", "解决",
            "错误", "报错", "失败", "问题",
            "deploy", "install", "fix", "error",
            "solution", "步骤", "方法",
        ]
        return any(s in combined.lower() for s in signals)


from dataclasses import dataclass, field


@dataclass
class ExperienceData:
    """Structured experience extracted from conversation."""

    context: dict[str, Any] = field(
        default_factory=dict
    )
    actions: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    solution: str = ""
    confidence: float = 0.0
