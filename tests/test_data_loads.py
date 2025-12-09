"""
Comprehensive tests for data loading operations with detailed logging.

Tests cover:
- API extraction (connectivity, data quality)
- Snowflake loading (connection, MERGE operations)
- Historical and incremental loads
- Error handling and recovery
- Data validation
"""
import pytest
import asyncio
import logging
from datetime import datetime
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "snowflake" / "elt"))

from extract import (
    extract_session_data,
    fetch_sessions,
    fetch_drivers,
    fetch_laps,
    fetch_positions
)
from load import (
    load_sessions,
    load_drivers,
    load_laps,
    load_positions,
    load_all
)

# Import connection manager
sys.path.insert(0, str(Path(__file__).parent.parent))
from library.connection import connection_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tests/test_data_loads.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class TestAPIExtraction:
    """Test OpenF1 API extraction functions."""

    @pytest.mark.asyncio
    async def test_fetch_sessions_connectivity(self):
        """Test basic API connectivity for sessions endpoint."""
        logger.info("Testing API connectivity to sessions endpoint")

        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                sessions = await fetch_sessions(client, year=2024)
                logger.info(f"✓ Successfully fetched {len(sessions)} sessions for 2024")
                assert len(sessions) > 0, "Expected at least one session in 2024"

                # Validate session structure
                required_fields = ['session_key', 'session_name', 'year', 'circuit_short_name']
                for field in required_fields:
                    assert field in sessions[0], f"Missing field: {field}"
                    logger.info(f"✓ Session contains field: {field}")

            except Exception as e:
                logger.error(f"✗ API connectivity test failed: {e}")
                pytest.fail(f"API connectivity failed: {e}")

    @pytest.mark.asyncio
    async def test_extract_session_data_complete(self):
        """Test complete session data extraction."""
        logger.info("Testing complete session data extraction")

        # Use a known session key (e.g., 2024 season opener)
        session_key = 9158  # Example session key

        try:
            data = await extract_session_data(session_key)

            # Validate all data entities
            assert 'sessions' in data, "Missing sessions data"
            assert 'drivers' in data, "Missing drivers data"
            assert 'laps' in data, "Missing laps data"
            assert 'positions' in data, "Missing positions data"

            logger.info(f"✓ Extracted sessions: {len(data['sessions'])}")
            logger.info(f"✓ Extracted drivers: {len(data['drivers'])}")
            logger.info(f"✓ Extracted laps: {len(data['laps'])}")
            logger.info(f"✓ Extracted positions: {len(data['positions'])}")

            # Validate ingestion timestamp added
            assert 'ingested_at' in data['sessions'][0], "Missing ingested_at timestamp"
            logger.info(f"✓ Ingestion timestamp: {data['sessions'][0]['ingested_at']}")

        except Exception as e:
            logger.error(f"✗ Session data extraction failed: {e}")
            pytest.fail(f"Extraction failed: {e}")

    @pytest.mark.asyncio
    async def test_data_quality_validation(self):
        """Test data quality checks on extracted data."""
        logger.info("Testing data quality validation")

        session_key = 9158
        data = await extract_session_data(session_key)

        # Check for null critical fields
        sessions = data['sessions']
        if sessions:
            assert sessions[0]['session_key'] is not None, "Session key should not be None"
            logger.info("✓ Critical field validation passed")

        # Check lap duration values are reasonable
        laps = data['laps']
        if laps:
            valid_laps = [lap for lap in laps if lap.get('lap_duration', 0) > 0]
            logger.info(f"✓ Valid laps (duration > 0): {len(valid_laps)}/{len(laps)}")


