"""Test library/connection.py"""
import pytest
from library.connection import connection_manager
from library.exceptions import SnowflakeConnectionError


def test_connection_manager_creates_connection():
    """Test that connection manager can create connections."""
    with connection_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE()")
        result = cursor.fetchone()

        assert result is not None
        assert len(result) == 3

        user, role, database = result
        print(f"\n✓ Connected as: {user}")
        print(f"✓ Using role: {role}")
        print(f"✓ Database: {database}")

        cursor.close()


def test_connection_with_custom_schema():
    """Test connection with custom schema parameter."""
    with connection_manager.get_connection(schema="RAW") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_SCHEMA()")
        schema = cursor.fetchone()[0]

        assert schema == "RAW"
        print(f"\n✓ Using schema: {schema}")

        cursor.close()


def test_connection_cleanup():
    """Test that connections are properly closed."""
    with connection_manager.get_connection() as conn:
        # Connection should be active
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        assert cursor.fetchone()[0] == 1
        cursor.close()

    # After context manager exits, connection should be closed
    # Attempting to use it should fail
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        pytest.fail("Connection should be closed")
    except Exception:
        print("\n✓ Connection properly cleaned up")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
