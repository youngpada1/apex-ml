"""Centralized configuration using Pydantic."""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator
from pathlib import Path
from functools import lru_cache
from typing import Optional, Literal

# Get the project root directory (where .env file is located)
PROJECT_ROOT = Path(__file__).parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Supports environment-specific configurations for dev, staging, and prod.
    Environment variables override defaults.
    """

    # ========================================================================
    # ENVIRONMENT
    # ========================================================================
    environment: Literal["dev", "staging", "prod"] = "dev"

    # ========================================================================
    # SNOWFLAKE CONFIGURATION
    # ========================================================================
    snowflake_account: Optional[str] = None
    snowflake_user: Optional[str] = None
    snowflake_database: str = "APEXML_DEV"
    snowflake_schema: str = "ANALYTICS"
    snowflake_warehouse: str = "ETL_WH_DEV"
    snowflake_role: str = "ACCOUNTADMIN"
    snowflake_private_key_path: Path = Path.home() / ".ssh" / "snowflake_key.p8"

    # ========================================================================
    # AI/ML CONFIGURATION
    # ========================================================================
    openrouter_api_key: Optional[str] = None

    # ========================================================================
    # APPLICATION CONFIGURATION
    # ========================================================================
    # Cache TTL in seconds (overrides app constants if needed)
    cache_ttl_seconds: int = 300

    # Connection pool size
    connection_pool_size: int = 5

    # Debug mode
    debug: bool = False

    # Logging level
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="",
        env_nested_delimiter="__"
    )

    @field_validator('snowflake_private_key_path')
    @classmethod
    def validate_key_path(cls, v: Path) -> Path:
        """Validate that private key path exists."""
        if not v.exists():
            raise ValueError(f"Snowflake private key not found at {v}")
        return v

    @model_validator(mode='after')
    def set_environment_defaults(self):
        """Set environment-specific defaults based on environment."""
        env = self.environment

        # Set database based on environment
        if env == "dev":
            if self.snowflake_database == "APEXML_DEV":  # Only set if using default
                pass  # Already correct
            if self.snowflake_warehouse == "ETL_WH_DEV":
                pass  # Already correct
        elif env == "staging":
            if self.snowflake_database == "APEXML_DEV":  # Using default, update for staging
                self.snowflake_database = "APEXML_STAGING"
            if self.snowflake_warehouse == "ETL_WH_DEV":
                self.snowflake_warehouse = "ETL_WH_STAGING"
        elif env == "prod":
            if self.snowflake_database == "APEXML_DEV":  # Using default, update for prod
                self.snowflake_database = "APEXML_PROD"
            if self.snowflake_warehouse == "ETL_WH_DEV":
                self.snowflake_warehouse = "ETL_WH_PROD"
            # In production, require explicit configuration
            if not self.snowflake_account or not self.snowflake_user:
                raise ValueError("SNOWFLAKE_ACCOUNT and SNOWFLAKE_USER must be set in production")

        return self

    @property
    def is_dev(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "dev"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.environment == "staging"

    @property
    def is_prod(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "prod"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance (singleton pattern).

    Returns:
        Settings: Singleton settings object

    Example:
        >>> from library.config import get_settings
        >>> settings = get_settings()
        >>> print(settings.snowflake_database)
        >>> if settings.is_prod:
        >>>     print("Running in production!")
    """
    return Settings()
