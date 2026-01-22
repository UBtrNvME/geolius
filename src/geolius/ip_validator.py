from pydantic import IPvAnyAddress

from geolius.models import IpRequestInternal


def validate_ip_address(ip_address: str) -> IPvAnyAddress:
    """Validate IP address."""
    return IpRequestInternal.model_validate({"ip_address": ip_address}).ip_address
