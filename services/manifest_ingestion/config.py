"""
Configuration settings for the Manifest Ingestion Service
Loads from settings.yml with environment variable overrides
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseSettings, Field
from loguru import logger


class Settings(BaseSettings):
    """Application settings with YAML and environment variable support"""
    
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
        env="MANIFEST_ROOT"
    )
    
    # Hot-reload Configuration
    hot_reload_enabled: bool = Field(default=True, env="HOT_RELOAD_ENABLED")
    hot_reload_debounce: float = Field(default=0.5, env="HOT_RELOAD_DEBOUNCE")
    
    # Context Variables
    variables_enabled: bool = Field(default=True, env="VARIABLES_ENABLED")
    variables_strict: bool = Field(default=False, env="VARIABLES_STRICT")
    
    # Registry Configuration
    registry_cache_ttl: int = Field(default=3600, env="REGISTRY_CACHE_TTL")
    auto_sync_filesystem: bool = Field(default=True, env="AUTO_SYNC_FILESYSTEM")
    max_manifests: int = Field(default=10000, env="MAX_MANIFESTS")
    
    # CORS Configuration
    cors_origins: list[str] = Field(default=["*"], env="CORS_ORIGINS")
    
    # Full YAML config (loaded dynamically)
    _yaml_config: Optional[Dict[str, Any]] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def load_yaml_config(self, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Load configuration from settings.yml
        
        Args:
            config_path: Optional path to settings file
            
        Returns:
            Dictionary of configuration values
        """
        if config_path is None:
            config_path = Path(__file__).parent / "settings.yml"
        
        if not config_path.exists():
            logger.warning(f"Settings file not found: {config_path}, using defaults")
            return {}
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                self._yaml_config = config
                logger.info(f"Loaded configuration from {config_path}")
                return config
        except Exception as e:
            logger.error(f"Failed to load settings from {config_path}: {e}")
            return {}
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Example: get("hot_reload.enabled") -> bool
        
        Args:
            key_path: Dot-separated path to config value
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        if self._yaml_config is None:
            self.load_yaml_config()
        
        if self._yaml_config is None:
            return default
        
        keys = key_path.split('.')
        value = self._yaml_config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value


# Global settings instance
settings = Settings()

# Auto-load YAML config on import
settings.load_yaml_config()