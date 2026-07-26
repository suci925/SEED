"""
World Updater — 检测并更新世界状态。

每次对话后调用 LLM 判断：
"这段对话包含用户世界状态的更新吗？"
"""

from __future__ import annotations

import json
from typing import Any

from app.cognition.world_model.base import LLMProvider
from app.personality.world_model import WorldModel


class WorldUpdater:
    """
    Detects changes in the user's world state
    from conversation and updates the WorldModel.
    """

    def __init__(
        self, llm: LLMProvider, vault_path: str
    ) -> None:
        self._llm = llm
        self._model = WorldModel(vault_path)

    async def process_conversation(
        self,
        user_message: str,
        assistant_reply: str,
    ) -> bool:
        """
        Check if a conversation contains world state updates.

        Returns True if the model was updated.
        """
        if not self._contains_signal(user_message):
            return False

        updates = await self._extract_updates(
            user_message
        )
        if not updates:
            return False

        count = self._model.update(updates)
        return count > 0

    @staticmethod
    def _contains_signal(message: str) -> bool:
        """Quick check if message might contain state info."""
        signals = [
            "我最近",
            "我正在",
            "我准备",
            "我打算",
            "我换了",
            "我开始",
            "我转行",
            "我创业",
            "我辞职",
            "我加入",
            "我买了",
            "我学了",
            "我的目标是",
            "我在做",
            "我现在",
            "我换了新",
        ]
        return any(s in message for s in signals)

    async def _extract_updates(
        self, message: str
    ) -> dict[str, Any] | None:
        """Use LLM to extract structured updates."""
        prompt = (
            "从用户的话中提取世界状态更新。"
            "只提取明确提到的信息，不要猜测。\n\n"
            f"用户说: {message}\n\n"
            "用 JSON 返回更新，格式：\n"
            "{\n"
            '  "owner": {"career": "", "current_goal": "",'
            ' "interests": []},\n'
            '  "projects": [{"name": "", "status": "active"}],\n'
            '  "environment": {"os": "", "editor": "",'
            ' "main_lang": ""}\n'
            "}\n\n"
            "只填有明确信息的部分，没有的留空或省略。"
            "如果没有任何状态更新，返回 null。"
        )
        try:
            reply = await self._llm.chat_async(
                prompt, max_tokens=400
            )
            start = reply.find("{")
            end = reply.rfind("}")
            if start >= 0 and end > start:
                data = json.loads(
                    reply[start : end + 1]
                )
                # Filter out empty updates
                cleaned = {}
                for section, values in data.items():
                    if isinstance(values, dict):
                        non_empty = {
                            k: v
                            for k, v in values.items()
                            if v
                        }
                        if non_empty:
                            cleaned[section] = (
                                non_empty
                            )
                    elif values:
                        cleaned[section] = values
                return cleaned or None
        except Exception:
            pass
        return None
