"""Tests for Pydantic models."""

from datetime import datetime

import pytest

from geolius.models import (
    BatchIpError,
    BatchIpGeolocationResponse,
    BatchIpRequest,
    ErrorResponse,
    HealthResponse,
    IpGeolocationResponse,
)


class TestHealthResponse:
    """Test HealthResponse model."""

    def test_valid_health_response(self) -> None:
        """Test valid health response."""
        response = HealthResponse(status="healthy", timestamp=datetime.utcnow())
        assert response.status == "healthy"
        assert isinstance(response.timestamp, datetime)


class TestIpGeolocationResponse:
    """Test IpGeolocationResponse model."""

    def test_valid_response(self) -> None:
        """Test valid geolocation response."""
        response = IpGeolocationResponse(
            ip="8.8.8.8",
            country="United States",
            country_code="US",
            query_timestamp=datetime.utcnow(),
        )
        assert response.ip == "8.8.8.8"
        assert response.country == "United States"
        assert response.country_code == "US"

    def test_minimal_response(self) -> None:
        """Test response with only required fields."""
        response = IpGeolocationResponse(
            ip="8.8.8.8",
            country="United States",
            country_code="US",
            query_timestamp=datetime.utcnow(),
        )
        assert response.region is None
        assert response.city is None

    def test_coordinate_validation(self) -> None:
        """Test coordinate validation."""
        # Valid coordinates
        response = IpGeolocationResponse(
            ip="8.8.8.8",
            country="United States",
            country_code="US",
            latitude=37.4056,
            longitude=-122.0775,
            query_timestamp=datetime.utcnow(),
        )
        assert response.latitude == 37.4056
        assert response.longitude == -122.0775

        # Invalid latitude
        with pytest.raises(Exception):  # Pydantic validation error
            IpGeolocationResponse(
                ip="8.8.8.8",
                country="United States",
                country_code="US",
                latitude=100.0,  # Invalid
                query_timestamp=datetime.utcnow(),
            )


class TestBatchIpRequest:
    """Test BatchIpRequest model."""

    def test_valid_request(self) -> None:
        """Test valid batch request."""
        request = BatchIpRequest(ip_addresses=["8.8.8.8", "1.1.1.1"])
        assert len(request.ip_addresses) == 2

    def test_empty_list(self) -> None:
        """Test empty list validation."""
        with pytest.raises(Exception):  # Pydantic validation error
            BatchIpRequest(ip_addresses=[])

    def test_too_many_ips(self) -> None:
        """Test too many IPs validation."""
        with pytest.raises(Exception):  # Pydantic validation error
            BatchIpRequest(ip_addresses=[f"8.8.8.{i}" for i in range(101)])


class TestBatchIpGeolocationResponse:
    """Test BatchIpGeolocationResponse model."""

    def test_valid_response(self) -> None:
        """Test valid batch response."""
        results = [
            IpGeolocationResponse(
                ip="8.8.8.8",
                country="United States",
                country_code="US",
                query_timestamp=datetime.utcnow(),
            )
        ]
        errors = [BatchIpError(ip="192.168.1.1", error="Not found")]

        response = BatchIpGeolocationResponse(results=results, errors=errors)
        assert len(response.results) == 1
        assert len(response.errors) == 1


class TestErrorResponse:
    """Test ErrorResponse model."""

    def test_valid_error_response(self) -> None:
        """Test valid error response."""
        error = ErrorResponse(
            error="Invalid IP address format",
            detail="The IP address is invalid",
            status_code=400,
        )
        assert error.error == "Invalid IP address format"
        assert error.status_code == 400
