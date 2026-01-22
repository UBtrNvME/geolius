"""FastAPI dependencies for the geolocation service."""

from geolius.geolocation_service import GeolocationService

# Global service instance - initialized at application startup
_geolocation_service: GeolocationService | None = None


def get_geolocation_service() -> GeolocationService:
    """
    Dependency to provide GeolocationService instance.

    Returns the shared service instance created at application startup.
    Raises RuntimeError if the service has not been initialized.
    """
    if _geolocation_service is None:
        raise RuntimeError(
            "GeolocationService not initialized. Application may not have started properly."
        )
    return _geolocation_service


def set_geolocation_service(service: GeolocationService) -> None:
    """
    Set the global geolocation service instance.

    This should be called during application startup.
    """
    global _geolocation_service
    _geolocation_service = service


def close_geolocation_service() -> None:
    """
    Close the global geolocation service instance.

    This should be called during application shutdown.
    """
    global _geolocation_service
    if _geolocation_service is not None:
        _geolocation_service.close()
        _geolocation_service = None
