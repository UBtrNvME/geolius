"""API routes for IP geolocation service."""

from fastapi import APIRouter, Depends, Request

from geolius.dependencies import get_geolocation_service
from geolius.geolocation_service import GeolocationService
from geolius.ip_validator import validate_ip_address
from geolius.models import (
    ErrorResponse,
    HealthResponse,
    IpGeolocationResponse,
)

router = APIRouter()

# Module-level dependency to avoid Ruff B008 warning
_geolocation_service_dependency = Depends(get_geolocation_service)


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns the health status of the API service.
    """
    from datetime import UTC, datetime

    return HealthResponse(status="healthy", timestamp=datetime.now(UTC))


def get_client_ip(request: Request) -> str:
    """
    Get the client IP address from the request.

    Checks X-Forwarded-For header first (for proxied requests),
    then X-Real-IP, and finally falls back to the direct client host.
    """
    # Check X-Forwarded-For header (most common for proxied requests)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded_for.split(",")[0].strip()

    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fall back to direct client connection
    if request.client:
        return request.client.host

    # Last resort
    return "127.0.0.1"


@router.get(
    "/ip",
    response_model=IpGeolocationResponse,
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
        404: {"model": ErrorResponse, "description": "IP address not found"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    },
    tags=["Geolocation"],
)
async def get_requester_ip_geolocation(
    request: Request,
    service: GeolocationService = _geolocation_service_dependency,
) -> IpGeolocationResponse:
    """
    Get geolocation for the requester's IP address.

    Retrieves geolocation information for the IP address of the client making the request.
    Supports both IPv4 and IPv6 addresses.
    """
    client_ip = get_client_ip(request)
    _ip_address = validate_ip_address(client_ip)
    return await service.get_geolocation(_ip_address)


@router.get(
    "/ip/{ip_address}",
    response_model=IpGeolocationResponse,
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
        404: {"model": ErrorResponse, "description": "IP address not found"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    },
    tags=["Geolocation"],
)
async def get_ip_geolocation(
    ip_address: str,
    service: GeolocationService = _geolocation_service_dependency,
) -> IpGeolocationResponse:
    """
    Get geolocation for a specific IP address.

    Retrieves geolocation information for a single IP address.
    Supports both IPv4 and IPv6 addresses.
    """
    _ip_address = validate_ip_address(ip_address)
    return await service.get_geolocation(_ip_address)
