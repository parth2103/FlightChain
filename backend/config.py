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
    ganache_url: str = "http://127.0.0.1:8545"  # Default Ganache CLI port
    contract_address: Optional[str] = "0xCfEB869F69431e42cdB54A4F4f105C19C080A601"
    private_key: Optional[str] = None  # Account private key for signing transactions
    
    # CSV Flight Data
    csv_flights_path: Optional[str] = None  # Path to flights.csv file. If None, will search for it automatically.
    
    # OpenSky Network API (DEPRECATED - kept for backwards compatibility if needed)
    opensky_base_url: str = "https://opensky-network.org/api"
    opensky_auth_url: str = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
    opensky_username: Optional[str] = None
    opensky_password: Optional[str] = None
    opensky_access_token: Optional[str] = None
    opensky_client_id: Optional[str] = None
    opensky_client_secret: Optional[str] = None
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
