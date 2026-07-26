"""
World Model — 用户世界状态模型。

维护用户当前的人生状态：职业、目标、项目、环境、关系。
每次对话时注入 system prompt，让 LLM 能基于用户状态辅助决策。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


# Default world model (empty, will be filled over time)
DEFAULT_MODEL = {
    "owner": {
        "career": "",
        "current_goal": "",
        "risk": "medium",
        "interests": [],
    },
    "projects": [],
    "environment": {
        "os": "",
        "editor": "",
        "main_lang": "",
    },
    "relationship": {
        "style": "partner",
        "trust": "building",
    },
}


class WorldModel:
    """
    Structured model of the user's world state.

    Persisted to Obsidian/seed/world-model.md as YAML.
    Injected into every LLM call as context.
    """

    def __init__(
        self, vault_path: str | Path
    ) -> None:
        self._path = Path(vault_path) / "seed"
        self._file = self._path / "world-model.md"
        self._data: dict[str, Any] = dict(
            DEFAULT_MODEL
        )
        self._load()

    # --------------------------------------------------
    # Load / Save
    # --------------------------------------------------

    def _load(self) -> None:
        """Load world model from YAML file."""
        if not self._file.exists():
            self._data = dict(DEFAULT_MODEL)
            return
        try:
            content = self._file.read_text(
                encoding="utf-8"
            )
            # Strip frontmatter if present
            if content.startswith("---"):
                end = content.find("---", 3)
                if end > 0:
                    content = content[end + 3 :]
            parsed = yaml.safe_load(content)
            if isinstance(parsed, dict):
                self._data = parsed
        except Exception:
            self._data = dict(DEFAULT_MODEL)

    def save(self) -> None:
        """Save world model to YAML file."""
        self._path.mkdir(parents=True, exist_ok=True)
        self._data["last_updated"] = datetime.now(
            timezone.utc
        ).isoformat()
        yaml_content = yaml.dump(
            self._data,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )
        self._file.write_text(
            yaml_content, encoding="utf-8"
        )

    # --------------------------------------------------
    # Access
    # --------------------------------------------------

    @property
    def data(self) -> dict[str, Any]:
        return self._data

    def to_context(self) -> str:
        """Format as context string for LLM system prompt."""
        lines = ["## 用户世界状态", ""]
        owner = self._data.get("owner", {})
        if owner.get("career"):
            lines.append(
                f"- 职业: {owner['career']}"
            )
        if owner.get("current_goal"):
            lines.append(
                f"- 当前目标: {owner['current_goal']}"
            )
        if owner.get("interests"):
            lines.append(
                f"- 兴趣: {', '.join(owner['interests'])}"
            )
        projects = self._data.get("projects", [])
        if projects:
            active = [
                p["name"]
                for p in projects
                if p.get("status") == "active"
            ]
            if active:
                lines.append(
                    f"- 活跃项目: {', '.join(active)}"
                )
        env = self._data.get("environment", {})
        if env.get("main_lang"):
            lines.append(
                f"- 主要语言: {env['main_lang']}"
            )
        if env.get("os"):
            lines.append(f"- 系统: {env['os']}")
        return "\n".join(lines)

    # --------------------------------------------------
    # Update
    # --------------------------------------------------

    def update(self, updates: dict[str, Any]) -> int:
        """
        Apply updates to the world model.

        Returns number of fields changed.
        """
        count = 0

        for section, values in updates.items():
            if section not in self._data:
                self._data[section] = values
                count += 1
                continue

            if isinstance(values, dict):
                for key, val in values.items():
                    if val and self._data[section].get(
                        key
                    ) != val:
                        self._data[section][key] = val
                        count += 1
            elif isinstance(values, list):
                existing = self._data[section]
                for item in values:
                    if item not in existing:
                        existing.append(item)
                        count += 1

        if count:
            self.save()

        return count
