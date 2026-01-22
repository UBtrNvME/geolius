"""Tests for Pydantic models."""

from datetime import datetime

import pytest

from geolius.models import (
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
        from geolius.ip_validator import validate_ip_address

        response = IpGeolocationResponse(
            ip="8.8.8.8",
            country="United States",
            country_code="US",
            query_timestamp=datetime.utcnow(),
        )
        assert response.ip == validate_ip_address("8.8.8.8")
        assert str(response.ip) == "8.8.8.8"
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


class TestErrorResponse:
    """Test ErrorResponse model."""

    def test_valid_error_response(self) -> None:
        """Test valid error response."""
        from geolius.models import ErrorDetail

        error = ErrorResponse(
            message="Invalid IP address format",
            details=[
                ErrorDetail(
                    loc=["path", "ip_address"],
                    msg="The IP address is invalid",
                    type="validation_error",
                )
            ],
        )
        assert error.message == "Invalid IP address format"
        assert len(error.details) == 1
        assert error.details[0].msg == "The IP address is invalid"
