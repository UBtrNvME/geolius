"""Tests for IP address validation."""

from pydantic import ValidationError
import pytest

from geolius.ip_validator import validate_ip_address


class TestValidateIpAddress:
    """Test IP address validation."""

    def test_valid_ipv4(self) -> None:
        """Test valid IPv4 address."""
        result = validate_ip_address("8.8.8.8")
        assert str(result) == "8.8.8.8"

    def test_valid_ipv6(self) -> None:
        """Test valid IPv6 address."""
        result = validate_ip_address("2001:4860:4860::8888")
        assert str(result) == "2001:4860:4860::8888"

    def test_invalid_ip(self) -> None:
        """Test invalid IP address."""
        with pytest.raises(ValidationError) as exc_info:
            validate_ip_address("invalid-ip")
        assert "invalid-ip" in str(exc_info.value)

    def test_empty_string(self) -> None:
        """Test empty string."""
        with pytest.raises(ValidationError):
            validate_ip_address("")

    def test_invalid_format(self) -> None:
        """Test invalid IP format."""
        with pytest.raises(ValidationError):
            validate_ip_address("999.999.999.999")
