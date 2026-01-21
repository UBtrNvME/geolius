"""Tests for IP address validation."""

import pytest

from geolius.exceptions import InvalidIpAddressError
from geolius.ip_validator import is_private_ip, validate_ip_address


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
        with pytest.raises(InvalidIpAddressError) as exc_info:
            validate_ip_address("invalid-ip")
        assert "invalid-ip" in str(exc_info.value)

    def test_empty_string(self) -> None:
        """Test empty string."""
        with pytest.raises(InvalidIpAddressError):
            validate_ip_address("")

    def test_invalid_format(self) -> None:
        """Test invalid IP format."""
        with pytest.raises(InvalidIpAddressError):
            validate_ip_address("999.999.999.999")


class TestIsPrivateIp:
    """Test private IP detection."""

    def test_private_ipv4(self) -> None:
        """Test private IPv4 address."""
        assert is_private_ip("192.168.1.1") is True
        assert is_private_ip("10.0.0.1") is True
        assert is_private_ip("172.16.0.1") is True

    def test_public_ipv4(self) -> None:
        """Test public IPv4 address."""
        assert is_private_ip("8.8.8.8") is False
        assert is_private_ip("1.1.1.1") is False

    def test_invalid_ip(self) -> None:
        """Test invalid IP returns False."""
        assert is_private_ip("invalid") is False
