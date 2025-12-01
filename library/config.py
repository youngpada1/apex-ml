"""Centralized configuration using Pydantic."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Snowflake
    snowflake_account: Optional[str] = None
    snowflake_user: Optional[str] = None
    snowflake_database: str = "APEXML_DEV"
    snowflake_schema: str = "ANALYTICS"
    snowflake_warehouse: str = "ETL_WH_DEV"
    snowflake_role: str = "ACCOUNTADMIN"
    snowflake_private_key_path: Path = Path.home() / ".ssh" / "snowflake_key.p8"

    # OpenRouter
    openrouter_api_key: Optional[str] = None

    # Environment
    environment: str = "dev"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Singleton settings object

    Example:
        >>> from library.config import get_settings
        >>> settings = get_settings()
        >>> print(settings.snowflake_account)
    """
    return Settings()
