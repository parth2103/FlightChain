"""
FlightChain Backend Configuration

This module provides configuration settings for the FlightChain backend,
loading values from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "FlightChain API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database
    database_url: str = "mysql+pymysql://root:password@localhost:3306/flightchain"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    
    # Blockchain
    ganache_url: str = "http://127.0.0.1:7545"  # Default Ganache GUI port
    contract_address: Optional[str] = None
    private_key: Optional[str] = None  # Account private key for signing transactions
    
    # OpenSky Network API
    opensky_base_url: str = "https://opensky-network.org/api"
    opensky_auth_url: str = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
    opensky_username: Optional[str] = None
    opensky_password: Optional[str] = None
    opensky_access_token: Optional[str] = None  # Bearer token for authentication (if you have a pre-obtained token)
    opensky_client_id: Optional[str] = None  # OAuth 2.0 client ID (preferred method)
    opensky_client_secret: Optional[str] = None  # OAuth 2.0 client secret (preferred method)
    opensky_timeout: int = 30
    
    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables that aren't in the model


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience access
settings = get_settings()
