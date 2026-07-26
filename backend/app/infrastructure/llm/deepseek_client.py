"""
DeepSeek API Client.

Uses the OpenAI-compatible DeepSeek API
to provide LLM services for the Seed agent.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# Load .env if pydantic-settings hasn't done it yet
_env_path = Path(__file__).resolve().parents[3] / ".env"
if _env_path.exists() and not os.environ.get("DEEPSEEK_API_KEY"):
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_path)
    except ImportError:
        pass

from openai import OpenAI, AsyncOpenAI


DEEPSEEK_BASE_URL = "https://api.deepseek.com"


class DeepSeekClient:
    """
    Wraps the DeepSeek API (OpenAI-compatible)
    for Seed.

    Provides sync and async access to DeepSeek
    models with built-in error handling.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "deepseek-v4-pro",
        max_tokens: int = 4096,
        base_url: str = DEEPSEEK_BASE_URL,
    ) -> None:
        self._model = model
        self._max_tokens = max_tokens

        resolved_key = api_key or os.environ.get(
            "DEEPSEEK_API_KEY", ""
        )

        self._sync = OpenAI(
            api_key=resolved_key,
            base_url=base_url,
        )

        self._async = AsyncOpenAI(
            api_key=resolved_key,
            base_url=base_url,
        )

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def model(self) -> str:
        """DeepSeek model ID in use."""
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

        messages: list[dict[str, str]] = []

        if system:
            messages.append(
                {"role": "system", "content": system},
            )

        messages.append(
            {"role": "user", "content": message},
        )

        response = self._sync.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens or self._max_tokens,
            messages=messages,
        )

        return response.choices[0].message.content or ""

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

        messages: list[dict[str, str]] = []

        if system:
            messages.append(
                {"role": "system", "content": system},
            )

        messages.append(
            {"role": "user", "content": message},
        )

        response = await self._async.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens or self._max_tokens,
            messages=messages,
        )

        return response.choices[0].message.content or ""

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

        full_messages: list[dict[str, Any]] = []

        if system:
            full_messages.append(
                {"role": "system", "content": system},
            )

        full_messages.extend(messages)

        response = await self._async.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens or self._max_tokens,
            messages=full_messages,
        )

        return response.choices[0].message.content or ""

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
