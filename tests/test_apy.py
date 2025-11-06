import pytest
import httpx
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

BASE_URL = "https://api.openf1.org/v1"


class TestOpenF1API:
    """Tests for OpenF1 API connectivity and response validation"""

    @pytest.fixture
    def client(self):
        """Create httpx client with timeout"""
        return httpx.Client(timeout=10.0)

    def test_api_availability(self, client):
        """Test that the OpenF1 API is reachable"""
        logger.info("Testing API availability")
        try:
            response = client.get(f"{BASE_URL}/sessions", params={"limit": 1})
            logger.info(f"API response status: {response.status_code}")
            assert response.status_code == 200
            logger.info("✓ API is available")
        except httpx.TimeoutException as e:
            logger.error(f"API timeout: {e}")
            pytest.fail("API request timed out")
        except httpx.RequestError as e:
            logger.error(f"API request error: {e}")
            pytest.fail(f"Failed to connect to API: {e}")

    def test_sessions_endpoint(self, client):
        """Test sessions endpoint returns valid data"""
        logger.info("Testing /sessions endpoint")
        response = client.get(f"{BASE_URL}/sessions", params={"year": 2024, "limit": 5})

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Validate session structure
        session = data[0]
        required_fields = ["session_key", "session_name", "date_start", "year"]
        for field in required_fields:
            assert field in session, f"Missing required field: {field}"

        logger.info(f"✓ Sessions endpoint returned {len(data)} sessions")

    def test_drivers_endpoint(self, client):
        """Test drivers endpoint returns valid data"""
        logger.info("Testing /drivers endpoint")
        response = client.get(f"{BASE_URL}/drivers", params={"session_key": 9662, "limit": 5})

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        if len(data) > 0:
            driver = data[0]
            required_fields = ["driver_number", "full_name", "team_name"]
            for field in required_fields:
                assert field in driver, f"Missing required field: {field}"
            logger.info(f"✓ Drivers endpoint returned {len(data)} drivers")
        else:
            logger.warning("No drivers returned for session_key 9662")

    def test_laps_endpoint(self, client):
        """Test laps endpoint returns valid data"""
        logger.info("Testing /laps endpoint")
        response = client.get(f"{BASE_URL}/laps", params={"session_key": 9662, "limit": 10})

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        if len(data) > 0:
            lap = data[0]
            required_fields = ["session_key", "driver_number", "lap_number", "lap_duration"]
            for field in required_fields:
                assert field in lap, f"Missing required field: {field}"
            logger.info(f"✓ Laps endpoint returned {len(data)} laps")
        else:
            logger.warning("No laps returned for session_key 9662")

    def test_positions_endpoint(self, client):
        """Test positions endpoint returns valid data"""
        logger.info("Testing /position endpoint")
        response = client.get(f"{BASE_URL}/position", params={"session_key": 9662, "limit": 10})

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        if len(data) > 0:
            position = data[0]
            required_fields = ["session_key", "driver_number", "position"]
            for field in required_fields:
                assert field in position, f"Missing required field: {field}"
            logger.info(f"✓ Position endpoint returned {len(data)} positions")
        else:
            logger.warning("No positions returned for session_key 9662")

    def test_invalid_endpoint(self, client):
        """Test that invalid endpoints return 404"""
        logger.info("Testing invalid endpoint handling")
        response = client.get(f"{BASE_URL}/invalid_endpoint")
        assert response.status_code == 404
        logger.info("✓ Invalid endpoint correctly returns 404")

    def test_malformed_parameters(self, client):
        """Test API handles malformed parameters gracefully"""
        logger.info("Testing malformed parameters")
        response = client.get(f"{BASE_URL}/sessions", params={"year": "invalid"})

        # API should either return 400 or empty list
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
        logger.info("✓ Malformed parameters handled gracefully")

    def test_rate_limiting(self, client):
        """Test multiple rapid requests to check rate limiting"""
        logger.info("Testing rate limiting behavior")
        responses = []

        for i in range(5):
            response = client.get(f"{BASE_URL}/sessions", params={"limit": 1})
            responses.append(response.status_code)
            logger.debug(f"Request {i+1}: {response.status_code}")

        # All requests should succeed (OpenF1 is generally permissive)
        assert all(status == 200 for status in responses)
        logger.info("✓ Rate limiting test passed (5 rapid requests)")

    def test_response_time(self, client):
        """Test that API responds within acceptable time"""
        logger.info("Testing API response time")
        start_time = datetime.now()
        response = client.get(f"{BASE_URL}/sessions", params={"limit": 1})
        elapsed = (datetime.now() - start_time).total_seconds()

        assert response.status_code == 200
        assert elapsed < 5.0, f"API response too slow: {elapsed}s"
        logger.info(f"✓ API responded in {elapsed:.2f}s")

    def test_empty_result_handling(self, client):
        """Test API behavior with queries that return no results"""
        logger.info("Testing empty result handling")
        response = client.get(f"{BASE_URL}/sessions", params={"year": 1900})

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
        logger.info("✓ Empty results handled correctly")

        