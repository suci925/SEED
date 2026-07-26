"""
LLM Provider Base Interface.

All LLM providers (DeepSeek, Qwen, Moonshot, OpenAI, Claude)
implement this abstract base class.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """
    Abstract interface for LLM providers.

    Every provider must implement these methods
    so the orchestrator can use them interchangeably.
    """

    @property
    @abstractmethod
    def model(self) -> str:
        """The model ID in use."""
        ...

    @abstractmethod
    def chat(
        self,
        message: str,
        *,
        system: str | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Sync: send a single message, get a reply."""
        ...

    @abstractmethod
    async def chat_async(
        self,
        message: str,
        *,
        system: str | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Async: send a single message, get a reply."""
        ...

    @abstractmethod
    async def conversation(
        self,
        messages: list[dict[str, Any]],
        *,
        system: str | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Async multi-turn conversation."""
        ...

    @abstractmethod
    async def chat_with_context(
        self,
        message: str,
        context: str = "",
        *,
        system: str | None = None,
    ) -> str:
        """Chat with retrieved context prepended."""
        ...
