"""Application configuration with environment variable support."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "MetaGPT"
    app_version: str = "0.1.0"
    debug: bool = False

    # API
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # LLM Configuration - Gemini 3 Flash
    google_api_key: str = ""
    llm_model: str = "gemini-2.0-flash"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 8192
    llm_timeout: int = 120

    # Storage
    projects_dir: str = "./projects"
    storage_type: Literal["file", "memory"] = "file"

    # Agent Configuration
    agent_max_retries: int = 3
    agent_retry_delay: float = 1.0


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
