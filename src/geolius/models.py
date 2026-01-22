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


class IpRequestInternal(BaseModel):
    """IP geolocation request model."""

    ip_address: IPvAnyAddress = Field(
        ...,
        description="The IP address to look up",
    )


class ErrorDetail(BaseModel):
    loc: list[str | int]
    msg: str
    type: str


class ErrorResponse(BaseModel):
    message: str
    details: list[ErrorDetail]
