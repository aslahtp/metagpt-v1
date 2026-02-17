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
    llm_temperature: float | None = None
    llm_max_tokens: int | None = None
    llm_timeout: int = 120

    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "metagpt"

    # JWT Authentication
    jwt_secret: str = "change-this-secret-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Credits
    free_credits: int = 2

    # Storage (file-based storage kept for generated code files)
    projects_dir: str = "./projects"
    storage_type: Literal["file", "memory"] = "file"

    # Agent Configuration
    agent_max_retries: int = 3
    agent_retry_delay: float = 1.0


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
