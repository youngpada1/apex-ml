"""Centralized configuration using Pydantic."""
from pydantic_settings import BaseSettings
from pathlib import Path
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Snowflake
    snowflake_account: str
    snowflake_user: str
    snowflake_database: str = "APEXML_DEV"
    snowflake_schema: str = "ANALYTICS"
    snowflake_warehouse: str = "ETL_WH_DEV"
    snowflake_role: str = "ACCOUNTADMIN"
    snowflake_private_key_path: Path = Path.home() / ".ssh" / "snowflake_key.p8"

    # OpenRouter
    openrouter_api_key: str

    # Environment
    environment: str = "dev"

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = False


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
