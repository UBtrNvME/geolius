"""Integration tests for API routes."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from geolius.main import app

client = TestClient(app)


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

    @pytest.mark.asyncio
    @patch("geolius.routes.GeolocationService")
    async def test_get_ip_geolocation_success(self, mock_service_class: type) -> None:
        """Test successful IP geolocation lookup."""
        from datetime import datetime

        from geolius.models import IpGeolocationResponse

        mock_response = IpGeolocationResponse(
            ip="8.8.8.8",
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
            query_timestamp=datetime.utcnow(),
        )

        mock_service = AsyncMock()
        mock_service.__aenter__ = AsyncMock(return_value=mock_service)
        mock_service.__aexit__ = AsyncMock(return_value=None)
        mock_service.get_geolocation = AsyncMock(return_value=mock_response)
        mock_service_class.return_value = mock_service

        response = client.get("/ip/8.8.8.8")
        assert response.status_code == 200
        data = response.json()
        assert data["ip"] == "8.8.8.8"
        assert data["country"] == "United States"

    def test_get_ip_geolocation_invalid_ip(self) -> None:
        """Test IP geolocation with invalid IP."""
        with patch("geolius.routes.GeolocationService") as mock_service_class:
            from geolius.exceptions import InvalidIpAddressError

            mock_service = AsyncMock()
            mock_service.__aenter__ = AsyncMock(return_value=mock_service)
            mock_service.__aexit__ = AsyncMock(return_value=None)
            mock_service.get_geolocation = AsyncMock(
                side_effect=InvalidIpAddressError("invalid-ip")
            )
            mock_service_class.return_value = mock_service

            response = client.get("/ip/invalid-ip")
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data

    def test_get_ip_geolocation_not_found(self) -> None:
        """Test IP geolocation when IP not found."""
        with patch("geolius.routes.GeolocationService") as mock_service_class:
            from geolius.exceptions import IpAddressNotFoundError

            mock_service = AsyncMock()
            mock_service.__aenter__ = AsyncMock(return_value=mock_service)
            mock_service.__aexit__ = AsyncMock(return_value=None)
            mock_service.get_geolocation = AsyncMock(
                side_effect=IpAddressNotFoundError("192.168.1.1")
            )
            mock_service_class.return_value = mock_service

            response = client.get("/ip/192.168.1.1")
            assert response.status_code == 404



class TestBatchIpGeolocationEndpoint:
    """Test batch IP geolocation endpoint."""

    def test_get_batch_ip_geolocation_success(self) -> None:
        """Test successful batch IP geolocation lookup."""
        with patch("geolius.routes.GeolocationService") as mock_service_class:
            from datetime import datetime

            from geolius.models import IpGeolocationResponse

            mock_response1 = IpGeolocationResponse(
                ip="8.8.8.8",
                country="United States",
                country_code="US",
                query_timestamp=datetime.utcnow(),
            )
            mock_response2 = IpGeolocationResponse(
                ip="1.1.1.1",
                country="Australia",
                country_code="AU",
                query_timestamp=datetime.utcnow(),
            )

            mock_service = AsyncMock()
            mock_service.__aenter__ = AsyncMock(return_value=mock_service)
            mock_service.__aexit__ = AsyncMock(return_value=None)
            mock_service.get_batch_geolocation = AsyncMock(
                return_value=([mock_response1, mock_response2], [])
            )
            mock_service_class.return_value = mock_service

            response = client.post(
                "/ip/batch", json={"ip_addresses": ["8.8.8.8", "1.1.1.1"]}
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) == 2
            assert len(data["errors"]) == 0

    def test_get_batch_ip_geolocation_with_errors(self) -> None:
        """Test batch IP geolocation with some errors."""
        with patch("geolius.routes.GeolocationService") as mock_service_class:
            from datetime import datetime

            from geolius.models import IpGeolocationResponse

            mock_response = IpGeolocationResponse(
                ip="8.8.8.8",
                country="United States",
                country_code="US",
                query_timestamp=datetime.utcnow(),
            )

            errors = [
                {
                    "ip": "192.168.1.1",
                    "error": "IP address not found",
                    "detail": "Private IP",
                }
            ]

            mock_service = AsyncMock()
            mock_service.__aenter__ = AsyncMock(return_value=mock_service)
            mock_service.__aexit__ = AsyncMock(return_value=None)
            mock_service.get_batch_geolocation = AsyncMock(
                return_value=([mock_response], errors)
            )
            mock_service_class.return_value = mock_service

            response = client.post(
                "/ip/batch", json={"ip_addresses": ["8.8.8.8", "192.168.1.1"]}
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) == 1
            assert len(data["errors"]) == 1
            assert data["errors"][0]["ip"] == "192.168.1.1"

    def test_get_batch_ip_geolocation_invalid_request(self) -> None:
        """Test batch IP geolocation with invalid request."""
        # Too many IPs
        response = client.post(
            "/ip/batch",
            json={"ip_addresses": [f"8.8.8.{i}" for i in range(101)]},
        )
        assert response.status_code == 422  # Validation error

        # Empty list
        response = client.post("/ip/batch", json={"ip_addresses": []})
        assert response.status_code == 422  # Validation error


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
