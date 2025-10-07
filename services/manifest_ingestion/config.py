"""
Configuration settings for the Manifest Ingestion Service
"""

import os
from pathlib import Path
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8082, env="PORT")
    log_level: str = Field(default="info", env="LOG_LEVEL")
    reload: bool = Field(default=False, env="RELOAD")
    
    # Service Configuration
    service_name: str = "manifest-ingestion"
    version: str = "1.0.0"
    
    # Manifest Configuration
    manifests_root: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent / "manifests",
        env="MANIFESTS_ROOT"
    )
    
    # Registry Configuration
    registry_cache_ttl: int = Field(default=3600, env="REGISTRY_CACHE_TTL")  # seconds
    auto_sync_filesystem: bool = Field(default=True, env="AUTO_SYNC_FILESYSTEM")
    
    # CORS Configuration
    cors_origins: list[str] = Field(default=["*"], env="CORS_ORIGINS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()