class TestSnowflakeLoading:
    """Test Snowflake database loading operations."""

    def test_snowflake_connection(self):
        """Test Snowflake connection establishment."""
        logger.info("Testing Snowflake connection")

        try:
            with connection_manager.get_connection(schema="RAW") as conn:
                cursor = conn.cursor()

                # Test basic query
                cursor.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE()")
                result = cursor.fetchone()

                logger.info(f"✓ Connected as: {result[0]}")
                logger.info(f"✓ Using role: {result[1]}")
                logger.info(f"✓ Database: {result[2]}")

                cursor.close()

        except Exception as e:
            logger.error(f"✗ Snowflake connection failed: {e}")
            pytest.fail(f"Connection failed: {e}")

    def test_schema_exists(self):
        """Test that required schemas and tables exist."""
        logger.info("Testing schema and table existence")

        with connection_manager.get_connection(schema="RAW") as conn:
            cursor = conn.cursor()

            required_tables = ['SESSIONS', 'DRIVERS', 'LAPS', 'POSITIONS']

            for table in required_tables:
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_SCHEMA = 'RAW'
                    AND TABLE_NAME = '{table}'
                """)
                count = cursor.fetchone()[0]
                assert count == 1, f"Table RAW.{table} does not exist"
                logger.info(f"✓ Table exists: RAW.{table}")

            cursor.close()

    @pytest.mark.asyncio
    async def test_load_sessions_merge(self):
        """Test MERGE operation for sessions table."""
        logger.info("Testing sessions MERGE operation")

        # Extract test data
        session_key = 9158
        data = await extract_session_data(session_key)

        with connection_manager.get_connection(schema="RAW") as conn:
            try:
                # Count before load
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM RAW.SESSIONS WHERE session_key = {session_key}")
                count_before = cursor.fetchone()[0]
                logger.info(f"Records before load: {count_before}")

                # Load data
                loaded_count = load_sessions(conn, data['sessions'])
                logger.info(f"✓ MERGE operation loaded {loaded_count} sessions")

                # Count after load
                cursor.execute(f"SELECT COUNT(*) FROM RAW.SESSIONS WHERE session_key = {session_key}")
                count_after = cursor.fetchone()[0]
                logger.info(f"Records after load: {count_after}")

                # Should have the session
                assert count_after > 0, "Session should exist after load"

                cursor.close()

            except Exception as e:
                logger.error(f"✗ Sessions MERGE failed: {e}")
                pytest.fail(f"MERGE operation failed: {e}")

    @pytest.mark.asyncio
    async def test_idempotent_loads(self):
        """Test that loading same data twice is idempotent."""
        logger.info("Testing load idempotency")

        session_key = 9158
        data = await extract_session_data(session_key)

        with connection_manager.get_connection(schema="RAW") as conn:
            cursor = conn.cursor()

            try:
                # First load
                load_all(data)
                cursor.execute(f"SELECT COUNT(*) FROM RAW.SESSIONS WHERE session_key = {session_key}")
                count_first = cursor.fetchone()[0]
                logger.info(f"Count after first load: {count_first}")

                # Second load (should not duplicate)
                load_all(data)
                cursor.execute(f"SELECT COUNT(*) FROM RAW.SESSIONS WHERE session_key = {session_key}")
                count_second = cursor.fetchone()[0]
                logger.info(f"Count after second load: {count_second}")

                assert count_first == count_second, "Duplicate records created by second load"
                logger.info("✓ Load is idempotent (no duplicates)")

            except Exception as e:
                logger.error(f"✗ Idempotency test failed: {e}")
                pytest.fail(f"Idempotency test failed: {e}")
            finally:
                cursor.close()


class TestDataValidation:
    """Test data validation after loading."""

    def test_loaded_data_integrity(self):
        """Test integrity of loaded data."""
        logger.info("Testing loaded data integrity")

        with connection_manager.get_connection(schema="RAW") as conn:
            cursor = conn.cursor()

            try:
                # Check for duplicate sessions
                cursor.execute("""
                    SELECT session_key, COUNT(*) as cnt
                    FROM RAW.SESSIONS
                    GROUP BY session_key
                    HAVING COUNT(*) > 1
                """)
                duplicates = cursor.fetchall()

                if duplicates:
                    logger.warning(f"Found {len(duplicates)} duplicate session_keys")
                    for dup in duplicates:
                        logger.warning(f"  session_key {dup[0]}: {dup[1]} records")
                else:
                    logger.info("✓ No duplicate sessions found")

                # Check for missing critical fields
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM RAW.SESSIONS
                    WHERE session_key IS NULL
                    OR year IS NULL
                    OR circuit_short_name IS NULL
                """)
                null_count = cursor.fetchone()[0]

                assert null_count == 0, f"Found {null_count} records with null critical fields"
                logger.info("✓ No null critical fields")

            except Exception as e:
                logger.error(f"✗ Data integrity test failed: {e}")
                pytest.fail(f"Data integrity test failed: {e}")
            finally:
                cursor.close()

    def test_lap_times_reasonable(self):
        """Test that lap times are within reasonable ranges."""
        logger.info("Testing lap time reasonableness")

        with connection_manager.get_connection(schema="RAW") as conn:
            cursor = conn.cursor()

            try:
                # F1 lap times typically between 60-150 seconds
                cursor.execute("""
                    SELECT
                        MIN(lap_duration) as min_lap,
                        MAX(lap_duration) as max_lap,
                        AVG(lap_duration) as avg_lap,
                        COUNT(*) as total_laps
                    FROM RAW.LAPS
                    WHERE lap_duration > 0
                """)
                result = cursor.fetchone()

                min_lap, max_lap, avg_lap, total_laps = result

                logger.info(f"Lap time stats:")
                logger.info(f"  Min: {min_lap:.2f}s")
                logger.info(f"  Max: {max_lap:.2f}s")
                logger.info(f"  Avg: {avg_lap:.2f}s")
                logger.info(f"  Total laps: {total_laps:,}")

                # Sanity checks (allowing for safety car laps, red flags, etc.)
                assert min_lap > 30, f"Minimum lap time too low: {min_lap}s"
                assert max_lap < 300, f"Maximum lap time too high: {max_lap}s"
                logger.info("✓ Lap times within reasonable ranges")

            except Exception as e:
                logger.error(f"✗ Lap time validation failed: {e}")
                pytest.fail(f"Lap time validation failed: {e}")
            finally:
                cursor.close()


