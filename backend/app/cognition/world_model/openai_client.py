"""
Unified OpenAI-Compatible LLM Client.

Works with any OpenAI-compatible API provider:
DeepSeek, Qwen (通义千问), Moonshot (Kimi), OpenAI, etc.
"""

from __future__ import annotations

from typing import Any

from openai import OpenAI, AsyncOpenAI

from app.cognition.world_model.base import LLMProvider


# Well-known OpenAI-compatible endpoints
PROVIDER_ENDPOINTS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-v4-pro",
    },
    "qwen": {
        "base_url": (
            "https://dashscope.aliyuncs.com/"
            "compatible-mode/v1"
        ),
        "default_model": "qwen-plus",
    },
    "moonshot": {
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "kimi-k2.6",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
    },
}


class OpenAIClient(LLMProvider):
    """
    Unified client for any OpenAI-compatible API.

    Supports DeepSeek, Qwen, Moonshot, OpenAI, and
    any provider with an OpenAI-compatible endpoint.
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-v4-pro",
        max_tokens: int = 4096,
    ) -> None:
        self._model = model
        self._max_tokens = max_tokens

        self._sync = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        self._async = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def model(self) -> str:
        return self._model

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

    async def conversation(
        self,
        messages: list[dict[str, Any]],
        *,
        system: str | None = None,
        max_tokens: int | None = None,
    ) -> str:
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

    async def chat_with_context(
        self,
        message: str,
        context: str = "",
        *,
        system: str | None = None,
    ) -> str:
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
