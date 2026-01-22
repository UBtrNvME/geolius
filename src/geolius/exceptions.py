"""Custom exceptions for the IP geolocation service."""

from pydantic import IPvAnyAddress


class GeolocationError(Exception):
    """Base exception for geolocation errors."""

    pass


class IpAddressNotFoundError(GeolocationError):
    """Raised when IP address geolocation data is not found."""

    def __init__(self, ip_address: IPvAnyAddress, message: str | None = None) -> None:
        """Initialize the exception."""
        self.ip_address = ip_address
        self.message = (
            message or f"No geolocation data available for IP address: {ip_address}"
        )
        super().__init__(self.message)


class ExternalApiError(GeolocationError):
    """Raised when external API fails."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize the exception."""
        self.status_code = status_code
        self.message = message
        super().__init__(self.message)


class RateLimitError(GeolocationError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded") -> None:
        """Initialize the exception."""
        self.message = message
        super().__init__(self.message)