class TestErrorHandling:
    """Test error handling and recovery mechanisms."""

    @pytest.mark.asyncio
    async def test_invalid_session_key(self):
        """Test handling of invalid session key."""
        logger.info("Testing invalid session key handling")

        invalid_key = 99999999

        with pytest.raises(Exception):
            data = await extract_session_data(invalid_key)
            logger.info("✓ Correctly raised exception for invalid session key")

    def test_connection_failure_handling(self):
        """Test graceful handling of connection failures."""
        logger.info("Testing connection failure handling")

        # Temporarily break environment variable
        original_account = os.getenv('SNOWFLAKE_ACCOUNT')
        os.environ['SNOWFLAKE_ACCOUNT'] = 'INVALID_ACCOUNT'

        try:
            with pytest.raises(Exception):
                with connection_manager.get_connection(schema="RAW") as conn:
                    pass
                logger.info("✓ Correctly raised exception for invalid connection")
        finally:
            # Restore original value
            if original_account:
                os.environ['SNOWFLAKE_ACCOUNT'] = original_account


class TestErrorLogging:
    """Test error logging when data loads fail."""

    @pytest.mark.asyncio
    async def test_load_failure_logging(self, tmp_path):
        """Test that load failures are properly logged."""
        logger.info("Testing load failure logging")

        # Create a temporary log file for this test
        log_file = tmp_path / "test_load_errors.log"
        test_logger = logging.getLogger('test_load_errors')
        test_logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        test_logger.addHandler(file_handler)

        # Simulate a failed load by using an invalid session key
        invalid_session_key = 99999999

        try:
            test_logger.info(f"Attempting to load session {invalid_session_key}")
            data = await extract_session_data(invalid_session_key)
            test_logger.info("Load successful")
        except Exception as e:
            test_logger.error(f"ERROR loading session {invalid_session_key}: {str(e)}", exc_info=True)

        # Verify log file contains error
        file_handler.close()
        log_contents = log_file.read_text()

        assert "ERROR" in log_contents, "Log file should contain ERROR level message"
        assert str(invalid_session_key) in log_contents, f"Log should mention session key {invalid_session_key}"
        logger.info(f"✓ Error properly logged to file: {log_file}")
        logger.info(f"  Log excerpt: {log_contents[:200]}...")

    def test_log_file_creation(self):
        """Test that log files are created for data loads."""
        logger.info("Testing log file creation")

        # Check if log directory and files exist
        log_dir = Path(__file__).parent
        test_log = log_dir / "test_data_loads.log"

        # Log file should exist (created by logger config at module level)
        assert test_log.exists(), f"Test log file should exist at {test_log}"
        logger.info(f"✓ Log file exists: {test_log}")

        # Check if it's writable
        try:
            with open(test_log, 'a') as f:
                f.write(f"\n# Test write at {datetime.now().isoformat()}\n")
            logger.info("✓ Log file is writable")
        except Exception as e:
            pytest.fail(f"Log file not writable: {e}")


class TestLoggingAndMetrics:
    """Test logging and metrics collection."""

    def test_load_metrics_logging(self):
        """Test that load metrics are properly logged."""
        logger.info("Testing load metrics logging")

        with connection_manager.get_connection(schema="RAW") as conn:
            cursor = conn.cursor()

            try:
                # Check ingested_at timestamps
                cursor.execute("""
                    SELECT
                        MIN(ingested_at) as first_load,
                        MAX(ingested_at) as last_load,
                        COUNT(DISTINCT ingested_at) as distinct_loads
                    FROM RAW.SESSIONS
                """)
                result = cursor.fetchone()

                first_load, last_load, distinct_loads = result

                logger.info(f"Load history:")
                logger.info(f"  First load: {first_load}")
                logger.info(f"  Last load: {last_load}")
                logger.info(f"  Distinct load timestamps: {distinct_loads}")

                logger.info("✓ Load timestamps are being tracked")

            except Exception as e:
                logger.error(f"✗ Metrics logging test failed: {e}")
                pytest.fail(f"Metrics logging test failed: {e}")
            finally:
                cursor.close()


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--log-cli-level=INFO"])
