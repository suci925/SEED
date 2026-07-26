# backend/app/core/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Seed"
    VERSION: str = "0.1.0"
    DATABASE_URL: str = "sqlite+aiosqlite:///./seed.db"

    # ==========================================
    # LLM Provider 配置
    # 支持的供应商：deepseek / qwen / moonshot / openai / claude
    # ==========================================
    LLM_PROVIDER: str = "deepseek"

    # DeepSeek (国内, OpenAI 兼容)
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-v4-pro"

    # 通义千问 Qwen (国内, OpenAI 兼容)
    QWEN_API_KEY: str = ""
    QWEN_MODEL: str = "qwen-plus"

    # Moonshot Kimi (国内, OpenAI 兼容)
    MOONSHOT_API_KEY: str = ""
    MOONSHOT_MODEL: str = "kimi-k2.6"

    # OpenAI (国外)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"

    # Anthropic Claude (国外)
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-opus-4-8"

    # ==========================================
    # Obsidian
    # ==========================================
    OBSIDIAN_VAULT_PATH: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
