"""Single source of truth for Snowflake connections.

This module provides a singleton connection manager that all parts of the
application should use to connect to Snowflake.

Usage:
    from library.connection import connection_manager

    # Use as context manager (recommended)
    with connection_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()

    # With custom schema
    with connection_manager.get_connection(schema="RAW") as conn:
        # connection uses RAW schema
        pass
"""
from contextlib import contextmanager
from typing import Optional
import snowflake.connector
from snowflake.connector import SnowflakeConnection
from library.config import get_settings
from library.exceptions import SnowflakeConnectionError
from library.error_handling import setup_logger, DatabaseError

# Setup logger
logger = setup_logger(__name__)


class SnowflakeConnectionManager:
    """Manages Snowflake connections with automatic cleanup."""

    def __init__(self):
        """Initialize connection manager with settings."""
        self.settings = get_settings()

    @contextmanager
    def get_connection(
        self,
        role: Optional[str] = None,
        schema: Optional[str] = None,
        database: Optional[str] = None,
        warehouse: Optional[str] = None
    ) -> SnowflakeConnection:
        """
        Get Snowflake connection with automatic cleanup.

        Args:
            role: Optional role to use (default: from settings)
            schema: Optional schema to use (default: from settings)
            database: Optional database to use (default: from settings)
            warehouse: Optional warehouse to use (default: from settings)

        Yields:
            SnowflakeConnection: Active Snowflake connection

        Raises:
            SnowflakeConnectionError: If connection fails

        Example:
            >>> with connection_manager.get_connection() as conn:
            ...     cursor = conn.cursor()
            ...     cursor.execute("SELECT CURRENT_USER()")
            ...     user = cursor.fetchone()[0]
            ...     cursor.close()
        """
        conn = None
        try:
            if not self.settings.snowflake_account or not self.settings.snowflake_user:
                error_msg = "SNOWFLAKE_ACCOUNT and SNOWFLAKE_USER must be set in environment variables"
                logger.error(error_msg)
                raise DatabaseError(
                    error_msg,
                    user_message="Database configuration is incomplete. Please contact support."
                )

            logger.info(f"Connecting to Snowflake database: {database or self.settings.snowflake_database}")

            conn = snowflake.connector.connect(
                account=self.settings.snowflake_account,
                user=self.settings.snowflake_user,
                authenticator='SNOWFLAKE_JWT',
                private_key_file=str(self.settings.snowflake_private_key_path),
                database=database or self.settings.snowflake_database,
                schema=schema or self.settings.snowflake_schema,
                warehouse=warehouse or self.settings.snowflake_warehouse,
                role=role or self.settings.snowflake_role
            )

            logger.debug("Successfully connected to Snowflake")
            yield conn

        except snowflake.connector.errors.Error as e:
            logger.error(f"Snowflake connection error: {e}", exc_info=True)
            raise DatabaseError(
                f"Failed to connect to Snowflake: {e}",
                user_message="Unable to connect to database. Please try again later."
            ) from e

        except Exception as e:
            logger.error(f"Unexpected connection error: {e}", exc_info=True)
            raise DatabaseError(
                f"Unexpected error connecting to Snowflake: {e}",
                user_message="Database connection failed. Please contact support."
            ) from e

        finally:
            if conn:
                try:
                    conn.close()
                    logger.debug("Snowflake connection closed")
                except Exception as e:
                    logger.warning(f"Error closing connection: {e}")


# Singleton instance - import this in other modules
connection_manager = SnowflakeConnectionManager()
