"""Application configuration."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    api_title: str = "IP Geolocation API"
    api_version: str = "1.0.0"
    api_description: str = "A RESTful API service for retrieving geolocation information based on IP addresses"

    # MaxMind GeoLite2 Database Configuration
    maxmind_city_db_path: str = "data/GeoLite2-City_20260120/GeoLite2-City.mmdb"
    maxmind_asn_db_path: str = "data/GeoLite2-ASN_20260120/GeoLite2-ASN.mmdb"
    maxmind_db_timeout: float = 5.0  # Timeout for database operations

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    def get_city_db_path(self) -> Path:
        """Get absolute path to City database."""
        return Path(self.maxmind_city_db_path).expanduser().resolve()

    def get_asn_db_path(self) -> Path:
        """Get absolute path to ASN database."""
        return Path(self.maxmind_asn_db_path).expanduser().resolve()


settings = Settings()
