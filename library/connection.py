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
                raise SnowflakeConnectionError(
                    "SNOWFLAKE_ACCOUNT and SNOWFLAKE_USER must be set in environment variables"
                )

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
            yield conn

        except snowflake.connector.errors.Error as e:
            raise SnowflakeConnectionError(f"Failed to connect to Snowflake: {e}") from e

        except Exception as e:
            raise SnowflakeConnectionError(f"Unexpected error connecting to Snowflake: {e}") from e

        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    # Ignore errors during cleanup
                    pass


# Singleton instance - import this in other modules
connection_manager = SnowflakeConnectionManager()
