"""Single source of truth for Snowflake connections with connection pooling.

This module provides a singleton connection manager that all parts of the
application should use to connect to Snowflake. It implements connection
pooling for better performance and resource management.

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
from typing import Optional, Dict
from queue import Queue, Empty
import threading
import snowflake.connector
from snowflake.connector import SnowflakeConnection
from library.config import get_settings
from library.exceptions import SnowflakeConnectionError
from library.error_handling import setup_logger, DatabaseError

# Setup logger
logger = setup_logger(__name__)


class SnowflakeConnectionManager:
    """Manages Snowflake connections with connection pooling and automatic cleanup.

    Connection pooling reduces overhead by reusing connections instead of
    creating new ones for each query. This improves performance especially
    for web applications with multiple concurrent users.
    """

    def __init__(self, pool_size: int = 5):
        """Initialize connection manager with settings and connection pool.

        Args:
            pool_size: Maximum number of connections to pool (default: 5)
        """
        self.settings = get_settings()
        self.pool_size = pool_size
        self._pool: Queue = Queue(maxsize=pool_size)
        self._pool_lock = threading.Lock()
        self._total_connections = 0

        logger.info(f"Initialized connection manager with pool size: {pool_size}")

    def _create_connection(
        self,
        role: Optional[str] = None,
        schema: Optional[str] = None,
        database: Optional[str] = None,
        warehouse: Optional[str] = None
    ) -> SnowflakeConnection:
        """Create a new Snowflake connection.

        Args:
            role: Optional role to use
            schema: Optional schema to use
            database: Optional database to use
            warehouse: Optional warehouse to use

        Returns:
            Active Snowflake connection

        Raises:
            DatabaseError: If connection fails
        """
        try:
            logger.debug(f"Creating new connection to database: {database or self.settings.snowflake_database}")

            conn = snowflake.connector.connect(
                account=self.settings.snowflake_account,
                user=self.settings.snowflake_user,
                authenticator='SNOWFLAKE_JWT',
                private_key_file=str(self.settings.snowflake_private_key_path),
                database=database or self.settings.snowflake_database,
                schema=schema or self.settings.snowflake_schema,
                warehouse=warehouse or self.settings.snowflake_warehouse,
                role=role or self.settings.snowflake_role,
                client_session_keep_alive=True  # Keep connection alive
            )

            with self._pool_lock:
                self._total_connections += 1

            logger.debug(f"Connection created successfully (total: {self._total_connections})")
            return conn

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

    def _get_pooled_connection(
        self,
        role: Optional[str] = None,
        schema: Optional[str] = None,
        database: Optional[str] = None,
        warehouse: Optional[str] = None
    ) -> SnowflakeConnection:
        """Get a connection from the pool or create a new one.

        Args:
            role: Optional role to use
            schema: Optional schema to use
            database: Optional database to use
            warehouse: Optional warehouse to use

        Returns:
            Active Snowflake connection
        """
        # Try to get from pool (non-blocking)
        try:
            conn = self._pool.get_nowait()
            # Test if connection is still valid
            if conn and not conn.is_closed():
                logger.debug("Reusing connection from pool")
                return conn
            else:
                logger.debug("Connection from pool was closed, creating new one")
        except Empty:
            logger.debug("No connections available in pool, creating new one")

        # Create new connection if pool is empty or connection was invalid
        return self._create_connection(role, schema, database, warehouse)

    def _return_to_pool(self, conn: SnowflakeConnection) -> None:
        """Return a connection to the pool if it's still valid.

        Args:
            conn: Connection to return to pool
        """
        if conn and not conn.is_closed():
            try:
                self._pool.put_nowait(conn)
                logger.debug("Connection returned to pool")
            except:
                # Pool is full, close the connection
                logger.debug("Pool is full, closing connection")
                try:
                    conn.close()
                    with self._pool_lock:
                        self._total_connections -= 1
                except Exception as e:
                    logger.warning(f"Error closing connection: {e}")
        else:
            logger.debug("Connection was closed, not returning to pool")
            with self._pool_lock:
                if self._total_connections > 0:
                    self._total_connections -= 1

    @contextmanager
    def get_connection(
        self,
        role: Optional[str] = None,
        schema: Optional[str] = None,
        database: Optional[str] = None,
        warehouse: Optional[str] = None
    ) -> SnowflakeConnection:
        """
        Get Snowflake connection from pool with automatic cleanup.

        This method uses connection pooling to reuse existing connections
        when possible, improving performance for repeated queries.

        Args:
            role: Optional role to use (default: from settings)
            schema: Optional schema to use (default: from settings)
            database: Optional database to use (default: from settings)
            warehouse: Optional warehouse to use (default: from settings)

        Yields:
            SnowflakeConnection: Active Snowflake connection from pool

        Raises:
            DatabaseError: If connection fails

        Example:
            >>> with connection_manager.get_connection() as conn:
            ...     cursor = conn.cursor()
            ...     cursor.execute("SELECT CURRENT_USER()")
            ...     user = cursor.fetchone()[0]
            ...     cursor.close()
        """
        conn = None
        try:
            # Get connection from pool or create new one
            conn = self._get_pooled_connection(role, schema, database, warehouse)
            yield conn

        except Exception as e:
            # If we got an error, close the connection (don't return to pool)
            if conn:
                try:
                    conn.close()
                    with self._pool_lock:
                        if self._total_connections > 0:
                            self._total_connections -= 1
                except Exception:
                    pass
            raise

        finally:
            # Return connection to pool if it's still valid
            if conn:
                self._return_to_pool(conn)

    def close_all_connections(self) -> None:
        """Close all pooled connections. Useful for cleanup."""
        logger.info("Closing all pooled connections")
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                if conn and not conn.is_closed():
                    conn.close()
                    with self._pool_lock:
                        if self._total_connections > 0:
                            self._total_connections -= 1
            except Empty:
                break
            except Exception as e:
                logger.warning(f"Error closing pooled connection: {e}")

        logger.info(f"All connections closed. Total connections remaining: {self._total_connections}")

    def get_pool_status(self) -> Dict[str, int]:
        """Get current connection pool status.

        Returns:
            Dictionary with pool statistics
        """
        return {
            "pool_size": self.pool_size,
            "available_connections": self._pool.qsize(),
            "total_connections": self._total_connections,
            "active_connections": self._total_connections - self._pool.qsize()
        }


# Singleton instance - import this in other modules
# Pool size is loaded from settings
_settings = get_settings()
connection_manager = SnowflakeConnectionManager(pool_size=_settings.connection_pool_size)
