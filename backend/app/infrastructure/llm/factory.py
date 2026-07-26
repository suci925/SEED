"""
LLM Provider Factory.

Creates the correct LLM provider based on
configuration. Users switch providers by
changing `LLM_PROVIDER` in .env.
"""

from __future__ import annotations

from app.core.config import settings

from app.infrastructure.llm.base import LLMProvider
from app.infrastructure.llm.openai_client import (
    OpenAIClient,
    PROVIDER_ENDPOINTS,
)


# Provider configurations: maps provider name to
# (config_key_prefix, env_var_for_api_key)
_PROVIDER_CONFIGS = {
    "deepseek": {
        "key_attr": "DEEPSEEK_API_KEY",
        "model_attr": "DEEPSEEK_MODEL",
    },
    "qwen": {
        "key_attr": "QWEN_API_KEY",
        "model_attr": "QWEN_MODEL",
    },
    "moonshot": {
        "key_attr": "MOONSHOT_API_KEY",
        "model_attr": "MOONSHOT_MODEL",
    },
    "openai": {
        "key_attr": "OPENAI_API_KEY",
        "model_attr": "OPENAI_MODEL",
    },
    "claude": {
        "key_attr": "ANTHROPIC_API_KEY",
        "model_attr": "ANTHROPIC_MODEL",
    },
}


def create_llm_provider() -> LLMProvider:
    """
    Create an LLM provider based on settings.

    Reads `LLM_PROVIDER` from config to determine
    which provider to instantiate, then reads the
    corresponding API key and model from settings.

    Raises:
        ValueError: If provider is unknown or key missing.
    """

    provider_name = settings.LLM_PROVIDER or "deepseek"
    provider_name = provider_name.strip().lower()

    # --- OpenAI-compatible providers ---
    if provider_name in PROVIDER_ENDPOINTS:
        return _create_openai_compatible(provider_name)

    # --- Anthropic Claude ---
    if provider_name == "claude":
        return _create_claude()

    raise ValueError(
        f"Unknown LLM provider: {provider_name}. "
        f"Supported: {', '.join(_PROVIDER_CONFIGS)}"
    )


def _create_openai_compatible(
    provider: str,
) -> OpenAIClient:
    """
    Create an OpenAI-compatible client.
    """
    cfg = _PROVIDER_CONFIGS[provider]
    endpoint = PROVIDER_ENDPOINTS[provider]

    api_key = getattr(settings, cfg["key_attr"], "")
    model = (
        getattr(settings, cfg["model_attr"], "")
        or endpoint["default_model"]
    )

    if not api_key:
        raise ValueError(
            f"{cfg['key_attr']} not configured. "
            f"Set it in .env for {provider} provider."
        )

    return OpenAIClient(
        api_key=api_key,
        base_url=endpoint["base_url"],
        model=model,
    )


def _create_claude() -> LLMProvider:
    """
    Create an Anthropic Claude client.
    """
    api_key = settings.ANTHROPIC_API_KEY or ""
    model = settings.ANTHROPIC_MODEL or "claude-opus-4-8"

    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not configured. "
            "Set it in .env for Claude provider."
        )

    from app.infrastructure.llm.client import (
        ClaudeClient,
    )

    return ClaudeClient(
        api_key=api_key,
        model=model,
    )
