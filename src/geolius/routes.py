"""API routes for IP geolocation service."""

from geolius.exceptions import (
    ExternalApiError,
    InvalidIpAddressError,
    IpAddressNotFoundError,
)
from geolius.geolocation_service import GeolocationService
from geolius.ip_validator import validate_ip_address
from geolius.models import (
    BatchIpError,
    BatchIpGeolocationResponse,
    BatchIpRequest,
    ErrorResponse,
    HealthResponse,
    IpGeolocationResponse,
)
from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns the health status of the API service.
    """
    from datetime import datetime, timezone
    

    return HealthResponse(
        status="healthy", timestamp=datetime.now(timezone.utc)
    )


@router.get(
    "/ip/{ip_address}",
    response_model=IpGeolocationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid IP address format"},
        404: {"model": ErrorResponse, "description": "IP address not found"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    },
    tags=["Geolocation"],
)
async def get_ip_geolocation(ip_address: str) -> IpGeolocationResponse:
    """
    Get geolocation for a single IP address.

    Retrieves geolocation information for a single IP address.
    Supports both IPv4 and IPv6 addresses.
    """
    _ip_address = validate_ip_address(ip_address)
    async with GeolocationService() as service:
        try:
            return await service.get_geolocation(_ip_address)
        except InvalidIpAddressError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e
        except IpAddressNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            ) from e
        except ExternalApiError as e:
            status_code = (
                status.HTTP_503_SERVICE_UNAVAILABLE
                if e.status_code == 503
                else status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            raise HTTPException(
                status_code=status_code,
                detail=str(e),
            ) from e


@router.post(
    "/ip/batch",
    response_model=BatchIpGeolocationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Geolocation"],
)
async def get_batch_ip_geolocation(
    request: BatchIpRequest,
) -> BatchIpGeolocationResponse:
    """
    Get geolocation for multiple IP addresses.

    Retrieves geolocation information for multiple IP addresses in a single request.
    Supports up to 100 IP addresses per request.
    """
    async with GeolocationService() as service:
        try:
            results, errors = await service.get_batch_geolocation(request.ip_addresses)
            error_models = [BatchIpError(**error) for error in errors]
            return BatchIpGeolocationResponse(results=results, errors=error_models)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error: {str(e)}",
            ) from e
