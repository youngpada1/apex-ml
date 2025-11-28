"""Custom exceptions for the Apex ML application."""


class ApexMLError(Exception):
    """Base exception for Apex ML."""
    pass


class SnowflakeConnectionError(ApexMLError):
    """Raised when Snowflake connection fails."""
    pass


class APIError(ApexMLError):
    """Raised when OpenF1 API call fails."""
    pass


class DataValidationError(ApexMLError):
    """Raised when data validation fails."""
    pass


class ConfigurationError(ApexMLError):
    """Raised when configuration is invalid."""
    pass
