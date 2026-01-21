"""IP geolocation service using MaxMind GeoLite2 database."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

import geoip2.database
import geoip2.errors
from pydantic import IPvAnyAddress

from geolius.config import settings
from geolius.exceptions import (
    ExternalApiError,
    InvalidIpAddressError,
    IpAddressNotFoundError,
)
from geolius.models import IpGeolocationResponse


class GeolocationService:
    """Service for retrieving IP geolocation data from MaxMind GeoLite2 database."""

    def __init__(
        self,
        city_db_path: Path | str | None = None,
        asn_db_path: Path | str | None = None,
    ) -> None:
        """
        Initialize the geolocation service.

        Args:
            city_db_path: Path to GeoLite2-City.mmdb file (defaults to settings)
            asn_db_path: Path to GeoLite2-ASN.mmdb file (defaults to settings)
        """
        self.city_db_path = Path(city_db_path) if city_db_path else settings.get_city_db_path()
        self.asn_db_path = Path(asn_db_path) if asn_db_path else settings.get_asn_db_path()
        self._city_reader: geoip2.database.Reader | None = None
        self._asn_reader: geoip2.database.Reader | None = None

    def _ensure_readers(self) -> None:
        """Ensure database readers are initialized."""
        if self._city_reader is None:
            if not self.city_db_path.exists():
                raise ExternalApiError(
                    f"MaxMind City database not found at {self.city_db_path}. "
                    "Please download GeoLite2-City.mmdb and place it in the data directory.",
                    status_code=503,
                )
            self._city_reader = geoip2.database.Reader(str(self.city_db_path))

        if self._asn_reader is None:
            if not self.asn_db_path.exists():
                # ASN database is optional, so we don't raise an error if it's missing
                # We'll just skip ASN/ISP data if it's not available
                pass
            else:
                self._asn_reader = geoip2.database.Reader(str(self.asn_db_path))

        print("DB type:", self._city_reader.metadata().database_type)
        print("DB desc:", self._city_reader.metadata().description)

    def _parse_city_response(
        self, city_response: geoip2.models.City, ip_address: IPvAnyAddress
    ) -> IpGeolocationResponse:
        """
        Parse MaxMind City response into our response model.

        Args:
            city_response: MaxMind City response object
            ip_address: The queried IP address

        Returns:
            IpGeolocationResponse object
        """
        # Get ASN/ISP data if available
        asn_number: str | None = None
        isp: str | None = None
        org: str | None = None

        if self._asn_reader:
            try:
                asn_response = self._asn_reader.asn(str(ip_address))
                asn_number = f"AS{asn_response.autonomous_system_number}" if asn_response.autonomous_system_number else None
                org = asn_response.autonomous_system_organization or None
            except (geoip2.errors.AddressNotFoundError, ValueError):
                # ASN data not available for this IP
                pass

        # Extract location data
        country = city_response.country.name or "Unknown"
        country_code = city_response.country.iso_code or ""
        print("Country:", city_response.country.name)
        print("Subdivisions:", city_response.subdivisions)
        print("City.names:", city_response.city.names)
        print("Lat/Lon:", city_response.location.latitude, city_response.location.longitude)
        print("Accuracy radius:", city_response.location.accuracy_radius)



        # Get region/subdivision (state/province)
        region: str | None = None
        region_code: str | None = None
        if city_response.subdivisions:
            # Get the most specific subdivision
            subdivision = city_response.subdivisions.most_specific
            region = subdivision.name
            region_code = subdivision.iso_code

        # Get city
        city: str | None = city_response.city.name if city_response.city.name else None

        # Get postal code
        postal_code: str | None = (
            city_response.postal.code if city_response.postal.code else None
        )

        # Get coordinates
        latitude: float | None = None
        longitude: float | None = None
        if city_response.location.latitude is not None:
            latitude = float(city_response.location.latitude)
        if city_response.location.longitude is not None:
            longitude = float(city_response.location.longitude)

        # Get timezone
        timezone: str | None = (
            city_response.location.time_zone if city_response.location.time_zone else None
        )

        return IpGeolocationResponse(
            ip=ip_address,
            country=country,
            country_code=country_code,
            region=region,
            region_code=region_code,
            city=city,
            postal_code=postal_code,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
            isp=isp,
            org=org,
            asn=asn_number,
            query_timestamp=datetime.utcnow(),
        )

    async def get_geolocation(self, ip_address: IPvAnyAddress) -> IpGeolocationResponse:
        """
        Get geolocation data for a single IP address.

        Args:
            ip_address: The IP address to look up

        Returns:
            IpGeolocationResponse with geolocation data

        Raises:
            InvalidIpAddressError: If IP address format is invalid
            IpAddressNotFoundError: If geolocation data is not found
            ExternalApiError: If database is unavailable
        """
        # Ensure readers are initialized
        self._ensure_readers()

        # Run database query in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        try:
            city_response = await loop.run_in_executor(
                None, self._city_reader.city, str(ip_address)
            )
        except geoip2.errors.AddressNotFoundError:
            raise IpAddressNotFoundError(
                ip_address,
                f"No geolocation data available for IP address: {ip_address}",
            )
        except Exception as e:
            raise ExternalApiError(
                f"Error querying geolocation database: {str(e)}", status_code=500
            ) from e
        return self._parse_city_response(city_response, ip_address)

    async def get_batch_geolocation(
        self, ip_addresses: list[IPvAnyAddress]
    ) -> tuple[list[IpGeolocationResponse], list[dict[str, str]]]:
        """
        Get geolocation data for multiple IP addresses concurrently.

        Args:
            ip_addresses: List of IP addresses to look up

        Returns:
            Tuple of (successful results, errors)
        """
        # Create tasks for concurrent lookups
        tasks = [self._get_geolocation_with_error_handling(ip) for ip in ip_addresses]

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=False)

        # Separate successful results from errors
        successful_results: list[IpGeolocationResponse] = []
        errors: list[dict[str, str]] = []

        for ip, result in zip(ip_addresses, results, strict=True):
            if isinstance(result, IpGeolocationResponse):
                successful_results.append(result)
            else:
                error_type, error_detail = result
                errors.append(
                    {"ip": str(ip), "error": error_type, "detail": error_detail}
                )

        return successful_results, errors

    async def _get_geolocation_with_error_handling(
        self, ip_address: IPvAnyAddress
    ) -> IpGeolocationResponse | tuple[str, str]:
        """
        Get geolocation with error handling, returning error tuple instead of raising.

        Args:
            ip_address: The IP address to look up

        Returns:
            IpGeolocationResponse on success, or (error_type, error_detail) tuple on failure
        """
        try:
            return await self.get_geolocation(ip_address)
        except InvalidIpAddressError as e:
            return ("Invalid IP address format", str(e))
        except IpAddressNotFoundError as e:
            return ("IP address not found", str(e))
        except ExternalApiError as e:
            return ("Database error", str(e))
        except Exception as e:
            return ("Internal error", f"Unexpected error: {str(e)}")

    def close(self) -> None:
        """Close database readers."""
        if self._city_reader:
            self._city_reader.close()
            self._city_reader = None
        if self._asn_reader:
            self._asn_reader.close()
            self._asn_reader = None

    async def __aenter__(self) -> "GeolocationService":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        self.close()
