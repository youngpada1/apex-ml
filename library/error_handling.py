"""Error handling and retry logic for ApexML.

This module provides:
- Custom exception classes for different error types
- Retry decorators for handling transient failures
- Logging utilities
- User-friendly error message formatting
"""
import logging
import time
from functools import wraps
from typing import Callable, Type, Tuple, Optional, Any
import pandas as pd


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class ApexMLError(Exception):
    """Base exception for all ApexML errors."""

    def __init__(self, message: str, user_message: Optional[str] = None):
        """Initialize error with technical and user-friendly messages.

        Args:
            message: Technical error message for logging
            user_message: User-friendly message to display in UI
        """
        self.message = message
        self.user_message = user_message or message
        super().__init__(message)


class DatabaseError(ApexMLError):
    """Database connection or query errors."""
    pass


class DataNotFoundError(ApexMLError):
    """Requested data not found in database."""
    pass


class MLModelError(ApexMLError):
    """Machine learning model training or prediction errors."""
    pass


class ConfigurationError(ApexMLError):
    """Configuration or environment setup errors."""
    pass


class APIError(ApexMLError):
    """External API call errors (OpenRouter, etc.)."""
    pass


# ============================================================================
# RETRY DECORATOR
# ============================================================================

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    logger: Optional[logging.Logger] = None
) -> Callable:
    """Decorator to retry function calls on transient failures.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry (exponential backoff)
        exceptions: Tuple of exception types to catch and retry
        logger: Logger instance for logging retry attempts

    Returns:
        Decorated function with retry logic

    Example:
        @retry(max_attempts=3, delay=1.0, exceptions=(DatabaseError,))
        def query_database():
            # This will retry up to 3 times if DatabaseError occurs
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        # Last attempt failed, re-raise
                        if logger:
                            logger.error(
                                f"{func.__name__} failed after {max_attempts} attempts: {e}"
                            )
                        raise

                    # Log retry attempt
                    if logger:
                        logger.warning(
                            f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                            f"Retrying in {current_delay}s..."
                        )

                    # Wait before retry
                    time.sleep(current_delay)
                    current_delay *= backoff

            # Should never reach here, but just in case
            raise last_exception

        return wrapper
    return decorator


# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """Setup a logger with consistent formatting.

    Args:
        name: Logger name (usually __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to

    Returns:
        Configured logger instance

    Example:
        logger = setup_logger(__name__, level="DEBUG")
        logger.info("Application started")
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger

    # Console handler with formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Optional file handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# ============================================================================
# ERROR MESSAGE FORMATTING
# ============================================================================

def format_user_error(error: Exception) -> str:
    """Format error for display to user.

    Args:
        error: Exception to format

    Returns:
        User-friendly error message

    Example:
        try:
            query_database()
        except Exception as e:
            st.error(format_user_error(e))
    """
    if isinstance(error, ApexMLError):
        return error.user_message

    # Map common error types to user-friendly messages
    error_type = type(error).__name__

    if "Connection" in error_type or "Timeout" in error_type:
        return (
            "Database connection error. Please check your network connection "
            "and try again. If the problem persists, contact support."
        )

    if "SQL" in error_type or "Query" in error_type:
        return (
            "There was an error executing your query. Please try again with "
            "different parameters or contact support if the issue persists."
        )

    if "API" in error_type or "HTTPError" in error_type:
        return (
            "Error communicating with external service. Please try again later."
        )

    # Generic error message
    return (
        f"An unexpected error occurred: {str(error)[:100]}. "
        "Please try again or contact support if the issue persists."
    )


def validate_dataframe(
    df: pd.DataFrame,
    required_columns: Optional[list] = None,
    min_rows: int = 0
) -> None:
    """Validate DataFrame meets requirements.

    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        min_rows: Minimum number of rows required

    Raises:
        DataNotFoundError: If validation fails

    Example:
        validate_dataframe(df, required_columns=['driver_name', 'lap_time'], min_rows=1)
    """
    if df is None or df.empty:
        raise DataNotFoundError(
            "Query returned no data",
            user_message="No data found for your query. Try adjusting your filters."
        )

    if len(df) < min_rows:
        raise DataNotFoundError(
            f"Insufficient data: got {len(df)} rows, need at least {min_rows}",
            user_message=f"Found only {len(df)} records. Please try a broader search."
        )

    if required_columns:
        missing = set(required_columns) - set(df.columns)
        if missing:
            raise DataNotFoundError(
                f"Missing required columns: {missing}",
                user_message="Data structure mismatch. Please contact support."
            )


# ============================================================================
# SAFE EXECUTION WRAPPER
# ============================================================================

def safe_execute(
    func: Callable,
    *args: Any,
    default_value: Any = None,
    logger: Optional[logging.Logger] = None,
    **kwargs: Any
) -> Any:
    """Safely execute a function with error handling.

    Args:
        func: Function to execute
        *args: Positional arguments for function
        default_value: Value to return on error (default: None)
        logger: Logger for error logging
        **kwargs: Keyword arguments for function

    Returns:
        Function result or default_value on error

    Example:
        result = safe_execute(query_database, query="SELECT * FROM table", default_value=pd.DataFrame())
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if logger:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
        return default_value
