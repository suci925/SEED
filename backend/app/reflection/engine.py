"""
Reflection Engine 2.0 — 每日成长反思。

像人睡觉时整理一天的记忆一样，Seed 每天运行一次：

Input:  今天的所有结构化经验
Analyze: 新知识？新偏好？新技能？失败模式？用户变化？
Output:  记忆更新 + 技能更新 + 人格更新
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from app.cognition.world_model.base import LLMProvider
from app.memory.coordinator import MemoryCoordinator
from app.memory.procedural.manager import SkillManager
from app.memory.procedural.learner import SkillLearner


class ReflectionEngine:
    """
    Daily reflection cycle for Seed.

    Call `.run(date=...)` once per day to consolidate
    the day's experiences into lasting growth.
    """

    def __init__(
        self,
        llm: LLMProvider,
        coordinator: MemoryCoordinator,
        vault_path: str | Path,
    ) -> None:
        self._llm = llm
        self._coordinator = coordinator
        self._vault_path = Path(vault_path)
        self._skill_learner = SkillLearner(llm=llm)

    async def run(
        self,
        experiences: list[dict[str, Any]],
        *,
        target_date: date | None = None,
    ) -> DailyReflection:
        """
        Run a full daily reflection cycle.

        Args:
            experiences: Today's structured experiences
                (from ExperienceRepository).
            target_date: The date being reflected on.

        Returns:
            DailyReflection with insights and actions.
        """

        target = target_date or date.today()

        if not experiences:
            return DailyReflection(
                date=target,
                summary="No experiences to reflect on.",
            )

        # 1. Analyze across 5 dimensions
        analysis = await self._analyze(experiences)

        # 2. Execute concrete updates
        updates = await self._execute_updates(
            analysis, experiences
        )

        # 3. Write reflection note
        note_path = self._write_note(target, analysis, updates)

        return DailyReflection(
            date=target,
            summary=analysis.get("summary", ""),
            new_knowledge=analysis.get("new_knowledge", []),
            new_preferences=analysis.get("new_preferences", []),
            new_skills=analysis.get("new_skills", []),
            failure_patterns=analysis.get("failure_patterns", []),
            user_changes=analysis.get("user_changes", []),
            actions_taken=updates,
            note_path=str(note_path) if note_path else None,
        )

    # --------------------------------------------------
    # Analysis
    # --------------------------------------------------

    async def _analyze(
        self,
        experiences: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Use LLM to analyze experiences across 5 dimensions."""

        # Build a compact summary for the LLM
        lines = []
        for i, exp in enumerate(experiences[:20], 1):
            action = exp.get("action", "")[:60]
            outcome = exp.get("outcome", "")
            context = exp.get("context", {})
            failures = exp.get("failures", [])
            solution = exp.get("solution", "")[:80]
            lesson = exp.get("lesson", "")[:80]

            line = f"{i}. [{outcome}] {action}"
            if failures:
                line += f" ⚠️ {', '.join(failures[:2])}"
            if solution:
                line += f" → {solution}"
            if lesson:
                line += f" 📝 {lesson}"
            lines.append(line)

        experiences_text = "\n".join(lines)

        prompt = (
            "你是 Seed 的每日反思引擎。分析今天的经验，"
            "从 5 个维度提取洞察。\n\n"
            f"今天 ({date.today()}) 的经验：\n"
            f"{experiences_text}\n\n"
            "请用 JSON 返回分析结果：\n"
            "{\n"
            '  "summary": "今天整体总结（一句话）",\n'
            '  "new_knowledge": ["学到的知识1", "知识2"],\n'
            '  "new_preferences": ["发现的偏好1"],\n'
            '  "new_skills": ["可形成的技能1"],\n'
            '  "failure_patterns": ["重复出现的失败模式1"],\n'
            '  "user_changes": ["用户的变化1"]\n'
            "}\n\n"
            "每个数组最多 3 项。没有就返回空数组。"
        )

        try:
            reply = await self._llm.chat_async(
                prompt, max_tokens=1000
            )
            start = reply.find("{")
            end = reply.rfind("}")
            if start >= 0 and end > start:
                return json.loads(
                    reply[start : end + 1]
                )
        except Exception:
            pass

        return {"summary": "Analysis completed."}

    # --------------------------------------------------
    # Execute Updates
    # --------------------------------------------------

    async def _execute_updates(
        self,
        analysis: dict[str, Any],
        experiences: list[dict[str, Any]],
    ) -> list[str]:
        """Execute concrete updates based on analysis."""
        actions: list[str] = []

        # Update skills (from new_skills)
        for skill_desc in analysis.get("new_skills", []):
            if skill_desc and len(experiences) > 0:
                exp = experiences[0]
                result = await self._skill_learner.learn(
                    user_message=exp.get("action", ""),
                    assistant_reply=skill_desc,
                    topic=skill_desc[:40],
                )
                if result.learned:
                    actions.append(
                        f"🆕 新技能: {result.skill_name}"
                    )

        return actions

    # --------------------------------------------------
    # Note Writing
    # --------------------------------------------------

    def _write_note(
        self,
        target: date,
        analysis: dict[str, Any],
        updates: list[str],
    ) -> Path | None:
        """Write daily reflection to Obsidian."""

        date_str = target.isoformat()

        lines = [
            "---",
            f"title: 每日反思 {date_str}",
            "type: reflection",
            f"date: {date_str}",
            "tags: [seed, reflection, daily]",
            "---",
            "",
            f"# 每日反思 {date_str}",
            "",
        ]

        summary = analysis.get("summary", "")
        if summary:
            lines += [f"> {summary}", ""]

        sections = [
            ("新知识", "new_knowledge"),
            ("新偏好", "new_preferences"),
            ("新技能", "new_skills"),
            ("失败模式", "failure_patterns"),
            ("用户变化", "user_changes"),
        ]

        for title, key in sections:
            items = analysis.get(key, [])
            if items:
                lines += [f"## {title}", ""]
                lines += [f"- {item}" for item in items]
                lines += [""]

        if updates:
            lines += ["## 执行的动作", ""]
            lines += [f"- {u}" for u in updates]
            lines += [""]

        ref_dir = self._vault_path / "Reflections"
        ref_dir.mkdir(parents=True, exist_ok=True)
        path = ref_dir / f"反思-{date_str}.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        return path


from dataclasses import dataclass, field


@dataclass
class DailyReflection:
    """Result of a daily reflection cycle."""

    date: date
    summary: str = ""
    new_knowledge: list[str] = field(
        default_factory=list
    )
    new_preferences: list[str] = field(
        default_factory=list
    )
    new_skills: list[str] = field(default_factory=list)
    failure_patterns: list[str] = field(
        default_factory=list
    )
    user_changes: list[str] = field(
        default_factory=list
    )
    actions_taken: list[str] = field(
        default_factory=list
    )
    note_path: str | None = None
