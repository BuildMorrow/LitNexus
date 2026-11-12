from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "LitNexus"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-only-secret-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    DATABASE_URL: str = (
        "postgresql+asyncpg://litnexus:litnexus_dev_pass@localhost:5432/litnexus"
    )

    # Centralized LiteLLM settings
    LLM_PRIMARY_MODEL: str = "gemini/gemini-2.5-flash"
    LLM_FALLBACK_MODELS: str = "openai/gpt-4o-mini"
    LLM_EMBEDDING_MODEL: str = "text-embedding-3-small"
    LLM_TEMPERATURE: float = 0.2

    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    OPENALEX_MAILTO: str = ""
    SEMANTIC_SCHOLAR_API_KEY: str = ""

    @property
    def fallback_models_list(self) -> List[str]:
        return [m.strip() for m in self.LLM_FALLBACK_MODELS.split(",") if m.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
