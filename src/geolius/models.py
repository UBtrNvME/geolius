"""Pydantic models for request and response validation."""

from datetime import datetime

from pydantic import BaseModel, Field
from pydantic.networks import IPvAnyAddress


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Health status of the service")
    timestamp: datetime = Field(..., description="Current server timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {"status": "healthy", "timestamp": "2024-01-15T10:30:00Z"}
        }
    }


class IpGeolocationResponse(BaseModel):
    """IP geolocation response model."""

    ip: IPvAnyAddress = Field(..., description="The queried IP address")
    country: str = Field(..., description="Full country name")
    country_code: str = Field(
        ..., description="ISO 3166-1 alpha-2 country code", min_length=2, max_length=2
    )
    region: str | None = Field(None, description="Region or state name")
    region_code: str | None = Field(None, description="Region or state code")
    city: str | None = Field(None, description="City name")
    postal_code: str | None = Field(None, description="Postal or ZIP code")
    latitude: float | None = Field(
        None, description="Latitude coordinate", ge=-90, le=90
    )
    longitude: float | None = Field(
        None, description="Longitude coordinate", ge=-180, le=180
    )
    timezone: str | None = Field(None, description="IANA timezone identifier")
    isp: str | None = Field(None, description="Internet Service Provider name")
    org: str | None = Field(None, description="Organization name")
    asn: str | None = Field(None, description="Autonomous System Number")
    query_timestamp: datetime = Field(
        ..., description="Timestamp when the query was made"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "ip": "8.8.8.8",
                "country": "United States",
                "country_code": "US",
                "region": "California",
                "region_code": "CA",
                "city": "Mountain View",
                "postal_code": "94043",
                "latitude": 37.4056,
                "longitude": -122.0775,
                "timezone": "America/Los_Angeles",
                "isp": "Google LLC",
                "org": "Google Public DNS",
                "asn": "AS15169",
                "query_timestamp": "2024-01-15T10:30:00Z",
            }
        }
    }


class BatchIpRequest(BaseModel):
    """Batch IP geolocation request model."""

    ip_addresses: list[IPvAnyAddress] = Field(
        ...,
        description="Array of IP addresses to look up",
        min_length=1,
        max_length=100,
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "ip_addresses": ["8.8.8.8", "1.1.1.1"],
            }
        }
    }

class IpRequestInternal(BaseModel):
    """IP geolocation request model."""

    ip_address: IPvAnyAddress = Field(
        ...,
        description="The IP address to look up",
    )

class BatchIpError(BaseModel):
    """Error model for batch IP geolocation failures."""

    ip: str = Field(..., description="The IP address that failed")
    error: str = Field(..., description="Error type")
    detail: str | None = Field(None, description="Detailed error message")

    model_config = {
        "json_schema_extra": {
            "example": {
                "ip": "192.168.1.1",
                "error": "IP address not found",
                "detail": "No geolocation data available for private IP address",
            }
        }
    }


class BatchIpGeolocationResponse(BaseModel):
    """Batch IP geolocation response model."""

    results: list[IpGeolocationResponse] = Field(
        ..., description="Array of successful geolocation lookups"
    )
    errors: list[BatchIpError] = Field(
        ..., description="Array of failed lookups with error details"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "results": [
                    {
                        "ip": "8.8.8.8",
                        "country": "United States",
                        "country_code": "US",
                        "query_timestamp": "2024-01-15T10:30:00Z",
                    }
                ],
                "errors": [
                    {
                        "ip": "192.168.1.1",
                        "error": "IP address not found",
                        "detail": "No geolocation data available for private IP address",
                    }
                ],
            }
        }
    }


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error type or message")
    detail: str | None = Field(None, description="Detailed error message")
    status_code: int = Field(..., description="HTTP status code")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "Invalid IP address format",
                "detail": "The provided IP address 'invalid-ip' is not a valid IPv4 or IPv6 address",
                "status_code": 400,
            }
        }
    }
