"""Integration tests for API routes."""

from collections.abc import Generator
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from geolius.dependencies import get_geolocation_service
from geolius.exceptions import IpAddressNotFoundError
from geolius.geolocation_service import GeolocationService
from geolius.ip_validator import validate_ip_address
from geolius.main import app
from geolius.models import IpGeolocationResponse

client = TestClient(app)


@pytest.fixture
def mock_geolocation_service() -> AsyncMock:
    """Create a mock geolocation service for testing."""
    return AsyncMock(spec=GeolocationService)


@pytest.fixture(autouse=True)
def cleanup_dependency_overrides() -> Generator[None, None, None]:
    """Automatically clean up dependency overrides after each test."""
    yield
    app.dependency_overrides.clear()


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self) -> None:
        """Test health check returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestIpGeolocationEndpoint:
    """Test single IP geolocation endpoint."""

    def test_get_ip_geolocation_success(
        self, mock_geolocation_service: AsyncMock
    ) -> None:
        """Test successful IP geolocation lookup."""
        mock_response = IpGeolocationResponse(
            ip=validate_ip_address("8.8.8.8"),
            country="United States",
            country_code="US",
            region="California",
            region_code="CA",
            city="Mountain View",
            postal_code="94043",
            latitude=37.4056,
            longitude=-122.0775,
            timezone="America/Los_Angeles",
            isp="Google LLC",
            org="Google Public DNS",
            asn="AS15169",
            query_timestamp=datetime.now(timezone.utc),
        )

        mock_geolocation_service.get_geolocation = AsyncMock(return_value=mock_response)

        # Override the dependency
        app.dependency_overrides[get_geolocation_service] = (
            lambda: mock_geolocation_service
        )

        response = client.get("/ip/8.8.8.8")
        assert response.status_code == 200
        data = response.json()
        assert data["ip"] == "8.8.8.8"
        assert data["country"] == "United States"

    def test_get_ip_geolocation_invalid_ip(
        self, mock_geolocation_service: AsyncMock
    ) -> None:
        """Test IP geolocation with invalid IP."""
        # Override the dependency (service won't be called due to validation error)
        app.dependency_overrides[get_geolocation_service] = (
            lambda: mock_geolocation_service
        )

        # Invalid IP will be caught by validation before reaching the service
        response = client.get("/ip/invalid-ip")
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "message" in data
        assert "details" in data

    def test_get_ip_geolocation_not_found(
        self, mock_geolocation_service: AsyncMock
    ) -> None:
        """Test IP geolocation when IP not found."""
        mock_geolocation_service.get_geolocation = AsyncMock(
            side_effect=IpAddressNotFoundError(validate_ip_address("192.168.1.1"))
        )

        # Override the dependency
        app.dependency_overrides[get_geolocation_service] = (
            lambda: mock_geolocation_service
        )

        response = client.get("/ip/192.168.1.1")
        assert response.status_code == 404
        data = response.json()
        assert "message" in data
        assert "details" in data


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root(self) -> None:
        """Test root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
