"""
Skill Learner — 第五种学习。

从成功解决的任务中自动提取步骤，
生成可复用的技能包 (SKILL.md)。

流程：
  检测 → 提取 → 生成 → 评估 → 成熟
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.cognition.world_model.base import LLMProvider


# Default skills directory
SKILLS_DIR = Path(__file__).resolve().parents[3] / "skills"


class SkillLearner:
    """
    Learns reusable skills from successful task completion.

    After Seed solves a problem, this module:
    1. Checks if the solution is worth saving as a skill
    2. Uses LLM to extract structured steps
    3. Generates SKILL.md in the skills directory
    4. Tracks confidence over multiple uses
    """

    def __init__(
        self,
        llm: LLMProvider,
        skills_dir: str | Path = SKILLS_DIR,
    ) -> None:
        self._llm = llm
        self._skills_dir = Path(skills_dir)

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    async def learn(
        self,
        *,
        user_message: str,
        assistant_reply: str,
        topic: str = "",
    ) -> SkillLearningResult:
        """
        Attempt to learn a skill from a conversation.

        Only creates a skill if the exchange contains
        a clear problem-solving pattern with steps.
        """

        if not self._is_skill_worthy(user_message, assistant_reply):
            return SkillLearningResult(learned=False)

        # Ask LLM to extract the skill
        skill_data = await self._extract_skill(
            user_message, assistant_reply,
        )

        if skill_data is None:
            return SkillLearningResult(learned=False)

        # Generate SKILL.md
        skill_name = self._generate_skill_name(
            topic or skill_data.get("name", ""),
        )
        skill_path = self._write_skill(
            name=skill_name,
            data=skill_data,
        )

        return SkillLearningResult(
            learned=True,
            skill_name=skill_name,
            skill_path=skill_path,
            steps=skill_data.get("steps", []),
            confidence=skill_data.get("confidence", 0.5),
        )

    # --------------------------------------------------
    # Heuristics
    # --------------------------------------------------

    @staticmethod
    def _is_skill_worthy(
        user_message: str,
        assistant_reply: str,
    ) -> bool:
        """Check if this exchange contains a learnable skill."""

        combined = f"{user_message} {assistant_reply}".lower()

        # Must be substantive
        if len(combined) < 80:
            return False

        # Look for action signals
        signals = [
            "部署", "配置", "安装", "搭建", "编写",
            "实现", "创建", "设置", "修复", "解决",
            "deploy", "install", "configure", "setup",
            "build", "create", "implement", "fix",
            "步骤", "方法", "办法",
            "step", "method",
        ]

        return any(s in combined for s in signals)

    # --------------------------------------------------
    # LLM Extraction
    # --------------------------------------------------

    async def _extract_skill(
        self,
        user_message: str,
        assistant_reply: str,
    ) -> dict[str, Any] | None:
        """Use LLM to extract structured skill data."""

        prompt = (
            "从以下对话中提取可复用的技能步骤。\n\n"
            f"用户: {user_message}\n"
            f"助手: {assistant_reply}\n\n"
            "如果这段对话包含明确的解决问题步骤，"
            "请用 JSON 返回：\n"
            "{\n"
            '  "name": "技能名称（简短）",\n'
            '  "description": "一句话说明",\n'
            '  "steps": ["步骤1", "步骤2", ...],\n'
            '  "prerequisites": "前置条件（没有则留空）",\n'
            '  "confidence": 0.7\n'
            "}\n\n"
            "如果不包含可复用的技能，只返回 null。"
        )

        try:
            reply = await self._llm.chat_async(
                prompt, max_tokens=800,
            )
            start = reply.find("{")
            end = reply.rfind("}")
            if start >= 0 and end > start:
                return json.loads(reply[start:end+1])
        except Exception:
            pass

        return None

    # --------------------------------------------------
    # Skill Generation
    # --------------------------------------------------

    def _generate_skill_name(
        self, topic: str,
    ) -> str:
        """Generate a unique skill name from topic."""
        safe = "".join(
            c if c.isalnum() or c in "-_" else "_"
            for c in topic.lower().strip()
        ) or "learned_skill"
        # Add version
        return f"{safe}_v1"

    def _write_skill(
        self,
        *,
        name: str,
        data: dict[str, Any],
    ) -> Path:
        """Write skill files to disk."""

        skill_dir = self._skills_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now(timezone.utc).isoformat()
        steps_yaml = "\n".join(
            f"  - {s}" for s in data.get("steps", [])
        )

        skilling_content = (
            "---\n"
            f"name: {name}\n"
            f"description: {data.get('description', '')}\n"
            f"version: 1.0.0\n"
            f"confidence: {data.get('confidence', 0.5)}\n"
            f"learned_at: {now}\n"
            "keywords:\n"
            f"{self._keywords_yaml(data)}\n"
            "---\n\n"
            f"# {name}\n\n"
            f"{data.get('description', '')}\n\n"
            "## 步骤\n\n"
            f"{steps_yaml}\n\n"
        )

        prereq = data.get("prerequisites", "")
        if prereq:
            skilling_content += f"## 前置条件\n\n{prereq}\n\n"

        skilling_content += (
            "## 说明\n\n"
            "此技能由 Seed 的 Skill Learner 自动从对话中生成。\n"
            "每次成功使用后 confidence 会提升。\n"
        )

        skill_path = skill_dir / "SKILL.md"
        skill_path.write_text(
            skilling_content, encoding="utf-8",
        )
        return skill_path

    @staticmethod
    def _keywords_yaml(data: dict) -> str:
        """Generate YAML keywords from skill data."""
        words = []
        for step in data.get("steps", []):
            words.extend(step.lower().split()[:3])
        unique = list(dict.fromkeys(words))[:8]
        return "\n".join(f"  - {w}" for w in unique)


from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SkillLearningResult:
    """Result of a skill learning attempt."""

    learned: bool = False
    skill_name: str = ""
    skill_path: Path | None = None
    steps: list[str] = field(default_factory=list)
    confidence: float = 0.0
