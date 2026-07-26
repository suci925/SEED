"""
Episode — 事件记忆实体。

记录完整的事件链：触发条件 → 上下文 → 行动 → 结果 → 教训。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class Episode:
    """
    A complete event with context, actions, and outcome.

    Unlike a raw Experience (single interaction),
    an Episode captures the full narrative:
    what happened, what was done, what was learned.
    """

    trigger: str
    """What initiated this episode (user request / event)."""

    summary: str
    """One-line summary of what happened."""

    outcome: str = "success"
    """success / failure / partial"""

    id: str = field(default_factory=lambda: f"ep_{uuid4().hex[:12]}")
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    context: str = ""
    """Background context (Docker network failed, ...)."""

    actions: list[str] = field(default_factory=list)
    """Steps taken to resolve."""

    lesson: str = ""
    """What was learned from this episode."""

    tags: list[str] = field(default_factory=list)
    """Relevant tags."""

    importance: float = 0.5
    """0.0 - 1.0"""
