"""
Claude API Client.

Encapsulates Anthropic SDK interactions
for the Seed agent system.
"""

from __future__ import annotations

from typing import Any

from anthropic import (
    Anthropic,
    AsyncAnthropic,
)

from app.infrastructure.llm.base import LLMProvider


class ClaudeClient(LLMProvider):
    """
    Wraps the Anthropic SDK for Seed.

    Provides sync and async access to Claude
    with built-in error handling and logging.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-opus-4-8",
        max_tokens: int = 4096,
    ) -> None:
        self._model = model
        self._max_tokens = max_tokens

        self._sync = Anthropic(
            api_key=api_key,
        )

        self._async = AsyncAnthropic(
            api_key=api_key,
        )

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def model(self) -> str:
        """Claude model ID in use."""
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        self._model = value

    # --------------------------------------------------
    # Sync API
    # --------------------------------------------------

    def chat(
        self,
        message: str,
        *,
        system: str | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """
        Send a single user message and get a response.
        """

        response = self._sync.messages.create(
            model=self._model,
            max_tokens=max_tokens or self._max_tokens,
            system=system,
            messages=[
                {"role": "user", "content": message},
            ],
        )

        text_blocks = [
            b.text
            for b in response.content
            if b.type == "text"
        ]

        return "\n".join(text_blocks)

    # --------------------------------------------------
    # Async API
    # --------------------------------------------------

    async def chat_async(
        self,
        message: str,
        *,
        system: str | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """
        Async version of chat.
        """

        response = await self._async.messages.create(
            model=self._model,
            max_tokens=max_tokens or self._max_tokens,
            system=system,
            messages=[
                {"role": "user", "content": message},
            ],
        )

        text_blocks = [
            b.text
            for b in response.content
            if b.type == "text"
        ]

        return "\n".join(text_blocks)

    # --------------------------------------------------
    # Multi-turn conversation
    # --------------------------------------------------

    async def conversation(
        self,
        messages: list[dict[str, Any]],
        *,
        system: str | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """
        Send a multi-turn conversation and get a response.
        """

        response = await self._async.messages.create(
            model=self._model,
            max_tokens=max_tokens or self._max_tokens,
            system=system,
            messages=messages,
        )

        text_blocks = [
            b.text
            for b in response.content
            if b.type == "text"
        ]

        return "\n".join(text_blocks)

    # --------------------------------------------------
    # Chat with context (for Agent use)
    # --------------------------------------------------

    async def chat_with_context(
        self,
        message: str,
        context: str = "",
        *,
        system: str | None = None,
    ) -> str:
        """
        Send a message with retrieved context.

        This is the primary method the Agent will use:
        it prepends retrieved knowledge from Obsidian
        or other sources before the user's message.
        """

        if context:
            full_message = (
                "## 相关上下文\n\n"
                f"{context}\n\n"
                "---\n\n"
                f"## 用户问题\n\n{message}"
            )
        else:
            full_message = message

        return await self.chat_async(
            full_message,
            system=system,
        )
