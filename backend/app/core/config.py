# backend/app/core/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Seed"
    VERSION: str = "0.1.0"
    DATABASE_URL: str = "sqlite+aiosqlite:///./seed.db"

    # DeepSeek LLM 配置 (OpenAI 兼容)
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-v4-pro"

    # Obsidian 仓库路径
    OBSIDIAN_VAULT_PATH: str = ""

    class Config:
        # 指定加载同级目录下的 .env 文件
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
