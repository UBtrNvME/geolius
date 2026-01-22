"""Main FastAPI application."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from geolius.config import settings
from geolius.dependencies import close_geolocation_service, set_geolocation_service
from geolius.exceptions import (
    ExternalApiError,
    IpAddressNotFoundError,
    RateLimitError,
)
from geolius.geolocation_service import GeolocationService
from geolius.models import ErrorDetail, ErrorResponse
from geolius.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifespan - create and cleanup service."""
    # Startup: Create and initialize service instance
    service = GeolocationService()
    service.initialize()  # Initialize database readers once at startup
    set_geolocation_service(service)
    yield

    # Shutdown: Close service
    close_geolocation_service()


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


def custom_openapi() -> dict:
    """Generate custom OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.api_title,
        version=settings.api_version,
        description=settings.api_description,
        routes=app.routes,
    )

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "IP Geolocation API",
        "version": settings.api_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
    }


@app.exception_handler(ValidationError)
async def validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    details = [
        ErrorDetail(
            loc=list(error.get("loc", [])),
            msg=error.get("msg", "Validation error"),
            type=error.get("type", "validation_error"),
        )
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(message="Validation error", details=details).model_dump(),
    )


@app.exception_handler(IpAddressNotFoundError)
async def ip_not_found_exception_handler(
    request: Request, exc: IpAddressNotFoundError
) -> JSONResponse:
    """Handle IP address not found errors."""
    detail = ErrorDetail(
        loc=["path", "ip_address"],
        msg=str(exc),
        type="ip_address_not_found_error",
    )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(
            message="IP address not found", details=[detail]
        ).model_dump(),
    )


@app.exception_handler(ExternalApiError)
async def external_api_exception_handler(
    request: Request, exc: ExternalApiError
) -> JSONResponse:
    """Handle external API errors."""
    status_code = (
        status.HTTP_503_SERVICE_UNAVAILABLE
        if exc.status_code == 503
        else status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    detail = ErrorDetail(
        loc=["server"],
        msg=str(exc),
        type="external_api_error",
    )
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            message="Service unavailable", details=[detail]
        ).model_dump(),
    )


@app.exception_handler(RateLimitError)
async def rate_limit_exception_handler(
    request: Request, exc: RateLimitError
) -> JSONResponse:
    """Handle rate limit errors."""
    detail = ErrorDetail(
        loc=["server"],
        msg=str(exc),
        type="rate_limit_error",
    )
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=ErrorResponse(
            message="Rate limit exceeded", details=[detail]
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other unhandled exceptions."""
    # Log the exception here for debugging
    detail = ErrorDetail(
        loc=["server"], msg="Internal server error", type="generic_error"
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            message="An unexpected error occurred", details=[detail]
        ).model_dump(),
    )
