"""Tests for geolocation service."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import geoip2.errors
import pytest

from geolius.exceptions import ExternalApiError, IpAddressNotFoundError
from geolius.geolocation_service import GeolocationService
from geolius.ip_validator import validate_ip_address
from geolius.models import IpGeolocationResponse


class TestGeolocationService:
    """Test geolocation service."""

    @pytest.fixture
    def mock_city_db_path(self, tmp_path: Path) -> Path:
        """Create a temporary mock database path."""
        db_path = tmp_path / "GeoLite2-City.mmdb"
        db_path.touch()
        return db_path

    @pytest.fixture
    def mock_asn_db_path(self, tmp_path: Path) -> Path:
        """Create a temporary mock ASN database path."""
        db_path = tmp_path / "GeoLite2-ASN.mmdb"
        db_path.touch()
        return db_path

    @pytest.fixture
    def service(
        self, mock_city_db_path: Path, mock_asn_db_path: Path
    ) -> GeolocationService:
        """Create a geolocation service instance."""
        return GeolocationService(
            city_db_path=mock_city_db_path, asn_db_path=mock_asn_db_path
        )

    def _create_mock_city_response(self) -> Mock:
        """Create a mock MaxMind City response."""
        mock_response = Mock()
        # Country
        mock_response.country.name = "United States"
        mock_response.country.iso_code = "US"
        # Subdivisions
        mock_subdivision = Mock()
        mock_subdivision.name = "California"
        mock_subdivision.iso_code = "CA"
        mock_subdivisions = Mock()
        mock_subdivisions.most_specific = mock_subdivision
        mock_response.subdivisions = mock_subdivisions
        # City
        mock_response.city.name = "Mountain View"
        # Postal
        mock_response.postal.code = "94043"
        # Location
        mock_response.location.latitude = 37.4056
        mock_response.location.longitude = -122.0775
        mock_response.location.time_zone = "America/Los_Angeles"
        return mock_response

    def _create_mock_asn_response(self) -> Mock:
        """Create a mock MaxMind ASN response."""
        mock_response = Mock()
        mock_response.autonomous_system_number = 15169
        mock_response.autonomous_system_organization = "Google LLC"
        return mock_response

    @pytest.mark.asyncio
    async def test_get_geolocation_success(
        self, service: GeolocationService, mock_city_db_path: Path
    ) -> None:
        """Test successful geolocation lookup."""
        mock_city_response = self._create_mock_city_response()

        with patch("geoip2.database.Reader") as mock_reader_class:
            mock_reader = Mock()
            mock_reader.city.return_value = mock_city_response
            mock_reader_class.return_value = mock_reader

            # Initialize service with mocked readers
            service._city_reader = mock_reader
            service._asn_reader = None  # No ASN data for this test

            result = await service.get_geolocation(validate_ip_address("8.8.8.8"))

            assert isinstance(result, IpGeolocationResponse)
            assert str(result.ip) == "8.8.8.8"
            assert result.country == "United States"
            assert result.country_code == "US"
            assert result.region == "California"
            assert result.region_code == "CA"
            assert result.city == "Mountain View"
            assert result.postal_code == "94043"
            assert result.latitude == 37.4056
            assert result.longitude == -122.0775
            assert result.timezone == "America/Los_Angeles"

    @pytest.mark.asyncio
    async def test_get_geolocation_with_asn(
        self,
        service: GeolocationService,
        mock_city_db_path: Path,
        mock_asn_db_path: Path,
    ) -> None:
        """Test geolocation lookup with ASN data."""
        mock_city_response = self._create_mock_city_response()
        mock_asn_response = self._create_mock_asn_response()

        with patch("geoip2.database.Reader") as mock_reader_class:
            mock_city_reader = Mock()
            mock_city_reader.city.return_value = mock_city_response
            mock_asn_reader = Mock()
            mock_asn_reader.asn.return_value = mock_asn_response
            mock_reader_class.return_value = mock_city_reader

            # Initialize service with mocked readers
            service._city_reader = mock_city_reader
            service._asn_reader = mock_asn_reader

            result = await service.get_geolocation(validate_ip_address("8.8.8.8"))

            assert result.asn == "AS15169"
            assert result.org == "Google LLC"

    @pytest.mark.asyncio
    async def test_get_geolocation_not_found(
        self, service: GeolocationService, mock_city_db_path: Path
    ) -> None:
        """Test geolocation lookup when IP not found."""

        with patch("geoip2.database.Reader") as mock_reader_class:
            mock_reader = Mock()
            mock_reader.city.side_effect = geoip2.errors.AddressNotFoundError(
                "Not found"
            )
            mock_reader_class.return_value = mock_reader

            # Initialize service with mocked reader
            service._city_reader = mock_reader
            service._asn_reader = None

            with pytest.raises(IpAddressNotFoundError):
                await service.get_geolocation(validate_ip_address("192.168.1.1"))

    def test_initialize_database_not_found(self, tmp_path: Path) -> None:
        """Test error when database file doesn't exist during initialization."""
        non_existent_db = tmp_path / "nonexistent.mmdb"
        service = GeolocationService(city_db_path=non_existent_db)

        with pytest.raises(ExternalApiError) as exc_info:
            service.initialize()
        assert exc_info.value.status_code == 503
        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_geolocation_database_error(
        self, service: GeolocationService, mock_city_db_path: Path
    ) -> None:
        """Test database error handling."""
        with patch("geoip2.database.Reader") as mock_reader_class:
            mock_reader = Mock()
            mock_reader.city.side_effect = Exception("Database error")
            mock_reader_class.return_value = mock_reader

            # Initialize service with mocked reader
            service._city_reader = mock_reader
            service._asn_reader = None

            with pytest.raises(ExternalApiError) as exc_info:
                await service.get_geolocation(validate_ip_address("8.8.8.8"))
            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_city_db_path: Path) -> None:
        """Test service as async context manager."""
        service = GeolocationService(city_db_path=mock_city_db_path)
        mock_city_reader = Mock()
        service._city_reader = mock_city_reader
        service._asn_reader = None

        async with service:
            assert service._city_reader is not None

        # Reader should be closed after context exit
        mock_city_reader.close.assert_called_once()

    def test_close(self, service: GeolocationService) -> None:
        """Test closing database readers."""
        mock_city_reader = Mock()
        mock_asn_reader = Mock()
        service._city_reader = mock_city_reader
        service._asn_reader = mock_asn_reader

        service.close()

        mock_city_reader.close.assert_called_once()
        mock_asn_reader.close.assert_called_once()
        assert service._city_reader is None
        assert service._asn_reader is None
