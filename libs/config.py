"""Configuration management using pydantic-settings."""

from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")

    # Log level: one of DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # Spinner settings
    spinner_type: str = "dots"


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the global settings instance (singleton pattern).

    Returns:
        The application Settings object
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


__all__ = ["Settings", "get_settings"]
